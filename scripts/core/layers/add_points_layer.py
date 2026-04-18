#!/usr/bin/env python3
"""Render a points-of-interest layer on a map as context.

Use this to overlay grocery stores, transit stops, hospitals, schools,
or any other point layer on top of a choropleth. Supports category-based
marker styling and optional labeling of named features.

Usage (module):
    from scripts.core.layers.add_points_layer import render
    render(ax, study_gdf, points_gdf,
           marker="o", size=20, color="#2a7f3e",
           label="Supermarkets")

Usage (CLI):
    python -m scripts.core.layers.add_points_layer study.gpkg \
        --points groceries.gpkg -o overlaid.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core" / "layers"))

from _base import basemap_theme_from_ax


def render(ax, study_gdf: gpd.GeoDataFrame,
           points_gdf: gpd.GeoDataFrame, *,
           marker: str = "o",
           size: float = 20,
           color: str = "#2a7f3e",
           edge_color: str = "#ffffff",
           edge_width: float = 0.6,
           alpha: float = 0.85,
           label: str | None = None,
           clip_to_study: bool = True,
           theme: str | None = None,
           zorder: int = 15) -> int:
    """Render a point layer on an existing axes.

    Returns number of points rendered.

    Points are clipped to the study area geometry by default so points
    in adjacent counties don't show up.
    """
    if points_gdf is None or points_gdf.empty:
        return 0

    # Reproject to match the study area
    if study_gdf.crs and points_gdf.crs != study_gdf.crs:
        points_gdf = points_gdf.to_crs(study_gdf.crs)

    # Clip to study area geometry (not bbox)
    if clip_to_study:
        study_union = study_gdf.union_all()
        points_gdf = points_gdf[points_gdf.geometry.within(study_union)].copy()

    if points_gdf.empty:
        return 0

    points_gdf.plot(
        ax=ax,
        marker=marker,
        markersize=size,
        color=color,
        edgecolor=edge_color,
        linewidth=edge_width,
        alpha=alpha,
        zorder=zorder,
        label=label,
    )
    return len(points_gdf)


def main() -> int:
    import argparse
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = argparse.ArgumentParser(description="Overlay points on a map.")
    p.add_argument("input", help="Study-area GeoPackage (provides bounds + clip)")
    p.add_argument("--points", required=True, help="Points GeoPackage")
    p.add_argument("--marker", default="o")
    p.add_argument("--size", type=float, default=20)
    p.add_argument("--color", default="#2a7f3e")
    p.add_argument("--label", help="Legend label")
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    study = gpd.read_file(args.input)
    points = gpd.read_file(args.points)

    fig, ax = plt.subplots(figsize=(10, 10))
    bg = "#222222" if args.theme == "dark" else "#ffffff"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    study.boundary.plot(ax=ax, color="#888888", linewidth=0.5)
    bounds = study.total_bounds
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])

    n = render(ax, study, points, marker=args.marker, size=args.size,
               color=args.color, label=args.label, theme=args.theme)

    if args.label:
        ax.legend(loc="lower right")

    ax.set_axis_off()
    fig.tight_layout()

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi, bbox_inches="tight")

    print(f"points layer: {n} rendered -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
