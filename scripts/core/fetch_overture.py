#!/usr/bin/env python3
"""Fetch data from Overture Maps Foundation releases.

Overture distributes global geospatial data (buildings, places, roads, land use)
as GeoParquet on S3. This script supports direct URL downloads and provides
guidance for bbox-filtered queries.

Usage:
    # Download a specific Overture release file
    python scripts/core/fetch_overture.py \
        --url "https://overturemaps-us-west-2.s3.amazonaws.com/release/2024-11-13.0/theme=places/type=place/part-00000.zstd.parquet" \
        -o data/raw/overture_places.parquet

    # Show available themes and how to query by bbox
    python scripts/core/fetch_overture.py --help-themes

    # Download places for a bbox using the Overture CLI (if installed)
    python scripts/core/fetch_overture.py --bbox -96.2,41.1,-95.8,41.4 \
        --theme places --type place -o data/raw/omaha_places.geojson
"""
from __future__ import annotations

import json
import subprocess
import shutil
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

OVERTURE_THEMES = {
    "buildings": "Building footprints with height and class attributes",
    "places": "Points of interest (businesses, amenities, landmarks)",
    "transportation": "Road segments and connectors",
    "base": "Land use, water, and administrative boundaries",
    "addresses": "Address points with structured fields",
    "divisions": "Administrative and political boundaries",
}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch Overture Maps data (buildings, places, roads, etc.)."
    )
    parser.add_argument("--url", help="Direct URL to an Overture release file")
    parser.add_argument("--bbox", help="Bounding box for filtered query: minx,miny,maxx,maxy")
    parser.add_argument("--theme", choices=list(OVERTURE_THEMES.keys()),
                        help="Overture theme (used with --bbox)")
    parser.add_argument("--type", dest="data_type", help="Overture type within theme (e.g. place, building)")
    parser.add_argument("--help-themes", action="store_true", help="Show available Overture themes")
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    if args.help_themes:
        print("Overture Maps Themes:")
        for theme, desc in OVERTURE_THEMES.items():
            print(f"  {theme:20s} {desc}")
        print("\nFor bbox queries, install overturemaps-py: pip install overturemaps")
        print("Or use DuckDB with the spatial extension for direct Parquet queries.")
        return 0

    if not args.output:
        print("ERROR: -o/--output required (unless using --help-themes)")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.url:
        print(f"Downloading Overture Maps file")
        print(f"  from: {args.url}")

        try:
            with urlopen(args.url, timeout=300) as response:
                content = response.read()
        except (HTTPError, URLError) as exc:
            print(f"Download error: {exc}")
            return 1

        out_path.write_bytes(content)
        source_url = args.url
        notes = [f"size={len(content):,} bytes"]

    elif args.bbox and args.theme:
        # Try overturemaps CLI first, fall back to guidance
        overture_cli = shutil.which("overturemaps")
        if overture_cli:
            bbox_parts = args.bbox.split(",")
            cmd = [
                overture_cli, "download",
                "--bbox", args.bbox,
                "-f", "geojson" if args.output.endswith(".geojson") else "geoparquet",
                "--type", args.data_type or args.theme,
                "-o", str(out_path),
            ]
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                return 1
            print(result.stdout)
            source_url = f"overture-cli: {args.theme}/{args.data_type or args.theme}"
            notes = [f"bbox={args.bbox}"]
        else:
            print("Overture CLI (overturemaps-py) not installed.")
            print("Install with: pip install overturemaps")
            print()
            print("Alternatively, use DuckDB:")
            dtype = args.data_type or args.theme
            print(f"""
  INSTALL spatial; LOAD spatial;
  COPY (
    SELECT * FROM read_parquet('s3://overturemaps-us-west-2/release/2024-11-13.0/theme={args.theme}/type={dtype}/*', hive_partitioning=1)
    WHERE bbox.xmin > {args.bbox.split(',')[0]}
      AND bbox.ymin > {args.bbox.split(',')[1]}
      AND bbox.xmax < {args.bbox.split(',')[2]}
      AND bbox.ymax < {args.bbox.split(',')[3]}
  ) TO '{out_path}' WITH (FORMAT 'GDAL', DRIVER 'GeoJSON');
""")
            return 1
    else:
        print("ERROR: Provide --url for direct download, or --bbox + --theme for filtered query")
        return 1

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "overture-download",
        "source_name": "Overture Maps Foundation",
        "source_type": "open-data",
        "source_url": source_url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": out_path.suffix.lstrip("."),
        "notes": notes,
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
