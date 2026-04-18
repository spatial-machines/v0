from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    import geopandas as gpd
except Exception:
    gpd = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SPATIAL_EXTS = {".gpkg", ".geojson", ".shp", ".json"}
TABULAR_EXTS = {".csv", ".xlsx", ".xls", ".parquet"}


def inspect_tabular(path: Path) -> dict:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"unsupported tabular format: {path.suffix}")

    return {
        "kind": "tabular",
        "rows": int(len(df)),
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
    }


def inspect_spatial(path: Path) -> dict:
    if gpd is None:
        raise RuntimeError("geopandas is not available")

    gdf = gpd.read_file(path)
    return {
        "kind": "spatial",
        "rows": int(len(gdf)),
        "columns": list(gdf.columns),
        "geometry_type": sorted({str(x) for x in gdf.geometry.geom_type.dropna().unique()}) if "geometry" in gdf else [],
        "crs": str(gdf.crs) if gdf.crs else None,
        "bounds": list(gdf.total_bounds) if len(gdf) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a dataset and write an inspection JSON summary."
    )
    parser.add_argument("--input", required=True, help="Path to the dataset file to inspect")
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for the inspection JSON (default: same directory as input)"
    )
    args = parser.parse_args()

    path = Path(args.input).expanduser().resolve()
    if not path.exists():
        print(f"missing dataset: {path}")
        return 2

    ext = path.suffix.lower()
    try:
        if ext in TABULAR_EXTS:
            summary = inspect_tabular(path)
        elif ext in SPATIAL_EXTS:
            summary = inspect_spatial(path)
        elif ext == ".zip":
            summary = {
                "kind": "archive",
                "rows": None,
                "columns": [],
                "note": "zip archive retrieved; inspect extracted contents during processing",
            }
        else:
            summary = {
                "kind": "unknown",
                "rows": None,
                "columns": [],
                "note": f"unsupported extension for direct inspection: {ext}",
            }
    except Exception as exc:
        summary = {
            "kind": "error",
            "rows": None,
            "columns": [],
            "note": str(exc),
        }

    if args.output_dir:
        out_dir = Path(args.output_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{path.stem}.inspection.json"
    else:
        out = path.with_name(f"{path.stem}.inspection.json")
    out.write_text(json.dumps(summary, indent=2))
    print(f"inspection {out}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
