#!/usr/bin/env python3
"""Compute trade areas (buffers or isochrones) around POI locations.

Takes a GeoPackage of POI points and generates trade area polygons at
one or more radii. Outputs one layer per radius in the output GeoPackage.

Usage:
    python scripts/core/compute_trade_areas.py \
        --input data/raw/chipotles_mo.gpkg \
        --radii 1 3 5 \
        --output data/processed/trade_areas.gpkg

    python scripts/core/compute_trade_areas.py \
        --input data/raw/chipotles_mo.gpkg \
        --mode isochrone \
        --isochrone-travel-time 5 10 15 \
        --output data/processed/trade_areas_iso.gpkg
"""
from __future__ import annotations

import json
import time
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MILES_TO_METERS = 1609.344


def _get_utm_crs(gdf):
    """Determine the best UTM CRS for a GeoDataFrame based on centroid."""
    centroid = gdf.geometry.unary_union.centroid
    lon = centroid.x
    lat = centroid.y
    zone = int((lon + 180) / 6) + 1
    hemisphere = "north" if lat >= 0 else "south"
    epsg = 32600 + zone if hemisphere == "north" else 32700 + zone
    return f"EPSG:{epsg}"


def _compute_buffers(gdf, radii_miles):
    """Compute circular buffers at given radii (miles). Returns dict of layer_name -> GeoDataFrame."""
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise ImportError("Missing geopandas. Install: pip install geopandas") from exc

    # Determine UTM CRS for accurate buffering
    utm_crs = _get_utm_crs(gdf)
    print(f"  Reprojecting to {utm_crs} for buffering")
    gdf_utm = gdf.to_crs(utm_crs)

    layers = {}
    for radius_mi in radii_miles:
        radius_m = radius_mi * MILES_TO_METERS
        print(f"  Computing {radius_mi}-mile buffer ({radius_m:.0f}m)...")

        buffered = gdf_utm.copy()
        buffered["geometry"] = gdf_utm.geometry.buffer(radius_m)

        # Reproject back to 4326
        buffered = buffered.to_crs("EPSG:4326")

        # Use integer name if radius is a whole number (e.g. 3mi not 3.0mi)
        r_label = int(radius_mi) if radius_mi == int(radius_mi) else radius_mi
        layer_name = f"trade_area_{r_label}mi"
        layers[layer_name] = buffered
        print(f"    {layer_name}: {len(buffered)} polygons")

    return layers


def _compute_isochrones(gdf, travel_times, network_type):
    """Compute drive-time isochrones using OSMnx. Returns dict of layer_name -> GeoDataFrame."""
    try:
        import osmnx as ox
        import geopandas as gpd
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        import networkx as nx
    except ImportError as exc:
        raise ImportError(
            f"Missing dependency: {exc.name}. Install: pip install osmnx networkx"
        ) from exc

    if len(gdf) > 20:
        print(f"  WARNING: {len(gdf)} POIs — isochrone computation will be slow!")
        print(f"  Consider using --mode buffer or sampling POIs first.")

    layers = {}

    for travel_min in travel_times:
        print(f"  Computing {travel_min}-minute {network_type} isochrones...")
        polys = []
        attrs = []

        for idx, row in gdf.iterrows():
            pt = row.geometry
            try:
                G = ox.graph_from_point((pt.y, pt.x), dist=travel_min * 1500,
                                        network_type=network_type)
                G = ox.add_edge_speeds(G)
                G = ox.add_edge_travel_times(G)

                center_node = ox.nearest_nodes(G, pt.x, pt.y)
                subgraph = nx.ego_graph(G, center_node,
                                         radius=travel_min * 60,
                                         distance="travel_time")
                node_points = [
                    (data["x"], data["y"])
                    for node, data in subgraph.nodes(data=True)
                ]
                if len(node_points) >= 3:
                    from shapely.geometry import MultiPoint
                    hull = MultiPoint(node_points).convex_hull
                    polys.append(hull)
                else:
                    polys.append(pt.buffer(0.01))  # fallback tiny buffer
            except Exception as exc:
                print(f"    WARNING: isochrone failed for POI {idx}: {exc}")
                polys.append(pt.buffer(0.01))

            # Preserve attributes
            attr = {c: row[c] for c in gdf.columns if c != "geometry"}
            attrs.append(attr)

        result = gpd.GeoDataFrame(attrs, geometry=polys, crs="EPSG:4326")
        layer_name = f"trade_area_{travel_min}min"
        layers[layer_name] = result
        print(f"    {layer_name}: {len(result)} polygons")

    return layers


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute trade areas (buffers or isochrones) around POI locations."
    )
    parser.add_argument("--input", required=True, help="Input GeoPackage of POI points")
    parser.add_argument("--radii", nargs="+", type=float, default=[1, 3, 5],
                        help="Buffer radii in miles (default: 1 3 5)")
    parser.add_argument("--mode", choices=["buffer", "isochrone"], default="buffer",
                        help="Trade area method (default: buffer)")
    parser.add_argument("--isochrone-travel-time", nargs="+", type=int, default=[5, 10, 15],
                        help="Travel times in minutes for isochrone mode (default: 5 10 15)")
    parser.add_argument("--network-type", default="drive",
                        help="Network type for OSMnx isochrones (default: drive)")
    parser.add_argument("--output", "-o", required=True, help="Output GeoPackage path")
    args = parser.parse_args()

    try:
        import geopandas as gpd
    except ImportError:
        print("ERROR: geopandas not installed. Run: pip install geopandas")
        return 1

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: input not found: {src}")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Computing trade areas")
    print(f"  Input: {src}")
    print(f"  Mode: {args.mode}")

    gdf = gpd.read_file(src)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf = gdf.to_crs("EPSG:4326")

    print(f"  Loaded {len(gdf)} POIs")

    if len(gdf) == 0:
        print("WARNING: no POIs in input — writing empty output")
        gdf.to_file(out_path, driver="GPKG", layer="trade_area_empty")
        return 0

    t0 = time.time()

    if args.mode == "buffer":
        print(f"  Radii: {args.radii} miles")
        layers = _compute_buffers(gdf, args.radii)
    else:
        print(f"  Travel times: {args.isochrone_travel_time} minutes")
        print(f"  Network type: {args.network_type}")
        layers = _compute_isochrones(gdf, args.isochrone_travel_time, args.network_type)

    elapsed = round(time.time() - t0, 2)

    # Write all layers to output GeoPackage (delete first to avoid appending to stale file)
    if out_path.exists():
        out_path.unlink()
    first = True
    for layer_name, layer_gdf in layers.items():
        if first:
            layer_gdf.to_file(out_path, driver="GPKG", layer=layer_name)
            first = False
        else:
            layer_gdf.to_file(out_path, driver="GPKG", layer=layer_name, mode="a")
        print(f"  Wrote layer: {layer_name} ({len(layer_gdf)} features)")

    print(f"  Output: {out_path}")
    print(f"  Elapsed: {elapsed}s")

    # JSON log
    log = {
        "step": "compute_trade_areas",
        "input": str(src),
        "n_pois": len(gdf),
        "mode": args.mode,
        "radii": args.radii if args.mode == "buffer" else None,
        "travel_times": args.isochrone_travel_time if args.mode == "isochrone" else None,
        "layers": list(layers.keys()),
        "crs": "EPSG:4326",
        "output": str(out_path),
        "elapsed_s": elapsed,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".trade_areas.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
