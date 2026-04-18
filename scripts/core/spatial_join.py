#!/usr/bin/env python3
"""Spatial join two GeoPackage datasets with flexible join types and predicates.

Usage:
    python spatial_join.py \\
        --left data/processed/census_tracts.gpkg \\
        --right data/processed/schools.gpkg \\
        --how left \\
        --predicate intersects \\
        --output outputs/vectors/tracts_with_schools.gpkg

    # Nearest join with field selection:
    python spatial_join.py \\
        --left data/processed/parcels.gpkg \\
        --right data/processed/transit_stops.gpkg \\
        --how left \\
        --predicate nearest \\
        --fields stop_name route_id \\
        --output outputs/vectors/parcels_near_transit.gpkg
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Spatial join of two GeoPackage datasets."
    )
    parser.add_argument("--left", required=True, help="Left (base) GeoPackage")
    parser.add_argument("--right", required=True, help="Right (target) GeoPackage")
    parser.add_argument(
        "--how",
        default="left",
        choices=["left", "right", "inner"],
        help="Join type (default: left)",
    )
    parser.add_argument(
        "--predicate",
        default="intersects",
        choices=["intersects", "within", "contains", "overlaps",
                 "crosses", "touches", "nearest"],
        help="Spatial predicate (default: intersects)",
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        default=None,
        help="Fields from right dataset to transfer (default: all non-geometry fields)",
    )
    parser.add_argument("--output", required=True, help="Output GeoPackage")
    parser.add_argument(
        "--max-distance",
        type=float,
        default=None,
        help="Maximum distance for 'nearest' join (units match CRS)",
    )
    parser.add_argument(
        "--suffix-left",
        default="_left",
        help="Suffix for conflicting column names from left (default: _left)",
    )
    parser.add_argument(
        "--suffix-right",
        default="_right",
        help="Suffix for conflicting column names from right (default: _right)",
    )
    args = parser.parse_args()

    import geopandas as gpd
    import pandas as pd

    left_path = Path(args.left).expanduser().resolve()
    right_path = Path(args.right).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    for p, label in [(left_path, "left"), (right_path, "right")]:
        if not p.exists():
            print(f"ERROR: {label} dataset not found: {p}")
            return 1

    warnings = []
    assumptions = []

    # Load data
    print(f"Loading left dataset: {left_path.name}")
    left = gpd.read_file(left_path)
    print(f"  {len(left)} features, CRS: {left.crs}")

    print(f"Loading right dataset: {right_path.name}")
    right = gpd.read_file(right_path)
    print(f"  {len(right)} features, CRS: {right.crs}")

    # CRS alignment
    if left.crs is None and right.crs is None:
        warnings.append("Both datasets have no CRS — proceeding without reprojection")
    elif left.crs is None:
        warnings.append("Left dataset has no CRS — assuming same as right")
        left = left.set_crs(right.crs)
    elif right.crs is None:
        warnings.append("Right dataset has no CRS — assuming same as left")
        right = right.set_crs(left.crs)
    elif left.crs != right.crs:
        print(f"  CRS mismatch: left={left.crs}, right={right.crs}")
        print(f"  Reprojecting right to match left CRS...")
        right = right.to_crs(left.crs)
        warnings.append(f"Right dataset reprojected to match left CRS ({left.crs})")

    # Field selection on right
    right_cols = [c for c in right.columns if c != "geometry"]
    if args.fields is not None:
        missing_fields = [f for f in args.fields if f not in right_cols]
        if missing_fields:
            print(f"WARNING: Requested fields not found in right dataset: {missing_fields}")
            warnings.append(f"Missing requested right fields: {missing_fields}")
        keep_fields = [f for f in args.fields if f in right_cols]
        if not keep_fields:
            warnings.append("No requested fields exist in right dataset — using all")
            keep_fields = right_cols
        right_subset = right[keep_fields + ["geometry"]].copy()
    else:
        right_subset = right.copy()
        keep_fields = right_cols

    print(f"Fields transferred from right: {keep_fields}")

    # Remove empty geometries
    left_clean = left[left.geometry.notna() & ~left.geometry.is_empty].copy()
    right_clean = right_subset[right_subset.geometry.notna() & ~right_subset.geometry.is_empty].copy()

    n_left_dropped = len(left) - len(left_clean)
    n_right_dropped = len(right_subset) - len(right_clean)
    if n_left_dropped:
        warnings.append(f"Dropped {n_left_dropped} left features with null/empty geometry")
    if n_right_dropped:
        warnings.append(f"Dropped {n_right_dropped} right features with null/empty geometry")

    print(f"Performing spatial join: how={args.how}, predicate={args.predicate}...")

    if args.predicate == "nearest":
        result = gpd.sjoin_nearest(
            left_clean,
            right_clean,
            how=args.how,
            max_distance=args.max_distance,
            lsuffix=args.suffix_left.lstrip("_"),
            rsuffix=args.suffix_right.lstrip("_"),
            distance_col="join_distance",
        )
        if "join_distance" in result.columns:
            n_within_dist = int(result["join_distance"].notna().sum())
            mean_dist = float(result["join_distance"].mean()) if n_within_dist > 0 else None
            print(f"  Nearest join — mean distance: {mean_dist:.2f if mean_dist else 'N/A'}")
    else:
        result = gpd.sjoin(
            left_clean,
            right_clean,
            how=args.how,
            predicate=args.predicate,
            lsuffix=args.suffix_left.lstrip("_"),
            rsuffix=args.suffix_right.lstrip("_"),
        )

    # Drop internal join index column
    if "index_right" in result.columns:
        result = result.drop(columns=["index_right"])
    if "index_left" in result.columns:
        result = result.drop(columns=["index_left"])

    # Statistics
    n_total = len(left_clean)

    if args.how == "left":
        # Count unique left features that got a match
        # For left join, unmatched rows have NaN in right fields
        right_key = keep_fields[0] if keep_fields else None
        if right_key and right_key in result.columns:
            n_matched = int(result[right_key].notna().sum())
            n_unmatched = n_total - n_matched
        else:
            n_matched = len(result)
            n_unmatched = 0
    elif args.how == "inner":
        n_matched = len(result)
        n_unmatched = n_total - n_matched
    else:
        n_matched = len(result)
        n_unmatched = 0

    match_rate = round(n_matched / n_total * 100, 1) if n_total > 0 else 0.0

    print(f"Join results:")
    print(f"  Left features: {n_total}")
    print(f"  Output rows: {len(result)}")
    print(f"  Matched: {n_matched} ({match_rate}%)")
    print(f"  Unmatched: {n_unmatched}")

    if n_matched == 0:
        warnings.append("Zero matches found — check CRS alignment and geometry overlap")

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_file(output_path, driver="GPKG")
    print(f"Output: {output_path}")

    # Build log
    log = {
        "step": "spatial_join",
        "left": str(left_path),
        "right": str(right_path),
        "output": str(output_path),
        "how": args.how,
        "predicate": args.predicate,
        "fields_transferred": keep_fields,
        "max_distance": args.max_distance,
        "n_left_features": len(left),
        "n_right_features": len(right),
        "n_output_rows": len(result),
        "n_matched": n_matched,
        "n_unmatched": n_unmatched,
        "match_rate_pct": match_rate,
        "left_crs": str(left.crs),
        "right_crs": str(right.crs),
        "assumptions": assumptions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = output_path.with_name(f"{output_path.stem}.spatial_join.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
