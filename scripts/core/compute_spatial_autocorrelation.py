#!/usr/bin/env python3
"""Compute global and local spatial autocorrelation (Moran's I, LISA).

Usage:
    python compute_spatial_autocorrelation.py \\
        --input data/processed/tracts.gpkg \\
        --column poverty_rate \\
        --output-global outputs/tables/morans_i.json \\
        --output-lisa outputs/maps/lisa_clusters.gpkg \\
        [--weights queen|rook|knn] \\
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Spatial autocorrelation analysis")
    parser.add_argument("--input", required=True, help="Input GeoPackage")
    parser.add_argument("--layer", default=None, help="Layer name within GeoPackage")
    parser.add_argument("--column", required=True, help="Column to analyze")
    parser.add_argument("--output-global", required=True, help="Output JSON for global Moran's I")
    parser.add_argument("--output-lisa", default=None, help="Output GeoPackage with LISA clusters")
    parser.add_argument("--output-map", default=None, help="Output PNG for LISA cluster map")
    parser.add_argument("--weights", default="queen", choices=["queen", "rook", "knn"],
                        help="Spatial weights type")
    parser.add_argument("--k", type=int, default=8, help="Number of neighbors for KNN weights")
    parser.add_argument("--permutations", type=int, default=999, help="Permutations for significance")
    parser.add_argument("--significance", type=float, default=0.05, help="Significance threshold")
    args = parser.parse_args()

    try:
        from libpysal.weights import Queen, Rook, KNN
        from esda.moran import Moran, Moran_Local
    except ImportError:
        print("ERROR: libpysal and esda required. Install with: pip install libpysal esda")
        return 1

    # Load data
    gdf = gpd.read_file(args.input, layer=args.layer) if args.layer else gpd.read_file(args.input)
    print(f"Loaded {len(gdf)} features from {args.input}")

    # Drop rows with null values in the target column
    valid = gdf[gdf[args.column].notna()].copy()
    dropped = len(gdf) - len(valid)
    if dropped > 0:
        print(f"  Dropped {dropped} rows with null {args.column}")

    # Drop empty geometries
    valid = valid[~valid.geometry.is_empty & valid.geometry.notna()]
    print(f"  {len(valid)} features for analysis")

    if len(valid) < 10:
        print("ERROR: Too few features for spatial autocorrelation")
        return 1

    # Build spatial weights
    print(f"Building {args.weights} spatial weights...")
    if args.weights == "queen":
        w = Queen.from_dataframe(valid)
    elif args.weights == "rook":
        w = Rook.from_dataframe(valid)
    else:
        w = KNN.from_dataframe(valid, k=args.k)

    # Handle islands (features with no neighbors)
    islands = w.islands
    if islands:
        print(f"  WARNING: {len(islands)} island features (no neighbors) — excluding")
        valid = valid.drop(valid.index[islands])
        if args.weights == "queen":
            w = Queen.from_dataframe(valid)
        elif args.weights == "rook":
            w = Rook.from_dataframe(valid)
        else:
            w = KNN.from_dataframe(valid, k=args.k)

    w.transform = 'r'  # Row-standardize

    y = valid[args.column].values

    # Global Moran's I
    print("Computing global Moran's I...")
    mi = Moran(y, w, permutations=args.permutations)

    global_result = {
        "step": "spatial_autocorrelation",
        "type": "global_morans_i",
        "source": str(args.input),
        "column": args.column,
        "weights": args.weights,
        "n_features": len(valid),
        "n_dropped_null": dropped,
        "n_islands": len(islands) if islands else 0,
        "morans_i": round(float(mi.I), 6),
        "expected_i": round(float(mi.EI), 6),
        "p_value": round(float(mi.p_sim), 6),
        "z_score": round(float(mi.z_sim), 4),
        "permutations": args.permutations,
        "significant": bool(mi.p_sim < args.significance),
        "interpretation": "",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Interpret
    if mi.p_sim < args.significance:
        if mi.I > 0:
            global_result["interpretation"] = (
                f"Significant positive spatial autocorrelation (I={mi.I:.4f}, p={mi.p_sim:.4f}). "
                f"{args.column} values cluster spatially — similar values near similar values."
            )
        else:
            global_result["interpretation"] = (
                f"Significant negative spatial autocorrelation (I={mi.I:.4f}, p={mi.p_sim:.4f}). "
                f"{args.column} values show spatial dispersion — dissimilar values near each other."
            )
    else:
        global_result["interpretation"] = (
            f"No significant spatial autocorrelation (I={mi.I:.4f}, p={mi.p_sim:.4f}). "
            f"{args.column} values are spatially random."
        )

    print(f"  Moran's I = {mi.I:.4f}, p = {mi.p_sim:.4f}")
    print(f"  {global_result['interpretation']}")

    # Save global result
    Path(args.output_global).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_global, 'w') as f:
        json.dump(global_result, f, indent=2)
    print(f"  Saved: {args.output_global}")

    # Local Moran's I (LISA)
    if args.output_lisa or args.output_map:
        print("Computing local Moran's I (LISA)...")
        lisa = Moran_Local(y, w, permutations=args.permutations)

        # FDR correction for LISA (Benjamini-Hochberg)
        from esda import fdr as compute_fdr
        try:
            fdr_threshold = compute_fdr(lisa.p_sim, args.significance)
            print(f"  FDR correction: {args.significance} → {fdr_threshold:.4f}")
        except Exception:
            fdr_threshold = args.significance
        sig = lisa.p_sim < fdr_threshold
        quadrant = lisa.q  # 1=HH, 2=LH, 3=LL, 4=HL
        labels = {1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}

        valid = valid.copy()
        valid["lisa_i"] = lisa.Is
        valid["lisa_p"] = lisa.p_sim
        valid["lisa_q"] = quadrant
        valid["lisa_sig"] = sig
        valid["lisa_cluster"] = "Not Significant"
        for q, label in labels.items():
            mask = (quadrant == q) & sig
            valid.loc[valid.index[mask], "lisa_cluster"] = label

        cluster_counts = valid["lisa_cluster"].value_counts().to_dict()
        print(f"  Clusters: {cluster_counts}")

        if args.output_lisa:
            Path(args.output_lisa).parent.mkdir(parents=True, exist_ok=True)
            valid.to_file(args.output_lisa, driver="GPKG")
            print(f"  Saved LISA GeoPackage: {args.output_lisa}")

        if args.output_map:
            import matplotlib.pyplot as plt
            from matplotlib.colors import ListedColormap

            fig, ax = plt.subplots(1, 1, figsize=(12, 10))

            colors = {
                "Not Significant": "#d9d9d9",
                "High-High": "#d7191c",
                "Low-Low": "#2c7bb6",
                "Low-High": "#abd9e9",
                "High-Low": "#fdae61",
            }
            order = ["Not Significant", "High-High", "High-Low", "Low-High", "Low-Low"]
            present = [c for c in order if c in valid["lisa_cluster"].values]

            for cluster in present:
                subset = valid[valid["lisa_cluster"] == cluster]
                subset.plot(ax=ax, color=colors[cluster], edgecolor="#555555",
                            linewidth=0.3, label=cluster)

            # Always show full legend with all LISA categories
            from matplotlib.patches import Patch
            all_clusters = ["High-High", "Low-Low", "High-Low", "Low-High", "Not Significant"]
            legend_handles = [
                Patch(facecolor=colors[c], edgecolor="#555555", linewidth=0.5, label=c)
                for c in all_clusters if c in colors
            ]
            ax.legend(handles=legend_handles, loc="lower left", fontsize=9,
                      title="LISA Cluster", title_fontsize=9,
                      framealpha=0.92, edgecolor="#cccccc", fancybox=False)
            ax.set_title(f"LISA Cluster Map: {args.column}\n"
                         f"Moran's I = {mi.I:.4f} (p = {mi.p_sim:.4f})",
                         fontsize=13, fontweight="bold")
            ax.set_axis_off()
            plt.tight_layout()

            Path(args.output_map).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(args.output_map, dpi=150, bbox_inches="tight",
                        facecolor="white")
            plt.close(fig)
            print(f"  Saved LISA map: {args.output_map}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
