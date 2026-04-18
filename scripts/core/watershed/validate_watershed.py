#!/usr/bin/env python3
"""QA validation for watershed analysis outputs.

Checks geometric validity, spatial consistency, and network connectivity
of watershed delineation results.

Usage:
    python validate_watershed.py \\
        --watershed outputs/qgis/data/watershed_boundary.gpkg \\
        --pour-point outputs/qgis/data/pour_point_snapped.gpkg \\
        --streams outputs/qgis/data/streams_ordered.gpkg \\
        --flow-acc outputs/qgis/data/flow_acc.tif \\
        --output outputs/qa/validation_report.json
"""

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate watershed analysis outputs")
    parser.add_argument("--watershed", required=True, help="Watershed boundary GeoPackage")
    parser.add_argument("--pour-point", required=True, help="Snapped pour point GeoPackage")
    parser.add_argument("--streams", default=None, help="Ordered streams GeoPackage")
    parser.add_argument("--flow-acc", default=None, help="Flow accumulation GeoTIFF")
    parser.add_argument("--expected-area-km2", type=float, default=None,
                        help="Expected drainage area for cross-check")
    parser.add_argument("--output", required=True, help="Output validation report JSON")
    args = parser.parse_args()

    import geopandas as gpd

    checks = []
    all_pass = True

    # ── Check 1: Watershed polygon validity ───────────────────────
    print("Check 1: Watershed polygon validity...")
    ws_gdf = gpd.read_file(args.watershed)
    ws_geom = ws_gdf.geometry.iloc[0]

    is_valid = ws_geom.is_valid
    area = ws_geom.area
    has_area = area > 0
    no_self_intersection = is_valid  # shapely is_valid catches self-intersections

    check1 = {
        "name": "watershed_polygon_validity",
        "passed": is_valid and has_area,
        "details": {
            "is_valid": is_valid,
            "area_positive": has_area,
            "area_raw": round(area, 4),
            "geometry_type": ws_geom.geom_type,
        },
    }
    if not check1["passed"]:
        all_pass = False
        if not is_valid:
            check1["details"]["reason"] = ws_geom.explain_validity()
    checks.append(check1)
    print(f"  {'PASS' if check1['passed'] else 'FAIL'}: valid={is_valid}, area={area:.2f}")

    # ── Check 2: Pour point within watershed ──────────────────────
    print("Check 2: Pour point within watershed...")
    pp_gdf = gpd.read_file(args.pour_point)
    pp_geom = pp_gdf.geometry.iloc[0]

    # Use a small buffer to handle edge cases where point is on boundary
    pp_within = ws_geom.contains(pp_geom) or ws_geom.buffer(ws_geom.length * 0.001).contains(pp_geom)
    pp_distance = pp_geom.distance(ws_geom.boundary)

    check2 = {
        "name": "pour_point_within_watershed",
        "passed": bool(pp_within),
        "details": {
            "within": bool(pp_within),
            "distance_to_boundary": round(float(pp_distance), 6),
            "pour_point": {"x": round(pp_geom.x, 6), "y": round(pp_geom.y, 6)},
        },
    }
    if not check2["passed"]:
        all_pass = False
    checks.append(check2)
    print(f"  {'PASS' if check2['passed'] else 'FAIL'}: within={pp_within}")

    # ── Check 3: Stream network connectivity ──────────────────────
    if args.streams and Path(args.streams).exists():
        print("Check 3: Stream network connectivity...")
        import networkx as nx

        streams_gdf = gpd.read_file(args.streams)
        total_segments = len(streams_gdf)

        # Build a graph from stream endpoints
        G = nx.Graph()
        for idx, row in streams_gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue
            if geom.geom_type == "LineString":
                coords = list(geom.coords)
                if len(coords) >= 2:
                    # Round coordinates to handle floating point
                    start = tuple(round(c, 3) for c in coords[0])
                    end = tuple(round(c, 3) for c in coords[-1])
                    G.add_edge(start, end, segment=idx)
            elif geom.geom_type == "MultiLineString":
                for line in geom.geoms:
                    coords = list(line.coords)
                    if len(coords) >= 2:
                        start = tuple(round(c, 3) for c in coords[0])
                        end = tuple(round(c, 3) for c in coords[-1])
                        G.add_edge(start, end, segment=idx)

        n_components = nx.number_connected_components(G) if G.number_of_nodes() > 0 else 0
        is_connected = n_components <= 1

        check3 = {
            "name": "stream_network_connectivity",
            "passed": bool(is_connected),
            "details": {
                "total_segments": total_segments,
                "graph_nodes": G.number_of_nodes(),
                "graph_edges": G.number_of_edges(),
                "connected_components": n_components,
                "is_connected": bool(is_connected),
            },
        }
        if not check3["passed"]:
            all_pass = False
        checks.append(check3)
        print(f"  {'PASS' if check3['passed'] else 'FAIL'}: {n_components} component(s)")
    else:
        checks.append({
            "name": "stream_network_connectivity",
            "passed": False,
            "details": {"reason": "streams file not provided or not found"},
        })
        all_pass = False
        print("  SKIP: No streams file")

    # ── Check 4: Flow accumulation at pour point ──────────────────
    if args.flow_acc and Path(args.flow_acc).exists():
        print("Check 4: Flow accumulation at pour point...")
        from pysheds.grid import Grid

        grid = Grid.from_raster(args.flow_acc)
        acc = grid.read_raster(args.flow_acc)
        acc_arr = np.array(acc, dtype=np.float64)
        affine = grid.affine

        # Sample accumulation at pour point
        col_idx = int((pp_geom.x - affine.c) / affine.a)
        row_idx = int((pp_geom.y - affine.f) / affine.e)
        row_idx = max(0, min(row_idx, acc_arr.shape[0] - 1))
        col_idx = max(0, min(col_idx, acc_arr.shape[1] - 1))

        pp_acc = float(acc_arr[row_idx, col_idx])
        max_acc = float(np.nanmax(acc_arr))
        pp_pct = round(pp_acc / max_acc * 100, 2) if max_acc > 0 else 0

        # Pour point should have meaningful accumulation (at least 0.5% of max or 100 cells)
        high_acc = pp_pct >= 0.5 or pp_acc >= 100

        cell_area_m2 = abs(affine.a * affine.e)
        derived_area_km2 = round(pp_acc * cell_area_m2 / 1e6, 4)

        area_match = True
        if args.expected_area_km2:
            ratio = derived_area_km2 / args.expected_area_km2 if args.expected_area_km2 > 0 else 0
            area_match = 0.5 <= ratio <= 2.0  # within 2x

        check4 = {
            "name": "pour_point_accumulation",
            "passed": bool(high_acc and area_match),
            "details": {
                "accumulation_at_pp": round(pp_acc, 0),
                "max_accumulation": round(max_acc, 0),
                "pp_pct_of_max": pp_pct,
                "derived_area_km2": derived_area_km2,
                "high_accumulation": bool(high_acc),
            },
        }
        if args.expected_area_km2:
            check4["details"]["expected_area_km2"] = args.expected_area_km2
            check4["details"]["area_ratio"] = round(ratio, 4)
        if not check4["passed"]:
            all_pass = False
        checks.append(check4)
        print(f"  {'PASS' if check4['passed'] else 'FAIL'}: acc={pp_acc:.0f} ({pp_pct}% of max)")
    else:
        checks.append({
            "name": "pour_point_accumulation",
            "passed": False,
            "details": {"reason": "flow accumulation file not provided or not found"},
        })
        all_pass = False
        print("  SKIP: No flow accumulation file")

    # ── Write report ──────────────────────────────────────────────
    report = {
        "step": "validate_watershed",
        "all_passed": all_pass,
        "checks_total": len(checks),
        "checks_passed": sum(1 for c in checks if c["passed"]),
        "checks_failed": sum(1 for c in checks if not c["passed"]),
        "checks": checks,
        "validated_at": datetime.now(UTC).isoformat(),
    }

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nValidation report: {out_path}")
    print(f"Result: {'ALL PASSED' if all_pass else 'SOME CHECKS FAILED'} ({report['checks_passed']}/{report['checks_total']})")

    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
