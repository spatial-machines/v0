#!/usr/bin/env python3
"""Generate bivariate choropleth map showing two variables simultaneously.

Uses a 3x3 grid (9 classes) combining quantile breaks of two variables.
The classic bivariate color scheme: one axis is blue→purple, other is pink→purple.

Usage:
    python analyze_bivariate.py \\
        --input data/processed/tracts.gpkg \\
        --col-x poverty_rate --col-y uninsured_rate \\
        --output outputs/maps/bivariate_poverty_uninsured.png \\
        [--label-x "Poverty Rate (%)"] \\
        [--label-y "Uninsured Rate (%)"] \\
        [--title "Poverty vs Uninsured Rate"] \\
        [--classes 3] \\
        [--output-gpkg outputs/maps/bivariate.gpkg] \\
        [--output-stats outputs/tables/bivariate_stats.json]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle


# Stevens' bivariate color schemes (3x3)
BIVARIATE_COLORS_3x3 = [
    # Row 0 (low Y): light teal → light pink
    ["#e8e8e8", "#b5c0da", "#6c83b5"],
    # Row 1 (mid Y)
    ["#b8d6be", "#90b2b3", "#567994"],
    # Row 2 (high Y): green → dark purple
    ["#73ae80", "#5a9178", "#2a5a5b"],
]


def make_bivariate_legend(ax, colors, label_x, label_y, size=0.12):
    """Draw the bivariate legend square."""
    n = len(colors)
    cell = size / n

    # Position in bottom-left of axes
    x0, y0 = 0.02, 0.02

    for i in range(n):
        for j in range(n):
            rect = Rectangle((x0 + j * cell, y0 + i * cell), cell, cell,
                              facecolor=colors[i][j], edgecolor="white",
                              linewidth=0.5, transform=ax.transAxes)
            ax.add_patch(rect)

    # Labels
    ax.text(x0 + size / 2, y0 - 0.015, f"{label_x} →",
            transform=ax.transAxes, ha="center", va="top", fontsize=8)
    ax.text(x0 - 0.015, y0 + size / 2, f"{label_y} →",
            transform=ax.transAxes, ha="right", va="center", fontsize=8,
            rotation=90)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bivariate choropleth map")
    parser.add_argument("--input", required=True)
    parser.add_argument("--col-x", required=True, help="X-axis variable")
    parser.add_argument("--col-y", required=True, help="Y-axis variable")
    parser.add_argument("--output", required=True, help="Output PNG")
    parser.add_argument("--label-x", default=None)
    parser.add_argument("--label-y", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--classes", type=int, default=3, choices=[3])
    parser.add_argument("--output-gpkg", default=None)
    parser.add_argument("--output-stats", default=None)
    parser.add_argument("--attribution", default=None)
    args = parser.parse_args()

    def _auto_label(field_name, override=None):
        if override:
            return override
        fn = field_name.lower()
        nice = field_name.replace("_", " ").title()
        nice = nice.replace("Pct ", "% ").replace(" Pct", "")
        nice = nice.replace("Per Sqkm", "per sq km").replace("Sqkm", "sq km")
        nice = nice.replace("Nh ", "")
        if any(k in fn for k in ("rate", "pct", "percent")):
            return nice if "%" in nice else f"{nice} (%)"
        elif any(k in fn for k in ("income", "rent", "cost", "price", "value")):
            return f"{nice} ($)"
        elif any(k in fn for k in ("pop", "count", "total", "number", "universe")):
            return f"{nice} (count)"
        elif "per sq km" in nice:
            return nice
        return nice

    label_x = _auto_label(args.col_x, args.label_x)
    label_y = _auto_label(args.col_y, args.label_y)

    gdf = gpd.read_file(args.input)
    print(f"Loaded {len(gdf)} features")

    # Drop nulls in either column
    valid = gdf[gdf[args.col_x].notna() & gdf[args.col_y].notna()].copy()
    dropped = len(gdf) - len(valid)
    if dropped:
        print(f"  Dropped {dropped} with null values")

    n = args.classes

    # Compute quantile breaks
    x_breaks = np.quantile(valid[args.col_x].values, np.linspace(0, 1, n + 1))
    y_breaks = np.quantile(valid[args.col_y].values, np.linspace(0, 1, n + 1))

    # Classify
    def classify(val, breaks):
        for i in range(len(breaks) - 1):
            if val <= breaks[i + 1]:
                return min(i, n - 1)
        return n - 1

    valid["biv_x"] = valid[args.col_x].apply(lambda v: classify(v, x_breaks))
    valid["biv_y"] = valid[args.col_y].apply(lambda v: classify(v, y_breaks))
    valid["biv_class"] = valid["biv_y"] * n + valid["biv_x"]

    colors = BIVARIATE_COLORS_3x3
    flat_colors = [colors[j][i] for j in range(n) for i in range(n)]

    # Map
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Plot each class
    for j in range(n):
        for i in range(n):
            cls = j * n + i
            subset = valid[valid["biv_class"] == cls]
            if len(subset) > 0:
                subset.plot(ax=ax, color=colors[j][i], edgecolor="#33333322",
                            linewidth=0.25)

    # Plot nulls in gray
    if dropped > 0:
        nulls = gdf[~gdf.index.isin(valid.index)]
        nulls.plot(ax=ax, color="#d9d9d9", edgecolor="#33333322", linewidth=0.25)

    title = args.title or f"{label_x} vs {label_y}"
    ax.set_title(title, fontsize=16, fontweight="bold", pad=16)
    ax.set_axis_off()

    # Add bivariate legend
    make_bivariate_legend(ax, colors, label_x, label_y, size=0.15)

    # Attribution
    if args.attribution:
        ax.text(0.99, 0.01, args.attribution, transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#999")

    plt.tight_layout()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved map: {args.output}")

    # Write style sidecar for QGIS inheritance
    try:
        SCRIPTS_CORE = Path(__file__).resolve().parent
        import sys as _sys
        _sys.path.insert(0, str(SCRIPTS_CORE))
        from write_style_sidecar import write_style_sidecar
        write_style_sidecar(
            output_path=args.output,
            map_family="thematic_choropleth",
            palette="bivariate_3x3",
            title=args.title or f"{args.col_x} vs {args.col_y}",
            crs=str(valid.crs) if valid.crs else None,
            source_gpkg=args.input,
            extra={"field_x": args.col_x, "field_y": args.col_y, "classes": n},
        )
    except ImportError:
        pass

    # Stats
    cross_tab = {}
    for j in range(n):
        for i in range(n):
            cls_name = f"x{i}_y{j}"
            count = int((valid["biv_class"] == (j * n + i)).sum())
            cross_tab[cls_name] = count

    stats = {
        "step": "bivariate_choropleth",
        "source": str(args.input),
        "col_x": args.col_x,
        "col_y": args.col_y,
        "classes": n,
        "x_breaks": [round(float(b), 4) for b in x_breaks],
        "y_breaks": [round(float(b), 4) for b in y_breaks],
        "cross_tab": cross_tab,
        "n_features": len(valid),
        "n_dropped": dropped,
        "correlation": round(float(valid[args.col_x].corr(valid[args.col_y])), 4),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
    print(f"  Correlation: {stats['correlation']}")
    print(f"  Cross-tab: {cross_tab}")

    if args.output_stats:
        Path(args.output_stats).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_stats, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Saved stats: {args.output_stats}")

    if args.output_gpkg:
        Path(args.output_gpkg).parent.mkdir(parents=True, exist_ok=True)
        valid.to_file(args.output_gpkg, driver="GPKG")
        print(f"Saved GeoPackage: {args.output_gpkg}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
