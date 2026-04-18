#!/usr/bin/env python3
"""Generate a small multiples map — multiple variables or time periods, same scale.

Each panel shows the same geography with a different variable or time slice,
using a consistent color scale so panels are directly comparable.

Use cases:
  - Compare 4 demographic variables across the same tracts
  - Show change over time (2010, 2015, 2020, 2022)
  - Compare sub-populations (poverty by race/ethnicity)

Outputs:
  - PNG map grid
  - JSON handoff log

Usage:
    python analyze_small_multiples.py \\
        --input data/processed/tracts_poverty.gpkg \\
        --cols poverty_rate uninsured_rate pct_rural median_age \\
        --titles "Poverty Rate" "Uninsured Rate" "Rural Population" "Median Age" \\
        [--shared-scale]         # use same vmin/vmax across all panels
        [--cmap YlOrRd] \\
        [--scheme quantiles] \\
        [--k 5] \\
        [--ncols 2] \\
        [--output outputs/maps/tracts_small_multiples.png]
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def classify_shared(values_list, scheme, k):
    """Compute shared classification bins across multiple columns."""
    import mapclassify
    all_vals = pd.concat([v.dropna() for v in values_list])
    if len(all_vals) == 0:
        return None
    k = min(k, all_vals.nunique())
    clf_map = {
        "quantiles": mapclassify.Quantiles,
        "equal_interval": mapclassify.EqualInterval,
        "natural_breaks": mapclassify.NaturalBreaks,
    }
    Clf = clf_map.get(scheme, mapclassify.Quantiles)
    return Clf(all_vals, k=k)


def classify_single(values, scheme, k):
    import mapclassify
    clean = values.dropna()
    if len(clean) == 0:
        return None
    k = min(k, clean.nunique())
    clf_map = {
        "quantiles": mapclassify.Quantiles,
        "equal_interval": mapclassify.EqualInterval,
        "natural_breaks": mapclassify.NaturalBreaks,
    }
    Clf = clf_map.get(scheme, mapclassify.Quantiles)
    return Clf(clean, k=k)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--cols", nargs="+", required=True, help="Columns to map (2-9)")
    parser.add_argument("--titles", nargs="+", help="Panel titles (default: column names)")
    parser.add_argument("--shared-scale", action="store_true",
                        help="Use same classification across all panels for comparability")
    parser.add_argument("--cmap", default="YlOrRd")
    parser.add_argument("--scheme", default="quantiles",
                        choices=["quantiles", "equal_interval", "natural_breaks"])
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--ncols", type=int, default=2, help="Number of columns in grid (default: 2)")
    parser.add_argument("--missing-color", default="#d0d0d0")
    parser.add_argument("--title", help="Overall figure title")
    parser.add_argument("--attribution", help="Source attribution")
    parser.add_argument("-o", "--output")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    gdf = gpd.read_file(src)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf = gdf.to_crs("EPSG:4326")

    missing = [c for c in args.cols if c not in gdf.columns]
    if missing:
        print(f"Columns not found: {missing}")
        print(f"Available: {[c for c in gdf.columns if c != 'geometry']}")
        return 2

    for col in args.cols:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce")

    n = len(args.cols)
    ncols = min(args.ncols, n)
    nrows = int(np.ceil(n / ncols))
    titles = args.titles or [c.replace("_", " ").title() for c in args.cols]
    if len(titles) < n:
        titles += [args.cols[i].replace("_", " ").title() for i in range(len(titles), n)]

    # Panel size: each panel ~6x5 inches
    panel_w, panel_h = 6.5, 5.0
    fig_w = panel_w * ncols
    fig_h = panel_h * nrows + (0.6 if args.title else 0.2)

    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_w, fig_h),
                             layout="constrained")
    fig.patch.set_facecolor("white")

    # Flatten axes
    if n == 1:
        axes = [axes]
    elif nrows == 1:
        axes = list(axes)
    else:
        axes = [ax for row in axes for ax in row]

    # Shared classification
    if args.shared_scale:
        shared_clf = classify_shared([gdf[c] for c in args.cols], args.scheme, args.k)
        shared_bins = [gdf[args.cols].values.min()] + list(shared_clf.bins) if shared_clf else None
    else:
        shared_clf = None
        shared_bins = None

    import matplotlib.colors as mcolors
    import matplotlib
    mpl_cmap = matplotlib.colormaps.get_cmap(args.cmap)

    for i, (col, title, ax) in enumerate(zip(args.cols, titles, axes)):
        ax.set_facecolor("white")
        col_data = gdf[col]

        if shared_clf:
            # Use shared bins for color mapping
            bins = shared_bins
            n_bins = len(bins) - 1
            colors = [mpl_cmap(j / max(n_bins - 1, 1)) for j in range(n_bins)]
            norm = matplotlib.colors.BoundaryNorm(bins, mpl_cmap.N)

            null_mask = col_data.isna()
            if null_mask.any():
                gdf[null_mask].plot(ax=ax, color=args.missing_color, edgecolor="white", linewidth=0.15)
            gdf[~null_mask].plot(
                column=col, ax=ax,
                cmap=args.cmap,
                norm=norm,
                edgecolor="white", linewidth=0.15,
                missing_kwds={"color": args.missing_color},
            )
        else:
            clf = classify_single(col_data, args.scheme, args.k)
            scheme_name = {
                "quantiles": "Quantiles",
                "equal_interval": "EqualInterval",
                "natural_breaks": "NaturalBreaks",
            }.get(args.scheme, "Quantiles")

            null_mask = col_data.isna()
            if null_mask.any():
                gdf[null_mask].plot(ax=ax, color=args.missing_color, edgecolor="white", linewidth=0.15)
            gdf[~null_mask].plot(
                column=col, ax=ax,
                cmap=args.cmap,
                scheme=scheme_name,
                k=min(args.k, col_data.dropna().nunique()),
                edgecolor="white", linewidth=0.15,
                legend=False,
                missing_kwds={"color": args.missing_color},
            )

        # State outline
        try:
            gdf.dissolve().boundary.plot(ax=ax, edgecolor="#444", linewidth=0.8, zorder=5)
        except Exception:
            pass

        ax.set_title(title, fontsize=11, fontweight="bold", loc="left", pad=6)
        ax.set_axis_off()

        # Min/max annotation
        clean = col_data.dropna()
        if len(clean) > 0:
            ax.text(0.99, 0.01,
                    f"min {clean.min():.1f} / max {clean.max():.1f}",
                    transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=6.5, color="#888")

    # Hide unused panels
    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    # Shared colorbar
    if args.shared_scale and shared_bins:
        norm = matplotlib.colors.BoundaryNorm(shared_bins, mpl_cmap.N)
        sm = plt.cm.ScalarMappable(cmap=args.cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=axes[:n], orientation="horizontal",
                            fraction=0.02, pad=0.04, shrink=0.5)
        cbar.ax.tick_params(labelsize=7)
        cbar.set_label("Shared scale", fontsize=8)

    # Figure title
    if args.title:
        fig.suptitle(args.title, fontsize=15, fontweight="bold", y=1.0)

    if args.attribution:
        fig.text(0.99, 0.005, args.attribution, ha="right", fontsize=6.5,
                 color="#aaa", style="italic")

    # Output (layout handled by constrained_layout)
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "maps"
        col_slug = "_".join(args.cols[:3])
        out_path = out_dir / f"{src.stem}_{col_slug}_small_multiples.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")

    log = {
        "step": "analyze_small_multiples",
        "source": str(src),
        "cols": args.cols,
        "shared_scale": args.shared_scale,
        "n_panels": n,
        "output": str(out_path),
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
