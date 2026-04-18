from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"


def parse_field_map(raw: str) -> dict[str, str]:
    """Parse 'old1=new1,old2=new2' into a rename dict."""
    mapping = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if "=" in pair:
            old, new = pair.split("=", 1)
            mapping[old.strip()] = new.strip()
    return mapping


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Process a vector dataset.")
    parser.add_argument("input", help="Path to input spatial file (shp, gpkg, geojson)")
    parser.add_argument("-o", "--output", help="Output path (default: data/interim/<stem>.gpkg)")
    parser.add_argument("--set-crs", help="Assign CRS if missing (e.g. EPSG:4326)")
    parser.add_argument("--reproject", help="Reproject to this CRS (e.g. EPSG:4326)")
    parser.add_argument("--fields", help="Comma-separated fields to keep (geometry always kept)")
    parser.add_argument("--rename", help="Rename fields: old1=new1,old2=new2")
    parser.add_argument("--where", help="Row filter expression (pandas query syntax)")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    gdf = gpd.read_file(src)
    steps = []
    warnings = []

    # CRS handling
    if gdf.crs is None and args.set_crs:
        gdf = gdf.set_crs(args.set_crs)
        steps.append(f"set CRS to {args.set_crs}")
    elif gdf.crs is None and not args.set_crs:
        warnings.append("CRS is missing and --set-crs was not provided; output will have no CRS")

    if args.reproject:
        if gdf.crs is None:
            print("error: cannot reproject without a CRS; use --set-crs first")
            return 2
        gdf = gdf.to_crs(args.reproject)
        steps.append(f"reprojected to {args.reproject}")

    # Field selection
    if args.fields:
        keep = [f.strip() for f in args.fields.split(",")]
        keep = [f for f in keep if f in gdf.columns]
        if "geometry" not in keep:
            keep.append("geometry")
        gdf = gdf[keep]
        steps.append(f"selected fields: {keep}")

    # Field rename
    if args.rename:
        rename_map = parse_field_map(args.rename)
        gdf = gdf.rename(columns=rename_map)
        steps.append(f"renamed fields: {rename_map}")

    # Row filter
    if args.where:
        before = len(gdf)
        gdf = gdf.query(args.where)
        steps.append(f"filtered rows: {before} -> {len(gdf)} ({args.where})")

    # Output
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_path = INTERIM_DIR / f"{src.stem}.gpkg"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")

    log = {
        "step": "process_vector",
        "source": str(src),
        "output": str(out_path),
        "rows": len(gdf),
        "columns": [c for c in gdf.columns if c != "geometry"],
        "crs": str(gdf.crs) if gdf.crs else None,
        "processing_steps": steps,
        "warnings": warnings,
        "processed_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_suffix(".processing.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"wrote {len(gdf)} rows -> {out_path}")
    print(f"log: {log_path}")
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
