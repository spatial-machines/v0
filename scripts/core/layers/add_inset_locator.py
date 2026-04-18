#!/usr/bin/env python3
"""Add an inset locator map showing study area within a larger context.

Fetches the containing state (or custom context geometry) from Census
cartographic boundary files and draws a small inset showing where the
study area sits.

Usage (module):
    from scripts.core.layers.add_inset_locator import render
    render(fig, ax, study_gdf, placement="upper-left", size=0.18)

Usage (CLI):
    python -m scripts.core.layers.add_inset_locator study.gpkg \
        -o with_inset.png --placement upper-left
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core" / "layers"))

from _base import detect_fips, basemap_theme_from_ax

STATE_CB_URL = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip"


def fetch_state_boundary(state_fips: str) -> gpd.GeoDataFrame:
    """Fetch state boundary from Census cartographic boundary files."""
    all_states = gpd.read_file(STATE_CB_URL)
    return all_states[all_states["STATEFP"] == state_fips].copy()


def render(fig, ax, study_gdf: gpd.GeoDataFrame, *,
           placement: str = "upper-left",
           size: float = 0.18,
           state_fips: str | None = None,
           context_gdf: gpd.GeoDataFrame | None = None,
           theme: str | None = None,
           highlight_color: str = "#c04040") -> bool:
    """Add inset locator map to the figure.

    Returns True if rendered successfully.

    Placement uses figure-relative coordinates so the inset sits in the
    margin, not over data.
    """
    # Detect FIPS or use provided context geometry
    if context_gdf is None:
        if not state_fips:
            detected_state, _ = detect_fips(study_gdf)
            state_fips = detected_state
        if not state_fips:
            return False
        try:
            context_gdf = fetch_state_boundary(state_fips)
        except Exception:
            return False

    if context_gdf.empty:
        return False

    if context_gdf.crs != study_gdf.crs:
        context_gdf = context_gdf.to_crs(study_gdf.crs)

    # Theme-aware palette
    if theme is None:
        theme = basemap_theme_from_ax(ax)
    if theme == "dark":
        ctx_fill, ctx_edge, border = "#2a2a2a", "#666666", "#888888"
    else:
        ctx_fill, ctx_edge, border = "#e8e8e8", "#888888", "#555555"

    # Figure-coordinate placement: put inset in the margin
    size = float(size)
    positions = {
        "upper-left":  [0.02, 0.78, size, size * 0.75],
        "upper-right": [0.98 - size, 0.78, size, size * 0.75],
        "lower-left":  [0.02, 0.02, size, size * 0.75],
        "lower-right": [0.98 - size, 0.02, size, size * 0.75],
    }
    bbox = positions.get(placement, positions["upper-left"])
    inset_ax = fig.add_axes(bbox)

    # Context (state outline)
    context_gdf.plot(ax=inset_ax, color=ctx_fill, edgecolor=ctx_edge, linewidth=0.5)

    # Highlight study area
    study_gdf.dissolve().plot(ax=inset_ax, color=highlight_color,
                              edgecolor=highlight_color, alpha=0.7, linewidth=0.5)

    # Frame
    for spine in inset_ax.spines.values():
        spine.set_edgecolor(border)
        spine.set_linewidth(0.7)
        spine.set_visible(True)

    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    # Zoom to context bounds with a small padding
    cb = context_gdf.total_bounds
    pad_x = (cb[2] - cb[0]) * 0.06
    pad_y = (cb[3] - cb[1]) * 0.06
    inset_ax.set_xlim(cb[0] - pad_x, cb[2] + pad_x)
    inset_ax.set_ylim(cb[1] - pad_y, cb[3] + pad_y)

    return True


def main() -> int:
    import argparse
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = argparse.ArgumentParser(description="Add inset locator map.")
    p.add_argument("input", help="Study area file")
    p.add_argument("--layer", help="Layer name for GeoPackage")
    p.add_argument("--placement", choices=["upper-left", "upper-right",
                                            "lower-left", "lower-right"],
                   default="upper-left")
    p.add_argument("--size", type=float, default=0.18, help="Inset size (figure fraction)")
    p.add_argument("--state-fips", help="Override state FIPS")
    p.add_argument("--context-gpkg", help="Use custom context geometry instead of state")
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    gdf = gpd.read_file(args.input, layer=args.layer) if args.layer else gpd.read_file(args.input)

    fig, ax = plt.subplots(figsize=(10, 10))
    bg = "#222222" if args.theme == "dark" else "#ffffff"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    gdf.plot(ax=ax, color="#cccccc", edgecolor="#444444", linewidth=0.3)
    ax.set_axis_off()

    ctx = gpd.read_file(args.context_gpkg) if args.context_gpkg else None
    ok = render(fig, ax, gdf, placement=args.placement, size=args.size,
                state_fips=args.state_fips, context_gdf=ctx, theme=args.theme)

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi)

    print(f"inset locator: {'rendered' if ok else 'SKIPPED'} -> {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
