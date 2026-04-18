#!/usr/bin/env python3
"""Generate an animated GIF or MP4 choropleth showing change across time periods.

Each frame is one choropleth map for one time period. Frames are styled
identically (same classification, same color scale when --shared-scale is set).
A year/period label is overlaid on every frame.

Outputs:
  - Animated GIF or MP4
  - JSON log

Usage:
    python animate_time_series.py \\
        --inputs data/tracts_2010.gpkg data/tracts_2015.gpkg data/tracts_2020.gpkg \\
        --col poverty_rate \\
        --labels "2010" "2015" "2020" \\
        --output outputs/animations/poverty_time_series.gif \\
        --fps 2 \\
        --shared-scale \\
        --cmap YlOrRd \\
        --title "Poverty Rate Change 2010–2020"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _classify(values: pd.Series, scheme: str, k: int):
    """Return (bins, labels) using mapclassify."""
    import mapclassify

    clean = values.dropna()
    k = min(k, clean.nunique())
    if k < 2:
        k = 2

    clf_map = {
        "quantiles": mapclassify.Quantiles,
        "equal_interval": mapclassify.EqualInterval,
        "natural_breaks": mapclassify.NaturalBreaks,
        "std_mean": mapclassify.StdMean,
    }
    cls = clf_map.get(scheme, mapclassify.Quantiles)
    try:
        result = cls(clean, k=k)
    except Exception:
        result = mapclassify.Quantiles(clean, k=k)
    return result


def _get_shared_bins(gdfs: list, col: str, scheme: str, k: int):
    """Compute classification bins across all frames combined."""
    all_vals = pd.concat([gdf[col].dropna() for gdf in gdfs])
    return _classify(all_vals, scheme, k)


def _assign_colors(series: pd.Series, bins, cmap_name: str, missing_color: str) -> list:
    """Map series values to RGBA colors using pre-computed bins."""
    import mapclassify
    cmap = plt.get_cmap(cmap_name)
    n_classes = bins.k
    colors = []
    for val in series:
        if pd.isna(val):
            colors.append(missing_color)
        else:
            cls_idx = int(bins.find_bin(val))
            # Normalise to [0, 1]
            norm = cls_idx / max(n_classes - 1, 1)
            colors.append(cmap(norm))
    return colors


# ---------------------------------------------------------------------------
# Single-frame renderer
# ---------------------------------------------------------------------------

def render_frame(
    gdf: gpd.GeoDataFrame,
    col: str,
    label: str,
    title: str,
    cmap: str,
    scheme: str,
    k: int,
    missing_color: str,
    edge_color: str,
    edge_width: float,
    shared_bins=None,
    figsize=(14, 10),
    dpi: int = 100,
) -> plt.Figure:
    """Render one choropleth frame and return the Figure."""
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    null_mask = gdf[col].isna()
    non_null = gdf[~null_mask].copy()
    null_gdf = gdf[null_mask].copy()

    # Determine classification
    if shared_bins is not None:
        bins = shared_bins
    elif len(non_null) > 0:
        bins = _classify(non_null[col], scheme, k)
    else:
        bins = None

    # Plot null features as background
    if len(null_gdf) > 0:
        null_gdf.plot(ax=ax, color=missing_color, edgecolor=edge_color, linewidth=edge_width)

    # Plot classified features
    if bins is not None and len(non_null) > 0:
        face_colors = _assign_colors(non_null[col], bins, cmap, missing_color)
        non_null.plot(ax=ax, color=face_colors, edgecolor=edge_color, linewidth=edge_width)
    elif len(non_null) > 0:
        non_null.plot(ax=ax, edgecolor=edge_color, linewidth=edge_width)

    # State / dissolved outline on top
    try:
        outline = gdf.dissolve()
        outline.boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.2, zorder=20)
    except Exception:
        pass

    # Title
    if title:
        ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=10)

    # Period label overlay (bottom-right)
    text_obj = ax.text(
        0.97, 0.05, label,
        transform=ax.transAxes,
        fontsize=22, fontweight="bold",
        ha="right", va="bottom",
        color="white",
        zorder=30,
    )
    text_obj.set_path_effects([
        pe.Stroke(linewidth=3, foreground="#222222"),
        pe.Normal(),
    ])

    # Colorbar / legend
    if bins is not None and len(non_null) > 0:
        import matplotlib.patches as mpatches
        cmap_obj = plt.get_cmap(cmap)
        n_classes = bins.k
        patches = []
        bin_edges = sorted(set(bins.bins.tolist()))
        low = float(non_null[col].min())
        for i in range(n_classes):
            norm = i / max(n_classes - 1, 1)
            color = cmap_obj(norm)
            hi = bin_edges[i] if i < len(bin_edges) else float(non_null[col].max())
            if i == 0:
                lbl = f"≤ {hi:,.1f}"
            elif i == n_classes - 1:
                lbl = f"> {low:,.1f}"
            else:
                lbl = f"{low:,.1f} – {hi:,.1f}"
            patches.append(mpatches.Patch(facecolor=color, edgecolor="#888", label=lbl))
            low = hi
        ax.legend(
            handles=patches,
            loc="lower left",
            fontsize=7,
            title=col,
            title_fontsize=8,
            framealpha=0.85,
        )

    ax.set_axis_off()
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    return fig


# ---------------------------------------------------------------------------
# Frame-to-numpy array
# ---------------------------------------------------------------------------

def fig_to_array(fig: plt.Figure) -> "np.ndarray":
    """Convert a matplotlib Figure to a uint8 RGB numpy array."""
    fig.canvas.draw()
    buf = fig.canvas.buffer_rgba()
    arr = np.asarray(buf)
    plt.close(fig)
    return arr[:, :, :3]  # drop alpha → RGB


# ---------------------------------------------------------------------------
# GIF output via imageio
# ---------------------------------------------------------------------------

def save_gif(frames: list, output: Path, fps: int) -> None:
    import imageio.v3 as iio  # type: ignore

    duration_ms = int(1000 / fps)
    iio.imwrite(
        str(output),
        frames,
        extension=".gif",
        plugin="pillow",
        loop=0,
        duration=duration_ms,
    )


# ---------------------------------------------------------------------------
# MP4 output via ffmpeg subprocess
# ---------------------------------------------------------------------------

def save_mp4(frames: list, output: Path, fps: int) -> None:
    import imageio.v3 as iio  # type: ignore

    with tempfile.TemporaryDirectory() as tmpdir:
        frame_paths = []
        for i, arr in enumerate(frames):
            fpath = Path(tmpdir) / f"frame_{i:04d}.png"
            iio.imwrite(str(fpath), arr)
            frame_paths.append(fpath)

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(Path(tmpdir) / "frame_%04d.png"),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # ensure even dims
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(output),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg error:\n{result.stderr}", file=sys.stderr)
            raise RuntimeError("ffmpeg failed — see stderr above")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Animate a choropleth variable across multiple time periods."
    )
    parser.add_argument(
        "--inputs", nargs="+", required=True,
        help="Space-separated GeoPackage paths, one per time period (in order)",
    )
    parser.add_argument("--col", required=True, help="Column to animate")
    parser.add_argument(
        "--labels", nargs="+", required=True,
        help='Time-period labels matching --inputs order e.g. "2010" "2015" "2020"',
    )
    parser.add_argument(
        "--output", required=True,
        help="Output path (.gif or .mp4)",
    )
    parser.add_argument("--fps", type=int, default=2, help="Frames per second (default: 2)")
    parser.add_argument(
        "--shared-scale", action="store_true",
        help="Use the same classification bins across all frames",
    )
    parser.add_argument("--cmap", default="YlOrRd", help="Matplotlib colormap (default: YlOrRd)")
    parser.add_argument("--title", default="", help="Map title shown on every frame")
    parser.add_argument("--scheme", default="quantiles",
                        help="Classification scheme: quantiles|equal_interval|natural_breaks (default: quantiles)")
    parser.add_argument("--k", type=int, default=5, help="Number of classes (default: 5)")
    parser.add_argument("--missing-color", default="#d9d9d9",
                        help="Fill color for null values (default: #d9d9d9)")
    parser.add_argument("--figsize", default="14,10",
                        help="Figure size width,height in inches (default: 14,10)")
    parser.add_argument("--dpi", type=int, default=100, help="Frame DPI (default: 100)")
    parser.add_argument("--no-border", action="store_true",
                        help="Remove white edge lines between features")
    args = parser.parse_args()

    # --- validate inputs / labels match ---
    if len(args.inputs) != len(args.labels):
        print(
            f"ERROR: --inputs ({len(args.inputs)}) and --labels ({len(args.labels)}) must have the same count",
            file=sys.stderr,
        )
        return 1

    output = Path(args.output).expanduser().resolve()
    suffix = output.suffix.lower()
    if suffix not in (".gif", ".mp4"):
        print("ERROR: --output must end in .gif or .mp4", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        fw, fh = [float(x) for x in args.figsize.split(",")]
    except ValueError:
        fw, fh = 14, 10

    edge_color = "none" if args.no_border else "white"
    edge_width = 0 if args.no_border else 0.18

    warnings: list[str] = []
    assumptions: list[str] = []

    # --- load all GeoPackages ---
    print(f"Loading {len(args.inputs)} input layers...")
    gdfs: list[gpd.GeoDataFrame] = []
    for i, path_str in enumerate(args.inputs):
        p = Path(path_str).expanduser().resolve()
        if not p.exists():
            print(f"ERROR: input not found: {p}", file=sys.stderr)
            return 1
        gdf = gpd.read_file(p)
        if args.col not in gdf.columns:
            print(
                f"ERROR: column '{args.col}' not found in {p}\n"
                f"  available: {[c for c in gdf.columns if c != 'geometry']}",
                file=sys.stderr,
            )
            return 1
        if not pd.api.types.is_numeric_dtype(gdf[args.col]):
            gdf[args.col] = pd.to_numeric(gdf[args.col], errors="coerce")
            assumptions.append(f"coerced '{args.col}' to numeric in frame {i}")
        null_ct = int(gdf[args.col].isna().sum())
        if null_ct > 0:
            warnings.append(f"frame {i} ({args.labels[i]}): {null_ct}/{len(gdf)} nulls in '{args.col}'")
        gdfs.append(gdf)
        print(f"  [{i+1}/{len(args.inputs)}] loaded {p.name}  ({len(gdf)} features, {null_ct} nulls)")

    # --- shared classification ---
    shared_bins = None
    if args.shared_scale:
        shared_bins = _get_shared_bins(gdfs, args.col, args.scheme, args.k)
        assumptions.append(f"shared classification: {args.scheme}, k={shared_bins.k}")
        print(f"Shared classification: {args.scheme}, k={shared_bins.k}")
    else:
        assumptions.append(f"per-frame classification: {args.scheme}, k={args.k}")

    # --- render frames ---
    frames: list[np.ndarray] = []
    n = len(gdfs)
    print(f"\nRendering {n} frames...")
    for i, (gdf, label) in enumerate(zip(gdfs, args.labels)):
        pct = int((i + 1) / n * 40)
        bar = "█" * pct + "░" * (40 - pct)
        print(f"  [{bar}] frame {i+1}/{n}  ({label})", end="\r", flush=True)
        fig = render_frame(
            gdf=gdf,
            col=args.col,
            label=label,
            title=args.title or args.col.replace("_", " ").title(),
            cmap=args.cmap,
            scheme=args.scheme,
            k=args.k,
            missing_color=args.missing_color,
            edge_color=edge_color,
            edge_width=edge_width,
            shared_bins=shared_bins,
            figsize=(fw, fh),
            dpi=args.dpi,
        )
        frames.append(fig_to_array(fig))

    print()  # newline after progress bar
    print(f"\nRendered {len(frames)} frames at {fw:.0f}x{fh:.0f}in @ {args.dpi} DPI")

    # --- encode output ---
    print(f"Encoding {suffix.upper()} → {output} ...")
    if suffix == ".gif":
        save_gif(frames, output, args.fps)
    else:
        save_mp4(frames, output, args.fps)

    # --- log ---
    log = {
        "step": "animate_time_series",
        "inputs": [str(Path(p).expanduser().resolve()) for p in args.inputs],
        "col": args.col,
        "labels": args.labels,
        "output": str(output),
        "format": suffix.lstrip("."),
        "fps": args.fps,
        "shared_scale": args.shared_scale,
        "scheme": args.scheme,
        "k": args.k if shared_bins is None else shared_bins.k,
        "cmap": args.cmap,
        "title": args.title,
        "frame_count": len(frames),
        "dpi": args.dpi,
        "figsize": f"{fw},{fh}",
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = output.with_suffix(".animation.json")
    log_path.write_text(json.dumps(log, indent=2))

    print(f"\nDone: {output}")
    print(f"Log:  {log_path}")
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
