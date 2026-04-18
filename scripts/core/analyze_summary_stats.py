from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _smart_round(value, field_name: str = ""):
    """Round a stat value based on field name heuristics."""
    if value is None:
        return None
    v = float(value)
    fn = field_name.lower()
    if any(k in fn for k in ("rate", "pct", "percent", "ratio", "proportion")):
        return round(v, 2)
    elif any(k in fn for k in ("income", "cost", "price", "rent", "value", "median_h")):
        return int(round(v))
    elif any(k in fn for k in ("count", "total", "pop", "universe", "number")):
        return int(round(v))
    elif abs(v) >= 1000:
        return int(round(v))
    elif abs(v) >= 1:
        return round(v, 1)
    else:
        return round(v, 2)


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
        description="Compute summary statistics for numeric fields in a dataset."
    )
    parser.add_argument("input", help="Path to spatial or tabular file")
    parser.add_argument(
        "--fields", required=True,
        help="Comma-separated numeric fields to summarize"
    )
    parser.add_argument(
        "--where",
        help="Optional pandas query expression to filter rows before summarizing"
    )
    parser.add_argument("-o", "--output", help="Output CSV path (default: outputs/tables/<stem>_summary.csv)")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    data, is_spatial = load(src)
    fields = [f.strip() for f in args.fields.split(",")]
    warnings = []
    assumptions = []

    # Validate fields exist
    missing = [f for f in fields if f not in data.columns]
    if missing:
        print(f"fields not found in dataset: {missing}")
        return 2

    # Coerce fields to numeric where possible
    for f in fields:
        if not pd.api.types.is_numeric_dtype(data[f]):
            coerced = pd.to_numeric(data[f], errors="coerce")
            non_null_before = data[f].notna().sum()
            non_null_after = coerced.notna().sum()
            if non_null_after > 0:
                data[f] = coerced
                assumptions.append(f"coerced '{f}' to numeric ({non_null_after} valid values)")
            else:
                warnings.append(f"'{f}' could not be converted to numeric — skipping")

    non_numeric = [f for f in fields if not pd.api.types.is_numeric_dtype(data[f])]
    if non_numeric:
        warnings.append(f"skipping non-numeric fields: {non_numeric}")
        print(f"WARNING: skipping non-numeric fields: {non_numeric}")
        fields = [f for f in fields if f not in non_numeric]
    if not fields:
        print("no numeric fields to summarize")
        return 2

    # Optional filter
    if args.where:
        before = len(data)
        data = data.query(args.where)
        assumptions.append(f"filtered with: {args.where} ({before} -> {len(data)} rows)")

    # Check for nulls in target fields
    for f in fields:
        null_count = int(data[f].isna().sum())
        total = len(data)
        if null_count > 0:
            pct = round(null_count / total * 100, 1)
            warnings.append(f"{f}: {null_count}/{total} values are null ({pct}%) — excluded from stats")

    # Compute summary statistics per field (build row-by-row to handle all-null fields)
    rows = []
    for f in fields:
        col = data[f]
        non_null = col.dropna()
        row = {"field": f}
        if len(non_null) > 0:
            row["count"] = len(non_null)
            row["mean"] = _smart_round(non_null.mean(), f)
            row["std"] = _smart_round(non_null.std(), f) if len(non_null) > 1 else None
            row["min"] = _smart_round(non_null.min(), f)
            row["p25"] = _smart_round(non_null.quantile(0.25), f)
            row["median"] = _smart_round(non_null.quantile(0.50), f)
            row["p75"] = _smart_round(non_null.quantile(0.75), f)
            row["max"] = _smart_round(non_null.max(), f)
        else:
            row.update({k: None for k in ["count", "mean", "std", "min", "p25", "median", "p75", "max"]})
            row["count"] = 0
        row["null_count"] = int(col.isna().sum())
        row["non_null_count"] = int(col.notna().sum())
        rows.append(row)
    stats = pd.DataFrame(rows)

    # Output
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "tables"
        out_path = out_dir / f"{src.stem}_summary.csv"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    stats.to_csv(out_path, index=False)

    log = {
        "step": "analyze_summary_stats",
        "source": str(src),
        "output": str(out_path),
        "fields": fields,
        "filter": args.where,
        "total_rows": len(data),
        "assumptions": assumptions,
        "warnings": warnings,
        "analyzed_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.summary-stats.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"summary stats for {len(fields)} fields ({len(data)} rows) -> {out_path}")
    print(f"log: {log_path}")
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
