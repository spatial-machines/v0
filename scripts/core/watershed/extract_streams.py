#!/usr/bin/env python3
"""Extract and classify a stream network with Strahler ordering.

Extracts streams from a flow accumulation raster using a configurable
threshold, then assigns Strahler stream orders via graph traversal.

Usage:
    python extract_streams.py \\
        --flow-acc outputs/qgis/data/flow_acc.tif \\
        --flow-dir outputs/qgis/data/flow_dir.tif \\
        --watershed outputs/qgis/data/watershed_boundary.gpkg \\
        --output-dir outputs/qgis/data \\
        [--threshold 0.01] \\
        [--output-stats outputs/tables/stream_stats.json]
"""

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import numpy as np

# pysheds uses deprecated np.in1d removed in NumPy 2.x
if not hasattr(np, "in1d"):
    np.in1d = np.isin


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract stream network with Strahler ordering")
    parser.add_argument("--flow-acc", required=True, help="Flow accumulation GeoTIFF")
    parser.add_argument("--flow-dir", required=True, help="Flow direction GeoTIFF (ESRI D8)")
    parser.add_argument("--watershed", required=True, help="Watershed boundary GeoPackage")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    parser.add_argument("--threshold", type=float, default=0.01,
                        help="Stream threshold as fraction of max accumulation (default: 0.01)")
    parser.add_argument("--output-stats", default=None, help="Output JSON stats")
    args = parser.parse_args()

    facc_path = Path(args.flow_acc).resolve()
    fdir_path = Path(args.flow_dir).resolve()
    ws_path = Path(args.watershed).resolve()
    for p, name in [(facc_path, "flow accumulation"), (fdir_path, "flow direction"), (ws_path, "watershed")]:
        if not p.exists():
            print(f"ERROR: {name} not found: {p}")
            return 1

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    import geopandas as gpd
    from pysheds.grid import Grid
    from shapely.geometry import LineString, MultiLineString
    import networkx as nx

    # ── Load grids ────────────────────────────────────────────────
    print(f"Loading flow accumulation: {facc_path}")
    grid = Grid.from_raster(str(facc_path))
    acc = grid.read_raster(str(facc_path))
    acc_arr = np.array(acc, dtype=np.float64)

    print(f"Loading flow direction: {fdir_path}")
    fdir = grid.read_raster(str(fdir_path))
    fdir_arr = np.array(fdir, dtype=np.int32)

    affine = grid.affine

    # ── Load watershed mask ───────────────────────────────────────
    print(f"Loading watershed: {ws_path}")
    ws_gdf = gpd.read_file(ws_path)
    crs = str(ws_gdf.crs)

    # Rasterize watershed boundary to mask
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds

    ws_mask = rasterize(
        [(geom, 1) for geom in ws_gdf.geometry],
        out_shape=acc_arr.shape,
        transform=affine,
        fill=0,
        dtype=np.uint8,
    ).astype(bool)

    # ── Extract stream cells ──────────────────────────────────────
    max_acc = float(np.nanmax(acc_arr[ws_mask]))
    threshold_abs = max_acc * args.threshold
    print(f"Stream threshold: {threshold_abs:.0f} cells ({args.threshold*100:.1f}% of max {max_acc:.0f})")

    stream_mask = (acc_arr >= threshold_abs) & ws_mask
    stream_cells = int(np.sum(stream_mask))
    print(f"  {stream_cells} stream cells identified")

    if stream_cells == 0:
        print("ERROR: No stream cells found — try lowering --threshold")
        return 1

    # ── Build directed graph of stream cells ──────────────────────
    # ESRI D8 dirmap: direction -> (row_offset, col_offset)
    esri_offsets = {
        1: (0, 1),     # E
        2: (1, 1),     # SE
        4: (1, 0),     # S
        8: (1, -1),    # SW
        16: (0, -1),   # W
        32: (-1, -1),  # NW
        64: (-1, 0),   # N
        128: (-1, 1),  # NE
    }

    print("Building stream graph...")
    G = nx.DiGraph()
    rows, cols = acc_arr.shape
    stream_indices = np.argwhere(stream_mask)

    for r, c in stream_indices:
        G.add_node((r, c), accumulation=float(acc_arr[r, c]))
        d = int(fdir_arr[r, c])
        if d in esri_offsets:
            dr, dc = esri_offsets[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and stream_mask[nr, nc]:
                # Edge from upstream to downstream
                G.add_edge((r, c), (nr, nc))

    print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # ── Strahler ordering ─────────────────────────────────────────
    print("Computing Strahler stream orders...")
    strahler = {}

    # Find headwater nodes (no upstream neighbors in the stream graph)
    headwaters = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"  {len(headwaters)} headwater nodes")

    # Topological ordering — process from headwaters downstream
    try:
        topo_order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        print("  WARNING: Cycle detected in stream graph, breaking cycles")
        # Break cycles by removing back edges
        while True:
            try:
                cycle = nx.find_cycle(G, orientation="original")
                G.remove_edge(cycle[0][0], cycle[0][1])
            except nx.NetworkXNoCycle:
                break
        topo_order = list(nx.topological_sort(G))

    for node in topo_order:
        predecessors = list(G.predecessors(node))
        if not predecessors:
            strahler[node] = 1
        else:
            pred_orders = [strahler.get(p, 1) for p in predecessors]
            max_order = max(pred_orders)
            count_max = pred_orders.count(max_order)
            if count_max >= 2:
                strahler[node] = max_order + 1
            else:
                strahler[node] = max_order

    max_strahler = max(strahler.values()) if strahler else 0
    print(f"  Max Strahler order: {max_strahler}")

    # ── Vectorize stream segments by order ────────────────────────
    print("Vectorizing stream segments...")
    cell_x = abs(affine.a)
    cell_y = abs(affine.e)

    # Group connected cells into line segments by Strahler order
    segments = []
    segment_orders = []

    # Walk each edge and create line segments grouped by order
    visited_edges = set()
    for node in topo_order:
        for succ in G.successors(node):
            if (node, succ) in visited_edges:
                continue
            visited_edges.add((node, succ))
            order = strahler.get(node, 1)
            r1, c1 = node
            r2, c2 = succ
            x1 = affine.c + c1 * affine.a + 0.5 * affine.a
            y1 = affine.f + r1 * affine.e + 0.5 * affine.e
            x2 = affine.c + c2 * affine.a + 0.5 * affine.a
            y2 = affine.f + r2 * affine.e + 0.5 * affine.e
            segments.append(LineString([(x1, y1), (x2, y2)]))
            segment_orders.append(order)

    if not segments:
        print("ERROR: No stream segments generated")
        return 1

    streams_gdf = gpd.GeoDataFrame(
        {"strahler_order": segment_orders},
        geometry=segments,
        crs=crs,
    )

    # Merge adjacent segments of the same order for cleaner output
    merged_records = []
    for order in sorted(streams_gdf["strahler_order"].unique()):
        subset = streams_gdf[streams_gdf["strahler_order"] == order]
        merged_geom = subset.geometry.union_all()
        if merged_geom.geom_type == "MultiLineString":
            for line in merged_geom.geoms:
                merged_records.append({"strahler_order": order, "geometry": line})
        elif merged_geom.geom_type == "LineString":
            merged_records.append({"strahler_order": order, "geometry": merged_geom})
        else:
            merged_records.append({"strahler_order": order, "geometry": merged_geom})

    streams_ordered = gpd.GeoDataFrame(merged_records, crs=crs)

    out_path = out_dir / "streams_ordered.gpkg"
    streams_ordered.to_file(out_path, driver="GPKG")
    print(f"  Saved ordered streams: {out_path} ({len(streams_ordered)} segments)")

    # ── Stats ─────────────────────────────────────────────────────
    total_length_m = float(streams_ordered.geometry.length.sum())
    total_length_km = round(total_length_m / 1000, 4)
    ws_area_km2 = float(ws_gdf.geometry.area.sum()) / 1e6
    drainage_density = round(total_length_km / ws_area_km2, 4) if ws_area_km2 > 0 else 0

    order_dist = {}
    for order in sorted(streams_ordered["strahler_order"].unique()):
        subset = streams_ordered[streams_ordered["strahler_order"] == order]
        order_dist[str(int(order))] = {
            "count": len(subset),
            "total_length_km": round(float(subset.geometry.length.sum()) / 1000, 4),
        }

    stats = {
        "step": "extract_streams",
        "threshold_fraction": args.threshold,
        "threshold_cells": round(threshold_abs, 0),
        "stream_cells": stream_cells,
        "total_stream_length_km": total_length_km,
        "drainage_density_km_per_km2": drainage_density,
        "max_strahler_order": max_strahler,
        "headwater_count": len(headwaters),
        "order_distribution": order_dist,
        "segment_count": len(streams_ordered),
        "watershed_area_km2": round(ws_area_km2, 4),
        "outputs": {
            "streams_ordered": str(out_path),
        },
        "extracted_at": datetime.now(UTC).isoformat(),
    }

    if args.output_stats:
        stats_path = Path(args.output_stats).resolve()
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(json.dumps(stats, indent=2))
        print(f"  Saved stats: {stats_path}")

    print(f"Stream extraction complete. {total_length_km} km total, max order {max_strahler}, drainage density {drainage_density} km/km².")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
