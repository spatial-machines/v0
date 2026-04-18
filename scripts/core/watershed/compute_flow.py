#!/usr/bin/env python3
"""Compute D8 flow direction and flow accumulation from a filled DEM.

Usage:
    python compute_flow.py \\
        --dem outputs/qgis/data/dem_filled.tif \\
        --output-dir outputs/qgis/data \\
        [--output-stats outputs/tables/flow_stats.json]
"""

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import numpy as np

# pysheds uses deprecated np.in1d removed in NumPy 2.x
if not hasattr(np, "in1d"):
    np.in1d = np.isin


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute D8 flow direction and flow accumulation")
    parser.add_argument("--dem", required=True, help="Filled DEM GeoTIFF (output of preprocess_dem)")
    parser.add_argument("--output-dir", required=True, help="Directory for output rasters")
    parser.add_argument("--output-stats", default=None, help="Output JSON stats")
    args = parser.parse_args()

    dem_path = Path(args.dem).resolve()
    if not dem_path.exists():
        print(f"ERROR: Filled DEM not found: {dem_path}")
        return 1

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    from pysheds.grid import Grid

    # ── Load filled DEM ───────────────────────────────────────────
    print(f"Loading filled DEM: {dem_path}")
    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))
    print(f"  Shape: {dem.shape}")

    # ── D8 flow direction (ESRI convention) ───────────────────────
    # ESRI dirmap: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    print("Computing D8 flow direction...")
    fdir = grid.flowdir(dem, dirmap=dirmap)

    fdir_path = out_dir / "flow_dir.tif"
    grid.to_raster(fdir, str(fdir_path))
    print(f"  Saved flow direction: {fdir_path}")

    # ── Flow accumulation ─────────────────────────────────────────
    print("Computing flow accumulation...")
    acc = grid.accumulation(fdir, dirmap=dirmap)

    acc_path = out_dir / "flow_acc.tif"
    grid.to_raster(acc, str(acc_path))
    print(f"  Saved flow accumulation: {acc_path}")

    # ── Stats ─────────────────────────────────────────────────────
    acc_arr = np.array(acc, dtype=np.float64)
    total_cells = int(np.prod(acc_arr.shape))
    max_acc = int(np.nanmax(acc_arr))
    mean_acc = round(float(np.nanmean(acc_arr)), 2)
    median_acc = round(float(np.nanmedian(acc_arr)), 2)

    # High-accumulation cells (potential channels)
    p99 = float(np.nanpercentile(acc_arr, 99))
    high_acc_cells = int(np.sum(acc_arr >= p99))

    stats = {
        "step": "compute_flow",
        "source": str(dem_path),
        "output_dir": str(out_dir),
        "dirmap_convention": "ESRI",
        "total_cells": total_cells,
        "max_accumulation": max_acc,
        "mean_accumulation": mean_acc,
        "median_accumulation": median_acc,
        "p99_accumulation": round(p99, 2),
        "high_acc_cells_above_p99": high_acc_cells,
        "outputs": {
            "flow_dir": str(fdir_path),
            "flow_acc": str(acc_path),
        },
        "computed_at": datetime.now(UTC).isoformat(),
    }

    if args.output_stats:
        stats_path = Path(args.output_stats).resolve()
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(json.dumps(stats, indent=2))
        print(f"  Saved stats: {stats_path}")

    print(f"Flow routing complete. Max accumulation: {max_acc} cells.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
