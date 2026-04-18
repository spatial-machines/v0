#!/usr/bin/env python3
"""Compose a delivery-quality food access map for Cook County, Illinois.

This script demonstrates how a cartography agent would chain modular
layer scripts to build a complete map. Reference layer selection
follows the narrative test from wiki/standards/CARTOGRAPHY_STANDARD.md
and wiki/domains/PHARMACY_AND_FOOD_ACCESS.md:

- Supermarkets are the CAUSAL layer: food deserts are defined by
  absence of food retailers, so the point layer makes the story
  legible at a glance (gaps in the point cloud = food access risk).
- Transit lines are RELEVANT: people without cars depend on transit
  to reach supermarkets, so showing CTA/Metra/Pace lines clarifies
  who is truly cut off.
- Hydrography is NOT included: water does not affect food access in
  Cook County. Adding Lake Michigan as blue would be decorative
  clutter, not analytical context. The basemap's faint water
  rendering is sufficient.

Layer stack (z-order low → high):
  1. Base: poverty-rate choropleth by tract (the structural driver)
  2. Basemap: CartoDB Positron for contextual streets
  3. Supermarkets: OSM retailers — where food physically IS. Gaps
     in this point layer tell the food-desert story.
  4. Place labels: major Cook County cities/suburbs for orientation
  5. Top-N annotations: neighborhoods with highest poverty, plus
     multivariable context (food access score, median income)
  6. Inset locator: Cook County within Illinois, placed in margin
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core" / "layers"))

from style_utils import load_styles  # noqa: E402
import add_place_labels  # noqa: E402
import add_inset_locator  # noqa: E402
import add_top_n_annotations  # noqa: E402
import add_points_layer  # noqa: E402

ANALYSIS_DIR = Path(__file__).resolve().parent
DATA = ANALYSIS_DIR / "data" / "processed" / "cook_food_access.gpkg"
SUPERMARKETS = ANALYSIS_DIR / "data" / "raw" / "cook_supermarkets.gpkg"
OUT = ANALYSIS_DIR / "outputs" / "maps" / "food_access_composed.png"


def main() -> int:
    # --- Load the joined data once ------------------------------------
    gdf = gpd.read_file(DATA)
    print(f"loaded {len(gdf)} Cook County tracts")

    # --- Build the figure ---------------------------------------------
    # Compute aspect ratio from data bounds so the frame fits the geography
    import math
    bounds = gdf.total_bounds
    mean_lat = (bounds[1] + bounds[3]) / 2
    aspect = ((bounds[2] - bounds[0]) * math.cos(math.radians(mean_lat))) / (bounds[3] - bounds[1])
    target_area = 140  # inches^2
    fh = max(6, min(14, math.sqrt(target_area / aspect)))
    fw = max(6, min(14, fh * aspect))

    fig, ax = plt.subplots(figsize=(fw, fh))

    # --- Layer 1: basemap + choropleth ---------------------------------
    # For this composition demo we draw the polygons directly here with
    # the same palette choices analyze_choropleth.py would make. A cleaner
    # path is to import a render() function from analyze_choropleth — we
    # are doing it inline here for clarity.
    import contextily as cx
    import mapclassify as mc

    # Choice of rendered variable:
    #   food_access_score is heavily saturated — ~25% of tracts score 0 and
    #   a long tail hits the 100-point ceiling, which made every top-3
    #   callout read "100 pts" (uninformative). PovertyRate is the
    #   structural driver of food access inequity, varies continuously
    #   from 0.3% to 77%, and maps to the same YlOrRd palette
    #   (poverty_rate → YlOrRd in config/map_styles.json).
    field = "PovertyRate"
    values = gdf[field].dropna().to_numpy()
    cls = mc.NaturalBreaks(values, k=5)

    # Build legend labels with en-dash separators and integer % units
    # (replaces geopandas' default "a.bc, d.ef" formatting which looks
    # amateur and ignores the en-dash rule in the cartography standard).
    breaks = [float(values.min())] + [float(b) for b in cls.bins]
    legend_labels = [
        f"{breaks[i]:.0f}\u2013{breaks[i+1]:.0f}%" for i in range(len(breaks) - 1)
    ]

    # Plot polygons
    gdf.plot(
        ax=ax,
        column=field,
        scheme="NaturalBreaks",
        k=5,
        cmap="YlOrRd",
        edgecolor="#444444",
        linewidth=0.25,
        alpha=0.92,
        legend=True,
        legend_kwds={
            "loc": "lower left",
            "fontsize": 9,
            "title": "Poverty Rate",
            "title_fontsize": 10,
            "framealpha": 1.0,
            "edgecolor": "#666666",
            "facecolor": "#ffffff",
            "borderpad": 1.0,
            "labels": legend_labels,
        },
        missing_kwds={"color": "#d0d0d0"},
    )

    # Light basemap for geographic context
    try:
        cx.add_basemap(ax, crs=gdf.crs, source=cx.providers.CartoDB.PositronNoLabels,
                       attribution=False, zoom="auto")
        print("basemap: CartoDB Positron")
    except Exception as e:
        print(f"basemap skipped: {e}")

    # --- Layer 2: supermarket overlay (the causal story) ---------------
    # Food deserts are defined by distance to supermarkets. Showing where
    # supermarkets ARE makes the absence visible and turns the choropleth
    # into a causal narrative: where is poverty high AND supermarkets absent?
    if SUPERMARKETS.exists():
        sm = gpd.read_file(SUPERMARKETS)
        sm_n = add_points_layer.render(
            ax, gdf, sm,
            marker="o", size=8, color="#1e4d8c",
            edge_color="#ffffff", edge_width=0.4,
            alpha=0.85, label="Supermarket", zorder=14,
        )
        print(f"supermarkets: {sm_n} rendered")

    # --- Layer 4: place labels -----------------------------------------
    place_n = add_place_labels.render(ax, gdf, top_n=8, theme="light", fontsize=10)
    print(f"place labels: {place_n} rendered")

    # --- Layer 4: top-N annotations ------------------------------------
    # Popup-style multi-line callouts with the neighborhood name plus
    # multiple context variables so readers see WHY each tract matters.
    # PovertyRate is the primary value (it's the rendered variable);
    # food_access_score and median income add concrete context.
    #
    # The layer script auto-generates a primary-line label from the
    # field name via field.replace("_"," ").title(), which turns the
    # camelCase "PovertyRate" into the ugly "Povertyrate". Rebind the
    # column to a snake_case alias just for annotation input so the
    # auto-label renders as "Poverty Rate".
    gdf_annot = gdf.rename(columns={"PovertyRate": "poverty_rate",
                                    "MedianFamilyIncome": "median_family_income"})
    annot_n = add_top_n_annotations.render(
        ax, gdf_annot, field="poverty_rate", n=3, label_field="community_area",
        value_format="{:.0f}", value_suffix="%",
        extra_fields=[
            ("food_access_score", "Food access burden", "{:.0f}/100"),
            ("median_family_income", "Med. income", "${:,.0f}"),
        ],
        theme="light",
    )
    print(f"top-N annotations: {annot_n} rendered")

    # --- Title, attribution, axis -------------------------------------
    # Title frames the story: poverty is the structural driver of the
    # food access gap. The rendered variable is PovertyRate; food access
    # score shows up as context in the callouts and in the subtitle.
    ax.set_title(
        "Poverty as the Structural Driver of Food Access in Cook County, Illinois",
        fontsize=14, fontweight="bold", color="#1a1a1a",
        fontfamily=["Georgia", "Palatino Linotype", "serif"], pad=14,
    )
    ax.set_axis_off()

    # Attribution goes in the lower-RIGHT so it does not collide with
    # the legend (lower-left). Vision QA #4 requires them in separate
    # corners.
    ax.text(
        0.99, 0.01,
        "Sources: USDA Food Access Research Atlas (2019); ACS 5-Year (2018–2022); Census TIGER 2022",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7, style="italic", color="#666666",
        fontfamily=["Gill Sans MT", "Calibri", "sans-serif"],
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=2.0),
    )

    # --- Layer 5: inset locator (added last, uses figure coords) -------
    inset_ok = add_inset_locator.render(
        fig, ax, gdf, placement="upper-left", size=0.15, theme="light"
    )
    print(f"inset locator: {'rendered' if inset_ok else 'skipped'}")

    # --- Save ---------------------------------------------------------
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\n-> {OUT}")
    print(f"   {OUT.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
