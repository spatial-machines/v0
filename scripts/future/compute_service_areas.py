#!/usr/bin/env python3
"""Compute drive-time or walk-time service areas (isochrones) from point locations.

Uses OSMnx to download the street network and NetworkX to compute reachable
subgraphs within specified travel-time thresholds.

Outputs:
  - GeoPackage with isochrone polygons (one feature per facility × time band)
  - Static map (PNG) showing isochrones overlaid on a contextily basemap
  - JSON handoff log

Usage:
    python compute_service_areas.py \\
        --points data/raw/hospitals.gpkg \\
        --times 10 20 30 \\
        --travel-mode drive \\
        --speed-kmh 50 \\
        --output data/processed/hospital_service_areas.gpkg \\
        [--output-map outputs/maps/hospital_service_areas.png] \\
        [--name-col facility_name] \\
        [--id-col facility_id] \\
        [--dissolve-times]

Inputs:
  --points         Path to point GeoPackage or CSV (with --lat/--lon)
  --lat            Latitude column (CSV only, default: latitude)
  --lon            Longitude column (CSV only, default: longitude)
  --times          Space-separated travel time thresholds in minutes (default: 10 20 30)
  --travel-mode    'drive' or 'walk' (default: drive)
  --speed-kmh      Average speed in km/h for drive mode (default: 50)
  --walk-speed     Walk speed in km/h (default: 4.8)
  --network-type   OSMnx network type: drive, walk, bike, all (default: drive)
  --buffer-km      Buffer around points to download OSM network, in km (default: auto)
  --dissolve-times Merge all facility isochrones per time band into one polygon
  --name-col       Column in points file to use as facility label
  --id-col         Column in points file to use as facility ID
  --output         Output GeoPackage path
  --output-map     Output PNG map path
  --dpi            Map DPI (default: 200)
  --crs            Output CRS EPSG (default: 4326)
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union

# Suppress noisy warnings from OSMnx/shapely
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_ROOT = Path(__file__).parent.parent


def load_points(args):
    """Load point facilities from GeoPackage or CSV."""
    path = Path(args.points).expanduser().resolve()
    if not path.exists():
        print(f"Points file not found: {path}")
        sys.exit(1)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        lat_col = getattr(args, "lat", "latitude") or "latitude"
        lon_col = getattr(args, "lon", "longitude") or "longitude"
        if lat_col not in df.columns or lon_col not in df.columns:
            print(f"CSV must have columns '{lat_col}' and '{lon_col}'. Found: {list(df.columns)}")
            sys.exit(1)
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
            crs="EPSG:4326",
        )
    else:
        gdf = gpd.read_file(path)
        if gdf.crs is None:
            print("WARNING: Points file has no CRS. Assuming EPSG:4326.")
            gdf = gdf.set_crs("EPSG:4326")
        gdf = gdf.to_crs("EPSG:4326")

    # Filter to Point geometries only
    gdf = gdf[gdf.geometry.geom_type == "Point"].copy()
    if len(gdf) == 0:
        print("No point features found in input.")
        sys.exit(1)

    return gdf


def make_isochrones_for_point(lat, lon, times_min, speed_kmh, network_type, buffer_km=None):
    """
    Download OSM network around a point and compute isochrone polygons.

    Returns a dict: {time_minutes: shapely_polygon_or_none}
    """
    max_time = max(times_min)
    # Auto-buffer: max possible travel distance + 20% margin
    if buffer_km is None:
        buffer_km = (speed_kmh * max_time / 60) * 1.3
    buffer_km = max(buffer_km, 2.0)  # minimum 2km

    try:
        G = ox.graph_from_point(
            (lat, lon),
            dist=buffer_km * 1000,
            network_type=network_type,
            simplify=True,
        )
    except Exception as e:
        print(f"  WARNING: Could not download OSM network for ({lat:.4f}, {lon:.4f}): {e}")
        return {t: None for t in times_min}

    # Project to UTM for metric calculations
    G_proj = ox.project_graph(G)
    crs_proj = G_proj.graph.get("crs", "EPSG:3857")

    # Add travel time in seconds as edge attribute
    meters_per_minute = (speed_kmh * 1000) / 60
    for u, v, data in G_proj.edges(data=True):
        data["travel_time"] = data.get("length", 0) / meters_per_minute

    # Find nearest node to the origin point
    orig_node = ox.nearest_nodes(G_proj, lon, lat)

    isochrones = {}
    for t_min in sorted(times_min, reverse=True):
        # Nodes reachable within t_min minutes
        subgraph = nx.ego_graph(
            G_proj, orig_node, radius=t_min, distance="travel_time"
        )
        node_points = [
            Point((data["x"], data["y"]))
            for node, data in subgraph.nodes(data=True)
        ]
        if len(node_points) < 3:
            isochrones[t_min] = None
            continue

        # Convex hull of reachable nodes, buffered slightly
        from shapely.geometry import MultiPoint
        hull = MultiPoint(node_points).convex_hull
        # Buffer by ~200m in projected units to smooth edges
        hull_buffered = hull.buffer(200)

        # Reproject hull back to WGS84
        hull_gdf = gpd.GeoDataFrame(geometry=[hull_buffered], crs=crs_proj)
        hull_wgs84 = hull_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        isochrones[t_min] = hull_wgs84

    return isochrones


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", required=True, help="Input points file (GeoPackage or CSV)")
    parser.add_argument("--lat", default="latitude", help="Latitude column (CSV only)")
    parser.add_argument("--lon", default="longitude", help="Longitude column (CSV only)")
    parser.add_argument("--times", nargs="+", type=int, default=[10, 20, 30],
                        help="Travel time thresholds in minutes (default: 10 20 30)")
    parser.add_argument("--travel-mode", default="drive", choices=["drive", "walk"],
                        help="Travel mode (default: drive)")
    parser.add_argument("--speed-kmh", type=float, default=50.0,
                        help="Drive speed in km/h (default: 50)")
    parser.add_argument("--walk-speed", type=float, default=4.8,
                        help="Walk speed in km/h (default: 4.8)")
    parser.add_argument("--network-type", default="drive",
                        choices=["drive", "walk", "bike", "all"],
                        help="OSMnx network type (default: drive)")
    parser.add_argument("--buffer-km", type=float, default=None,
                        help="OSM network download buffer in km (default: auto)")
    parser.add_argument("--dissolve-times", action="store_true",
                        help="Merge all facility isochrones per time band into one polygon")
    parser.add_argument("--name-col", help="Facility name column for labels")
    parser.add_argument("--id-col", help="Facility ID column")
    parser.add_argument("-o", "--output", help="Output GeoPackage path")
    parser.add_argument("--output-map", help="Output PNG map path")
    parser.add_argument("--dpi", type=int, default=200, help="Map DPI (default: 200)")
    parser.add_argument("--crs", default="EPSG:4326", help="Output CRS (default: EPSG:4326)")
    args = parser.parse_args()

    speed = args.walk_speed if args.travel_mode == "walk" else args.speed_kmh
    network_type = "walk" if args.travel_mode == "walk" else args.network_type
    times = sorted(args.times)

    pts = load_points(args)
    print(f"Loaded {len(pts)} point features")
    print(f"Computing {args.travel_mode} isochrones for {times} minutes at {speed} km/h")

    rows = []
    warnings_list = []

    for idx, row in pts.iterrows():
        lat = row.geometry.y
        lon = row.geometry.x
        name = row.get(args.name_col, f"Facility {idx}") if args.name_col and args.name_col in pts.columns else f"Facility {idx}"
        fid = row.get(args.id_col, str(idx)) if args.id_col and args.id_col in pts.columns else str(idx)

        print(f"  [{idx+1}/{len(pts)}] {name} ({lat:.4f}, {lon:.4f})")

        isochrones = make_isochrones_for_point(
            lat, lon, times, speed, network_type, args.buffer_km
        )

        for t_min, geom in isochrones.items():
            if geom is None:
                warnings_list.append(f"Could not compute {t_min}min isochrone for {name}")
                continue
            rows.append({
                "facility_id": fid,
                "facility_name": name,
                "travel_minutes": t_min,
                "travel_mode": args.travel_mode,
                "speed_kmh": speed,
                "geometry": geom,
            })

    if not rows:
        print("ERROR: No isochrones could be computed. Check your network connection and input CRS.")
        sys.exit(1)

    iso_gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")

    if args.dissolve_times:
        dissolved = []
        for t_min in times:
            subset = iso_gdf[iso_gdf["travel_minutes"] == t_min]
            if len(subset) > 0:
                merged_geom = unary_union(subset.geometry)
                dissolved.append({
                    "travel_minutes": t_min,
                    "travel_mode": args.travel_mode,
                    "speed_kmh": speed,
                    "facility_count": len(subset),
                    "geometry": merged_geom,
                })
        iso_gdf = gpd.GeoDataFrame(dissolved, crs="EPSG:4326")

    if args.crs and args.crs != "EPSG:4326":
        iso_gdf = iso_gdf.to_crs(args.crs)

    # Output
    src = Path(args.points).expanduser().resolve()
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "processed"
        out_path = out_dir / f"{src.stem}_service_areas.gpkg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    iso_gdf.to_file(out_path, driver="GPKG")
    print(f"Saved: {out_path} ({len(iso_gdf)} isochrone features)")

    # Static map
    if args.output_map or True:
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            import contextily as ctx

            map_path = args.output_map
            if not map_path:
                map_dir = PROJECT_ROOT / "outputs" / "maps"
                map_path = str(map_dir / f"{src.stem}_service_areas.png")
            Path(map_path).parent.mkdir(parents=True, exist_ok=True)

            fig, ax = plt.subplots(1, 1, figsize=(14, 10))
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")

            # Color bands from light to dark
            palette = {
                times[-1]: "#fdbb84",  # largest (lightest)
                times[len(times)//2] if len(times) > 2 else times[0]: "#e34a33",
                times[0]: "#7f0000",   # smallest (darkest)
            }
            # Fallback: generate gradient
            colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(times)))[::-1]
            time_colors = {t: colors[i] for i, t in enumerate(sorted(times, reverse=True))}

            iso_plot = iso_gdf.to_crs("EPSG:3857")
            for t_min in sorted(times, reverse=True):
                subset = iso_plot[iso_plot["travel_minutes"] == t_min]
                if len(subset) > 0:
                    subset.plot(ax=ax, alpha=0.45, color=time_colors[t_min],
                                edgecolor="white", linewidth=0.5, zorder=5)

            # Plot facility points
            pts_plot = pts.to_crs("EPSG:3857")
            pts_plot.plot(ax=ax, color="white", edgecolor="#1a1a1a",
                          markersize=70, linewidth=1.5, zorder=20)

            # Basemap
            try:
                ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom="auto")
            except Exception:
                pass

            # Legend
            legend_patches = [
                mpatches.Patch(color=time_colors[t], alpha=0.7,
                               label=f"{t} min {args.travel_mode}")
                for t in sorted(times)
            ]
            ax.legend(handles=legend_patches, loc="lower left", fontsize=9,
                      framealpha=0.9, title="Service Area")

            title = f"Drive-Time Service Areas ({args.travel_mode.title()}, {speed} km/h)"
            ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=12)
            ax.set_axis_off()
            plt.tight_layout()
            fig.savefig(map_path, dpi=args.dpi, bbox_inches="tight")
            plt.close(fig)
            print(f"Saved map: {map_path}")
        except Exception as e:
            print(f"WARNING: Map generation failed: {e}")
            map_path = None

    # Handoff JSON
    log = {
        "step": "compute_service_areas",
        "source_points": str(src),
        "output": str(out_path),
        "output_map": args.output_map,
        "travel_mode": args.travel_mode,
        "speed_kmh": speed,
        "times_minutes": times,
        "features_computed": len(iso_gdf),
        "dissolved": args.dissolve_times,
        "warnings": warnings_list,
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
