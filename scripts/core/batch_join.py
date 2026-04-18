#!/usr/bin/env python3
"""Join multiple tabular files to a single spatial base in one step.

Usage:
    python scripts/batch_join.py \
        --spatial data/processed/ks_tracts.gpkg \
        --tables data/raw/pop.csv,data/raw/poverty.csv,data/raw/income.csv \
        --join-field GEOID \
        -o data/processed/ks_tracts_enriched.gpkg
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_table(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path)
    elif ext == ".parquet":
        return pd.read_parquet(path)
    else:
        raise ValueError(f"unsupported table format: {ext}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Join multiple tabular files to a spatial base dataset."
    )
    parser.add_argument("--spatial", required=True, help="Path to spatial base file (gpkg, shp, geojson)")
    parser.add_argument(
        "--tables", required=True,
        help="Comma-separated list of tabular file paths (CSV, parquet)",
    )
    parser.add_argument("--join-field", required=True, help="Common join key field name")
    parser.add_argument("-o", "--output", required=True, help="Output GeoPackage path")
    args = parser.parse_args()

    spatial_path = Path(args.spatial).expanduser().resolve()
    if not spatial_path.exists():
        print(f"spatial file not found: {spatial_path}")
        return 1

    table_paths = [Path(p.strip()).expanduser().resolve() for p in args.tables.split(",")]
    for tp in table_paths:
        if not tp.exists():
            print(f"table file not found: {tp}")
            return 1

    gdf = gpd.read_file(spatial_path)
    if args.join_field not in gdf.columns:
        print(f"join field '{args.join_field}' not found in spatial data. columns: {list(gdf.columns)}")
        return 2

    gdf[args.join_field] = gdf[args.join_field].astype(str)

    per_table_diagnostics = []
    total_fields_added = 0

    for tp in table_paths:
        table_label = tp.stem
        print(f"\n--- joining {table_label} ---")

        df = load_table(tp)
        if args.join_field not in df.columns:
            print(f"  WARNING: join field '{args.join_field}' not found in {tp.name}, skipping")
            per_table_diagnostics.append({
                "table": str(tp),
                "status": "skipped",
                "reason": f"join field '{args.join_field}' not found",
            })
            continue

        df[args.join_field] = df[args.join_field].astype(str)

        # Check for field name conflicts and prefix with table stem
        existing_cols = set(gdf.columns)
        rename_map = {}
        for col in df.columns:
            if col == args.join_field:
                continue
            if col in existing_cols:
                new_name = f"{table_label}_{col}"
                rename_map[col] = new_name
                print(f"  field conflict: '{col}' renamed to '{new_name}'")
        if rename_map:
            df = df.rename(columns=rename_map)

        # Compute match diagnostics
        spatial_keys = set(gdf[args.join_field])
        table_keys = set(df[args.join_field])
        matched = spatial_keys & table_keys
        spatial_only = len(spatial_keys - table_keys)
        table_only = len(table_keys - spatial_keys)
        match_pct = round(100 * len(matched) / max(len(spatial_keys), 1), 1)

        fields_added = [c for c in df.columns if c != args.join_field]
        total_fields_added += len(fields_added)

        diag = {
            "table": str(tp),
            "status": "joined",
            "table_rows": len(df),
            "matched_keys": len(matched),
            "spatial_unmatched": spatial_only,
            "table_unmatched": table_only,
            "match_rate_pct": match_pct,
            "fields_added": fields_added,
            "fields_renamed": rename_map,
        }
        per_table_diagnostics.append(diag)

        print(f"  matched: {len(matched)}/{len(spatial_keys)} ({match_pct}%)")
        if spatial_only > 0:
            print(f"  WARNING: {spatial_only} spatial features have no match in {table_label}")
        if table_only > 0:
            print(f"  WARNING: {table_only} table rows have no spatial match")

        # Perform the join
        gdf = gdf.merge(df, on=args.join_field, how="left")

    # Output
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")

    # Aggregate coverage
    non_geo_cols = [c for c in gdf.columns if c not in ("geometry", args.join_field)]
    null_coverage = {col: int(gdf[col].isna().sum()) for col in non_geo_cols}

    print(f"\n=== batch join complete ===")
    print(f"  tables joined: {len(per_table_diagnostics)}")
    print(f"  fields added: {total_fields_added}")
    print(f"  output rows: {len(gdf)}")

    log = {
        "step": "batch_join",
        "spatial_source": str(spatial_path),
        "join_field": args.join_field,
        "output": str(out_path),
        "result_rows": len(gdf),
        "result_columns": [c for c in gdf.columns if c != "geometry"],
        "tables_joined": len(per_table_diagnostics),
        "total_fields_added": total_fields_added,
        "per_table_diagnostics": per_table_diagnostics,
        "null_coverage": null_coverage,
        "joined_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.batch_join.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"wrote {out_path}")
    print(f"log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
