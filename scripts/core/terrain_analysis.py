#!/usr/bin/env python3
"""Compute terrain derivatives from a DEM raster.

Usage:
    python terrain_analysis.py \\
        --input data/rasters/dem.tif \\
        --output-dir outputs/terrain/ \\
        --products slope aspect hillshade tri tpi roughness
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def _hillshade_numpy(arr, transform, azimuth=315.0, altitude=45.0, nodata=None):
    """Compute hillshade from a DEM array using numpy (fallback if richdem unavailable)."""
    mask = None
    if nodata is not None:
        mask = arr == nodata

    az_rad = np.deg2rad(360.0 - azimuth + 90.0)
    alt_rad = np.deg2rad(altitude)

    # Pixel size from transform
    px = abs(transform.a)
    py = abs(transform.e)

    # Gradient
    dz_dx = np.gradient(arr.astype(float), px, axis=1)
    dz_dy = np.gradient(arr.astype(float), py, axis=0)

    slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect = np.arctan2(-dz_dy, dz_dx)

    hs = (np.cos(alt_rad) * np.cos(slope)
          + np.sin(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
    hs = np.clip(hs, 0, 1) * 255.0

    if mask is not None:
        hs[mask] = 0

    return hs.astype(np.float32)


def _slope_numpy(arr, transform, nodata=None):
    """Compute slope in degrees using numpy gradient."""
    mask = None
    if nodata is not None:
        mask = arr == nodata

    px = abs(transform.a)
    py = abs(transform.e)
    dz_dx = np.gradient(arr.astype(float), px, axis=1)
    dz_dy = np.gradient(arr.astype(float), py, axis=0)
    slope = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))

    if mask is not None:
        slope[mask] = np.nan

    return slope.astype(np.float32)


def _aspect_numpy(arr, transform, nodata=None):
    """Compute aspect in degrees (0=N, 90=E) using numpy gradient."""
    mask = None
    if nodata is not None:
        mask = arr == nodata

    px = abs(transform.a)
    py = abs(transform.e)
    dz_dx = np.gradient(arr.astype(float), px, axis=1)
    dz_dy = np.gradient(arr.astype(float), py, axis=0)

    aspect = np.degrees(np.arctan2(dz_dy, dz_dx))
    aspect = (450.0 - aspect) % 360.0  # Convert to compass bearing

    if mask is not None:
        aspect[mask] = np.nan

    return aspect.astype(np.float32)


def _tri_numpy(arr, nodata=None):
    """Terrain Ruggedness Index: mean absolute difference from neighbors."""
    from scipy.ndimage import generic_filter

    def tri_kernel(x):
        center = x[4]
        if np.isnan(center):
            return np.nan
        neighbors = np.delete(x, 4)
        valid = neighbors[~np.isnan(neighbors)]
        if len(valid) == 0:
            return 0.0
        return float(np.mean(np.abs(valid - center)))

    arr_f = arr.astype(float)
    if nodata is not None:
        arr_f[arr == nodata] = np.nan

    result = generic_filter(arr_f, tri_kernel, size=3, mode='nearest')
    return result.astype(np.float32)


def _tpi_numpy(arr, nodata=None):
    """Topographic Position Index: center minus mean of neighbors."""
    from scipy.ndimage import uniform_filter

    arr_f = arr.astype(float)
    if nodata is not None:
        arr_f[arr == nodata] = np.nan

    mean_neighbors = uniform_filter(arr_f, size=3, mode='nearest')
    tpi = arr_f - mean_neighbors
    return tpi.astype(np.float32)


def _roughness_numpy(arr, nodata=None):
    """Roughness: max - min in 3x3 neighborhood."""
    from scipy.ndimage import maximum_filter, minimum_filter

    arr_f = arr.astype(float)
    if nodata is not None:
        arr_f[arr == nodata] = np.nan

    arr_clean = np.where(np.isnan(arr_f), -1e9, arr_f)
    arr_clean2 = np.where(np.isnan(arr_f), 1e9, arr_f)
    roughness = maximum_filter(arr_clean, size=3) - minimum_filter(arr_clean2, size=3)
    roughness[np.isnan(arr_f)] = np.nan
    return roughness.astype(np.float32)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute terrain derivatives from a DEM raster."
    )
    parser.add_argument("--input", required=True, help="Input DEM raster (GeoTIFF)")
    parser.add_argument("--output-dir", required=True, help="Output directory for products")
    parser.add_argument(
        "--products",
        nargs="+",
        default=["slope", "hillshade"],
        choices=["slope", "aspect", "hillshade", "tri", "tpi", "roughness"],
        help="Terrain products to compute (default: slope hillshade)",
    )
    parser.add_argument(
        "--hillshade-azimuth", type=float, default=315.0,
        help="Hillshade azimuth in degrees (default: 315)"
    )
    parser.add_argument(
        "--hillshade-altitude", type=float, default=45.0,
        help="Hillshade sun altitude in degrees (default: 45)"
    )
    parser.add_argument("--dpi", type=int, default=150, help="PNG output DPI (default: 150)")
    args = parser.parse_args()

    import rasterio
    from rasterio.transform import from_bounds
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dem_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()

    if not dem_path.exists():
        print(f"ERROR: DEM not found: {dem_path}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    # Try to import richdem
    try:
        import richdem as rd
        has_richdem = True
        print("richdem available — using for terrain analysis")
    except Exception as e:
        has_richdem = False
        print(f"richdem not available ({e}) — using numpy fallback implementations")

    # Load DEM
    print(f"Loading DEM from {dem_path}...")
    with rasterio.open(dem_path) as src:
        dem_arr = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        bounds = src.bounds
        shape = (src.height, src.width)

    print(f"  Shape: {shape}, CRS: {crs}, nodata: {nodata}")
    print(f"  Elevation range: {np.nanmin(dem_arr.astype(float)):.1f} – {np.nanmax(dem_arr.astype(float)):.1f}")

    warnings = []
    assumptions = []
    outputs = {}

    if nodata is not None:
        dem_arr_masked = dem_arr.astype(float)
        dem_arr_masked[dem_arr == nodata] = np.nan
    else:
        dem_arr_masked = dem_arr.astype(float)

    # Update profile for float32 outputs
    out_profile = profile.copy()
    out_profile.update(dtype="float32", count=1, nodata=np.nan, compress="lzw")

    def save_tiff(arr, name):
        path = out_dir / f"{dem_path.stem}_{name}.tif"
        p = out_profile.copy()
        arr_out = arr.copy()
        with rasterio.open(path, "w", **p) as dst:
            dst.write(arr_out[np.newaxis, :, :])
        return path

    def save_png(arr, name, cmap, title):
        path = out_dir / f"{dem_path.stem}_{name}.png"
        fig, ax = plt.subplots(figsize=(10, 8))
        # Mask nans for display
        display = np.where(np.isnan(arr), np.nanmin(arr), arr)
        im = ax.imshow(display, cmap=cmap, interpolation="bilinear")
        plt.colorbar(im, ax=ax, shrink=0.6, label=title)
        ax.set_title(f"{title}\n{dem_path.stem}", fontsize=12, fontweight="bold")
        ax.set_axis_off()
        plt.tight_layout()
        fig.savefig(path, dpi=args.dpi, bbox_inches="tight")
        plt.close(fig)
        return path

    for product in args.products:
        print(f"Computing {product}...")

        if product == "slope":
            if has_richdem:
                try:
                    rd_arr = rd.rdarray(dem_arr_masked, no_data=np.nan)
                    result = rd.TerrainAttribute(rd_arr, attrib="slope_degrees")
                    arr = np.array(result).astype(np.float32)
                except Exception as e:
                    print(f"  richdem failed ({e}), using numpy fallback")
                    warnings.append(f"richdem slope failed: {e}")
                    arr = _slope_numpy(dem_arr, transform, nodata)
            else:
                arr = _slope_numpy(dem_arr, transform, nodata)

            tiff_path = save_tiff(arr, "slope")
            png_path = save_png(arr, "slope", "RdYlGn_r", "Slope (degrees)")
            outputs["slope_tif"] = str(tiff_path)
            outputs["slope_png"] = str(png_path)
            print(f"  Slope range: {np.nanmin(arr):.1f}° – {np.nanmax(arr):.1f}°")
            print(f"  -> {tiff_path}")

        elif product == "aspect":
            if has_richdem:
                try:
                    rd_arr = rd.rdarray(dem_arr_masked, no_data=np.nan)
                    result = rd.TerrainAttribute(rd_arr, attrib="aspect")
                    arr = np.array(result).astype(np.float32)
                except Exception as e:
                    print(f"  richdem failed ({e}), using numpy fallback")
                    warnings.append(f"richdem aspect failed: {e}")
                    arr = _aspect_numpy(dem_arr, transform, nodata)
            else:
                arr = _aspect_numpy(dem_arr, transform, nodata)

            tiff_path = save_tiff(arr, "aspect")
            png_path = save_png(arr, "aspect", "hsv", "Aspect (degrees, 0=N)")
            outputs["aspect_tif"] = str(tiff_path)
            outputs["aspect_png"] = str(png_path)
            print(f"  -> {tiff_path}")

        elif product == "hillshade":
            arr = _hillshade_numpy(
                dem_arr, transform,
                azimuth=args.hillshade_azimuth,
                altitude=args.hillshade_altitude,
                nodata=nodata,
            )
            assumptions.append(
                f"Hillshade: azimuth={args.hillshade_azimuth}°, altitude={args.hillshade_altitude}°"
            )

            tiff_path = save_tiff(arr, "hillshade")
            png_path = save_png(arr, "hillshade", "gray", "Hillshade")
            outputs["hillshade_tif"] = str(tiff_path)
            outputs["hillshade_png"] = str(png_path)
            print(f"  -> {tiff_path}")

        elif product == "tri":
            if has_richdem:
                try:
                    rd_arr = rd.rdarray(dem_arr_masked, no_data=np.nan)
                    result = rd.TerrainAttribute(rd_arr, attrib="TRI")
                    arr = np.array(result).astype(np.float32)
                except Exception as e:
                    print(f"  richdem TRI failed ({e}), using numpy fallback")
                    warnings.append(f"richdem TRI failed: {e}")
                    arr = _tri_numpy(dem_arr, nodata)
            else:
                arr = _tri_numpy(dem_arr, nodata)

            tiff_path = save_tiff(arr, "tri")
            png_path = save_png(arr, "tri", "YlOrRd", "Terrain Ruggedness Index")
            outputs["tri_tif"] = str(tiff_path)
            outputs["tri_png"] = str(png_path)
            print(f"  -> {tiff_path}")

        elif product == "tpi":
            if has_richdem:
                try:
                    rd_arr = rd.rdarray(dem_arr_masked, no_data=np.nan)
                    result = rd.TerrainAttribute(rd_arr, attrib="TPI")
                    arr = np.array(result).astype(np.float32)
                except Exception as e:
                    print(f"  richdem TPI failed ({e}), using numpy fallback")
                    warnings.append(f"richdem TPI failed: {e}")
                    arr = _tpi_numpy(dem_arr, nodata)
            else:
                arr = _tpi_numpy(dem_arr, nodata)

            tiff_path = save_tiff(arr, "tpi")
            png_path = save_png(arr, "tpi", "RdBu", "Topographic Position Index")
            outputs["tpi_tif"] = str(tiff_path)
            outputs["tpi_png"] = str(png_path)
            print(f"  -> {tiff_path}")

        elif product == "roughness":
            arr = _roughness_numpy(dem_arr, nodata)

            tiff_path = save_tiff(arr, "roughness")
            png_path = save_png(arr, "roughness", "magma", "Roughness (m)")
            outputs["roughness_tif"] = str(tiff_path)
            outputs["roughness_png"] = str(png_path)
            print(f"  -> {tiff_path}")

    # Build log
    log = {
        "step": "terrain_analysis",
        "input": str(dem_path),
        "output_dir": str(out_dir),
        "products": args.products,
        "hillshade_azimuth": args.hillshade_azimuth,
        "hillshade_altitude": args.hillshade_altitude,
        "raster_shape": list(shape),
        "raster_crs": str(crs),
        "raster_nodata": nodata,
        "elevation_range": [
            float(np.nanmin(dem_arr_masked)),
            float(np.nanmax(dem_arr_masked)),
        ],
        "richdem_used": has_richdem,
        "outputs": outputs,
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = out_dir / f"{dem_path.stem}_terrain_analysis.json"
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    print(f"Terrain analysis complete — {len(args.products)} product(s) saved to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
