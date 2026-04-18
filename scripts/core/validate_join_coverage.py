from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate join/coverage quality of a joined dataset."
    )
    parser.add_argument("input", help="Path to joined dataset (gpkg, csv, parquet)")
    parser.add_argument(
        "--join-fields",
        help="Comma-separated fields that came from the tabular join "
             "(used to measure how many features have join data)"
    )
    parser.add_argument(
        "--key-field",
        help="Join key field to check for uniqueness"
    )
    parser.add_argument(
        "--expected-total", type=int,
        help="Expected total feature count (for coverage percentage)"
    )
    parser.add_argument(
        "--coverage-warn-pct", type=float, default=25.0,
        help="Warn if join coverage is below this percentage (default: 25)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to write JSON result"
    )
    args = parser.parse_args()

    import geopandas as gpd
    import pandas as pd

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    ext = src.suffix.lower()
    if ext in {".gpkg", ".shp", ".geojson"}:
        df = gpd.read_file(src)
    elif ext == ".csv":
        df = pd.read_csv(src)
    elif ext == ".parquet":
        df = pd.read_parquet(src)
    else:
        print(f"unsupported format: {ext}")
        return 2

    checks = []
    warnings = []
    total_rows = len(df)

    # --- Key uniqueness ---
    if args.key_field:
        if args.key_field not in df.columns:
            checks.append({
                "check": "key_field_exists",
                "status": "FAIL",
                "message": f"key field '{args.key_field}' not found",
            })
        else:
            n_unique = df[args.key_field].nunique()
            n_dupes = total_rows - n_unique
            if n_dupes == 0:
                checks.append({
                    "check": "key_uniqueness",
                    "status": "PASS",
                    "message": f"{n_unique} unique keys, no duplicates",
                    "unique_keys": n_unique,
                    "duplicates": 0,
                })
            else:
                checks.append({
                    "check": "key_uniqueness",
                    "status": "WARN",
                    "message": f"{n_dupes} duplicate key values ({n_unique} unique of {total_rows} rows)",
                    "unique_keys": n_unique,
                    "duplicates": n_dupes,
                })
                warnings.append(f"{n_dupes} duplicate keys on '{args.key_field}'")

    # --- Join field coverage ---
    if args.join_fields:
        join_fields = [f.strip() for f in args.join_fields.split(",")]
        missing_fields = [f for f in join_fields if f not in df.columns]
        if missing_fields:
            checks.append({
                "check": "join_fields_exist",
                "status": "FAIL",
                "message": f"join fields not found: {missing_fields}",
                "missing": missing_fields,
            })

        present_fields = [f for f in join_fields if f in df.columns]
        if present_fields:
            # Coverage = rows where at least one join field is non-null
            has_any = df[present_fields].notna().any(axis=1)
            covered = int(has_any.sum())
            uncovered = total_rows - covered
            coverage_pct = round(100 * covered / max(total_rows, 1), 1)

            if coverage_pct < args.coverage_warn_pct:
                status = "WARN"
                warnings.append(
                    f"join coverage {covered}/{total_rows} ({coverage_pct}%) "
                    f"is below {args.coverage_warn_pct}% threshold"
                )
            else:
                status = "PASS"

            checks.append({
                "check": "join_coverage",
                "status": status,
                "message": (
                    f"{covered}/{total_rows} features have join data "
                    f"({coverage_pct}% coverage)"
                ),
                "covered": covered,
                "uncovered": uncovered,
                "coverage_pct": coverage_pct,
                "join_fields_checked": present_fields,
            })

            # Per-field breakdown
            for field in present_fields:
                non_null = int(df[field].notna().sum())
                field_pct = round(100 * non_null / max(total_rows, 1), 1)
                checks.append({
                    "check": f"join_field_coverage:{field}",
                    "status": "PASS" if field_pct >= args.coverage_warn_pct else "WARN",
                    "message": f"{field}: {non_null}/{total_rows} non-null ({field_pct}%)",
                    "non_null": non_null,
                    "coverage_pct": field_pct,
                })

    # --- Expected total ---
    if args.expected_total is not None:
        if total_rows == args.expected_total:
            checks.append({
                "check": "expected_row_count",
                "status": "PASS",
                "message": f"row count {total_rows} matches expected {args.expected_total}",
            })
        else:
            checks.append({
                "check": "expected_row_count",
                "status": "WARN",
                "message": f"row count {total_rows} != expected {args.expected_total}",
            })
            warnings.append(f"row count {total_rows} != expected {args.expected_total}")

    # --- Summarize ---
    statuses = [c["status"] for c in checks]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "WARN" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    report = {
        "check": "join_coverage_qa",
        "source": str(src),
        "checked_at": datetime.now(UTC).isoformat(),
        "total_rows": total_rows,
        "overall_status": overall,
        "checks": checks,
        "warnings": warnings,
    }

    print(f"join coverage QA [{overall}]: {src.name} — {total_rows} rows")
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
