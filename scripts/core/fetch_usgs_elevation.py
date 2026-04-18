#!/usr/bin/env python3
"""Fetch USGS elevation data (DEM) from The National Map.

Downloads Digital Elevation Model tiles for a bounding box.

Usage:
    python scripts/core/fetch_usgs_elevation.py \
        --bbox -105.5,39.5,-104.5,40.5 \
        -o data/raw/denver_dem.tif

    python scripts/core/fetch_usgs_elevation.py \
        --bbox -96.2,41.1,-95.8,41.4 --dataset "1 arc-second" \
        -o data/raw/omaha_dem.tif
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlencode

TNM_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch USGS elevation data from The National Map."
    )
    parser.add_argument("--bbox", required=True,
                        help="Bounding box: minx,miny,maxx,maxy (decimal degrees)")
    parser.add_argument("--dataset", default="National Elevation Dataset (NED) 1/3 arc-second",
                        help="TNM dataset name")
    parser.add_argument("--format", dest="prod_format", default="GeoTIFF",
                        help="Product format (default: GeoTIFF)")
    parser.add_argument("--max-results", type=int, default=5, help="Max products to list")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    params = urlencode({
        "bbox": args.bbox,
        "datasets": args.dataset,
        "prodFormats": args.prod_format,
        "max": args.max_results,
    })
    url = f"{TNM_URL}?{params}"

    print(f"Searching USGS TNM for elevation data")
    print(f"  bbox: {args.bbox}")
    print(f"  dataset: {args.dataset}")

    try:
        with urlopen(url, timeout=60) as response:
            data = json.load(response)
    except (HTTPError, URLError) as exc:
        print(f"Error searching TNM: {exc}")
        return 1

    items = data.get("items", [])
    if not items:
        print("WARNING: No elevation products found for this bbox/dataset")
        print("  Try a different --dataset or wider --bbox")
        return 1

    print(f"  found {len(items)} products")
    for i, item in enumerate(items):
        print(f"    [{i}] {item.get('title', 'untitled')} ({item.get('sizeInBytes', 0) / 1e6:.1f} MB)")

    # Download the first matching product
    download_url = items[0].get("downloadURL")
    if not download_url:
        print("ERROR: No download URL in first result")
        return 1

    print(f"  downloading: {download_url}")
    try:
        with urlopen(download_url, timeout=300) as response:
            content = response.read()
    except (HTTPError, URLError) as exc:
        print(f"Error downloading: {exc}")
        return 1

    out_path.write_bytes(content)

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "tnm-download",
        "source_name": f"USGS {args.dataset}",
        "source_type": "federal-download",
        "source_url": download_url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": args.prod_format.lower(),
        "notes": [f"bbox={args.bbox}", f"size={len(content):,} bytes",
                  f"title={items[0].get('title', '')}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path} ({len(content) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
