#!/usr/bin/env python3
"""Clip a raster to a vector mask or bounding box.

Usage:
    # Vector mask clip:
    python raster_clip.py \\
        --raster data/rasters/elevation.tif \\
        --mask data/processed/study_area.gpkg \\
        --output outputs/rasters/elevation_clipped.tif

    # Bounding box clip:
    python raster_clip.py \\
        --raster data/rasters/elevation.tif \\
        --mask "-94.5,38.5,-93.0,39.5" \\
        --output outputs/rasters/elevation_bbox.tif
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clip a raster to a vector mask or bounding box."
    )
    parser.add_argument("--raster", required=True, help="Input raster (GeoTIFF)")
    parser.add_argument(
        "--mask",
        required=True,
        help='Vector mask (GeoPackage) or bbox as "minx,miny,maxx,maxy"',
    )
    parser.add_argument("--output", required=True, help="Output clipped GeoTIFF")
    parser.add_argument(
        "--nodata",
        type=float,
        default=None,
        help="Override nodata value for output (default: inherit from input)",
    )
    parser.add_argument(
        "--all-touched",
        action="store_true",
        help="Include all pixels touching the mask geometry (default: only fully inside)",
    )
    parser.add_argument(
        "--crop",
        action="store_true",
        default=True,
        help="Crop output extent to mask bounds (default: True)",
    )
    parser.add_argument(
        "--no-crop",
        action="store_true",
        help="Keep original raster extent with masked values set to nodata",
    )
    args = parser.parse_args()

    import rasterio
    from rasterio.mask import mask as rio_mask
    from rasterio.transform import from_bounds
    from rasterio.windows import from_bounds as window_from_bounds

    raster_path = Path(args.raster).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not raster_path.exists():
        print(f"ERROR: Raster not found: {raster_path}")
        return 1

    warnings = []
    assumptions = []
    crop = not args.no_crop

    # Determine if mask is a bbox string or a vector file
    mask_str = args.mask.strip()
    is_bbox = False
    bbox = None
    try:
        parts = [float(x) for x in mask_str.split(",")]
        if len(parts) == 4:
            is_bbox = True
            bbox = tuple(parts)  # (minx, miny, maxx, maxy)
    except ValueError:
        pass

    print(f"Loading raster: {raster_path}")
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        raster_nodata = src.nodata
        raster_shape = (src.height, src.width)
        raster_bounds = src.bounds
        profile = src.profile.copy()
        n_bands = src.count

    print(f"  Shape: {raster_shape}, CRS: {raster_crs}, bands: {n_bands}, nodata: {raster_nodata}")

    nodata_out = args.nodata if args.nodata is not None else raster_nodata
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if is_bbox:
        # Bounding box clip using rasterio window
        print(f"Clipping to bounding box: {bbox}")
        minx, miny, maxx, maxy = bbox

        with rasterio.open(raster_path) as src:
            # If raster has CRS and bbox might be in different CRS, just use as-is
            # (user is responsible for bbox CRS matching raster)
            window = src.window(minx, miny, maxx, maxy)
            window = window.intersection(
                rasterio.windows.Window(0, 0, src.width, src.height)
            )
            data = src.read(window=window)
            out_transform = src.window_transform(window)

        out_profile = profile.copy()
        out_profile.update(
            height=data.shape[1],
            width=data.shape[2],
            transform=out_transform,
            compress="lzw",
        )
        if nodata_out is not None:
            out_profile["nodata"] = nodata_out

        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(data)

        clip_method = "bbox"
        out_shape = data.shape[1:]
        assumptions.append(f"Bbox assumed to be in raster CRS ({raster_crs})")

    else:
        # Vector mask clip
        import geopandas as gpd

        mask_path = Path(mask_str).expanduser().resolve()
        if not mask_path.exists():
            print(f"ERROR: Mask file not found: {mask_path}")
            return 1

        print(f"Loading mask: {mask_path}")
        mask_gdf = gpd.read_file(mask_path)
        print(f"  {len(mask_gdf)} features, CRS: {mask_gdf.crs}")

        # CRS alignment
        if mask_gdf.crs is None:
            warnings.append("Mask has no CRS — assuming same as raster")
            mask_gdf = mask_gdf.set_crs(raster_crs)
        elif raster_crs is None:
            warnings.append("Raster has no CRS — cannot reproject mask")
        elif mask_gdf.crs != raster_crs:
            print(f"  CRS mismatch: mask={mask_gdf.crs}, raster={raster_crs}")
            print(f"  Reprojecting mask to raster CRS...")
            mask_gdf = mask_gdf.to_crs(raster_crs)
            warnings.append(f"Mask reprojected from {mask_gdf.crs} to {raster_crs}")
            assumptions.append(f"Mask reprojected to raster CRS for clipping")

        # Dissolve to single geometry for clipping
        from shapely.ops import unary_union
        geometries = [geom for geom in mask_gdf.geometry if geom is not None and not geom.is_empty]
        if not geometries:
            print("ERROR: Mask has no valid geometries")
            return 1

        clip_geom = unary_union(geometries)
        shapes = [clip_geom.__geo_interface__]

        print(f"Clipping raster with {len(geometries)} geometry(ies)...")
        with rasterio.open(raster_path) as src:
            out_data, out_transform = rio_mask(
                src,
                shapes,
                crop=crop,
                nodata=nodata_out,
                all_touched=args.all_touched,
            )
            out_profile = src.profile.copy()

        out_profile.update(
            height=out_data.shape[1],
            width=out_data.shape[2],
            transform=out_transform,
            compress="lzw",
        )
        if nodata_out is not None:
            out_profile["nodata"] = nodata_out

        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(out_data)

        clip_method = "vector"
        out_shape = out_data.shape[1:]

    print(f"Output: {output_path}")
    print(f"  Output shape: {out_shape}, nodata: {nodata_out}")

    # Build log
    log = {
        "step": "raster_clip",
        "raster": str(raster_path),
        "mask": args.mask,
        "output": str(output_path),
        "clip_method": clip_method,
        "all_touched": args.all_touched,
        "crop": crop,
        "raster_shape_in": list(raster_shape),
        "raster_shape_out": list(out_shape),
        "raster_crs": str(raster_crs),
        "n_bands": n_bands,
        "nodata_in": raster_nodata,
        "nodata_out": nodata_out,
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.clip.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
