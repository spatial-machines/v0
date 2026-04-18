from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load(path: Path):
    """Load tabular or spatial file as a DataFrame."""
    import geopandas as gpd
    import pandas as pd

    ext = path.suffix.lower()
    if ext in {".gpkg", ".shp", ".geojson"}:
        return gpd.read_file(path)
    elif ext == ".csv":
        return pd.read_csv(path)
    elif ext == ".parquet":
        return pd.read_parquet(path)
    else:
        raise ValueError(f"unsupported format: {ext}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate tabular data: row count, required fields, and null coverage."
    )
    parser.add_argument("input", help="Path to dataset file")
    parser.add_argument(
        "--required-fields",
        help="Comma-separated list of fields that must exist"
    )
    parser.add_argument(
        "--check-nulls",
        help="Comma-separated fields to check null coverage for"
    )
    parser.add_argument(
        "--min-rows", type=int, default=1,
        help="Minimum expected row count (default: 1)"
    )
    parser.add_argument(
        "--null-warn-pct", type=float, default=50.0,
        help="Warn if null percentage exceeds this threshold (default: 50)"
    )
    parser.add_argument(
        "--numeric-fields",
        help="Comma-separated fields that must be numeric (int or float) dtype"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to write JSON result"
    )
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    df = load(src)
    checks = []
    warnings = []

    # --- Row count ---
    n_rows = len(df)
    if n_rows >= args.min_rows:
        checks.append({
            "check": "row_count",
            "status": "PASS",
            "message": f"{n_rows} rows (min: {args.min_rows})",
            "count": n_rows,
        })
    else:
        checks.append({
            "check": "row_count",
            "status": "FAIL",
            "message": f"{n_rows} rows < minimum {args.min_rows}",
            "count": n_rows,
        })

    # --- Column listing ---
    columns = [c for c in df.columns if c != "geometry"]
    checks.append({
        "check": "columns",
        "status": "PASS",
        "message": f"{len(columns)} columns: {columns}",
        "columns": columns,
    })

    # --- Required fields ---
    if args.required_fields:
        required = [f.strip() for f in args.required_fields.split(",")]
        missing = [f for f in required if f not in df.columns]
        present = [f for f in required if f in df.columns]
        if missing:
            checks.append({
                "check": "required_fields",
                "status": "FAIL",
                "message": f"missing required fields: {missing}",
                "missing": missing,
                "present": present,
            })
        else:
            checks.append({
                "check": "required_fields",
                "status": "PASS",
                "message": f"all {len(required)} required fields present",
                "present": present,
            })

    # --- Null coverage ---
    if args.check_nulls:
        null_fields = [f.strip() for f in args.check_nulls.split(",")]
        for field in null_fields:
            if field not in df.columns:
                checks.append({
                    "check": f"null_coverage:{field}",
                    "status": "WARN",
                    "message": f"field '{field}' not found — cannot check nulls",
                })
                warnings.append(f"field '{field}' not found for null check")
                continue

            null_count = int(df[field].isna().sum())
            non_null = n_rows - null_count
            null_pct = round(100 * null_count / max(n_rows, 1), 1)
            coverage_pct = round(100 - null_pct, 1)

            if null_pct > args.null_warn_pct:
                status = "WARN"
                warnings.append(
                    f"{field}: {null_count}/{n_rows} null ({null_pct}%) — "
                    f"exceeds {args.null_warn_pct}% threshold"
                )
            else:
                status = "PASS"

            checks.append({
                "check": f"null_coverage:{field}",
                "status": status,
                "message": f"{field}: {non_null}/{n_rows} non-null ({coverage_pct}% coverage)",
                "null_count": null_count,
                "non_null_count": non_null,
                "null_pct": null_pct,
                "coverage_pct": coverage_pct,
            })

    # --- Numeric field types ---
    if args.numeric_fields:
        numeric_fields = [f.strip() for f in args.numeric_fields.split(",")]
        for field in numeric_fields:
            if field not in df.columns:
                checks.append({
                    "check": f"numeric_type:{field}",
                    "status": "WARN",
                    "message": f"field '{field}' not found — cannot check type",
                })
                warnings.append(f"field '{field}' not found for numeric type check")
                continue

            if np.issubdtype(df[field].dtype, np.number):
                checks.append({
                    "check": f"numeric_type:{field}",
                    "status": "PASS",
                    "message": f"{field} is numeric (dtype: {df[field].dtype})",
                    "dtype": str(df[field].dtype),
                })
            else:
                checks.append({
                    "check": f"numeric_type:{field}",
                    "status": "FAIL",
                    "message": f"{field} is NOT numeric (dtype: {df[field].dtype}) — graduated styling will fail",
                    "dtype": str(df[field].dtype),
                })

    # --- Summarize ---
    statuses = [c["status"] for c in checks]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "WARN" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    report = {
        "check": "tabular_qa",
        "source": str(src),
        "checked_at": datetime.now(UTC).isoformat(),
        "row_count": n_rows,
        "overall_status": overall,
        "checks": checks,
        "warnings": warnings,
    }

    print(f"tabular QA [{overall}]: {src.name} — {n_rows} rows, {len(columns)} columns")
    for c in checks:
        print(f"  [{c['status']}] {c['check']}: {c['message']}")

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        print(f"wrote result -> {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
