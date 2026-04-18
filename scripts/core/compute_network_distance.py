#!/usr/bin/env python3
"""Compute network-based distances from polygon centroids to nearest facilities.

Unlike overlay_points.py (Euclidean distance), this uses the actual road network
via OSMnx to compute real driving or walking distance. This is the correct way
to measure accessibility.

Adds columns to the input polygons:
  - dist_to_nearest_{label}_km: network distance in km
  - time_to_nearest_{label}_min: estimated travel time in minutes
  - nearest_{label}_name: name of the nearest facility

Usage:
    python compute_network_distance.py \\
        --polygons data/processed/denver_tracts.gpkg \\
        --points data/raw/hospitals.gpkg \\
        --label hospital \\
        --mode drive \\
        --output data/processed/denver_tracts_with_hospital_dist.gpkg

    python compute_network_distance.py \\
        --polygons data/processed/fulton_tracts.gpkg \\
        --points data/processed/marta_stations.gpkg \\
        --points-name-col station_name \\
        --label marta \\
        --mode walk \\
        --output data/processed/fulton_tracts_marta_walk.gpkg
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

SPEEDS = {
    "drive": 40,
    "walk": 4.8,
    "bike": 15,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--polygons", required=True, help="Input polygon GeoPackage (e.g., census tracts)")
    parser.add_argument("--points", required=True, help="Facility points GeoPackage")
    parser.add_argument("--points-name-col", help="Column in points for facility name")
    parser.add_argument("--label", required=True, help="Short label for output columns (e.g., 'hospital')")
    parser.add_argument("--mode", default="drive", choices=["drive", "walk", "bike"])
    parser.add_argument("--max-polygons", type=int, default=500,
                        help="Max polygons to process (default: 500)")
    parser.add_argument("-o", "--output", required=True, help="Output GeoPackage path")
    args = parser.parse_args()

    import osmnx as ox
    import networkx as nx

    # Load data
    polys = gpd.read_file(args.polygons).to_crs("EPSG:4326")
    pts = gpd.read_file(args.points).to_crs("EPSG:4326")

    if len(polys) > args.max_polygons:
        print(f"  Limiting to {args.max_polygons} of {len(polys)} polygons")
        polys = polys.head(args.max_polygons)

    print(f"Loaded {len(polys)} polygons, {len(pts)} facility points")

    # Get centroids of polygons
    centroids = polys.geometry.centroid

    # Compute study area bounds with buffer
    all_geom = pd.concat([centroids, pts.geometry])
    bounds = all_geom.total_bounds  # minx, miny, maxx, maxy
    center = ((bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2)

    # Network radius: diagonal of bbox + buffer
    diag_m = gpd.GeoSeries([
        gpd.points_from_xy([bounds[0]], [bounds[1]])[0],
        gpd.points_from_xy([bounds[2]], [bounds[3]])[0],
    ], crs="EPSG:4326").to_crs("EPSG:3857")
    diag_dist = diag_m.iloc[0].distance(diag_m.iloc[1])
    network_radius = int(diag_dist / 2 * 1.3)  # half diagonal + 30% buffer

    # Download network
    mode_map = {"drive": "drive", "walk": "walk", "bike": "bike"}
    print(f"  Downloading {args.mode} network ({network_radius/1000:.0f} km radius)...")
    try:
        G = ox.graph_from_point(center, dist=network_radius, network_type=mode_map[args.mode], simplify=True)
    except Exception as e:
        print(f"  Error: {e}")
        print("  Falling back to Euclidean distance...")
        # Fallback to straight-line
        polys_proj = polys.to_crs(polys.estimate_utm_crs())
        pts_proj = pts.to_crs(polys_proj.crs)
        cent_proj = polys_proj.geometry.centroid

        dists = []
        nearest_names = []
        for c in cent_proj:
            pt_dists = pts_proj.geometry.distance(c)
            min_idx = pt_dists.idxmin()
            dists.append(pt_dists[min_idx] / 1000)  # meters to km
            if args.points_name_col and args.points_name_col in pts.columns:
                nearest_names.append(pts.loc[min_idx, args.points_name_col])
            else:
                nearest_names.append(str(min_idx))

        polys[f"dist_to_nearest_{args.label}_km"] = dists
        polys[f"time_to_nearest_{args.label}_min"] = [d / SPEEDS[args.mode] * 60 for d in dists]
        polys[f"nearest_{args.label}_name"] = nearest_names
        polys[f"{args.label}_distance_method"] = "euclidean_fallback"

        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        polys.to_file(out_path, driver="GPKG")
        print(f"  Saved (Euclidean fallback): {out_path}")
        return 0

    # Add travel times to edges
    speed = SPEEDS[args.mode]
    for u, v, data in G.edges(data=True):
        length_km = data.get("length", 0) / 1000
        data["travel_time"] = (length_km / speed) * 60
        data["length_km"] = length_km

    print(f"  Network: {len(G.nodes)} nodes, {len(G.edges)} edges")

    # Snap all facility points to nearest network nodes
    print(f"  Snapping {len(pts)} facilities to network...")
    facility_nodes = ox.distance.nearest_nodes(G, pts.geometry.x.values, pts.geometry.y.values)

    # Compute shortest distances from each centroid to ALL facility nodes
    print(f"  Computing distances for {len(polys)} polygons...", end="", flush=True)

    dist_results = []
    time_results = []
    name_results = []

    for i, centroid in enumerate(centroids):
        if i % 50 == 0 and i > 0:
            print(f" {i}", end="", flush=True)

        try:
            origin = ox.distance.nearest_nodes(G, centroid.x, centroid.y)

            best_dist = float("inf")
            best_time = float("inf")
            best_name = "unknown"

            for j, fnode in enumerate(facility_nodes):
                try:
                    path_length = nx.shortest_path_length(G, origin, fnode, weight="length_km")
                    path_time = nx.shortest_path_length(G, origin, fnode, weight="travel_time")
                    if path_length < best_dist:
                        best_dist = path_length
                        best_time = path_time
                        if args.points_name_col and args.points_name_col in pts.columns:
                            best_name = pts.iloc[j][args.points_name_col]
                        else:
                            best_name = str(j)
                except nx.NetworkXNoPath:
                    continue
        except Exception:
            best_dist = np.nan
            best_time = np.nan
            best_name = "unreachable"

        dist_results.append(round(best_dist, 2) if best_dist != float("inf") else np.nan)
        time_results.append(round(best_time, 1) if best_time != float("inf") else np.nan)
        name_results.append(best_name)

    print(" done")

    # Add to polygons
    polys[f"dist_to_nearest_{args.label}_km"] = dist_results
    polys[f"time_to_nearest_{args.label}_min"] = time_results
    polys[f"nearest_{args.label}_name"] = name_results
    polys[f"{args.label}_distance_method"] = "network"

    # Output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    polys.to_file(out_path, driver="GPKG")

    # Stats
    valid = polys[f"dist_to_nearest_{args.label}_km"].dropna()
    print(f"\nResults:")
    print(f"  {len(valid)}/{len(polys)} polygons with valid network distance")
    print(f"  Mean distance: {valid.mean():.1f} km")
    print(f"  Median: {valid.median():.1f} km")
    print(f"  Max: {valid.max():.1f} km")
    print(f"  Mean travel time: {polys[f'time_to_nearest_{args.label}_min'].dropna().mean():.1f} min")
    print(f"\nSaved: {out_path}")

    # Log
    log = {
        "step": "compute_network_distance",
        "mode": args.mode,
        "speed_kmh": speed,
        "polygons": len(polys),
        "facilities": len(pts),
        "valid_distances": int(valid.notna().sum()),
        "mean_dist_km": round(float(valid.mean()), 2),
        "max_dist_km": round(float(valid.max()), 2),
        "network_nodes": len(G.nodes),
        "network_edges": len(G.edges),
        "output": str(out_path),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
