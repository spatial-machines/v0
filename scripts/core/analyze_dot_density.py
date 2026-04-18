#!/usr/bin/env python3
"""Generate a dot density map — each dot represents N units of a count variable.

Dot density is the right choice when:
  - You have count data (people, households, cases)
  - You want to show distribution within polygons, not just polygon-level rates
  - You want to avoid the "large empty polygon dominates" problem of choropleth

Supports:
  - Single variable (one dot = N people)
  - Multi-variable (colored dots for different sub-populations, e.g. race/ethnicity)

Outputs:
  - PNG map
  - JSON handoff log

Usage:
    # Single variable
    python analyze_dot_density.py \\
        --input data/processed/tracts.gpkg \\
        --cols total_population \\
        --dots-per-unit 100 \\
        --output outputs/maps/population_dot_density.png

    # Multi-variable (e.g. race breakdown)
    python analyze_dot_density.py \\
        --input data/processed/tracts.gpkg \\
        --cols pop_white pop_black pop_hispanic pop_asian \\
        --colors "#4e79a7" "#f28e2b" "#e15759" "#76b7b2" \\
        --labels "White" "Black" "Hispanic" "Asian" \\
        --dots-per-unit 50 \\
        --output outputs/maps/race_dot_density.png
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from shapely.geometry import MultiPoint, Point

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default color palette (Tableau-ish)
DEFAULT_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
    "#9c755f", "#bab0ac",
]


def random_points_in_polygon(polygon, n, rng):
    """Generate n random points within a polygon using rejection sampling."""
    if n <= 0 or polygon is None or polygon.is_empty:
        return []

    minx, miny, maxx, maxy = polygon.bounds
    points = []
    attempts = 0
    max_attempts = n * 20

    while len(points) < n and attempts < max_attempts:
        batch_size = min((n - len(points)) * 4, 1000)
        xs = rng.uniform(minx, maxx, batch_size)
        ys = rng.uniform(miny, maxy, batch_size)
        for x, y in zip(xs, ys):
            pt = Point(x, y)
            if polygon.contains(pt):
                points.append((x, y))
                if len(points) >= n:
                    break
        attempts += batch_size

    return points[:n]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input GeoPackage (polygons)")
    parser.add_argument("--cols", nargs="+", required=True,
                        help="Count column(s) to map")
    parser.add_argument("--dots-per-unit", type=float, default=None,
                        help="How many real units each dot represents (default: auto)")
    parser.add_argument("--max-dots", type=int, default=50000,
                        help="Cap total dots (default: 50000) — reduces auto dots-per-unit")
    parser.add_argument("--colors", nargs="+", help="Dot colors per column")
    parser.add_argument("--labels", nargs="+", help="Legend labels per column")
    parser.add_argument("--dot-size", type=float, default=0.8,
                        help="Matplotlib marker size (default: 0.8)")
    parser.add_argument("--dot-alpha", type=float, default=0.6)
    parser.add_argument("--background-color", default="#1a1a2e",
                        help="Map background color (default: dark navy — dots pop)")
    parser.add_argument("--outline-color", default="#444466",
                        help="Polygon outline color (default: subtle dark)")
    parser.add_argument("--title", help="Map title")
    parser.add_argument("--attribution", help="Source attribution")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("-o", "--output")
    parser.add_argument("--figsize", default="14,10")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    gdf = gpd.read_file(src)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    # Project to UTM for accurate area/point placement
    utm_crs = gdf.estimate_utm_crs()
    gdf_proj = gdf.to_crs(utm_crs)

    missing = [c for c in args.cols if c not in gdf.columns]
    if missing:
        print(f"Columns not found: {missing}")
        print(f"Available: {[c for c in gdf.columns if c != 'geometry']}")
        return 2

    for col in args.cols:
        gdf_proj[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0).clip(lower=0)

    # Auto dots-per-unit
    total_units = sum(gdf_proj[col].sum() for col in args.cols)
    if args.dots_per_unit:
        dots_per_unit = args.dots_per_unit
    else:
        dots_per_unit = max(1, total_units / args.max_dots)
        print(f"Auto dots-per-unit: {dots_per_unit:.1f} (total={total_units:,.0f}, max_dots={args.max_dots})")

    colors = args.colors or DEFAULT_COLORS[:len(args.cols)]
    labels = args.labels or [c.replace("_", " ").title() for c in args.cols]

    rng = np.random.default_rng(args.seed)

    # Generate dots
    all_dots = {col: {"x": [], "y": []} for col in args.cols}
    total_dots = 0

    for idx, row in gdf_proj.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        for col in args.cols:
            count = row[col]
            if count <= 0:
                continue
            n_dots = max(0, int(round(count / dots_per_unit)))
            if n_dots == 0:
                continue

            pts = random_points_in_polygon(geom, n_dots, rng)
            for x, y in pts:
                all_dots[col]["x"].append(x)
                all_dots[col]["y"].append(y)
            total_dots += len(pts)

    print(f"Generated {total_dots:,} total dots")

    # Plot
    fw, fh = [float(x) for x in args.figsize.split(",")]
    fig, ax = plt.subplots(1, 1, figsize=(fw, fh))
    fig.patch.set_facecolor(args.background_color)
    ax.set_facecolor(args.background_color)

    # Draw polygon outlines (subtle)
    gdf_proj.plot(ax=ax, facecolor="none", edgecolor=args.outline_color,
                  linewidth=0.3, zorder=2)

    # Draw dots — shuffle order to prevent one layer always on top
    col_order = list(args.cols)
    rng.shuffle(col_order)

    for col in col_order:
        color_idx = args.cols.index(col)
        color = colors[color_idx] if color_idx < len(colors) else DEFAULT_COLORS[color_idx % len(DEFAULT_COLORS)]
        xs = all_dots[col]["x"]
        ys = all_dots[col]["y"]
        if xs:
            ax.scatter(xs, ys, s=args.dot_size, c=color, alpha=args.dot_alpha,
                       linewidths=0, zorder=5, rasterized=True)

    # Legend
    legend_patches = []
    for col, color, label in zip(args.cols, colors, labels):
        dot_count = len(all_dots[col]["x"])
        legend_patches.append(
            mpatches.Patch(color=color, alpha=0.8,
                           label=f"{label} ({dot_count:,} dots)")
        )

    dots_label = f"1 dot = {int(dots_per_unit):,}" if dots_per_unit >= 1 else f"1 dot = {dots_per_unit:.1f}"
    legend_patches.append(
        mpatches.Patch(color="none", label=dots_label)
    )

    legend = ax.legend(
        handles=legend_patches,
        loc="lower left",
        fontsize=8,
        framealpha=0.85,
        facecolor="#111122",
        labelcolor="white",
        edgecolor="#444",
    )

    # Title
    title = args.title or f"{', '.join(labels)} — Dot Density"
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=12,
                 color="white")
    ax.set_axis_off()

    if args.attribution:
        ax.text(0.99, 0.01, args.attribution, transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#888", style="italic")

    plt.tight_layout()

    # Output
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "maps"
        col_slug = "_".join(args.cols[:2])
        out_path = out_dir / f"{src.stem}_{col_slug}_dot_density.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=args.dpi, bbox_inches="tight",
                facecolor=args.background_color)
    plt.close(fig)
    print(f"Saved: {out_path}")

    log = {
        "step": "analyze_dot_density",
        "source": str(src),
        "cols": args.cols,
        "dots_per_unit": dots_per_unit,
        "total_dots": total_dots,
        "seed": args.seed,
        "output": str(out_path),
        "note": "Dots are randomly placed within polygons — positions are illustrative, not precise locations.",
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
