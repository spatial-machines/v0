from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Join tabular data to a spatial dataset.")
    parser.add_argument("spatial", help="Path to spatial file (gpkg, shp, geojson)")
    parser.add_argument("table", help="Path to tabular file (csv, parquet)")
    parser.add_argument("--spatial-key", required=True, help="Join key column in spatial data")
    parser.add_argument("--table-key", required=True, help="Join key column in tabular data")
    parser.add_argument("-o", "--output", help="Output path (default: data/processed/<stem>_joined.gpkg)")
    parser.add_argument("--how", default="left", choices=["left", "inner"], help="Join type (default: left)")
    args = parser.parse_args()

    spatial_path = Path(args.spatial).expanduser().resolve()
    table_path = Path(args.table).expanduser().resolve()

    if not spatial_path.exists():
        print(f"spatial input not found: {spatial_path}")
        return 1
    if not table_path.exists():
        print(f"table input not found: {table_path}")
        return 1

    gdf = gpd.read_file(spatial_path)
    ext = table_path.suffix.lower()
    if ext == ".csv":
        # Read CSV with type inference so numeric columns survive into the
        # GeoPackage.  Only the join key is cast to string below.
        df = pd.read_csv(table_path)
    elif ext == ".parquet":
        df = pd.read_parquet(table_path)
    else:
        print(f"unsupported table format: {ext}")
        return 2

    # Validate keys exist
    if args.spatial_key not in gdf.columns:
        print(f"spatial key '{args.spatial_key}' not found. columns: {list(gdf.columns)}")
        return 3
    if args.table_key not in df.columns:
        print(f"table key '{args.table_key}' not found. columns: {list(df.columns)}")
        return 3

    # Ensure join keys are strings for reliable matching
    gdf[args.spatial_key] = gdf[args.spatial_key].astype(str)
    df[args.table_key] = df[args.table_key].astype(str)

    # Diagnostics before join
    spatial_keys = set(gdf[args.spatial_key])
    table_keys = set(df[args.table_key])
    matched = spatial_keys & table_keys
    spatial_only = spatial_keys - table_keys
    table_only = table_keys - spatial_keys
    table_dupes = df[args.table_key].duplicated().sum()

    diagnostics = {
        "spatial_rows": len(gdf),
        "table_rows": len(df),
        "spatial_unique_keys": len(spatial_keys),
        "table_unique_keys": len(table_keys),
        "matched_keys": len(matched),
        "spatial_unmatched": len(spatial_only),
        "table_unmatched": len(table_only),
        "table_duplicate_keys": int(table_dupes),
        "match_rate_pct": round(100 * len(matched) / max(len(spatial_keys), 1), 1),
    }

    # Report diagnostics
    print("--- join diagnostics ---")
    for k, v in diagnostics.items():
        print(f"  {k}: {v}")

    if table_dupes > 0:
        print(f"WARNING: {table_dupes} duplicate key(s) in table; join may produce extra rows")
    if diagnostics["spatial_unmatched"] > 0:
        print(f"WARNING: {diagnostics['spatial_unmatched']} spatial features have no table match")
    if diagnostics["table_unmatched"] > 0:
        print(f"WARNING: {diagnostics['table_unmatched']} table rows have no spatial match")

    # Perform join
    joined = gdf.merge(df, left_on=args.spatial_key, right_on=args.table_key, how=args.how)

    # Drop redundant table key if it differs from spatial key
    if args.table_key != args.spatial_key and args.table_key in joined.columns:
        joined = joined.drop(columns=[args.table_key])

    # Output
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_path = PROCESSED_DIR / f"{spatial_path.stem}_joined.gpkg"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    joined.to_file(out_path, driver="GPKG")

    log = {
        "step": "join_data",
        "spatial_source": str(spatial_path),
        "table_source": str(table_path),
        "spatial_key": args.spatial_key,
        "table_key": args.table_key,
        "join_type": args.how,
        "output": str(out_path),
        "result_rows": len(joined),
        "result_columns": [c for c in joined.columns if c != "geometry"],
        "diagnostics": diagnostics,
        "joined_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_suffix(".join.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"wrote {len(joined)} rows -> {out_path}")
    print(f"log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
