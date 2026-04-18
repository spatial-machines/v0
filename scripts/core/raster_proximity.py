#!/usr/bin/env python3
"""Compute a proximity (distance) raster from vector features.

Each output pixel contains the distance (in meters or CRS units) to the
nearest feature geometry.  Uses rasterization followed by
scipy.ndimage.distance_transform_edt — fully open-source, no GDAL
proximity required.

Usage:
    python raster_proximity.py \\
        --features data/processed/roads.gpkg \\
        --reference-raster data/rasters/dem.tif \\
        --output outputs/rasters/road_proximity.tif

    python raster_proximity.py \\
        --features data/processed/schools.gpkg \\
        --reference-raster data/rasters/population.tif \\
        --output outputs/rasters/school_distance.tif \\
        --max-distance 5000
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute distance raster to nearest vector feature."
    )
    parser.add_argument("--features", required=True, help="Input vector features (GeoPackage)")
    parser.add_argument(
        "--reference-raster",
        required=True,
        help="Reference raster for extent, resolution, and CRS",
    )
    parser.add_argument("--output", required=True, help="Output distance GeoTIFF")
    parser.add_argument(
        "--max-distance",
        type=float,
        default=None,
        help="Cap maximum distance value (pixels beyond this get the max value)",
    )
    parser.add_argument(
        "--burn-value",
        type=float,
        default=1.0,
        help="Value used when rasterizing features (default: 1)",
    )
    args = parser.parse_args()

    import rasterio
    from rasterio.features import rasterize
    from rasterio.warp import reproject, Resampling, calculate_default_transform
    from scipy.ndimage import distance_transform_edt
    import geopandas as gpd

    features_path = Path(args.features).expanduser().resolve()
    ref_path = Path(args.reference_raster).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    for p, label in [(features_path, "features"), (ref_path, "reference-raster")]:
        if not p.exists():
            print(f"ERROR: {label} not found: {p}")
            return 1

    warnings = []
    assumptions = []

    # Load reference raster metadata
    print(f"Loading reference raster: {ref_path.name}")
    with rasterio.open(ref_path) as src:
        ref_crs = src.crs
        ref_transform = src.transform
        ref_shape = (src.height, src.width)
        ref_nodata = src.nodata
        px_size_x = abs(ref_transform.a)  # Pixel width in CRS units
        px_size_y = abs(ref_transform.e)  # Pixel height in CRS units

    print(f"  Shape: {ref_shape}, CRS: {ref_crs}")
    print(f"  Pixel size: {px_size_x:.4f} × {px_size_y:.4f} CRS units")

    # Estimate meters per CRS unit for output labeling
    from pyproj import CRS as ProjCRS
    crs_obj = ProjCRS.from_user_input(ref_crs)
    if crs_obj.is_geographic:
        # Approximate degrees → meters at center
        warnings.append(
            "Reference raster uses geographic CRS — distances are in degrees, not meters. "
            "For accurate distances, reproject raster to a projected CRS first."
        )
        meters_per_unit = 111320.0  # rough meters per degree at equator
        distance_label = "degrees (approx)"
    else:
        meters_per_unit = 1.0
        distance_label = "meters (projected CRS)"

    # Load features
    print(f"Loading features: {features_path.name}")
    gdf = gpd.read_file(features_path)
    print(f"  {len(gdf)} features, CRS: {gdf.crs}")

    # CRS alignment
    if gdf.crs is None:
        warnings.append("Features have no CRS — assuming same as reference raster")
        gdf = gdf.set_crs(ref_crs)
    elif gdf.crs != ref_crs:
        print(f"  CRS mismatch — reprojecting features to {ref_crs}...")
        gdf = gdf.to_crs(ref_crs)
        warnings.append(f"Features reprojected from {gdf.crs} to {ref_crs}")

    # Remove empty/null geometries
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    if len(gdf) == 0:
        print("ERROR: No valid geometries found in features")
        return 1
    print(f"  {len(gdf)} valid geometries")

    # Rasterize features
    print("Rasterizing features...")
    shapes = [(geom.__geo_interface__, args.burn_value) for geom in gdf.geometry]

    rasterized = rasterize(
        shapes,
        out_shape=ref_shape,
        transform=ref_transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True,
    )

    n_target_pixels = int(np.sum(rasterized > 0))
    print(f"  {n_target_pixels:,} target pixels rasterized")

    if n_target_pixels == 0:
        warnings.append("No features fell within the reference raster extent — all pixels will be max distance")

    # Distance transform
    # EDT works on background (0) pixels → want distance FROM features (1s)
    print("Computing distance transform (EDT)...")
    background = (rasterized == 0).astype(np.uint8)

    # sampling argument scales EDT to actual pixel sizes
    sampling = (px_size_y, px_size_x)  # (row spacing, col spacing) in CRS units
    distance = distance_transform_edt(background, sampling=sampling)

    # Convert to meters if geographic
    if crs_obj.is_geographic:
        distance = distance * meters_per_unit

    # Cap at max distance
    if args.max_distance is not None:
        distance = np.clip(distance, 0, args.max_distance)
        print(f"  Capped at max distance: {args.max_distance}")

    dist_min = float(np.min(distance))
    dist_max = float(np.max(distance))
    print(f"  Distance range: {dist_min:.2f} – {dist_max:.2f} {distance_label}")

    distance_f32 = distance.astype(np.float32)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": ref_shape[1],
        "height": ref_shape[0],
        "count": 1,
        "crs": ref_crs,
        "transform": ref_transform,
        "nodata": None,
        "compress": "lzw",
    }

    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(distance_f32[np.newaxis, :, :])

    print(f"Output: {output_path}")

    # Build log
    log = {
        "step": "raster_proximity",
        "features": str(features_path),
        "reference_raster": str(ref_path),
        "output": str(output_path),
        "n_features": len(gdf),
        "n_target_pixels": n_target_pixels,
        "max_distance": args.max_distance,
        "distance_range": [dist_min, dist_max],
        "distance_units": distance_label,
        "pixel_size": [px_size_x, px_size_y],
        "raster_shape": list(ref_shape),
        "crs": str(ref_crs),
        "crs_is_geographic": bool(crs_obj.is_geographic),
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.proximity.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
