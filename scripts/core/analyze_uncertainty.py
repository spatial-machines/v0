#!/usr/bin/env python3
"""Visualize ACS margin of error alongside point estimates.

Shows where findings are statistically solid vs uncertain using coefficient of
variation (CV) classification. Generates a two-panel map: left panel is the
estimate choropleth, right panel is the reliability classification.

CV formula: CV = (MOE / 1.645) / estimate * 100
  - CV < 15%  → Reliable
  - CV 15–30% → Use with caution
  - CV > 30%  → Unreliable
  - MOE > estimate → Essentially meaningless (flagged separately)

Usage:
    python analyze_uncertainty.py \\
        --input data/processed/tracts_poverty.gpkg \\
        --estimate-col poverty_rate \\
        --moe-col poverty_rate_moe \\
        --output-map outputs/maps/poverty_uncertainty.png \\
        --output data/processed/tracts_poverty_reliability.gpkg
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Reliability classification thresholds
CV_RELIABLE = 15.0       # CV < 15% → Reliable
CV_CAUTION = 30.0        # 15% ≤ CV < 30% → Use with caution
                          # CV ≥ 30% → Unreliable

# Colors for reliability classes
RELIABILITY_COLORS = {
    "Reliable":           "#2ca25f",   # green
    "Use with Caution":   "#fec44f",   # yellow/amber
    "Unreliable":         "#f03b20",   # red
    "Effectively Zero":   "#aaaaaa",   # gray — estimate ≈ 0, CV undefined
    "Essentially Meaningless": "#8b0000",  # dark red — MOE > estimate
}

RELIABILITY_ORDER = [
    "Reliable",
    "Use with Caution",
    "Unreliable",
    "Essentially Meaningless",
    "Effectively Zero",
]


def compute_cv(estimate: pd.Series, moe: pd.Series) -> pd.Series:
    """Compute coefficient of variation (%). NaN where estimate is zero/NaN."""
    se = moe / 1.645  # Convert MOE (90% CI) to standard error
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = np.where(
            estimate.abs() > 0,
            (se / estimate.abs()) * 100.0,
            np.nan,
        )
    return pd.Series(cv, index=estimate.index)


def classify_reliability(estimate: pd.Series, moe: pd.Series, cv: pd.Series) -> pd.Series:
    """Return reliability class string for each row."""
    classes = []
    for est, m, c in zip(estimate, moe, cv):
        if pd.isna(est) or pd.isna(m):
            classes.append("Effectively Zero")
        elif abs(est) < 1e-9:  # estimate is effectively zero
            classes.append("Effectively Zero")
        elif m > abs(est):     # MOE larger than estimate — essentially meaningless
            classes.append("Essentially Meaningless")
        elif pd.isna(c):
            classes.append("Effectively Zero")
        elif c < CV_RELIABLE:
            classes.append("Reliable")
        elif c < CV_CAUTION:
            classes.append("Use with Caution")
        else:
            classes.append("Unreliable")
    return pd.Series(classes, index=estimate.index)


def make_two_panel_map(
    gdf: gpd.GeoDataFrame,
    estimate_col: str,
    reliability_class_col: str,
    cv_col: str,
    output_path: Path,
    title_estimate: str = "",
    title_reliability: str = "Reliability Classification (CV-based)",
) -> None:
    """Generate and save the two-panel PNG map."""

    fig, axes = plt.subplots(1, 2, figsize=(18, 9), facecolor="#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")
        ax.set_axis_off()

    # ── Left panel: estimate choropleth ──────────────────────────────────────
    ax_left = axes[0]
    valid = gdf[gdf[estimate_col].notna()].copy()
    nodata = gdf[gdf[estimate_col].isna()].copy()

    if len(nodata) > 0:
        nodata.plot(ax=ax_left, color="#555555", linewidth=0.2, edgecolor="#333333")

    if len(valid) > 0:
        valid.plot(
            ax=ax_left,
            column=estimate_col,
            cmap="YlOrRd",
            linewidth=0.2,
            edgecolor="#333333",
            legend=False,
            scheme="quantiles",
            k=5,
        )
        # Colorbar
        vmin = float(valid[estimate_col].min())
        vmax = float(valid[estimate_col].max())
        sm = ScalarMappable(cmap="YlOrRd", norm=Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax_left, fraction=0.03, pad=0.02, orientation="vertical")
        cbar.ax.yaxis.set_tick_params(color="white")
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white", fontsize=8)

    title_est = title_estimate or f"{estimate_col.replace('_', ' ').title()}"
    ax_left.set_title(title_est, color="white", fontsize=13, pad=12, fontweight="bold")

    # ── Right panel: reliability classification ───────────────────────────────
    ax_right = axes[1]

    # Plot each class in order so legend is consistent
    plotted_classes: list[str] = []
    for cls in RELIABILITY_ORDER:
        subset = gdf[gdf[reliability_class_col] == cls]
        if len(subset) == 0:
            continue
        color = RELIABILITY_COLORS[cls]
        subset.plot(ax=ax_right, color=color, linewidth=0.2, edgecolor="#222222")
        plotted_classes.append(cls)

    # Plot any unclassified tracts
    unclassified = gdf[~gdf[reliability_class_col].isin(RELIABILITY_ORDER)]
    if len(unclassified) > 0:
        unclassified.plot(ax=ax_right, color="#888888", linewidth=0.2, edgecolor="#222222")

    # Legend
    legend_patches = [
        mpatches.Patch(color=RELIABILITY_COLORS[cls], label=cls)
        for cls in plotted_classes
    ]
    ax_right.legend(
        handles=legend_patches,
        loc="lower left",
        fontsize=9,
        framealpha=0.7,
        facecolor="#2a2a2a",
        edgecolor="#555555",
        labelcolor="white",
    )

    # Count summary text
    class_counts = gdf[reliability_class_col].value_counts()
    summary_lines = [f"{cls}: {class_counts.get(cls, 0):,}" for cls in plotted_classes]
    summary_text = " | ".join(summary_lines)
    ax_right.annotate(
        summary_text,
        xy=(0.5, 0.02), xycoords="axes fraction",
        ha="center", va="bottom", fontsize=7.5, color="#cccccc",
    )

    ax_right.set_title(title_reliability, color="white", fontsize=13, pad=12, fontweight="bold")

    # ── Overall figure decoration ─────────────────────────────────────────────
    fig.suptitle(
        f"Estimate vs. Statistical Reliability — {estimate_col.replace('_', ' ').title()}",
        color="white", fontsize=15, fontweight="bold", y=0.98,
    )
    footnote = (
        f"Reliability: CV < {CV_RELIABLE:.0f}% = Reliable  |  "
        f"{CV_RELIABLE:.0f}–{CV_CAUTION:.0f}% = Use with Caution  |  "
        f"> {CV_CAUTION:.0f}% = Unreliable  |  "
        f"CV = (MOE / 1.645) / Estimate × 100"
    )
    fig.text(0.5, 0.01, footnote, ha="center", va="bottom", color="#888888", fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  map saved: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Input GeoPackage path")
    parser.add_argument("--estimate-col", required=True, help="Column with point estimates")
    parser.add_argument("--moe-col", required=True, help="Column with margins of error (90%% CI)")
    parser.add_argument(
        "--output-map",
        help="Output PNG path for two-panel map (default: <input>_uncertainty.png)",
    )
    parser.add_argument(
        "--output",
        help="Output GeoPackage path with reliability columns added (default: <input>_reliability.gpkg)",
    )
    parser.add_argument(
        "-o", "--log-output",
        help="JSON log output path (default: alongside --output)",
    )
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: input not found: {src}")
        return 1

    print(f"analyze_uncertainty: {src.name}")
    print(f"  estimate col: {args.estimate_col}")
    print(f"  MOE col:      {args.moe_col}")

    gdf = gpd.read_file(src)
    print(f"  features: {len(gdf):,}")

    if args.estimate_col not in gdf.columns:
        print(f"ERROR: estimate column '{args.estimate_col}' not found in {src.name}")
        print(f"  available: {list(gdf.columns)}")
        return 1

    if args.moe_col not in gdf.columns:
        print(f"ERROR: MOE column '{args.moe_col}' not found in {src.name}")
        print(f"  available: {list(gdf.columns)}")
        return 1

    # ── Compute CV and reliability class ──────────────────────────────────────
    estimate = pd.to_numeric(gdf[args.estimate_col], errors="coerce")
    moe = pd.to_numeric(gdf[args.moe_col], errors="coerce")

    cv = compute_cv(estimate, moe)
    reliability = classify_reliability(estimate, moe, cv)

    gdf["cv_pct"] = cv.round(2)
    gdf["reliability_class"] = reliability

    # ── Stats summary ─────────────────────────────────────────────────────────
    class_counts = reliability.value_counts().to_dict()
    meaningless_count = int(class_counts.get("Essentially Meaningless", 0))
    unreliable_count = int(class_counts.get("Unreliable", 0))
    reliable_count = int(class_counts.get("Reliable", 0))
    caution_count = int(class_counts.get("Use with Caution", 0))

    print(f"  reliability breakdown:")
    for cls in RELIABILITY_ORDER:
        n = class_counts.get(cls, 0)
        if n > 0:
            pct = n / len(gdf) * 100
            print(f"    {cls}: {n:,} ({pct:.1f}%)")

    if meaningless_count > 0:
        print(f"  ⚠ WARNING: {meaningless_count:,} tracts where MOE > estimate (effectively meaningless)")

    cv_stats = {
        "mean": round(float(cv.dropna().mean()), 2) if len(cv.dropna()) > 0 else None,
        "median": round(float(cv.dropna().median()), 2) if len(cv.dropna()) > 0 else None,
        "max": round(float(cv.dropna().max()), 2) if len(cv.dropna()) > 0 else None,
        "min": round(float(cv.dropna().min()), 2) if len(cv.dropna()) > 0 else None,
    }
    print(f"  CV stats: mean={cv_stats['mean']}%, median={cv_stats['median']}%, "
          f"min={cv_stats['min']}%, max={cv_stats['max']}%")

    # ── Output GeoPackage ─────────────────────────────────────────────────────
    if args.output:
        out_gpkg = Path(args.output).expanduser().resolve()
    else:
        out_gpkg = src.parent / f"{src.stem}_reliability.gpkg"

    out_gpkg.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_gpkg, driver="GPKG")
    print(f"  GeoPackage saved: {out_gpkg}")

    # ── Two-panel map ─────────────────────────────────────────────────────────
    if args.output_map:
        out_map = Path(args.output_map).expanduser().resolve()
    else:
        out_map = out_gpkg.parent / f"{src.stem}_uncertainty.png"

    make_two_panel_map(
        gdf=gdf,
        estimate_col=args.estimate_col,
        reliability_class_col="reliability_class",
        cv_col="cv_pct",
        output_path=out_map,
    )

    # ── JSON handoff log ──────────────────────────────────────────────────────
    log = {
        "step": "analyze_uncertainty",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "source": str(src),
        "estimate_col": args.estimate_col,
        "moe_col": args.moe_col,
        "features": len(gdf),
        "output_gpkg": str(out_gpkg),
        "output_map": str(out_map),
        "cv_stats": cv_stats,
        "reliability_counts": {
            "reliable": reliable_count,
            "use_with_caution": caution_count,
            "unreliable": unreliable_count,
            "essentially_meaningless": meaningless_count,
            "effectively_zero": int(class_counts.get("Effectively Zero", 0)),
        },
        "flags": {
            "has_meaningless_tracts": meaningless_count > 0,
            "meaningless_count": meaningless_count,
            "pct_reliable": round(reliable_count / len(gdf) * 100, 1) if len(gdf) > 0 else 0,
            "pct_unreliable": round((unreliable_count + meaningless_count) / len(gdf) * 100, 1)
                              if len(gdf) > 0 else 0,
        },
        "new_columns": ["cv_pct", "reliability_class"],
        "cv_thresholds": {
            "reliable": f"< {CV_RELIABLE}%",
            "use_with_caution": f"{CV_RELIABLE}–{CV_CAUTION}%",
            "unreliable": f"> {CV_CAUTION}%",
        },
    }

    if args.log_output:
        log_path = Path(args.log_output).expanduser().resolve()
    else:
        log_path = out_gpkg.with_suffix(".log.json")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  log saved: {log_path}")
    print(json.dumps({
        "output_gpkg": str(out_gpkg),
        "output_map": str(out_map),
        "reliable_pct": log["flags"]["pct_reliable"],
        "unreliable_pct": log["flags"]["pct_unreliable"],
        "meaningless_tracts": meaningless_count,
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
