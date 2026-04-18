#!/usr/bin/env python3
"""Preprocess a DEM for hydrological analysis.

Fills pits/sinks, resolves flats, and derives terrain products
(slope, aspect, hillshade) needed by downstream watershed steps.

Usage:
    python preprocess_dem.py \\
        --dem data/raw/elevation.tif \\
        --output-dir outputs/qgis/data \\
        [--output-stats outputs/tables/preprocess_stats.json]
"""

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import numpy as np
import rasterio

# pysheds uses deprecated np.in1d removed in NumPy 2.x
if not hasattr(np, "in1d"):
    np.in1d = np.isin


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess DEM: fill pits/sinks, resolve flats, derive terrain products")
    parser.add_argument("--dem", required=True, help="Input DEM GeoTIFF")
    parser.add_argument("--output-dir", required=True, help="Directory for output rasters")
    parser.add_argument("--output-stats", default=None, help="Output JSON metadata/stats")
    args = parser.parse_args()

    dem_path = Path(args.dem).resolve()
    if not dem_path.exists():
        print(f"ERROR: DEM not found: {dem_path}")
        return 1

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    from pysheds.grid import Grid

    # ── Load DEM ──────────────────────────────────────────────────
    print(f"Loading DEM: {dem_path}")
    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))
    print(f"  Shape: {dem.shape}, dtype: {dem.dtype}")
    print(f"  Elevation range: {float(np.nanmin(dem)):.2f} – {float(np.nanmax(dem)):.2f}")

    # ── Read source metadata via rasterio ─────────────────────────
    with rasterio.open(dem_path) as src:
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs

    cell_x = abs(transform.a)
    cell_y = abs(transform.e)
    rows, cols = dem.shape

    # ── Fill pits & depressions ───────────────────────────────────
    print("Filling pits...")
    pit_filled = grid.fill_pits(dem)
    print("Filling depressions...")
    flooded = grid.fill_depressions(pit_filled)
    print("Resolving flats...")
    inflated = grid.resolve_flats(flooded)

    filled_path = out_dir / "dem_filled.tif"
    grid.to_raster(inflated, str(filled_path))
    print(f"  Saved filled DEM: {filled_path}")

    # ── Derive slope (degrees) ────────────────────────────────────
    print("Computing slope...")
    elev = np.array(inflated, dtype=np.float64)
    dy, dx = np.gradient(elev, cell_y, cell_x)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad).astype(np.float32)

    slope_path = out_dir / "slope.tif"
    _write_geotiff(slope_path, slope_deg, transform, crs)
    print(f"  Saved slope: {slope_path}")

    # ── Derive aspect (degrees from north, clockwise) ─────────────
    print("Computing aspect...")
    aspect = np.degrees(np.arctan2(-dx, dy)).astype(np.float32)
    aspect[aspect < 0] += 360.0
    aspect_path = out_dir / "aspect.tif"
    _write_geotiff(aspect_path, aspect, transform, crs)
    print(f"  Saved aspect: {aspect_path}")

    # ── Derive hillshade ──────────────────────────────────────────
    print("Computing hillshade...")
    azimuth_rad = np.radians(315.0)
    altitude_rad = np.radians(45.0)
    hillshade = (
        np.cos(altitude_rad) * np.cos(slope_rad)
        + np.sin(altitude_rad) * np.sin(slope_rad)
        * np.cos(azimuth_rad - np.arctan2(-dx, dy))
    )
    hillshade = (np.clip(hillshade, 0, 1) * 255).astype(np.uint8)
    hs_path = out_dir / "hillshade.tif"
    _write_geotiff(hs_path, hillshade, transform, crs, dtype="uint8")
    print(f"  Saved hillshade: {hs_path}")

    # ── Stats ─────────────────────────────────────────────────────
    stats = {
        "step": "preprocess_dem",
        "source": str(dem_path),
        "output_dir": str(out_dir),
        "rows": rows,
        "cols": cols,
        "cell_size_x": cell_x,
        "cell_size_y": cell_y,
        "elevation_min": round(float(np.nanmin(elev)), 2),
        "elevation_max": round(float(np.nanmax(elev)), 2),
        "elevation_mean": round(float(np.nanmean(elev)), 2),
        "slope_max_deg": round(float(np.nanmax(slope_deg)), 2),
        "slope_mean_deg": round(float(np.nanmean(slope_deg)), 2),
        "outputs": {
            "dem_filled": str(filled_path),
            "slope": str(slope_path),
            "aspect": str(aspect_path),
            "hillshade": str(hs_path),
        },
        "processed_at": datetime.now(UTC).isoformat(),
    }

    if args.output_stats:
        stats_path = Path(args.output_stats).resolve()
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(json.dumps(stats, indent=2))
        print(f"  Saved stats: {stats_path}")

    print("DEM preprocessing complete.")
    return 0


def _write_geotiff(path, array, transform, crs, dtype="float32"):
    """Write a 2D numpy array as a single-band GeoTIFF."""
    rows, cols = array.shape
    with rasterio.open(
        path, "w", driver="GTiff",
        height=rows, width=cols, count=1,
        dtype=dtype, crs=crs, transform=transform,
    ) as dst:
        dst.write(array, 1)


if __name__ == "__main__":
    raise SystemExit(main())
