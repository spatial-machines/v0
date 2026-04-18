#!/usr/bin/env python3
"""Generate contour lines from a DEM raster.

Extracts elevation contours using matplotlib's contouring engine,
converts paths to shapely LineStrings, and writes a GeoPackage.

Usage:
    python contour_generation.py \\
        --input data/rasters/dem.tif \\
        --interval 10 \\
        --output outputs/vectors/contours_10m.gpkg

    python contour_generation.py \\
        --input data/rasters/dem.tif \\
        --interval 25 \\
        --output outputs/vectors/contours_25m.gpkg \\
        --output-map outputs/maps/contours.png
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import matplotlib.path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate contour lines from a DEM raster."
    )
    parser.add_argument("--input", required=True, help="Input DEM raster (GeoTIFF)")
    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Contour interval in DEM units (default: 10.0)",
    )
    parser.add_argument("--output", required=True, help="Output GeoPackage with contour lines")
    parser.add_argument("--output-map", default=None, help="Optional output PNG map")
    parser.add_argument(
        "--smooth",
        action="store_true",
        help="Apply light Gaussian smoothing to DEM before contouring (reduces noise)",
    )
    parser.add_argument("--dpi", type=int, default=150, help="PNG output DPI (default: 150)")
    args = parser.parse_args()

    import rasterio
    from rasterio.transform import xy as transform_xy
    import geopandas as gpd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from shapely.geometry import LineString, MultiLineString
    import pandas as pd

    dem_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not dem_path.exists():
        print(f"ERROR: DEM not found: {dem_path}")
        return 1

    warnings = []
    assumptions = []

    # Load DEM
    print(f"Loading DEM: {dem_path.name}")
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(float)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        bounds = src.bounds
        height, width = dem.shape

    print(f"  Shape: {height}×{width}, CRS: {crs}, nodata: {nodata}")

    if nodata is not None:
        dem = np.where(dem == nodata, np.nan, dem)

    elev_min = float(np.nanmin(dem))
    elev_max = float(np.nanmax(dem))
    print(f"  Elevation range: {elev_min:.1f} – {elev_max:.1f}")

    # Optional smoothing
    if args.smooth:
        from scipy.ndimage import gaussian_filter
        fill = np.nanmean(dem)
        dem_filled = np.where(np.isnan(dem), fill, dem)
        dem = gaussian_filter(dem_filled, sigma=1.0)
        dem = np.where(np.isnan(np.where(dem == nodata, np.nan, dem)), np.nan, dem) if nodata else dem
        assumptions.append("Light Gaussian smoothing applied (sigma=1)")

    # Build coordinate arrays
    # rasterio transform: (col, row) → (x, y)
    px_x = transform.a   # pixel width (positive = east)
    px_y = transform.e   # pixel height (negative = north)
    origin_x = transform.c + px_x * 0.5  # center of first pixel
    origin_y = transform.f + px_y * 0.5

    x_arr = origin_x + px_x * np.arange(width)
    y_arr = origin_y + px_y * np.arange(height)

    # Contour levels
    first_level = np.ceil(elev_min / args.interval) * args.interval
    levels = np.arange(first_level, elev_max + args.interval, args.interval)

    if len(levels) == 0:
        print(f"ERROR: No contour levels in range [{elev_min:.1f}, {elev_max:.1f}] with interval {args.interval}")
        return 1

    print(f"Generating {len(levels)} contour level(s) at interval {args.interval}...")

    # Use matplotlib contour to extract paths
    fig_tmp, ax_tmp = plt.subplots()
    # Replace NaN with a value below minimum so contours don't bleed across nodata
    dem_plot = np.where(np.isnan(dem), elev_min - args.interval, dem)
    cs = ax_tmp.contour(x_arr, y_arr, dem_plot, levels=levels)
    plt.close(fig_tmp)

    # Convert matplotlib paths to shapely LineStrings
    records = []
    for level_idx, level in enumerate(cs.levels):
        # Get paths for this contour level
        if hasattr(cs, 'collections'):
            # Older matplotlib
            paths = cs.collections[level_idx].get_paths()
        else:
            # Newer matplotlib: use allSegs
            paths = [matplotlib.path.Path(seg) for seg in cs.allsegs[level_idx]]
        for path in paths:
            verts = path.vertices
            # Split on CLOSEPOLY codes if present
            codes = path.codes
            if codes is not None:
                # Split at MOVETO (code=1) segments
                segments = []
                current = []
                for v, c in zip(verts, codes):
                    if c == 1 and current:
                        segments.append(current)
                        current = [v]
                    else:
                        current.append(v)
                if current:
                    segments.append(current)
            else:
                segments = [verts]

            for seg in segments:
                if len(seg) >= 2:
                    try:
                        line = LineString(seg)
                        if line.is_valid and not line.is_empty:
                            records.append({
                                "elevation": float(level),
                                "geometry": line,
                            })
                    except Exception:
                        pass

    if len(records) == 0:
        print("WARNING: No contour lines generated — check interval and elevation range")
        warnings.append("No contour lines generated")

    print(f"  {len(records)} contour line segments generated")

    # Build GeoDataFrame
    contour_gdf = gpd.GeoDataFrame(records, crs=crs)

    # Summarize
    n_levels_with_data = int(contour_gdf["elevation"].nunique()) if len(contour_gdf) else 0
    total_length = float(contour_gdf.geometry.length.sum()) if len(contour_gdf) else 0

    print(f"  {n_levels_with_data} elevation levels with lines, total length: {total_length:.0f} CRS units")

    # Save GeoPackage
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(contour_gdf) > 0:
        contour_gdf.to_file(output_path, driver="GPKG")
        print(f"Output: {output_path}")
    else:
        print("WARNING: Empty result — GeoPackage not written")

    # Optional map
    if args.output_map and len(contour_gdf) > 0:
        map_path = Path(args.output_map).expanduser().resolve()
        map_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 10))
        fig.patch.set_facecolor("white")

        # Hillshade background
        from matplotlib.colors import LightSource
        ls = LightSource(azdeg=315, altdeg=45)
        dem_hs = ls.hillshade(dem_plot, vert_exag=1.5, dx=abs(px_x), dy=abs(px_y))
        ax.imshow(
            dem_hs, cmap="gray", origin="upper",
            extent=[x_arr[0], x_arr[-1], y_arr[-1], y_arr[0]],
            alpha=0.6,
        )

        # Contours colored by elevation
        norm = plt.Normalize(elev_min, elev_max)
        cmap = plt.cm.terrain
        for elev, group in contour_gdf.groupby("elevation"):
            color = cmap(norm(elev))
            lw = 0.8 if elev % (args.interval * 5) != 0 else 1.4
            group.plot(ax=ax, color=color, linewidth=lw)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, shrink=0.6, label="Elevation")

        ax.set_title(
            f"Contours: {dem_path.stem} (interval={args.interval})",
            fontsize=13, fontweight="bold",
        )
        ax.set_axis_off()
        plt.tight_layout()
        fig.savefig(map_path, dpi=args.dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"Map: {map_path}")

    # Build log
    log = {
        "step": "contour_generation",
        "input": str(dem_path),
        "output": str(output_path),
        "output_map": args.output_map,
        "interval": args.interval,
        "smooth": args.smooth,
        "n_levels": len(levels),
        "n_levels_with_data": n_levels_with_data,
        "n_line_segments": len(records),
        "elevation_range": [elev_min, elev_max],
        "total_length_crs_units": round(total_length, 2),
        "crs": str(crs),
        "raster_shape": [height, width],
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.contours.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
