#!/usr/bin/env python3
"""Delineate a watershed catchment from flow grids and a pour point.

Snaps the pour point to the nearest high-accumulation cell, delineates
the upstream catchment, and extracts a threshold-based stream network.

Usage:
    python delineate_watersheds.py \\
        --flow-dir outputs/qgis/data/flow_dir.tif \\
        --flow-acc outputs/qgis/data/flow_acc.tif \\
        --pour-point "30.0,-97.0" \\
        --output-dir outputs/qgis/data \\
        [--snap-distance 500] \\
        [--stream-threshold 0.01] \\
        [--output-stats outputs/tables/watershed_stats.json]
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
    parser = argparse.ArgumentParser(description="Delineate watershed from pour point")
    parser.add_argument("--flow-dir", required=True, help="Flow direction GeoTIFF")
    parser.add_argument("--flow-acc", required=True, help="Flow accumulation GeoTIFF")
    parser.add_argument("--pour-point", required=True,
                        help="Pour point as 'lat,lon' or path to .gpkg point file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    parser.add_argument("--snap-distance", type=int, default=500,
                        help="Max snap distance in grid cells (default: 500)")
    parser.add_argument("--stream-threshold", type=float, default=0.01,
                        help="Stream extraction threshold as fraction of max accumulation (default: 0.01)")
    parser.add_argument("--output-stats", default=None, help="Output JSON stats")
    args = parser.parse_args()

    fdir_path = Path(args.flow_dir).resolve()
    facc_path = Path(args.flow_acc).resolve()
    for p, name in [(fdir_path, "flow direction"), (facc_path, "flow accumulation")]:
        if not p.exists():
            print(f"ERROR: {name} not found: {p}")
            return 1

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    import geopandas as gpd
    from pysheds.grid import Grid
    from shapely.geometry import shape, Point, mapping
    from shapely.ops import unary_union

    # ── Load grids ────────────────────────────────────────────────
    print(f"Loading flow direction: {fdir_path}")
    grid = Grid.from_raster(str(fdir_path))
    fdir = grid.read_raster(str(fdir_path))

    print(f"Loading flow accumulation: {facc_path}")
    acc = grid.read_raster(str(facc_path))
    acc_arr = np.array(acc, dtype=np.float64)

    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)

    # ── Parse pour point ──────────────────────────────────────────
    pp_str = args.pour_point.strip()
    if pp_str.endswith(".gpkg") or pp_str.endswith(".shp") or pp_str.endswith(".geojson"):
        pp_gdf = gpd.read_file(pp_str)
        pt = pp_gdf.geometry.iloc[0]
        pour_x, pour_y = pt.x, pt.y
    else:
        parts = pp_str.split(",")
        if len(parts) != 2:
            print("ERROR: --pour-point must be 'lat,lon' or a path to a point file")
            return 1
        pour_y, pour_x = float(parts[0].strip()), float(parts[1].strip())

    print(f"Pour point: ({pour_y}, {pour_x})")

    # ── Snap pour point to high-accumulation cell ─────────────────
    print(f"Snapping pour point (max {args.snap_distance} cells)...")
    x_snap, y_snap = grid.snap_to_mask(acc > np.nanpercentile(acc_arr, 95),
                                        (pour_x, pour_y),
                                        return_dist=False)
    print(f"  Snapped to: ({y_snap}, {x_snap})")

    # Save snapped pour point
    crs = _get_crs_from_raster(fdir_path)
    pp_snapped = gpd.GeoDataFrame(
        {"name": ["pour_point_snapped"], "orig_lat": [pour_y], "orig_lon": [pour_x]},
        geometry=[Point(x_snap, y_snap)],
        crs=crs,
    )
    pp_path = out_dir / "pour_point_snapped.gpkg"
    pp_snapped.to_file(pp_path, driver="GPKG")
    print(f"  Saved snapped pour point: {pp_path}")

    # ── Delineate catchment ───────────────────────────────────────
    print("Delineating catchment...")
    catch = grid.catchment(x=x_snap, y=y_snap, fdir=fdir, dirmap=dirmap, xytype='coordinate')
    catch_arr = np.array(catch, dtype=np.uint8)

    # Vectorize catchment to polygon
    from rasterio.features import shapes as rio_shapes
    from rasterio.transform import from_bounds

    affine = grid.affine
    mask = catch_arr.astype(bool)
    cell_count = int(np.sum(mask))

    polys = []
    for geom, val in rio_shapes(catch_arr, mask=mask, transform=affine):
        if val == 1:
            polys.append(shape(geom))

    if not polys:
        print("ERROR: No catchment polygon generated — check pour point location")
        return 1

    watershed_poly = unary_union(polys)
    ws_gdf = gpd.GeoDataFrame({"name": ["watershed"]}, geometry=[watershed_poly], crs=crs)

    ws_path = out_dir / "watershed_boundary.gpkg"
    ws_gdf.to_file(ws_path, driver="GPKG")
    print(f"  Saved watershed boundary: {ws_path}")

    # ── Extract stream network ────────────────────────────────────
    max_acc = float(np.nanmax(acc_arr))
    threshold = max_acc * args.stream_threshold
    print(f"Extracting streams (threshold: {threshold:.0f} cells, {args.stream_threshold*100:.1f}% of max)...")

    stream_mask = (acc_arr >= threshold) & mask
    stream_cells = int(np.sum(stream_mask))

    stream_polys = []
    for geom, val in rio_shapes(stream_mask.astype(np.uint8), mask=stream_mask, transform=affine):
        if val == 1:
            stream_polys.append(shape(geom))

    if stream_polys:
        from shapely.ops import linemerge
        stream_union = unary_union(stream_polys)
        # Convert polygons to lines (centerlines approximation via boundary)
        if stream_union.geom_type in ("Polygon", "MultiPolygon"):
            stream_lines = stream_union.boundary
        else:
            stream_lines = stream_union

        streams_gdf = gpd.GeoDataFrame(
            {"name": ["stream_network"]},
            geometry=[stream_lines],
            crs=crs,
        )
        streams_path = out_dir / "stream_network.gpkg"
        streams_gdf.to_file(streams_path, driver="GPKG")
        print(f"  Saved stream network: {streams_path}")
    else:
        streams_path = None
        print("  WARNING: No stream cells above threshold")

    # ── Compute stats ─────────────────────────────────────────────
    cell_area_m2 = abs(affine.a * affine.e)
    area_km2 = round(cell_count * cell_area_m2 / 1e6, 4)
    perimeter_km = round(watershed_poly.length / 1000, 4) if crs and "utm" in str(crs).lower() else round(watershed_poly.length, 6)
    centroid = watershed_poly.centroid
    bounds = watershed_poly.bounds

    # Accumulation at snapped pour point
    row_idx = int((y_snap - affine.f) / affine.e)
    col_idx = int((x_snap - affine.c) / affine.a)
    row_idx = max(0, min(row_idx, acc_arr.shape[0] - 1))
    col_idx = max(0, min(col_idx, acc_arr.shape[1] - 1))
    pp_accumulation = int(acc_arr[row_idx, col_idx])

    stats = {
        "step": "delineate_watersheds",
        "pour_point_original": {"lat": pour_y, "lon": pour_x},
        "pour_point_snapped": {"x": float(x_snap), "y": float(y_snap)},
        "pour_point_accumulation": pp_accumulation,
        "area_km2": area_km2,
        "perimeter_km": perimeter_km,
        "centroid": {"x": round(centroid.x, 6), "y": round(centroid.y, 6)},
        "bounding_box": {"minx": bounds[0], "miny": bounds[1], "maxx": bounds[2], "maxy": bounds[3]},
        "cell_count": cell_count,
        "cell_area_m2": round(cell_area_m2, 2),
        "stream_threshold": args.stream_threshold,
        "stream_cells": stream_cells,
        "crs": str(crs),
        "outputs": {
            "watershed_boundary": str(ws_path),
            "pour_point_snapped": str(pp_path),
            "stream_network": str(streams_path) if streams_path else None,
        },
        "delineated_at": datetime.now(UTC).isoformat(),
    }

    if args.output_stats:
        stats_path = Path(args.output_stats).resolve()
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(json.dumps(stats, indent=2))
        print(f"  Saved stats: {stats_path}")

    print(f"Watershed delineation complete. Area: {area_km2} km², {cell_count} cells.")
    return 0


def _get_crs_from_raster(path):
    """Extract CRS string from a raster file."""
    import rasterio
    with rasterio.open(path) as src:
        if src.crs:
            return str(src.crs)
    return "EPSG:4326"


if __name__ == "__main__":
    raise SystemExit(main())
