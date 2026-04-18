#!/usr/bin/env python3
"""Generate a Kernel Density Estimation raster from point features.

Uses sklearn.neighbors.KernelDensity to produce a smooth density surface.
Output is a GeoTIFF with relative density values + optional PNG visualization.

Usage:
    python kde_surface.py \\
        --input data/processed/crime_incidents.gpkg \\
        --resolution 500 \\
        --output outputs/rasters/crime_density.tif \\
        --output-map outputs/maps/crime_density.png

    # CSV input:
    python kde_surface.py \\
        --input data/raw/events.csv \\
        --lat latitude --lon longitude \\
        --bandwidth 2000 \\
        --resolution 500 \\
        --output outputs/rasters/event_density.tif
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate KDE density surface from point features."
    )
    parser.add_argument("--input", required=True, help="Input points (GeoPackage or CSV)")
    parser.add_argument(
        "--lat", default="lat", help="Latitude column for CSV (default: lat)"
    )
    parser.add_argument(
        "--lon", default="lon", help="Longitude column for CSV (default: lon)"
    )
    parser.add_argument(
        "--bandwidth",
        type=float,
        default=None,
        help="KDE bandwidth in CRS units (auto-selected if omitted using Silverman's rule)",
    )
    parser.add_argument(
        "--kernel",
        default="gaussian",
        choices=["gaussian", "tophat", "epanechnikov", "exponential", "linear", "cosine"],
        help="KDE kernel function (default: gaussian)",
    )
    parser.add_argument(
        "--resolution",
        type=float,
        required=True,
        help="Output pixel size in CRS units",
    )
    parser.add_argument("--output", required=True, help="Output density GeoTIFF")
    parser.add_argument("--output-map", default=None, help="Output PNG visualization")
    parser.add_argument(
        "--extent",
        default=None,
        help='Output extent as "minx,miny,maxx,maxy" or path to extent file',
    )
    parser.add_argument(
        "--crs",
        default="EPSG:4326",
        help="CRS for CSV inputs (default: EPSG:4326)",
    )
    parser.add_argument("--dpi", type=int, default=150, help="PNG DPI (default: 150)")
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
    print(f"Loading points: {input_path.name}")
    suffix = input_path.suffix.lower()

    if suffix in (".csv", ".tsv"):
        import pandas as pd
        import geopandas as gpd
        from shapely.geometry import Point

        df = pd.read_csv(input_path)
        if args.lat not in df.columns or args.lon not in df.columns:
            print(f"ERROR: CSV needs columns '{args.lat}' and '{args.lon}'")
            print(f"  Available: {list(df.columns)}")
            return 1
        df = df.dropna(subset=[args.lat, args.lon])
        gdf = gpd.GeoDataFrame(
            df,
            geometry=[Point(lo, la) for lo, la in zip(df[args.lon], df[args.lat])],
            crs=args.crs,
        )
        assumptions.append(f"CSV assumed CRS: {args.crs}")
    else:
        import geopandas as gpd
        gdf = gpd.read_file(input_path)

    # Drop null/empty geometries
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    print(f"  {len(gdf)} valid points, CRS: {gdf.crs}")

    if len(gdf) < 5:
        print(f"ERROR: Need at least 5 points for KDE, got {len(gdf)}")
        return 1

    # Auto-reproject geographic CRS (degrees) to metric for meaningful resolution values
    original_crs = gdf.crs
    if gdf.crs and gdf.crs.is_geographic:
        import pyproj
        # Use UTM zone estimated from centroid
        lon_center = float(gdf.geometry.x.mean())
        lat_center = float(gdf.geometry.y.mean())
        utm_crs = gdf.estimate_utm_crs()
        gdf = gdf.to_crs(utm_crs)
        print(f"  Auto-reprojected geographic CRS → {utm_crs} (metric, for resolution in meters)")
        assumptions.append(f"Reprojected {original_crs} → {utm_crs} so --resolution is in meters")

    # Extract coordinates
    coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])

    # Determine extent
    if args.extent:
        try:
            minx, miny, maxx, maxy = [float(x) for x in args.extent.split(",")]
        except (ValueError, AttributeError):
            ext_path = Path(args.extent).expanduser().resolve()
            if ext_path.exists():
                ext_gdf = gpd.read_file(ext_path)
                if ext_gdf.crs != gdf.crs:
                    ext_gdf = ext_gdf.to_crs(gdf.crs)
                b = ext_gdf.total_bounds
                minx, miny, maxx, maxy = b
            else:
                print(f"ERROR: Cannot parse extent: {args.extent}")
                return 1
    else:
        b = gdf.total_bounds
        buf_x = (b[2] - b[0]) * 0.1
        buf_y = (b[3] - b[1]) * 0.1
        minx = b[0] - buf_x
        miny = b[1] - buf_y
        maxx = b[2] + buf_x
        maxy = b[3] + buf_y
        assumptions.append("Extent from point bounds + 10% buffer")

    # Grid
    res = args.resolution
    nx = max(2, int(np.ceil((maxx - minx) / res)))
    ny = max(2, int(np.ceil((maxy - miny) / res)))
    print(f"Output grid: {ny}×{nx}, resolution={res}")

    xs = np.linspace(minx + res / 2, minx + res * nx - res / 2, nx)
    ys = np.linspace(miny + res / 2, miny + res * ny - res / 2, ny)
    grid_x, grid_y = np.meshgrid(xs, ys[::-1])
    grid_points = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # Bandwidth selection
    if args.bandwidth is None:
        # Silverman's rule of thumb: h = sigma * n^(-1/(d+4))
        n, d = len(coords), 2
        sigma = np.std(coords, axis=0).mean()
        bandwidth = sigma * (n ** (-1.0 / (d + 4)))
        print(f"  Auto bandwidth (Silverman's rule): {bandwidth:.4f} CRS units")
        assumptions.append(f"Bandwidth auto-selected via Silverman's rule: {bandwidth:.4f}")
    else:
        bandwidth = args.bandwidth
        print(f"  Bandwidth: {bandwidth} CRS units")

    # KDE
    try:
        from sklearn.neighbors import KernelDensity
    except ImportError:
        print("ERROR: scikit-learn required. Install with: pip install scikit-learn")
        return 1

    print(f"Fitting KDE ({args.kernel} kernel, bandwidth={bandwidth:.4f})...")
    kde = KernelDensity(kernel=args.kernel, bandwidth=bandwidth)
    kde.fit(coords)

    print("Scoring grid points (this may take a moment for large grids)...")
    log_density = kde.score_samples(grid_points)
    density = np.exp(log_density).reshape(ny, nx).astype(np.float32)

    # Normalize to 0–1 for interpretability
    d_min = float(density.min())
    d_max = float(density.max())
    if d_max > d_min:
        density_norm = (density - d_min) / (d_max - d_min)
    else:
        density_norm = np.zeros_like(density)
        warnings.append("All density values identical — output is all zeros")

    print(f"  Raw density range: {d_min:.6e} – {d_max:.6e}")
    print(f"  Normalized 0–1 output")

    # Write GeoTIFF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transform = from_origin(minx, maxy, res, res)
    out_profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": nx,
        "height": ny,
        "count": 1,
        "crs": gdf.crs,
        "transform": transform,
        "nodata": None,
        "compress": "lzw",
    }

    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(density_norm[np.newaxis, :, :])

    print(f"Output: {output_path}")

    # PNG visualization
    if args.output_map:
        map_path = Path(args.output_map).expanduser().resolve()
        map_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 8), facecolor="black")
        ax.set_facecolor("black")

        im = ax.imshow(
            density_norm,
            cmap="plasma",
            interpolation="bilinear",
            extent=[minx, maxx, miny, maxy],
            origin="upper",
            vmin=0,
            vmax=1,
        )

        cbar = plt.colorbar(im, ax=ax, shrink=0.6)
        cbar.set_label("Relative Density", color="white")
        cbar.ax.yaxis.set_tick_params(color="white")
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

        # Plot source points (small, semi-transparent)
        ax.scatter(
            coords[:, 0], coords[:, 1],
            c="white", s=3, alpha=0.3, linewidths=0, zorder=5,
        )

        ax.set_title(
            f"Kernel Density: {input_path.stem}\n"
            f"{args.kernel} kernel, bandwidth={bandwidth:.2f}, n={len(coords)}",
            color="white", fontsize=11, fontweight="bold",
        )
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")

        plt.tight_layout()
        fig.savefig(map_path, dpi=args.dpi, bbox_inches="tight", facecolor="black")
        plt.close(fig)
        print(f"Map: {map_path}")

    # Build log
    log = {
        "step": "kde_surface",
        "input": str(input_path),
        "output": str(output_path),
        "output_map": args.output_map,
        "n_points": len(gdf),
        "kernel": args.kernel,
        "bandwidth": float(bandwidth),
        "bandwidth_auto": args.bandwidth is None,
        "resolution": res,
        "grid_size": [ny, nx],
        "extent": [minx, miny, maxx, maxy],
        "crs": str(gdf.crs),
        "raw_density_range": [d_min, d_max],
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.kde.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
