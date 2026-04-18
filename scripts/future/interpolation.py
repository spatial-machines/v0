#!/usr/bin/env python3
"""Interpolate point observations to a continuous raster surface.

Usage:
    python interpolation.py \\
        --input data/processed/rain_gauges.gpkg \\
        --value-col precipitation_mm \\
        --method idw \\
        --resolution 1000 \\
        --output outputs/rasters/precip_surface.tif

    # CSV input with custom lat/lon columns:
    python interpolation.py \\
        --input data/raw/observations.csv \\
        --value-col temperature \\
        --lat latitude --lon longitude \\
        --method kriging \\
        --resolution 500 \\
        --output outputs/rasters/temp_surface.tif \\
        --output-map outputs/maps/temp_surface.png

Methods:
    idw      - Inverse Distance Weighting (scipy)
    linear   - Linear triangulation (scipy.griddata)
    nearest  - Nearest neighbor (scipy.griddata)
    kriging  - Ordinary kriging (pykrige, optional)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def _idw(points, values, grid_x, grid_y, power=2):
    """Inverse Distance Weighting interpolation."""
    from scipy.spatial import cKDTree

    grid_points = np.column_stack([grid_x.ravel(), grid_y.ravel()])
    tree = cKDTree(points)
    distances, indices = tree.query(grid_points, k=min(12, len(points)))

    # Avoid division by zero at exact point locations
    distances = np.where(distances == 0, 1e-10, distances)
    weights = 1.0 / (distances ** power)
    weights /= weights.sum(axis=1, keepdims=True)

    result = np.sum(weights * values[indices], axis=1)
    return result.reshape(grid_x.shape)


def main():
    parser = argparse.ArgumentParser(
        description="Interpolate point observations to a raster surface."
    )
    parser.add_argument("--input", required=True, help="Input points (GeoPackage or CSV)")
    parser.add_argument("--value-col", required=True, help="Column containing values to interpolate")
    parser.add_argument(
        "--method",
        choices=["idw", "linear", "nearest", "kriging"],
        default="idw",
        help="Interpolation method (default: idw)",
    )
    parser.add_argument(
        "--resolution",
        type=float,
        required=True,
        help="Output raster resolution in CRS units (e.g. 1000 = 1km for projected CRS)",
    )
    parser.add_argument("--output", required=True, help="Output GeoTIFF surface")
    parser.add_argument("--output-map", default=None, help="Optional output PNG visualization")
    parser.add_argument(
        "--extent",
        default=None,
        help='Output extent as "minx,miny,maxx,maxy" or path to a file whose bbox is used',
    )
    parser.add_argument("--lat", default="lat", help="Latitude column name for CSV input (default: lat)")
    parser.add_argument("--lon", default="lon", help="Longitude column name for CSV input (default: lon)")
    parser.add_argument(
        "--crs",
        default="EPSG:4326",
        help="CRS for CSV inputs (default: EPSG:4326)",
    )
    parser.add_argument("--nodata", type=float, default=-9999.0, help="Output nodata (default: -9999)")
    args = parser.parse_args()

    import rasterio
    from rasterio.transform import from_origin
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        print(f"ERROR: Input not found: {input_path}")
        return 1

    warnings = []
    assumptions = []

    # Load points
    print(f"Loading points from {input_path}...")
    suffix = input_path.suffix.lower()

    if suffix in (".csv", ".tsv"):
        import pandas as pd
        df = pd.read_csv(input_path)
        if args.lat not in df.columns or args.lon not in df.columns:
            print(f"ERROR: CSV must have columns '{args.lat}' and '{args.lon}'")
            print(f"  Available columns: {list(df.columns)}")
            return 1
        import geopandas as gpd
        from shapely.geometry import Point
        gdf = gpd.GeoDataFrame(
            df,
            geometry=[Point(lon, lat) for lon, lat in zip(df[args.lon], df[args.lat])],
            crs=args.crs,
        )
        assumptions.append(f"CSV coordinates assumed in {args.crs}")
    else:
        import geopandas as gpd
        gdf = gpd.read_file(input_path)

    print(f"  {len(gdf)} points loaded, CRS: {gdf.crs}")

    # Check value column
    if args.value_col not in gdf.columns:
        print(f"ERROR: Column '{args.value_col}' not found")
        print(f"  Available: {[c for c in gdf.columns if c != 'geometry']}")
        return 1

    import pandas as pd
    gdf[args.value_col] = pd.to_numeric(gdf[args.value_col], errors="coerce")
    null_count = int(gdf[args.value_col].isna().sum())
    if null_count > 0:
        warnings.append(f"{null_count} points with null values dropped")
        gdf = gdf[gdf[args.value_col].notna()].copy()

    if len(gdf) < 3:
        print(f"ERROR: Need at least 3 valid points, got {len(gdf)}")
        return 1

    # Determine output extent
    if args.extent:
        try:
            parts = [float(x) for x in args.extent.split(",")]
            minx, miny, maxx, maxy = parts
            assumptions.append(f"Extent from argument: {args.extent}")
        except (ValueError, AttributeError):
            # Try as a file path
            extent_path = Path(args.extent).expanduser().resolve()
            if extent_path.exists():
                import geopandas as gpd
                ext_gdf = gpd.read_file(extent_path)
                if ext_gdf.crs != gdf.crs:
                    ext_gdf = ext_gdf.to_crs(gdf.crs)
                b = ext_gdf.total_bounds
                minx, miny, maxx, maxy = b
                assumptions.append(f"Extent from file: {extent_path}")
            else:
                print(f"ERROR: Cannot parse extent: {args.extent}")
                return 1
    else:
        # Use point bounds with 10% buffer
        b = gdf.total_bounds
        buf_x = (b[2] - b[0]) * 0.1
        buf_y = (b[3] - b[1]) * 0.1
        minx = b[0] - buf_x
        miny = b[1] - buf_y
        maxx = b[2] + buf_x
        maxy = b[3] + buf_y
        assumptions.append("Extent derived from point bounds with 10% buffer")

    # Build output grid
    res = args.resolution
    nx = max(2, int(np.ceil((maxx - minx) / res)))
    ny = max(2, int(np.ceil((maxy - miny) / res)))
    print(f"Output grid: {ny} rows × {nx} cols, resolution={res} units")

    xs = np.linspace(minx + res / 2, minx + res * nx - res / 2, nx)
    ys = np.linspace(miny + res / 2, miny + res * ny - res / 2, ny)
    grid_x, grid_y = np.meshgrid(xs, ys[::-1])  # top-left origin

    # Get coordinates and values
    coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
    values = gdf[args.value_col].values.astype(float)

    print(f"Interpolating {len(coords)} points using method: {args.method}...")
    print(f"  Value range: {values.min():.4f} – {values.max():.4f}")

    surface = None

    if args.method == "idw":
        surface = _idw(coords, values, grid_x, grid_y, power=2)
        formula_used = "IDW (power=2, k=12 neighbors)"

    elif args.method in ("linear", "nearest"):
        from scipy.interpolate import griddata
        surface = griddata(coords, values, (grid_x, grid_y), method=args.method)
        surface = np.where(np.isnan(surface), args.nodata, surface)
        formula_used = f"scipy.interpolate.griddata method={args.method}"

    elif args.method == "kriging":
        try:
            from pykrige.ok import OrdinaryKriging
            print("  Using pykrige OrdinaryKriging...")
            ok = OrdinaryKriging(
                coords[:, 0], coords[:, 1], values,
                variogram_model="spherical",
                verbose=False,
                enable_plotting=False,
            )
            surface, variance = ok.execute("grid", xs, ys[::-1])
            surface = np.array(surface)
            formula_used = "OrdinaryKriging (pykrige, spherical variogram)"
        except ImportError:
            print("  pykrige not installed — falling back to IDW")
            warnings.append("pykrige not installed, fell back to IDW interpolation")
            surface = _idw(coords, values, grid_x, grid_y, power=2)
            formula_used = "IDW (power=2, k=12) — kriging fallback"

    if surface is None:
        print("ERROR: Interpolation produced no result")
        return 1

    # Mask nodata
    nodata_mask = surface == args.nodata
    surface_f = surface.astype(np.float32)
    surface_f = np.where(np.isnan(surface_f), args.nodata, surface_f)

    n_valid = int(np.sum(surface_f != args.nodata))
    print(f"  Surface pixels: {n_valid:,} valid, {surface_f.size - n_valid:,} nodata")

    # Write GeoTIFF
    transform = from_origin(minx, maxy, res, res)
    out_profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": nx,
        "height": ny,
        "count": 1,
        "crs": gdf.crs,
        "transform": transform,
        "nodata": args.nodata,
        "compress": "lzw",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(surface_f[np.newaxis, :, :])

    print(f"Output: {output_path}")

    # Optional PNG
    if args.output_map:
        map_path = Path(args.output_map).expanduser().resolve()
        map_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 8), facecolor="black")
        ax.set_facecolor("black")

        display = np.where(surface_f == args.nodata, np.nan, surface_f)
        im = ax.imshow(
            display, cmap="viridis", interpolation="bilinear",
            extent=[minx, maxx, miny, maxy], origin="upper",
        )
        cbar = plt.colorbar(im, ax=ax, shrink=0.6)
        cbar.ax.yaxis.set_tick_params(color="white")
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
        cbar.set_label(args.value_col, color="white")

        # Plot source points
        ax.scatter(
            coords[:, 0], coords[:, 1], c=values, cmap="viridis",
            edgecolors="white", linewidths=0.5, s=25, zorder=5,
        )
        ax.set_title(
            f"Interpolated Surface: {args.value_col}\nMethod: {args.method}",
            color="white", fontsize=12, fontweight="bold",
        )
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("white")

        plt.tight_layout()
        fig.savefig(map_path, dpi=150, bbox_inches="tight", facecolor="black")
        plt.close(fig)
        print(f"Map: {map_path}")

    # Build log
    log = {
        "step": "interpolation",
        "input": str(input_path),
        "value_col": args.value_col,
        "method": args.method,
        "formula_used": formula_used,
        "resolution": res,
        "output": str(output_path),
        "output_map": args.output_map,
        "n_input_points": len(gdf),
        "n_dropped_null": null_count,
        "grid_size": [ny, nx],
        "extent": [minx, miny, maxx, maxy],
        "nodata": args.nodata,
        "n_valid_pixels": n_valid,
        "value_range": [float(values.min()), float(values.max())],
        "crs": str(gdf.crs),
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.interpolation.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
