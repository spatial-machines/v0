#!/usr/bin/env python3
"""Extract raster statistics within polygon zones using rasterstats.

Usage:
    python zonal_stats.py \\
        --raster data/rasters/elevation.tif \\
        --zones data/processed/counties.gpkg \\
        --stats mean min max sum std count \\
        --output outputs/tables/elevation_by_county.gpkg \\
        [--prefix elev_]

Common uses:
  - Average elevation per county
  - Mean NDVI per census tract
  - Sum impervious surface per watershed
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract raster statistics within polygon zones."
    )
    parser.add_argument("--raster", required=True, help="Input raster file (GeoTIFF)")
    parser.add_argument("--zones", required=True, help="Zone polygons (GeoPackage)")
    parser.add_argument(
        "--stats",
        nargs="+",
        default=["mean", "min", "max"],
        help="Statistics to compute: mean min max sum std count median (default: mean min max)",
    )
    parser.add_argument("--output", required=True, help="Output GeoPackage path")
    parser.add_argument(
        "--prefix", default="", help="Column prefix for output stats (e.g. 'elev_')"
    )
    parser.add_argument("--band", type=int, default=1, help="Raster band to use (default: 1)")
    parser.add_argument(
        "--nodata", type=float, default=None, help="Override nodata value from raster"
    )
    args = parser.parse_args()

    try:
        from rasterstats import zonal_stats as rs_zonal_stats
    except ImportError:
        print("ERROR: rasterstats required. Install with: pip install rasterstats")
        return 1

    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    import tempfile
    import os

    raster_path = Path(args.raster).expanduser().resolve()
    zones_path = Path(args.zones).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not raster_path.exists():
        print(f"ERROR: Raster not found: {raster_path}")
        return 1
    if not zones_path.exists():
        print(f"ERROR: Zones not found: {zones_path}")
        return 1

    # Load zones
    print(f"Loading zones from {zones_path}...")
    gdf = gpd.read_file(zones_path)
    print(f"  {len(gdf)} zone features, CRS: {gdf.crs}")

    warnings = []
    assumptions = []

    # Inspect raster
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        raster_nodata = src.nodata
        raster_transform = src.transform
        raster_bounds = src.bounds
        raster_shape = (src.height, src.width)
        raster_dtype = src.dtypes[0]

    print(f"Raster: {raster_path.name}, shape {raster_shape}, CRS: {raster_crs}, dtype: {raster_dtype}")

    nodata_val = args.nodata if args.nodata is not None else raster_nodata

    # Handle CRS mismatch — reproject zones to match raster CRS
    working_raster = str(raster_path)
    tmp_file = None

    if gdf.crs is None:
        warnings.append("Zones have no CRS — assuming same as raster")
        gdf = gdf.set_crs(raster_crs)
    elif raster_crs is None:
        warnings.append("Raster has no CRS — proceeding without reprojection")
    elif gdf.crs != raster_crs:
        original_zones_crs = gdf.crs
        print(f"  CRS mismatch: zones={gdf.crs}, raster={raster_crs}")
        print(f"  Reprojecting zones to match raster CRS...")
        gdf = gdf.to_crs(raster_crs)
        assumptions.append(f"Reprojected zones from {original_zones_crs} to {raster_crs}")
        warnings.append("CRS mismatch detected — zones reprojected to raster CRS")

    # Validate stats
    valid_stats = {"min", "max", "mean", "sum", "std", "count", "median", "range",
                   "majority", "minority", "unique", "nodata", "percentile_25",
                   "percentile_75", "percentile_90", "percentile_95"}
    requested_stats = args.stats
    bad_stats = [s for s in requested_stats if s not in valid_stats]
    if bad_stats:
        warnings.append(f"Unknown stats ignored: {bad_stats}")
        requested_stats = [s for s in requested_stats if s in valid_stats]
    if not requested_stats:
        print("ERROR: No valid stats requested")
        return 1

    print(f"Computing zonal stats: {requested_stats}...")
    print(f"  Band: {args.band}, nodata: {nodata_val}")

    stats_result = rs_zonal_stats(
        gdf,
        working_raster,
        stats=requested_stats,
        band=args.band,
        nodata=nodata_val,
        geojson_out=False,
        all_touched=False,
    )

    # Attach results to GeoDataFrame
    stats_df = gpd.GeoDataFrame(stats_result)
    n_null_zones = int(stats_df.get("count", stats_df.iloc[:, 0]).isna().sum()) if len(stats_df) else 0

    for stat in requested_stats:
        col_name = f"{args.prefix}{stat}" if args.prefix else stat
        if stat in stats_df.columns:
            gdf[col_name] = stats_df[stat].values
        else:
            gdf[col_name] = np.nan
            warnings.append(f"Stat '{stat}' not returned by rasterstats — filled with NaN")

    # Summary
    n_zones = len(gdf)
    if "count" in requested_stats:
        count_col = f"{args.prefix}count" if args.prefix else "count"
        n_valid_zones = int((gdf[count_col] > 0).sum())
        n_empty_zones = int((gdf[count_col] == 0).sum())
    else:
        n_valid_zones = n_zones
        n_empty_zones = 0

    print(f"  {n_zones} zones processed: {n_valid_zones} with data, {n_empty_zones} empty/outside raster")

    if n_empty_zones > 0:
        warnings.append(f"{n_empty_zones} zones had no raster coverage (count=0 or outside extent)")

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG")
    print(f"Output: {output_path}")

    # Build log
    log = {
        "step": "zonal_stats",
        "raster": str(raster_path),
        "zones": str(zones_path),
        "output": str(output_path),
        "band": args.band,
        "stats": requested_stats,
        "prefix": args.prefix,
        "n_zones": n_zones,
        "n_valid_zones": n_valid_zones,
        "n_empty_zones": n_empty_zones,
        "nodata_value": nodata_val,
        "raster_crs": str(raster_crs),
        "zones_crs": str(gdf.crs),
        "raster_shape": list(raster_shape),
        "raster_dtype": str(raster_dtype),
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.zonal_stats.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
