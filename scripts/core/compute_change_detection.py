#!/usr/bin/env python3
"""Compare two versions of the same layer (e.g. ACS vintages) and compute change.

Outputs:
  - GeoPackage with change columns appended
  - Diverging choropleth map (blue = improvement, red = worsening)
  - Summary statistics of change
  - JSON handoff log

Usage:
    python compute_change_detection.py \\
        --baseline data/processed/tracts_poverty_2017.gpkg \\
        --current  data/processed/tracts_poverty_2022.gpkg \\
        --cols poverty_rate uninsured_rate \\
        --join-on GEOID \\
        [--output data/processed/tracts_poverty_change.gpkg] \\
        [--output-maps outputs/maps/] \\
        [--improvement-direction down]  # 'down' = lower is better (poverty, uninsured)
                                        # 'up'   = higher is better (income, coverage)
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent


def make_change_map(gdf, change_col, title, out_path, direction="down", dpi=200):
    """
    Diverging choropleth for a change column.
    direction='down' → negative change is good (blue), positive is bad (red)
    direction='up'   → positive change is good (blue), negative is bad (red)
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    data = pd.to_numeric(gdf[change_col], errors="coerce")
    vmax = float(data.abs().quantile(0.95))
    vmin = -vmax

    # For 'down' direction (lower is better): blue = decrease (good), red = increase (bad)
    # For 'up' direction (higher is better): blue = increase (good), red = decrease (bad)
    cmap = "RdBu" if direction == "down" else "RdBu_r"

    gdf_plot = gdf.copy()
    gdf_plot[change_col] = data

    gdf_plot.plot(
        column=change_col,
        ax=ax,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        legend=True,
        legend_kwds={
            "label": change_col.replace("_", " ").title(),
            "orientation": "vertical",
            "shrink": 0.6,
            "pad": 0.01,
        },
        edgecolor="white",
        linewidth=0.18,
        missing_kwds={"color": "#d0d0d0"},
    )

    try:
        gdf_plot.dissolve().boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.2, zorder=10)
    except Exception:
        pass

    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=12)
    ax.set_axis_off()

    if direction == "down":
        note = "Blue = decrease (improvement)  |  Red = increase (worsening)"
    else:
        note = "Blue = increase (improvement)  |  Red = decrease (worsening)"
    ax.text(0.99, 0.01, note, transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, color="#666", style="italic")

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved change map: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Baseline (older) GeoPackage")
    parser.add_argument("--current", required=True, help="Current (newer) GeoPackage")
    parser.add_argument("--cols", nargs="+", required=True, help="Columns to compare")
    parser.add_argument("--join-on", default="GEOID", help="Join key column (default: GEOID)")
    parser.add_argument("--improvement-direction", default="down",
                        choices=["down", "up"],
                        help="'down' = lower is better (poverty); 'up' = higher is better (income)")
    parser.add_argument("--baseline-label", default="baseline",
                        help="Label for baseline period (e.g. '2017')")
    parser.add_argument("--current-label", default="current",
                        help="Label for current period (e.g. '2022')")
    parser.add_argument("-o", "--output", help="Output GeoPackage path")
    parser.add_argument("--output-maps", help="Directory for output map PNGs")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    base_path = Path(args.baseline).expanduser().resolve()
    curr_path = Path(args.current).expanduser().resolve()

    if not base_path.exists():
        print(f"Baseline not found: {base_path}")
        return 1
    if not curr_path.exists():
        print(f"Current not found: {curr_path}")
        return 1

    base_gdf = gpd.read_file(base_path)
    curr_gdf = gpd.read_file(curr_path)

    print(f"Baseline: {len(base_gdf)} features  |  Current: {len(curr_gdf)} features")

    # Validate join key
    join_col = args.join_on
    if join_col not in base_gdf.columns:
        # Try case-insensitive match
        match = next((c for c in base_gdf.columns if c.upper() == join_col.upper()), None)
        if match:
            join_col = match
        else:
            print(f"Join column '{args.join_on}' not found in baseline. Available: {list(base_gdf.columns)}")
            return 2

    if join_col not in curr_gdf.columns:
        print(f"Join column '{join_col}' not found in current layer.")
        return 2

    # Validate columns
    missing_base = [c for c in args.cols if c not in base_gdf.columns]
    missing_curr = [c for c in args.cols if c not in curr_gdf.columns]
    if missing_base:
        print(f"Columns missing from baseline: {missing_base}")
        return 2
    if missing_curr:
        print(f"Columns missing from current: {missing_curr}")
        return 2

    # Join baseline values onto current geometry
    base_rename = {c: f"{c}_{args.baseline_label}" for c in args.cols}
    base_data = base_gdf[[join_col] + args.cols].rename(columns=base_rename)

    merged = curr_gdf.merge(base_data, on=join_col, how="left")

    n_joined = int(merged[[f"{c}_{args.baseline_label}" for c in args.cols[0:1]]].notna().sum().values[0])
    print(f"Joined {n_joined}/{len(merged)} features to baseline data")

    # Compute change columns
    change_summary = {}
    map_cols = []

    for col in args.cols:
        base_col = f"{col}_{args.baseline_label}"
        curr_col = col

        # Rename current column too for clarity
        curr_rename = f"{col}_{args.current_label}"
        merged[curr_rename] = pd.to_numeric(merged[curr_col], errors="coerce")
        merged[base_col] = pd.to_numeric(merged[base_col], errors="coerce")

        change_col = f"{col}_change"
        pct_change_col = f"{col}_pct_change"

        merged[change_col] = merged[curr_rename] - merged[base_col]
        merged[pct_change_col] = (merged[change_col] / merged[base_col].abs()) * 100
        merged[pct_change_col] = merged[pct_change_col].replace([np.inf, -np.inf], np.nan)

        map_cols.append((change_col, col))

        # Summary stats
        data = merged[change_col].dropna()
        n_improved = int((data < 0).sum()) if args.improvement_direction == "down" else int((data > 0).sum())
        n_worsened = int((data > 0).sum()) if args.improvement_direction == "down" else int((data < 0).sum())

        change_summary[col] = {
            "mean_change": round(float(data.mean()), 4),
            "median_change": round(float(data.median()), 4),
            "min_change": round(float(data.min()), 4),
            "max_change": round(float(data.max()), 4),
            "n_improved": n_improved,
            "n_worsened": n_worsened,
            "n_unchanged": int(len(data) - n_improved - n_worsened),
            "n_no_data": int(merged[change_col].isna().sum()),
        }
        direction_word = "decreased" if args.improvement_direction == "down" else "increased"
        print(f"  {col}: mean change {data.mean():+.2f} | {n_improved} areas {direction_word} ({direction_word} = improved)")

    # Output GeoPackage
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "processed"
        out_path = out_dir / f"{curr_path.stem}_change.gpkg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_file(out_path, driver="GPKG")
    print(f"Saved: {out_path}")

    # Maps
    map_dir = Path(args.output_maps) if args.output_maps else PROJECT_ROOT / "outputs" / "maps"
    map_paths = {}

    for change_col, orig_col in map_cols:
        map_path = str(map_dir / f"{curr_path.stem}_{change_col}.png")
        base_lbl = args.baseline_label
        curr_lbl = args.current_label
        title = f"{orig_col.replace('_', ' ').title()} Change: {base_lbl} → {curr_lbl}"
        make_change_map(
            merged, change_col, title, map_path,
            direction=args.improvement_direction, dpi=args.dpi
        )
        map_paths[change_col] = map_path

    # Handoff log
    log = {
        "step": "compute_change_detection",
        "baseline": str(base_path),
        "current": str(curr_path),
        "baseline_label": args.baseline_label,
        "current_label": args.current_label,
        "columns": args.cols,
        "join_on": join_col,
        "n_features": len(merged),
        "n_joined": n_joined,
        "improvement_direction": args.improvement_direction,
        "output": str(out_path),
        "maps": map_paths,
        "change_summary": change_summary,
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
