from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _smart_round(value, field_name: str = ""):
    """Round a value based on field name heuristics."""
    if value is None or (isinstance(value, float) and not (value == value)):  # NaN check
        return value
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
        description="Rank top and bottom features for a metric and export a clean table."
    )
    parser.add_argument("input", help="Path to spatial or tabular file")
    parser.add_argument("field", help="Numeric field to rank by")
    parser.add_argument("--n", type=int, default=5, help="Number of top/bottom entries (default: 5)")
    parser.add_argument(
        "--label", default="NAME",
        help="Column to use as feature label in output (default: NAME)"
    )
    parser.add_argument(
        "--extra-fields",
        help="Comma-separated additional fields to include in the output table"
    )
    parser.add_argument(
        "--where",
        help="Optional pandas query expression to filter rows before ranking"
    )
    parser.add_argument("-o", "--output", help="Output CSV path (default: outputs/tables/<stem>_top_<field>.csv)")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    data, is_spatial = load(src)
    warnings = []
    assumptions = []

    if args.field not in data.columns:
        print(f"field not found: {args.field}")
        return 2

    if args.label not in data.columns:
        print(f"label column not found: {args.label}")
        print(f"available: {[c for c in data.columns if c != 'geometry']}")
        return 2

    # Coerce ranking field to numeric if needed
    if not pd.api.types.is_numeric_dtype(data[args.field]):
        data[args.field] = pd.to_numeric(data[args.field], errors="coerce")
        assumptions.append(f"coerced '{args.field}' to numeric")

    # Coerce extra fields to numeric if needed
    if args.extra_fields:
        for ef in [f.strip() for f in args.extra_fields.split(",")]:
            if ef in data.columns and not pd.api.types.is_numeric_dtype(data[ef]):
                data[ef] = pd.to_numeric(data[ef], errors="coerce")

    # Optional filter
    if args.where:
        before = len(data)
        data = data.query(args.where)
        assumptions.append(f"filtered with: {args.where} ({before} -> {len(data)} rows)")

    # Drop nulls for ranking
    null_count = int(data[args.field].isna().sum())
    if null_count > 0:
        pct = round(null_count / len(data) * 100, 1)
        warnings.append(f"{null_count}/{len(data)} rows ({pct}%) have null '{args.field}' — excluded from ranking")
    ranked = data.dropna(subset=[args.field])

    if len(ranked) == 0:
        print(f"no non-null values for '{args.field}' — cannot rank")
        return 3

    n = min(args.n, len(ranked))
    if n < args.n:
        warnings.append(f"only {len(ranked)} non-null rows, showing top/bottom {n} instead of {args.n}")

    # Build output columns
    out_cols = [args.label, args.field]
    if args.extra_fields:
        extras = [f.strip() for f in args.extra_fields.split(",")]
        missing_extras = [f for f in extras if f not in data.columns]
        if missing_extras:
            warnings.append(f"extra fields not found (skipped): {missing_extras}")
            extras = [f for f in extras if f in data.columns]
        out_cols.extend(extras)

    # Top N
    top = ranked.nlargest(n, args.field)[out_cols].copy()
    top.insert(0, "rank_type", "top")
    top.insert(1, "rank", range(1, len(top) + 1))

    # Bottom N
    bottom = ranked.nsmallest(n, args.field)[out_cols].copy()
    bottom.insert(0, "rank_type", "bottom")
    bottom.insert(1, "rank", range(1, len(bottom) + 1))

    result = pd.concat([top, bottom], ignore_index=True)

    # Round numeric value columns
    numeric_out_cols = [c for c in out_cols if c not in (args.label,) and pd.api.types.is_numeric_dtype(result[c])]
    for col in numeric_out_cols:
        result[col] = result[col].apply(lambda v: _smart_round(v, col))

    # Output
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "tables"
        out_path = out_dir / f"{src.stem}_top_{args.field}.csv"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False)

    log = {
        "step": "analyze_top_n",
        "source": str(src),
        "output": str(out_path),
        "field": args.field,
        "label": args.label,
        "n": n,
        "filter": args.where,
        "total_rows": len(data),
        "ranked_rows": len(ranked),
        "null_excluded": null_count,
        "assumptions": assumptions,
        "warnings": warnings,
        "analyzed_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.top-n.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"top/bottom {n} by {args.field} ({len(ranked)} ranked) -> {out_path}")
    print(f"log: {log_path}")
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
