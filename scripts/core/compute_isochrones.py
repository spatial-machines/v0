#!/usr/bin/env python3
"""Compute drive-time or walk-time isochrones using OSMnx road networks.

Given a set of facility points and travel time thresholds, computes the
area reachable within each threshold along the actual road network.
Outputs polygon isochrones as a GeoPackage.

This is the real network-based accessibility tool — NOT straight-line buffers.

Usage:
    # 5, 10, 15 minute drive-time from hospitals
    python compute_isochrones.py \\
        --points data/raw/hospitals.gpkg \\
        --thresholds 5,10,15 \\
        --mode drive \\
        --output outputs/isochrones/hospital_drive.gpkg

    # Walk-time from transit stops
    python compute_isochrones.py \\
        --points data/raw/marta_stations.gpkg \\
        --thresholds 5,10,15,20 \\
        --mode walk \\
        --output outputs/isochrones/transit_walk.gpkg

    # Single point with lat/lon
    python compute_isochrones.py \\
        --lat 39.7392 --lon -104.9903 \\
        --thresholds 5,10,15 \\
        --mode drive \\
        --output outputs/isochrones/downtown_denver_drive.gpkg
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
from shapely.geometry import Point, MultiPoint
from shapely.ops import unary_union

warnings.filterwarnings("ignore", category=FutureWarning)

# Average travel speeds (km/h) by mode
SPEEDS = {
    "drive": 40,      # Urban average with stops/lights
    "walk": 4.8,      # Average walking speed
    "bike": 15,       # Average urban cycling
}


def get_network(center_point, dist_m, mode):
    """Download road network graph from OSMnx."""
    import osmnx as ox

    network_types = {
        "drive": "drive",
        "walk": "walk",
        "bike": "bike",
    }
    ntype = network_types.get(mode, "drive")

    print(f"  Downloading {ntype} network ({dist_m/1000:.1f} km radius)...")
    G = ox.graph_from_point(
        (center_point.y, center_point.x),
        dist=dist_m,
        network_type=ntype,
        simplify=True,
    )

    # Add edge travel times based on speed
    speed_kmh = SPEEDS[mode]
    for u, v, data in G.edges(data=True):
        length_km = data.get("length", 0) / 1000
        data["travel_time"] = (length_km / speed_kmh) * 60  # minutes

    return G


def compute_isochrone(G, center_point, threshold_minutes, mode):
    """Compute isochrone polygon for a single point and threshold."""
    import osmnx as ox
    import networkx as nx

    # Find nearest node
    center_node = ox.distance.nearest_nodes(G, center_point.x, center_point.y)

    # Compute shortest paths by travel time
    travel_times = nx.single_source_dijkstra_path_length(
        G, center_node, cutoff=threshold_minutes, weight="travel_time"
    )

    # Get reachable nodes
    reachable_nodes = list(travel_times.keys())
    if len(reachable_nodes) < 3:
        return None

    # Get node coordinates
    node_points = []
    for node in reachable_nodes:
        x = G.nodes[node].get("x")
        y = G.nodes[node].get("y")
        if x is not None and y is not None:
            node_points.append(Point(x, y))

    if len(node_points) < 3:
        return None

    # Convex hull of reachable nodes (simple but effective)
    return MultiPoint(node_points).convex_hull


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", help="Input point GeoPackage or GeoJSON")
    parser.add_argument("--lat", type=float, help="Single point latitude")
    parser.add_argument("--lon", type=float, help="Single point longitude")
    parser.add_argument("--name-col", help="Column for facility name labels")
    parser.add_argument("--thresholds", required=True,
                        help="Comma-separated travel time thresholds in minutes (e.g., 5,10,15)")
    parser.add_argument("--mode", default="drive", choices=["drive", "walk", "bike"],
                        help="Travel mode (default: drive)")
    parser.add_argument("--max-points", type=int, default=50,
                        help="Max facilities to process (default: 50)")
    parser.add_argument("-o", "--output", required=True,
                        help="Output GeoPackage path")
    args = parser.parse_args()

    # Parse thresholds
    thresholds = sorted([float(t.strip()) for t in args.thresholds.split(",")])
    max_threshold = max(thresholds)

    # Load or create points
    if args.points:
        pts_gdf = gpd.read_file(args.points).to_crs("EPSG:4326")
        if len(pts_gdf) > args.max_points:
            print(f"  Limiting to {args.max_points} of {len(pts_gdf)} points")
            pts_gdf = pts_gdf.head(args.max_points)
        print(f"Loaded {len(pts_gdf)} facility points from {args.points}")
    elif args.lat is not None and args.lon is not None:
        pts_gdf = gpd.GeoDataFrame(
            [{"name": "origin", "geometry": Point(args.lon, args.lat)}],
            crs="EPSG:4326",
        )
        print(f"Using single point: ({args.lat}, {args.lon})")
    else:
        print("Error: provide --points or --lat/--lon")
        return 1

    # Compute network coverage radius (generous buffer)
    speed = SPEEDS[args.mode]
    network_radius_m = int((speed * 1000 / 60) * max_threshold * 1.5)

    # Get centroid for network download
    all_bounds = pts_gdf.total_bounds
    center = Point((all_bounds[0] + all_bounds[2]) / 2, (all_bounds[1] + all_bounds[3]) / 2)

    # Download network once for the whole study area
    try:
        G = get_network(center, network_radius_m, args.mode)
    except Exception as e:
        print(f"  Error downloading network: {e}")
        print("  This may be a network issue or the study area may be too large.")
        print("  Try reducing --max-points or the study area extent.")
        return 1

    print(f"  Network: {len(G.nodes)} nodes, {len(G.edges)} edges")

    # Compute isochrones for each point × threshold
    results = []
    for idx, row in pts_gdf.iterrows():
        pt = row.geometry
        name = row.get(args.name_col, f"facility_{idx}") if args.name_col else f"facility_{idx}"
        print(f"  Computing isochrones for {name}...", end="", flush=True)

        for threshold in thresholds:
            try:
                iso_poly = compute_isochrone(G, pt, threshold, args.mode)
                if iso_poly is not None:
                    results.append({
                        "facility_name": name,
                        "facility_idx": idx,
                        "threshold_min": threshold,
                        "mode": args.mode,
                        "speed_kmh": speed,
                        "geometry": iso_poly,
                    })
            except Exception as e:
                print(f" ({threshold}min failed: {e})", end="")

        print(f" done ({len(thresholds)} thresholds)")

    if not results:
        print("No isochrones computed. Check if the points are within the network coverage.")
        return 1

    # Build GeoDataFrame
    iso_gdf = gpd.GeoDataFrame(results, crs="EPSG:4326")

    # Compute area for each isochrone (sq km)
    iso_proj = iso_gdf.to_crs(iso_gdf.estimate_utm_crs())
    iso_gdf["area_sqkm"] = iso_proj.geometry.area / 1e6

    # Output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    iso_gdf.to_file(out_path, driver="GPKG")
    print(f"\nSaved {len(iso_gdf)} isochrones to {out_path}")

    # Summary
    for threshold in thresholds:
        subset = iso_gdf[iso_gdf["threshold_min"] == threshold]
        if len(subset) > 0:
            mean_area = subset["area_sqkm"].mean()
            print(f"  {threshold} min {args.mode}: {len(subset)} isochrones, avg {mean_area:.1f} sq km")

    # Dissolved coverage polygons (union of all isochrones per threshold)
    dissolved_path = out_path.with_stem(out_path.stem + "_dissolved")
    dissolved_results = []
    for threshold in thresholds:
        subset = iso_gdf[iso_gdf["threshold_min"] == threshold]
        if len(subset) > 0:
            merged = unary_union(subset.geometry)
            dissolved_results.append({
                "threshold_min": threshold,
                "mode": args.mode,
                "facility_count": len(subset),
                "geometry": merged,
            })
    if dissolved_results:
        dissolved_gdf = gpd.GeoDataFrame(dissolved_results, crs="EPSG:4326")
        dissolved_gdf.to_file(dissolved_path, driver="GPKG")
        print(f"  Dissolved coverage: {dissolved_path}")

    # Log
    log = {
        "step": "compute_isochrones",
        "mode": args.mode,
        "speed_kmh": speed,
        "thresholds_min": thresholds,
        "facilities": len(pts_gdf),
        "isochrones_computed": len(iso_gdf),
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
