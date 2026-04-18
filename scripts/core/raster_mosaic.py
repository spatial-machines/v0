#!/usr/bin/env python3
"""Merge/mosaic multiple raster tiles into a single raster.

Usage:
    # Glob pattern:
    python raster_mosaic.py \\
        --inputs "data/rasters/tiles/*.tif" \\
        --output outputs/rasters/mosaic.tif

    # Explicit paths:
    python raster_mosaic.py \\
        --inputs tile1.tif tile2.tif tile3.tif \\
        --output outputs/rasters/mosaic.tif \\
        --resampling bilinear
"""

import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


RESAMPLING_METHODS = [
    "nearest", "bilinear", "cubic", "cubic_spline",
    "lanczos", "average", "mode", "gauss",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mosaic/merge multiple raster tiles into one raster."
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Input rasters (space-separated paths or a single glob pattern)",
    )
    parser.add_argument("--output", required=True, help="Output mosaic GeoTIFF")
    parser.add_argument(
        "--nodata",
        type=float,
        default=None,
        help="Override nodata value (default: inherit from first raster)",
    )
    parser.add_argument(
        "--resampling",
        default="nearest",
        choices=RESAMPLING_METHODS,
        help="Resampling method for reprojection (default: nearest)",
    )
    parser.add_argument(
        "--target-crs",
        default=None,
        help="Reproject all tiles to this CRS before merging (e.g. EPSG:4326)",
    )
    args = parser.parse_args()

    import rasterio
    from rasterio.merge import merge as rio_merge
    from rasterio.warp import calculate_default_transform, reproject
    from rasterio.enums import Resampling
    import tempfile
    import os

    # Resolve input paths (handle glob)
    input_paths = []
    for pattern in args.inputs:
        expanded = glob.glob(pattern)
        if expanded:
            input_paths.extend(sorted(expanded))
        else:
            input_paths.append(pattern)

    input_paths = [Path(p).expanduser().resolve() for p in input_paths]

    missing = [str(p) for p in input_paths if not p.exists()]
    if missing:
        print(f"ERROR: Missing input files:")
        for m in missing:
            print(f"  {m}")
        return 1

    if len(input_paths) == 0:
        print("ERROR: No input rasters found")
        return 1

    print(f"Found {len(input_paths)} input raster(s):")
    for p in input_paths:
        print(f"  {p.name}")

    warnings = []
    assumptions = []

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Inspect all rasters
    crss = []
    nodata_vals = []
    dtypes = []
    band_counts = []
    with rasterio.open(input_paths[0]) as src:
        reference_crs = src.crs
        reference_nodata = src.nodata
        reference_profile = src.profile.copy()

    for p in input_paths:
        with rasterio.open(p) as src:
            crss.append(src.crs)
            nodata_vals.append(src.nodata)
            dtypes.append(src.dtypes[0])
            band_counts.append(src.count)

    # Check band count consistency
    if len(set(band_counts)) > 1:
        print(f"ERROR: Inconsistent band counts: {dict(zip([p.name for p in input_paths], band_counts))}")
        return 1

    # CRS handling
    unique_crss = set(str(c) for c in crss)
    target_crs = args.target_crs or reference_crs
    needs_reproject = len(unique_crss) > 1 or (args.target_crs and args.target_crs != str(reference_crs))

    nodata_out = args.nodata if args.nodata is not None else reference_nodata

    resampling_map = {
        "nearest": Resampling.nearest,
        "bilinear": Resampling.bilinear,
        "cubic": Resampling.cubic,
        "cubic_spline": Resampling.cubic_spline,
        "lanczos": Resampling.lanczos,
        "average": Resampling.average,
        "mode": Resampling.mode,
        "gauss": Resampling.gauss,
    }
    resampling_method = resampling_map.get(args.resampling, Resampling.nearest)

    # Reproject if needed
    tmp_files = []
    working_paths = list(input_paths)

    if needs_reproject:
        print(f"CRS mismatch detected across {len(unique_crss)} CRS(es) — reprojecting to {target_crs}...")
        warnings.append(f"CRS mismatch: reprojected {len(input_paths)} tiles to {target_crs}")
        for i, p in enumerate(input_paths):
            with rasterio.open(p) as src:
                if str(src.crs) == str(target_crs) and not args.target_crs:
                    working_paths[i] = p
                    continue
                print(f"  Reprojecting {p.name}...")
                transform, width, height = calculate_default_transform(
                    src.crs, target_crs, src.width, src.height, *src.bounds
                )
                out_profile = src.profile.copy()
                out_profile.update(
                    crs=target_crs,
                    transform=transform,
                    width=width,
                    height=height,
                    nodata=nodata_out,
                )
                tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
                tmp.close()
                tmp_files.append(tmp.name)
                with rasterio.open(tmp.name, "w", **out_profile) as dst:
                    for band_idx in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, band_idx),
                            destination=rasterio.band(dst, band_idx),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=target_crs,
                            resampling=resampling_method,
                        )
                working_paths[i] = Path(tmp.name)

    # Open all rasters for merging
    print(f"Merging {len(working_paths)} raster(s)...")
    src_files = [rasterio.open(p) for p in working_paths]

    try:
        mosaic, mosaic_transform = rio_merge(
            src_files,
            nodata=nodata_out,
            resampling=resampling_method,
        )
    finally:
        for f in src_files:
            f.close()

    # Cleanup tmp files
    for tmp in tmp_files:
        try:
            os.unlink(tmp)
        except Exception:
            pass

    print(f"  Mosaic shape: {mosaic.shape}")
    n_valid = int(np.sum(mosaic != nodata_out)) if nodata_out is not None else mosaic.size
    print(f"  Valid pixels: {n_valid:,}")

    # Write output
    out_profile = reference_profile.copy()
    out_profile.update(
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=mosaic_transform,
        crs=target_crs,
        count=mosaic.shape[0],
        compress="lzw",
        bigtiff="IF_SAFER",
    )
    if nodata_out is not None:
        out_profile["nodata"] = nodata_out

    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(mosaic)

    print(f"Output: {output_path}")

    # Build log
    log = {
        "step": "raster_mosaic",
        "inputs": [str(p) for p in input_paths],
        "n_inputs": len(input_paths),
        "output": str(output_path),
        "resampling": args.resampling,
        "target_crs": str(target_crs),
        "nodata_out": nodata_out,
        "n_bands": int(mosaic.shape[0]),
        "output_shape": list(mosaic.shape[1:]),
        "n_valid_pixels": n_valid,
        "reprojected": needs_reproject,
        "unique_crs_count": len(unique_crss),
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.mosaic.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
