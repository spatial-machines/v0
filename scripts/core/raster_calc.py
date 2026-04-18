#!/usr/bin/env python3
"""Raster calculator with common spectral index presets and custom expressions.

Usage:
    # Preset index (NDVI from NIR=B1, Red=B2):
    python raster_calc.py \\
        --input nir_band.tif red_band.tif \\
        --index ndvi \\
        --output outputs/rasters/ndvi.tif

    # Custom expression:
    python raster_calc.py \\
        --input band1.tif band2.tif \\
        --expr "(B1 - B2) / (B1 + B2)" \\
        --output outputs/rasters/custom_index.tif

    # Single-band expression:
    python raster_calc.py \\
        --input elevation.tif \\
        --expr "B1 * 3.28084" \\
        --output outputs/rasters/elevation_feet.tif

Preset indices (input band order matters):
    ndvi:  (NIR - Red) / (NIR + Red)         — B1=NIR, B2=Red
    evi:   2.5*(NIR-Red)/(NIR+6*Red-7.5*Blue+1) — B1=NIR, B2=Red, B3=Blue
    savi:  ((NIR-Red)/(NIR+Red+0.5))*1.5    — B1=NIR, B2=Red
    ndwi:  (Green - NIR) / (Green + NIR)    — B1=Green, B2=NIR
    ndbi:  (SWIR - NIR) / (SWIR + NIR)      — B1=SWIR, B2=NIR
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Preset index definitions: (expression, band_labels, description)
INDEX_PRESETS = {
    "ndvi": {
        "expr": "(B1 - B2) / (B1 + B2 + 1e-10)",
        "bands": ["NIR", "Red"],
        "description": "Normalized Difference Vegetation Index",
        "range": (-1, 1),
    },
    "evi": {
        "expr": "2.5 * (B1 - B2) / (B1 + 6 * B2 - 7.5 * B3 + 1 + 1e-10)",
        "bands": ["NIR", "Red", "Blue"],
        "description": "Enhanced Vegetation Index",
        "range": (-1, 1),
    },
    "savi": {
        "expr": "((B1 - B2) / (B1 + B2 + 0.5 + 1e-10)) * 1.5",
        "bands": ["NIR", "Red"],
        "description": "Soil-Adjusted Vegetation Index (L=0.5)",
        "range": (-1.5, 1.5),
    },
    "ndwi": {
        "expr": "(B1 - B2) / (B1 + B2 + 1e-10)",
        "bands": ["Green", "NIR"],
        "description": "Normalized Difference Water Index",
        "range": (-1, 1),
    },
    "ndbi": {
        "expr": "(B1 - B2) / (B1 + B2 + 1e-10)",
        "bands": ["SWIR", "NIR"],
        "description": "Normalized Difference Built-up Index",
        "range": (-1, 1),
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Raster calculator — compute spectral indices or custom expressions."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Input raster(s) in band order (B1, B2, B3...)",
    )
    parser.add_argument("--output", required=True, help="Output GeoTIFF path")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--index",
        choices=list(INDEX_PRESETS.keys()),
        help=f"Preset spectral index: {', '.join(INDEX_PRESETS.keys())}",
    )
    group.add_argument(
        "--expr",
        help='Custom numpy expression, e.g. "(B1-B2)/(B1+B2)"',
    )
    parser.add_argument(
        "--nodata",
        type=float,
        default=-9999.0,
        help="Output nodata value (default: -9999)",
    )
    parser.add_argument(
        "--clip-range",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        help="Clip output values to [MIN, MAX] (useful for spectral indices)",
    )
    args = parser.parse_args()

    import rasterio
    from rasterio.warp import reproject, Resampling, calculate_default_transform

    input_paths = [Path(p).expanduser().resolve() for p in args.input]
    output_path = Path(args.output).expanduser().resolve()

    for p in input_paths:
        if not p.exists():
            print(f"ERROR: Input raster not found: {p}")
            return 1

    warnings = []
    assumptions = []

    # Determine expression and metadata
    if args.index:
        preset = INDEX_PRESETS[args.index]
        expr = preset["expr"]
        band_labels = preset["bands"]
        description = preset["description"]
        n_bands_needed = len(band_labels)
        print(f"Index: {args.index.upper()} — {description}")
        print(f"  Formula: {expr}")
        print(f"  Expected bands: {band_labels}")
    else:
        expr = args.expr
        description = f"Custom expression: {expr}"
        n_bands_needed = None
        print(f"Custom expression: {expr}")

    # Validate band count
    if n_bands_needed is not None and len(input_paths) < n_bands_needed:
        print(
            f"ERROR: {args.index.upper()} requires {n_bands_needed} bands "
            f"({band_labels}), got {len(input_paths)}"
        )
        return 1

    # Load all rasters — read first band from each
    print(f"Loading {len(input_paths)} input raster(s)...")
    bands = {}
    reference_profile = None
    reference_crs = None
    reference_transform = None
    reference_shape = None

    for i, path in enumerate(input_paths):
        band_key = f"B{i+1}"
        with rasterio.open(path) as src:
            if i == 0:
                reference_profile = src.profile.copy()
                reference_crs = src.crs
                reference_transform = src.transform
                reference_shape = (src.height, src.width)
                arr = src.read(1).astype(np.float64)
                nodata_in = src.nodata
            else:
                # Reproject to match first raster if needed
                if src.crs != reference_crs or src.transform != reference_transform or \
                   (src.height, src.width) != reference_shape:
                    print(f"  Reprojecting {path.name} to match {input_paths[0].name}...")
                    dest = np.empty(reference_shape, dtype=np.float64)
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=dest,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=reference_transform,
                        dst_crs=reference_crs,
                        resampling=Resampling.bilinear,
                    )
                    arr = dest
                    warnings.append(f"{path.name} reprojected/resampled to match B1 extent")
                else:
                    arr = src.read(1).astype(np.float64)
                nodata_in = src.nodata

            # Mask nodata values
            if nodata_in is not None:
                arr = np.where(arr == nodata_in, np.nan, arr)

        bands[band_key] = arr
        print(f"  {band_key}: {path.name}, range: {np.nanmin(arr):.4f} – {np.nanmax(arr):.4f}")

    # Evaluate expression
    print("Evaluating expression...")
    try:
        # Build namespace with band arrays
        namespace = {"np": np}
        namespace.update(bands)
        result = eval(expr, {"__builtins__": {}}, namespace)
        result = np.asarray(result, dtype=np.float32)
    except Exception as e:
        print(f"ERROR: Expression evaluation failed: {e}")
        print(f"  Expression: {expr}")
        print(f"  Available bands: {list(bands.keys())}")
        return 1

    # Handle infinities and NaN
    result = np.where(np.isinf(result), np.nan, result)

    # Clip range
    if args.clip_range:
        lo, hi = args.clip_range
        clipped_count = int(np.sum((result < lo) | (result > hi)))
        result = np.clip(result, lo, hi)
        if clipped_count > 0:
            assumptions.append(f"Clipped {clipped_count} values to [{lo}, {hi}]")
    elif args.index and "range" in INDEX_PRESETS[args.index]:
        lo, hi = INDEX_PRESETS[args.index]["range"]
        result = np.clip(result, lo, hi)

    # Replace NaN with nodata
    nan_mask = np.isnan(result)
    result[nan_mask] = args.nodata
    n_nodata = int(np.sum(nan_mask))
    n_valid = result.size - n_nodata

    print(f"  Valid pixels: {n_valid:,}, nodata pixels: {n_nodata:,}")
    valid_result = result[~nan_mask]
    if len(valid_result) > 0:
        print(f"  Output range: {float(np.min(valid_result)):.4f} – {float(np.max(valid_result)):.4f}")
        print(f"  Mean: {float(np.mean(valid_result)):.4f}, Std: {float(np.std(valid_result)):.4f}")

    # Write output
    out_profile = reference_profile.copy()
    out_profile.update(
        dtype="float32",
        count=1,
        nodata=args.nodata,
        compress="lzw",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(result[np.newaxis, :, :])

    print(f"Output: {output_path}")

    # Build log
    log = {
        "step": "raster_calc",
        "inputs": [str(p) for p in input_paths],
        "output": str(output_path),
        "index": args.index,
        "expression": expr,
        "description": description,
        "band_labels": band_labels if args.index else [f"B{i+1}" for i in range(len(input_paths))],
        "clip_range": args.clip_range,
        "nodata_out": args.nodata,
        "n_valid_pixels": n_valid,
        "n_nodata_pixels": n_nodata,
        "output_range": [
            float(np.min(valid_result)) if len(valid_result) > 0 else None,
            float(np.max(valid_result)) if len(valid_result) > 0 else None,
        ],
        "raster_crs": str(reference_crs),
        "raster_shape": list(reference_shape),
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.calc.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
