#!/usr/bin/env python3
"""Compute Getis-Ord Gi* hot spot analysis.

Usage:
    python compute_hotspots.py \\
        --input data/processed/tracts.gpkg \\
        --column poverty_rate \\
        --output-gpkg outputs/maps/hotspots.gpkg \\
        --output-map outputs/maps/hotspots.png \\
        [--output-stats outputs/tables/hotspot_stats.json] \\
        [--weights queen|knn] \\
        [--k 8] \\
        [--permutations 999] \\
        [--significance 0.05]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np

SCRIPTS_CORE = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_CORE))


def main() -> int:
    parser = argparse.ArgumentParser(description="Getis-Ord Gi* hot spot analysis")
    parser.add_argument("--input", required=True, help="Input GeoPackage")
    parser.add_argument("--layer", default=None, help="Layer name within GeoPackage")
    parser.add_argument("--column", required=True, help="Column to analyze")
    parser.add_argument("--output-gpkg", default=None, help="Output GeoPackage with hotspot classification")
    parser.add_argument("--output-map", default=None, help="Output PNG hotspot map")
    parser.add_argument("--output-stats", default=None, help="Output JSON summary stats")
    parser.add_argument("--weights", default="queen", choices=["queen", "knn"])
    parser.add_argument("--k", type=int, default=8, help="K for KNN weights")
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--significance", type=float, default=0.05)
    parser.add_argument("--no-fdr", action="store_true", help="Skip FDR correction (exploratory mode)")
    args = parser.parse_args()

    if not args.output_gpkg and not args.output_map and not args.output_stats:
        print("ERROR: Specify at least one output (--output-gpkg, --output-map, --output-stats)")
        return 1

    try:
        from libpysal.weights import Queen, KNN
        from esda.getisord import G_Local
    except ImportError:
        print("ERROR: libpysal and esda required. Install with: pip install libpysal esda")
        return 1

    # Load data
    gdf = gpd.read_file(args.input, layer=args.layer) if args.layer else gpd.read_file(args.input)
    print(f"Loaded {len(gdf)} features from {args.input}")

    # Clean
    valid = gdf[gdf[args.column].notna()].copy()
    valid = valid[~valid.geometry.is_empty & valid.geometry.notna()]
    dropped = len(gdf) - len(valid)
    if dropped:
        print(f"  Dropped {dropped} features (null/empty)")
    print(f"  {len(valid)} features for analysis")

    # Spatial weights
    print(f"Building {args.weights} weights...")
    if args.weights == "queen":
        w = Queen.from_dataframe(valid)
    else:
        w = KNN.from_dataframe(valid, k=args.k)

    # Handle islands
    if w.islands:
        print(f"  WARNING: {len(w.islands)} islands — excluding")
        valid = valid.drop(valid.index[w.islands])
        if args.weights == "queen":
            w = Queen.from_dataframe(valid)
        else:
            w = KNN.from_dataframe(valid, k=args.k)

    w.transform = 'b'  # Binary for Gi*

    y = valid[args.column].values

    # Getis-Ord Gi*
    print("Computing Getis-Ord Gi*...")
    g = G_Local(y, w, star=True, permutations=args.permutations)

    # Classify hotspots by z-score and significance
    z_scores = g.Zs
    p_values = g.p_sim

    # FDR correction (Benjamini-Hochberg) — prevents spurious hotspots from multiple testing
    # With N tracts, ~5% will appear significant by chance at p<0.05 without correction
    if args.no_fdr:
        fdr_threshold = args.significance
        fdr_applied = False
        print(f"  FDR correction skipped (exploratory mode), using raw threshold {args.significance}")
    else:
        from esda import fdr as compute_fdr
        try:
            fdr_threshold = compute_fdr(p_values, args.significance)
            fdr_applied = True
            print(f"  FDR correction: raw threshold {args.significance} → FDR threshold {fdr_threshold:.4f}")
        except Exception as e:
            print(f"  WARNING: FDR correction failed ({e}), using raw p-values")
            fdr_threshold = args.significance
            fdr_applied = False

    def classify(z, p, threshold):
        if p > threshold:
            return "Not Significant"
        if z >= 2.58:
            return "Hot Spot (99%)"
        elif z >= 1.96:
            return "Hot Spot (95%)"
        elif z >= 1.65:
            return "Hot Spot (90%)"
        elif z <= -2.58:
            return "Cold Spot (99%)"
        elif z <= -1.96:
            return "Cold Spot (95%)"
        elif z <= -1.65:
            return "Cold Spot (90%)"
        return "Not Significant"

    valid = valid.copy()
    valid["gi_z"] = z_scores
    valid["gi_p"] = p_values
    valid["gi_p_fdr"] = p_values  # same values, threshold differs
    valid["hotspot_class"] = [classify(z, p, fdr_threshold) for z, p in zip(z_scores, p_values)]
    # Also store raw (uncorrected) classification for comparison
    valid["hotspot_class_raw"] = [classify(z, p, args.significance) for z, p in zip(z_scores, p_values)]

    counts = valid["hotspot_class"].value_counts().to_dict()
    print(f"  Results: {counts}")

    # Save stats
    stats = {
        "step": "hotspot_analysis",
        "type": "getis_ord_gi_star",
        "source": str(args.input),
        "column": args.column,
        "weights": args.weights,
        "n_features": len(valid),
        "n_dropped": dropped,
        "significance_threshold": args.significance,
        "fdr_threshold": round(float(fdr_threshold), 6),
        "fdr_applied": fdr_applied,
        "permutations": args.permutations,
        "hotspot_counts": counts,
        "z_score_range": [round(float(z_scores.min()), 4), round(float(z_scores.max()), 4)],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    if args.output_stats:
        Path(args.output_stats).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_stats, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved stats: {args.output_stats}")

    # Save GeoPackage
    if args.output_gpkg:
        Path(args.output_gpkg).parent.mkdir(parents=True, exist_ok=True)
        valid.to_file(args.output_gpkg, driver="GPKG")
        print(f"  Saved GeoPackage: {args.output_gpkg}")

    # Save map
    if args.output_map:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 1, figsize=(12, 10))

        colors = {
            "Hot Spot (99%)": "#d73027",
            "Hot Spot (95%)": "#fc8d59",
            "Hot Spot (90%)": "#fee08b",
            "Not Significant": "#d9d9d9",
            "Cold Spot (90%)": "#d1e5f0",
            "Cold Spot (95%)": "#91bfdb",
            "Cold Spot (99%)": "#4575b4",
        }
        order = [
            "Hot Spot (99%)", "Hot Spot (95%)", "Hot Spot (90%)",
            "Not Significant",
            "Cold Spot (90%)", "Cold Spot (95%)", "Cold Spot (99%)",
        ]
        present = [c for c in order if c in valid["hotspot_class"].values]

        from matplotlib.patches import Patch

        for cls in present:
            subset = valid[valid["hotspot_class"] == cls]
            subset.plot(ax=ax, color=colors[cls], edgecolor="#555555",
                        linewidth=0.3)

        # Always show full legend including Not Significant
        all_classes = [
            "Hot Spot (99%)", "Hot Spot (95%)", "Hot Spot (90%)",
            "Not Significant",
            "Cold Spot (90%)", "Cold Spot (95%)", "Cold Spot (99%)",
        ]
        legend_handles = [Patch(facecolor=colors[cls], edgecolor="#555555", linewidth=0.5, label=cls)
                          for cls in all_classes if cls in colors]
        ax.legend(handles=legend_handles, loc="lower left", fontsize=8,
                  title="Gi* Significance", title_fontsize=9,
                  framealpha=0.92, edgecolor="#cccccc", fancybox=False)
        ax.set_title(f"Hot Spot Analysis: {args.column}\n"
                     f"Getis-Ord Gi* ({args.permutations} permutations)",
                     fontsize=13, fontweight="bold")
        ax.set_axis_off()
        plt.tight_layout()

        Path(args.output_map).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output_map, dpi=200, bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)
        print(f"  Saved map: {args.output_map}")

        # Write style sidecar for QGIS inheritance
        try:
            from write_style_sidecar import write_style_sidecar
            write_style_sidecar(
                output_path=args.output_map,
                map_family="thematic_categorical",
                field=args.column,
                palette="hotspot",
                categorical_map=colors,
                title=f"Hot Spot Analysis: {args.column}",
                crs=str(gdf.crs) if gdf.crs else None,
                source_gpkg=args.input,
            )
        except ImportError:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
