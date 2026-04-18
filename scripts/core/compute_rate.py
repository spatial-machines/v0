#!/usr/bin/env python3
"""Compute derived rates from Census numerator/denominator pairs.

Optionally propagates margin of error and flags unreliable estimates.

Usage:
    python scripts/compute_rate.py data/raw/ks_poverty.csv \
        --numerator B17001_002E --denominator B17001_001E \
        --output-field poverty_rate -o data/processed/ks_poverty_rate.csv

    python scripts/compute_rate.py data/raw/ks_poverty.csv \
        --numerator B17001_002E --denominator B17001_001E \
        --moe-numerator B17001_002M --moe-denominator B17001_001M \
        --output-field poverty_rate -o data/processed/ks_poverty_rate.csv
"""
from __future__ import annotations

import json
import math
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load(path: Path):
    """Load spatial or tabular file, returning (df, is_spatial)."""
    ext = path.suffix.lower()
    if ext in {".gpkg", ".shp", ".geojson"}:
        return gpd.read_file(path), True
    elif ext == ".csv":
        return pd.read_csv(path), False
    elif ext == ".parquet":
        return pd.read_parquet(path), False
    else:
        raise ValueError(f"unsupported format: {ext}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute a derived rate from numerator/denominator fields with optional MOE propagation."
    )
    parser.add_argument("input", help="Path to input file (CSV, GeoPackage, etc.)")
    parser.add_argument("--numerator", required=True, help="Numerator field name")
    parser.add_argument("--denominator", required=True, help="Denominator field name")
    parser.add_argument("--output-field", required=True, help="Name for the computed rate field")
    parser.add_argument("--moe-numerator", help="Margin of error field for numerator")
    parser.add_argument("--moe-denominator", help="Margin of error field for denominator")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    data, is_spatial = load(src)
    warnings = []

    # Validate fields exist
    for field_name, field_val in [("numerator", args.numerator), ("denominator", args.denominator)]:
        if field_val not in data.columns:
            print(f"{field_name} field '{field_val}' not found. columns: {list(data.columns)}")
            return 2

    if args.moe_numerator and args.moe_numerator not in data.columns:
        print(f"moe-numerator field '{args.moe_numerator}' not found. columns: {list(data.columns)}")
        return 2
    if args.moe_denominator and args.moe_denominator not in data.columns:
        print(f"moe-denominator field '{args.moe_denominator}' not found. columns: {list(data.columns)}")
        return 2

    # Coerce to numeric
    num = pd.to_numeric(data[args.numerator], errors="coerce")
    denom = pd.to_numeric(data[args.denominator], errors="coerce")

    # Compute rate (percent), guarding against division by zero
    rate = num / denom.replace(0, float("nan")) * 100
    data[args.output_field] = rate

    zero_denom = int((denom == 0).sum())
    null_rate = int(rate.isna().sum())
    if zero_denom > 0:
        warnings.append(f"{zero_denom} rows had zero denominator — rate set to NaN")

    # MOE propagation
    has_moe = args.moe_numerator and args.moe_denominator
    if has_moe:
        moe_num = pd.to_numeric(data[args.moe_numerator], errors="coerce")
        moe_denom = pd.to_numeric(data[args.moe_denominator], errors="coerce")

        # Propagated MOE for a ratio: sqrt(MOE_num^2 + (rate * MOE_denom)^2) / denominator
        rate_decimal = rate / 100
        moe_propagated = (
            (moe_num ** 2 + (rate_decimal * moe_denom) ** 2).pow(0.5)
            / denom.replace(0, float("nan"))
            * 100
        )
        moe_field = f"{args.output_field}_moe"
        data[moe_field] = moe_propagated

        # Reliability flag: MOE > 50% of estimate is unreliable
        reliability_field = f"{args.output_field}_reliable"
        data[reliability_field] = True
        unreliable_mask = moe_propagated > (rate.abs() * 0.5)
        data.loc[unreliable_mask, reliability_field] = False
        # Also mark NaN rates as unreliable
        data.loc[rate.isna(), reliability_field] = False

        unreliable_count = int(unreliable_mask.sum())
        if unreliable_count > 0:
            warnings.append(
                f"{unreliable_count} rows flagged as unreliable (MOE > 50% of estimate)"
            )

    # Output
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if is_spatial:
        data.to_file(out_path, driver="GPKG")
    elif out_path.suffix.lower() == ".parquet":
        data.to_parquet(out_path, index=False)
    else:
        data.to_csv(out_path, index=False)

    log = {
        "step": "compute_rate",
        "source": str(src),
        "output": str(out_path),
        "numerator": args.numerator,
        "denominator": args.denominator,
        "output_field": args.output_field,
        "moe_propagated": has_moe,
        "total_rows": len(data),
        "null_rate_rows": null_rate,
        "zero_denominator_rows": zero_denom,
        "warnings": warnings,
        "computed_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.rate.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"computed {args.output_field} for {len(data)} rows -> {out_path}")
    if has_moe:
        print(f"  MOE propagated to {moe_field}, reliability flagged in {reliability_field}")
    print(f"log: {log_path}")
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
