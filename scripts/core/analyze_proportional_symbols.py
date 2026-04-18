#!/usr/bin/env python3
"""Generate a proportional symbol map from polygon or point data.

Use this instead of choropleth when mapping COUNTS (not rates).
Symbol size is proportional to the value — larger circle = more of the thing.

Supports:
  - Polygon centroids with proportional circles (most common use)
  - Point features with proportional circles
  - Optional choropleth basemap with proportional symbols on top
  - Optional labels for top-N features

Outputs:
  - PNG map
  - JSON handoff log

Usage:
    python analyze_proportional_symbols.py \\
        --input data/processed/counties.gpkg \\
        --value-col population \\
        --output outputs/maps/county_population.png \\
        [--basemap-col poverty_rate] \\
        [--basemap-cmap YlOrRd] \\
        [--label-col county_name] \\
        [--label-top 10] \\
        [--title "County Population"] \\
        [--max-symbol-size 800] \\
        [--min-symbol-size 20] \\
        [--symbol-color "#2563eb"] \\
        [--legend-values 50000 100000 250000 500000]
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
import pandas as pd
from adjustText import adjust_text

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def proportional_radius(values, max_size=800, min_size=20):
    """
    Scale values to marker sizes using square-root scaling
    (perceptually accurate for area-based symbols).
    """
    clean = values.dropna()
    if len(clean) == 0 or clean.max() == 0:
        return values.fillna(0) * 0 + min_size

    # Square root scaling: area ∝ value → radius ∝ sqrt(value)
    sqrt_vals = np.sqrt(values.clip(lower=0))
    sqrt_max = np.sqrt(clean.max())
    if sqrt_max == 0:
        return values.fillna(0) * 0 + min_size

    scaled = (sqrt_vals / sqrt_max) * (max_size - min_size) + min_size
    scaled = scaled.fillna(0)
    return scaled


def make_legend_sizes(values, legend_values, max_size, min_size):
    """Compute marker sizes for legend reference circles."""
    clean = values.dropna()
    if len(clean) == 0:
        return []
    val_max = clean.max()
    sqrt_max = np.sqrt(val_max)
    result = []
    for v in legend_values:
        if v <= 0:
            continue
        s = (np.sqrt(v) / sqrt_max) * (max_size - min_size) + min_size
        result.append((v, float(s)))
    return result


def format_legend_label(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}K"
    return f"{int(v):,}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input GeoPackage")
    parser.add_argument("--value-col", required=True, help="Column for symbol size (counts)")
    parser.add_argument("--basemap-col", help="Optional choropleth basemap column (rates/indices)")
    parser.add_argument("--basemap-cmap", default="YlOrRd", help="Basemap colormap (default: YlOrRd)")
    parser.add_argument("--basemap-scheme", default="quantiles",
                        choices=["quantiles", "equal_interval", "natural_breaks"])
    parser.add_argument("--basemap-k", type=int, default=5)
    parser.add_argument("--label-col", help="Column for feature labels")
    parser.add_argument("--label-top", type=int, default=0,
                        help="Label only the top-N features by value (0 = no labels)")
    parser.add_argument("--title", help="Map title")
    parser.add_argument("--max-symbol-size", type=float, default=600,
                        help="Maximum marker size in points² (default: 600)")
    parser.add_argument("--min-symbol-size", type=float, default=15,
                        help="Minimum marker size in points² (default: 15)")
    parser.add_argument("--symbol-color", default="#2563eb",
                        help="Symbol fill color (default: #2563eb)")
    parser.add_argument("--symbol-alpha", type=float, default=0.65)
    parser.add_argument("--symbol-edge-color", default="white")
    parser.add_argument("--symbol-edge-width", type=float, default=0.5)
    parser.add_argument("--legend-values", nargs="+", type=float,
                        help="Reference values for size legend (default: auto)")
    parser.add_argument("--attribution", help="Source attribution text")
    parser.add_argument("-o", "--output", help="Output PNG path")
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

    if args.value_col not in gdf.columns:
        print(f"Value column '{args.value_col}' not found. Available: {[c for c in gdf.columns if c != 'geometry']}")
        return 2

    gdf[args.value_col] = pd.to_numeric(gdf[args.value_col], errors="coerce")

    # Compute centroids for polygons
    geom_types = gdf.geometry.geom_type.unique()
    if any(g in ("Polygon", "MultiPolygon") for g in geom_types):
        # Use projected CRS for centroid calculation
        proj_gdf = gdf.copy()
        if gdf.crs and gdf.crs.is_geographic:
            proj_gdf = gdf.to_crs(gdf.estimate_utm_crs())
        centroids = proj_gdf.copy()
        centroids["geometry"] = proj_gdf.geometry.centroid
        centroids = centroids.to_crs("EPSG:4326")
        has_polygons = True
    else:
        centroids = gdf.to_crs("EPSG:4326")
        has_polygons = False

    # Symbol sizes
    sizes = proportional_radius(gdf[args.value_col], args.max_symbol_size, args.min_symbol_size)

    # Figure
    fw, fh = [float(x) for x in args.figsize.split(",")]
    fig, ax = plt.subplots(1, 1, figsize=(fw, fh))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Basemap polygon layer
    base_plot = gdf.to_crs("EPSG:4326")

    if args.basemap_col and args.basemap_col in gdf.columns:
        base_plot.plot(
            column=args.basemap_col,
            ax=ax,
            cmap=args.basemap_cmap,
            scheme=args.basemap_scheme.replace("natural_breaks", "NaturalBreaks").replace("equal_interval", "EqualInterval").replace("quantiles", "Quantiles"),
            k=args.basemap_k,
            legend=True,
            legend_kwds={
                "loc": "lower left",
                "fontsize": 7,
                "title": args.basemap_col.replace("_", " ").title(),
                "title_fontsize": 8,
            },
            edgecolor="white",
            linewidth=0.18,
            alpha=0.7,
        )
    else:
        base_plot.plot(ax=ax, color="#e8e8e8", edgecolor="white", linewidth=0.18)

    # State outline
    try:
        base_plot.dissolve().boundary.plot(ax=ax, edgecolor="#555555", linewidth=1.0, zorder=8)
    except Exception:
        pass

    # Proportional symbols at centroids
    cent_plot = centroids.to_crs("EPSG:4326")
    x = cent_plot.geometry.x.values
    y = cent_plot.geometry.y.values
    s = sizes.values

    # Sort so smaller symbols render on top
    sort_idx = np.argsort(s)[::-1]
    ax.scatter(
        x[sort_idx], y[sort_idx],
        s=s[sort_idx],
        color=args.symbol_color,
        alpha=args.symbol_alpha,
        edgecolors=args.symbol_edge_color,
        linewidths=args.symbol_edge_width,
        zorder=10,
    )

    # Labels for top-N
    if args.label_top > 0 and args.label_col and args.label_col in gdf.columns:
        top_idx = gdf[args.value_col].nlargest(args.label_top).index
        texts = []
        for idx in top_idx:
            if idx not in cent_plot.index:
                continue
            pt = cent_plot.loc[idx].geometry
            label = str(gdf.loc[idx, args.label_col])
            t = ax.text(
                pt.x, pt.y, label,
                fontsize=7, fontweight="bold",
                color="#111",
                ha="center", va="bottom",
                zorder=15,
            )
            texts.append(t)
        if texts:
            try:
                adjust_text(texts, ax=ax, expand_points=(1.2, 1.4),
                            arrowprops=dict(arrowstyle="-", color="#888", lw=0.5))
            except Exception:
                pass

    # Size legend
    col_data = gdf[args.value_col].dropna()
    if args.legend_values:
        legend_vals = args.legend_values
    else:
        # Auto: 4 reference values at 25th, 50th, 75th, max
        legend_vals = [
            col_data.quantile(0.25),
            col_data.quantile(0.50),
            col_data.quantile(0.75),
            col_data.max(),
        ]
        legend_vals = sorted(set([round(v, -int(np.floor(np.log10(max(v, 1)))) + 1) for v in legend_vals if v > 0]))

    legend_sizes = make_legend_sizes(col_data, legend_vals, args.max_symbol_size, args.min_symbol_size)
    if legend_sizes:
        legend_handles = [
            mlines.Line2D([], [],
                          color=args.symbol_color,
                          marker="o",
                          linestyle="None",
                          markersize=np.sqrt(sz),
                          alpha=args.symbol_alpha,
                          markeredgecolor=args.symbol_edge_color,
                          markeredgewidth=args.symbol_edge_width,
                          label=format_legend_label(val))
            for val, sz in legend_sizes
        ]
        legend_title = args.value_col.replace("_", " ").title()
        ax.legend(
            handles=legend_handles,
            title=legend_title,
            title_fontsize=8,
            fontsize=7,
            loc="lower right",
            framealpha=0.9,
            labelspacing=1.0,
        )

    # Title & attribution
    title = args.title or f"{args.value_col.replace('_', ' ').title()} (Proportional Symbols)"
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=12)
    ax.set_axis_off()

    if args.attribution:
        ax.text(0.99, 0.01, args.attribution, transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#999", style="italic")

    # Stats annotation
    n_valid = int(col_data.notna().sum())
    total_val = col_data.sum()
    stats_text = f"n={n_valid:,}  |  Total: {format_legend_label(total_val)}  |  Median: {format_legend_label(col_data.median())}"
    ax.text(0.01, 0.01, stats_text, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7, color="#666")

    plt.tight_layout()

    # Output
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "maps"
        out_path = out_dir / f"{src.stem}_{args.value_col}_proportional.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")

    # Handoff log
    log = {
        "step": "analyze_proportional_symbols",
        "source": str(src),
        "value_col": args.value_col,
        "basemap_col": args.basemap_col,
        "n_features": len(gdf),
        "n_valid": n_valid,
        "total": float(total_val),
        "output": str(out_path),
        "scaling": "sqrt (area-proportional)",
        "note": "Use for counts, not rates. Rates should use choropleth.",
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
