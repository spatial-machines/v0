from __future__ import annotations

import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"


def normalize_column(name: str) -> str:
    """Lowercase, strip whitespace, replace non-alnum with underscore."""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def parse_field_map(raw: str) -> dict[str, str]:
    mapping = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if "=" in pair:
            old, new = pair.split("=", 1)
            mapping[old.strip()] = new.strip()
    return mapping


def parse_type_map(raw: str) -> dict[str, str]:
    """Parse 'col1=int,col2=float' into a type coercion dict."""
    mapping = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if "=" in pair:
            col, dtype = pair.split("=", 1)
            mapping[col.strip()] = dtype.strip()
    return mapping


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Process a tabular dataset.")
    parser.add_argument("input", help="Path to input table (csv, xlsx, parquet)")
    parser.add_argument("-o", "--output", help="Output path (default: data/interim/<stem>.csv)")
    parser.add_argument("--fields", help="Comma-separated fields to keep (after normalization)")
    parser.add_argument("--rename", help="Rename fields: old1=new1,old2=new2 (after normalization)")
    parser.add_argument("--types", help="Type coercion: col1=int,col2=float,col3=str")
    parser.add_argument("--no-normalize", action="store_true", help="Skip column name normalization")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    ext = src.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(src, dtype=str)
    elif ext in {".xlsx", ".xls"}:
        df = pd.read_excel(src, dtype=str)
    elif ext == ".parquet":
        df = pd.read_parquet(src)
    else:
        print(f"unsupported format: {ext}")
        return 2

    steps = []
    warnings = []

    # Normalize column names
    if not args.no_normalize:
        original_cols = list(df.columns)
        df.columns = [normalize_column(c) for c in df.columns]
        steps.append(f"normalized column names: {dict(zip(original_cols, df.columns))}")

    # Field selection
    if args.fields:
        keep = [f.strip() for f in args.fields.split(",")]
        missing = [f for f in keep if f not in df.columns]
        if missing:
            warnings.append(f"requested fields not found (skipped): {missing}")
        keep = [f for f in keep if f in df.columns]
        df = df[keep]
        steps.append(f"selected fields: {keep}")

    # Rename
    if args.rename:
        rename_map = parse_field_map(args.rename)
        df = df.rename(columns=rename_map)
        steps.append(f"renamed fields: {rename_map}")

    # Type coercion
    if args.types:
        type_map = parse_type_map(args.types)
        for col, dtype in type_map.items():
            if col not in df.columns:
                warnings.append(f"type coercion skipped for missing column: {col}")
                continue
            try:
                df[col] = df[col].astype(dtype)
                steps.append(f"coerced {col} to {dtype}")
            except (ValueError, TypeError) as exc:
                warnings.append(f"type coercion failed for {col}: {exc}")

    # Output
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_path = INTERIM_DIR / f"{src.stem}.csv"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".parquet":
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)

    log = {
        "step": "process_table",
        "source": str(src),
        "output": str(out_path),
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "processing_steps": steps,
        "warnings": warnings,
        "processed_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.processing.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"wrote {len(df)} rows -> {out_path}")
    print(f"log: {log_path}")
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
