#!/usr/bin/env python3
"""Annotate top-N features by a given field with spatially-aware callouts.

Label placement is a spatial decision: the script pushes labels outward
from the map center, enforces angular separation between adjacent labels,
and uses adjustText for final overlap resolution.

Usage (module):
    from scripts.core.layers.add_top_n_annotations import render
    render(ax, gdf, field="food_access_score", n=3,
           label_field="NAMELSAD", value_format="{:.1f}")

Usage (CLI):
    python -m scripts.core.layers.add_top_n_annotations study.gpkg \
        --field food_access_score --n 3 -o annotated.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core" / "layers"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core"))

from _base import basemap_theme_from_ax, font_chain

try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False


def _auto_label_field(gdf) -> str | None:
    """Find a reasonable column to use as the human-readable label."""
    for col in ["place_name", "neighborhood", "community_area", "NAMELSAD",
                "NAME", "name", "label"]:
        if col in gdf.columns:
            return col
    return None


def render(ax, gdf: gpd.GeoDataFrame, *,
           field: str,
           n: int = 3,
           label_field: str | None = None,
           value_format: str = "{:.1f}",
           value_suffix: str = "",
           extra_fields: list[tuple[str, str, str]] | None = None,
           ascending: bool = False,
           font_family: str = "Gill Sans MT, Calibri, sans-serif",
           theme: str | None = None,
           zorder: int = 25) -> int:
    """Render top-N annotations on an existing axes.

    Parameters:
        extra_fields: optional list of (field_name, display_label, format_str)
            tuples. Each adds a line to the callout like a data popup.
            Example: [("PovertyRate", "Poverty", "{:.0f}%")]

    Returns the number of annotations placed.
    """
    import numpy as np

    valid = gdf.dropna(subset=[field]).copy()
    if valid.empty:
        return 0

    top = valid.nsmallest(n, field) if ascending else valid.nlargest(n, field)
    if label_field is None:
        label_field = _auto_label_field(top)

    # Theme-aware
    if theme is None:
        theme = basemap_theme_from_ax(ax)
    if theme == "dark":
        text_color, box_face, box_edge, arrow_color = "#ffffff", "#2a2a2a", "#666666", "#cccccc"
    else:
        text_color, box_face, box_edge, arrow_color = "#1a1a1a", "#ffffff", "#bbbbbb", "#444444"

    # Spatial reasoning: push each label outward from map center
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    extent_diag = np.hypot(xmax - xmin, ymax - ymin)
    base_offset = extent_diag * 0.14

    entries = []
    for _, row in top.iterrows():
        pt = row.geometry.representative_point()
        name = str(row[label_field]) if label_field and label_field in row.index and pd.notna(row[label_field]) else ""

        # Build popup-style multi-line label
        lines = []
        if name:
            lines.append(name)
        # Primary value
        val_str = value_format.format(row[field]) + value_suffix
        # If extra fields are given, label the primary field too
        primary_label = None
        if extra_fields:
            primary_label = field.replace("_", " ").title()
            lines.append(f"{primary_label}: {val_str}")
        else:
            lines.append(val_str)
        # Extra variables (popup-style additional context)
        if extra_fields:
            for ef_field, ef_label, ef_fmt in extra_fields:
                if ef_field in row.index and pd.notna(row[ef_field]):
                    lines.append(f"{ef_label}: {ef_fmt.format(row[ef_field])}")
        label = "\n".join(lines)

        angle = np.arctan2(pt.y - cy, pt.x - cx)
        entries.append({"pt": pt, "label": label, "angle": angle})

    # Enforce minimum angular separation so labels don't bunch
    entries.sort(key=lambda e: e["angle"])
    min_sep = (2 * np.pi) / max(n * 2, 6)
    for i in range(1, len(entries)):
        prev = entries[i - 1]["angle"]
        if entries[i]["angle"] - prev < min_sep:
            entries[i]["angle"] = prev + min_sep

    font_list = font_chain(font_family)
    texts = []
    margin_x = (xmax - xmin) * 0.05
    margin_y = (ymax - ymin) * 0.05

    for e in entries:
        pt = e["pt"]
        lx = pt.x + base_offset * np.cos(e["angle"])
        ly = pt.y + base_offset * np.sin(e["angle"])
        lx = max(xmin + margin_x, min(xmax - margin_x, lx))
        ly = max(ymin + margin_y, min(ymax - margin_y, ly))

        dx, dy = lx - pt.x, ly - pt.y
        rad = 0.2 if abs(dx) > abs(dy) else -0.2

        t = ax.annotate(
            e["label"], xy=(pt.x, pt.y), xytext=(lx, ly),
            fontsize=9, fontfamily=font_list, fontweight="bold",
            color=text_color, ha="center", va="center",
            arrowprops=dict(arrowstyle="->", color=arrow_color, lw=0.8,
                            connectionstyle=f"arc3,rad={rad}",
                            shrinkA=0, shrinkB=4),
            bbox=dict(boxstyle="round,pad=0.35", facecolor=box_face,
                      edgecolor=box_edge, linewidth=0.6, alpha=0.96),
            zorder=zorder,
        )
        texts.append(t)

    if HAS_ADJUST_TEXT and texts:
        try:
            adjust_text(texts, ax=ax, avoid_self=True,
                        force_text=(0.8, 0.8), force_points=(1.2, 1.2),
                        expand_text=(1.3, 1.3), expand_points=(1.5, 1.5))
        except Exception:
            pass

    return len(texts)


def main() -> int:
    import argparse
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = argparse.ArgumentParser(description="Annotate top-N features.")
    p.add_argument("input")
    p.add_argument("--field", required=True, help="Numeric field to rank by")
    p.add_argument("--n", type=int, default=3)
    p.add_argument("--label-field", help="Column for human-readable label")
    p.add_argument("--layer", help="GeoPackage layer name")
    p.add_argument("--ascending", action="store_true",
                   help="Annotate smallest (bottom-N) instead of largest")
    p.add_argument("--value-format", default="{:.1f}")
    p.add_argument("--value-suffix", default="")
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    gdf = gpd.read_file(args.input, layer=args.layer) if args.layer else gpd.read_file(args.input)

    fig, ax = plt.subplots(figsize=(10, 10))
    bg = "#222222" if args.theme == "dark" else "#ffffff"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    gdf.plot(ax=ax, color="#dddddd", edgecolor="#888888", linewidth=0.3)
    ax.set_axis_off()

    n = render(ax, gdf, field=args.field, n=args.n,
               label_field=args.label_field, ascending=args.ascending,
               value_format=args.value_format, value_suffix=args.value_suffix,
               theme=args.theme)

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi, bbox_inches="tight")

    print(f"annotations: {n} rendered -> {out}")
    return 0 if n > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
