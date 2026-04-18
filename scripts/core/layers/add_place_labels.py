#!/usr/bin/env python3
"""Label cities, towns, or neighborhoods on a map.

Usable as CLI or module. Pulls Census TIGER PLACE features (incorporated
cities/towns) by default, with an option to use a user-provided labels
GeoPackage for neighborhoods or custom places.

Usage (CLI):
    python -m scripts.core.layers.add_place_labels study.gpkg \
        --top-n 10 -o labeled.png

Usage (module):
    from scripts.core.layers.add_place_labels import render
    render(ax, study_gdf, top_n=10, theme="dark")
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core" / "layers"))

from _base import detect_fips, basemap_theme_from_ax, font_chain

PLACE_URL = "https://www2.census.gov/geo/tiger/TIGER{year}/PLACE/tl_{year}_{state}_place.zip"


def fetch_places(state_fips: str, year: int = 2022) -> gpd.GeoDataFrame:
    """Fetch all incorporated places for a state."""
    url = PLACE_URL.format(year=year, state=state_fips)
    return gpd.read_file(url)


def render(ax, study_gdf: gpd.GeoDataFrame, *,
           top_n: int = 10,
           state_fips: str | None = None,
           year: int = 2022,
           custom_gdf: gpd.GeoDataFrame | None = None,
           name_col: str = "NAME",
           rank_col: str = "ALAND",
           theme: str | None = None,
           fontsize: float = 9,
           font_family: str = "Gill Sans MT, Calibri, sans-serif",
           zorder: int = 30) -> int:
    """Label the top-N places by area/rank on the existing axes.

    Returns the number of labels actually rendered.
    """
    if custom_gdf is not None:
        places = custom_gdf.copy()
    else:
        if not state_fips:
            detected_state, _ = detect_fips(study_gdf)
            state_fips = detected_state
        if not state_fips:
            return 0
        try:
            places = fetch_places(state_fips, year)
        except Exception:
            return 0

    if places.empty or name_col not in places.columns:
        return 0

    # Reproject to match study area
    if places.crs != study_gdf.crs:
        places = places.to_crs(study_gdf.crs)

    # Clip to the actual study area geometry, not just its bounding box.
    # Using bbox would include places in adjacent counties (e.g., Aurora
    # appears near Chicago's bbox but is in Kane County, not Cook).
    study_union = study_gdf.union_all()
    place_centroids = places.geometry.representative_point()
    places = places[place_centroids.within(study_union)].copy()
    if places.empty:
        return 0

    # Pick top N by rank column (default: area)
    if rank_col in places.columns:
        places = places.nlargest(top_n, rank_col)
    else:
        places = places.head(top_n)

    # Theme-aware label styling
    if theme is None:
        theme = basemap_theme_from_ax(ax)
    if theme == "dark":
        label_color, halo_color = "#ffffff", "#000000"
    else:
        label_color, halo_color = "#1a1a1a", "#ffffff"

    import matplotlib.patheffects as pe
    path_effects = [pe.withStroke(linewidth=2.5, foreground=halo_color)]

    rendered = 0
    for _, row in places.iterrows():
        pt = row.geometry.representative_point()
        ax.text(pt.x, pt.y, row[name_col],
                fontsize=fontsize, fontweight="bold",
                ha="center", va="center",
                color=label_color, fontfamily=font_chain(font_family),
                path_effects=path_effects, zorder=zorder)
        rendered += 1

    return rendered


def main() -> int:
    import argparse
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = argparse.ArgumentParser(description="Label places on a map.")
    p.add_argument("input", help="Study area file (provides bbox + FIPS)")
    p.add_argument("--layer", help="Layer name for GeoPackage")
    p.add_argument("--top-n", type=int, default=10, help="Number of top places to label")
    p.add_argument("--state-fips", help="Override state FIPS (2 digits)")
    p.add_argument("--year", type=int, default=2022, help="TIGER vintage year")
    p.add_argument("--custom-places", help="Use a custom GeoPackage of places instead of TIGER")
    p.add_argument("--name-col", default="NAME", help="Column containing place names")
    p.add_argument("--rank-col", default="ALAND",
                   help="Column to rank by (largest N)")
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    gdf = gpd.read_file(args.input, layer=args.layer) if args.layer else gpd.read_file(args.input)

    fig, ax = plt.subplots(figsize=(10, 10))
    bg = "#222222" if args.theme == "dark" else "#ffffff"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    outline_color = "#888888" if args.theme == "light" else "#aaaaaa"
    gdf.boundary.plot(ax=ax, color=outline_color, linewidth=0.5)

    custom = gpd.read_file(args.custom_places) if args.custom_places else None
    n = render(ax, gdf, top_n=args.top_n, state_fips=args.state_fips,
               year=args.year, custom_gdf=custom, name_col=args.name_col,
               rank_col=args.rank_col, theme=args.theme)

    ax.set_axis_off()
    fig.tight_layout()

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi, bbox_inches="tight")

    print(f"place labels: {n} rendered -> {out}")
    return 0 if n > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
