from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load(path: Path):
    """Load spatial or tabular file, returning (gdf_or_df, is_spatial)."""
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
        description="Add derived fields using simple expressions."
    )
    parser.add_argument("input", help="Path to spatial or tabular file")
    parser.add_argument(
        "-d", "--derive", action="append", required=True,
        help="Derivation: new_col=expression (pandas eval syntax). Repeatable."
    )
    parser.add_argument("-o", "--output", help="Output path (overwrites input format by default)")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    data, is_spatial = load(src)
    steps = []
    warnings = []

    for spec in args.derive:
        if "=" not in spec:
            print(f"invalid derivation (must be col=expr): {spec}")
            return 2
        col, expr = spec.split("=", 1)
        col = col.strip()
        expr = expr.strip()
        try:
            data[col] = data.eval(expr)
            steps.append(f"derived {col} = {expr}")
        except Exception as exc:
            warnings.append(f"derivation failed for {col}: {exc}")
            print(f"WARNING: derivation failed for {col}: {exc}")

    # Output
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_path = src

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if is_spatial:
        data.to_file(out_path, driver="GPKG")
    elif out_path.suffix.lower() == ".parquet":
        data.to_parquet(out_path, index=False)
    else:
        data.to_csv(out_path, index=False)

    log = {
        "step": "derive_fields",
        "source": str(src),
        "output": str(out_path),
        "derivations": args.derive,
        "processing_steps": steps,
        "warnings": warnings,
        "derived_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.derivation.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"wrote {len(data)} rows -> {out_path}")
    print(f"log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
