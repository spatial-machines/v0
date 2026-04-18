#!/usr/bin/env python3
"""White space / gap analysis — find underserved areas.

Dissolves existing trade areas into a "covered" surface, subtracts from
the study area boundary to find uncovered zones, then ranks them by a
demand proxy (population density x median income index).

Usage:
    python scripts/core/site_selection/compute_whitespace.py \
        --trade-areas data/processed/trade_areas.gpkg \
        --study-area data/raw/study_area.gpkg \
        --demographics data/processed/enriched.gpkg \
        --output outputs/spatial_stats/whitespace_zones.gpkg

    python scripts/core/site_selection/compute_whitespace.py \
        --trade-areas data/processed/trade_areas.gpkg \
        --study-area data/raw/study_area.gpkg \
        --min-population 3000 \
        --output outputs/spatial_stats/whitespace_zones.gpkg
"""
from __future__ import annotations

import json
import time
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

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


def compute_whitespace(
    trade_areas_gdf,
    study_area_gdf,
    tract_gdf=None,
    min_population: int = 5000,
    buffer_radius_mi: float = 1.0,
):
    """Compute uncovered (white space) zones within a study area.

    Parameters
    ----------
    trade_areas_gdf : GeoDataFrame
        Existing trade area polygons (coverage surface).
    study_area_gdf : GeoDataFrame
        Study area boundary polygon(s).
    tract_gdf : GeoDataFrame or None
        Census tracts with population/income columns for demand scoring.
    min_population : int
        Minimum population within buffer_radius_mi to keep a zone.
    buffer_radius_mi : float
        Radius for population threshold check (miles).

    Returns
    -------
    whitespace_gdf : GeoDataFrame
        Uncovered zones with demand scores.
    coverage_gdf : GeoDataFrame
        Coverage surface (covered + uncovered) for visualization.
    """
    import geopandas as gpd
    import numpy as np
    from shapely.ops import unary_union
    from shapely.validation import make_valid

    # Ensure consistent CRS
    target_crs = "EPSG:4326"
    trade_areas_gdf = trade_areas_gdf.to_crs(target_crs)
    study_area_gdf = study_area_gdf.to_crs(target_crs)

    utm_crs = _get_utm_crs(study_area_gdf)

    # Dissolve study area into single boundary
    study_union = unary_union(study_area_gdf.geometry)
    study_union = make_valid(study_union)

    # Dissolve all trade areas into covered surface
    print("  Dissolving trade areas into coverage surface...")
    covered_union = unary_union(trade_areas_gdf.geometry)
    covered_union = make_valid(covered_union)

    # Subtract covered from study area → uncovered
    print("  Computing uncovered zones...")
    uncovered = study_union.difference(covered_union)
    uncovered = make_valid(uncovered)

    if uncovered.is_empty:
        print("  WARNING: entire study area is covered — no white space found")
        empty = gpd.GeoDataFrame(
            columns=["geometry", "area_km2", "pop_estimate", "income_index",
                      "demand_score", "rank"],
            geometry="geometry", crs=target_crs,
        )
        coverage = gpd.GeoDataFrame(
            [{"geometry": covered_union, "status": "covered"}],
            geometry="geometry", crs=target_crs,
        )
        return empty, coverage

    # Explode multipolygon into individual zones
    from shapely.geometry import MultiPolygon
    if uncovered.geom_type == "MultiPolygon":
        parts = list(uncovered.geoms)
    elif uncovered.geom_type == "GeometryCollection":
        parts = [g for g in uncovered.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        expanded = []
        for p in parts:
            if p.geom_type == "MultiPolygon":
                expanded.extend(p.geoms)
            else:
                expanded.append(p)
        parts = expanded
    else:
        parts = [uncovered]

    # Filter tiny slivers (< 0.01 km2)
    zones_gdf = gpd.GeoDataFrame(
        [{"zone_id": i + 1, "geometry": p} for i, p in enumerate(parts)],
        geometry="geometry", crs=target_crs,
    )
    zones_utm = zones_gdf.to_crs(utm_crs)
    zones_gdf["area_km2"] = zones_utm.geometry.area / 1e6
    zones_gdf = zones_gdf[zones_gdf["area_km2"] >= 0.01].copy()
    zones_gdf["zone_id"] = range(1, len(zones_gdf) + 1)

    print(f"  Found {len(zones_gdf)} uncovered zones (after sliver removal)")

    # Score zones by demand proxy
    if tract_gdf is not None and len(tract_gdf) > 0:
        print("  Scoring zones by demographic demand proxy...")
        tract_gdf = tract_gdf.to_crs(target_crs)

        # Get population and income columns (flexible naming)
        pop_col = None
        inc_col = None
        for c in tract_gdf.columns:
            cl = c.lower()
            if "total_population" in cl or c == "B01003_001E" or cl == "population":
                pop_col = c
            if "median_income" in cl or c == "B19013_001E":
                inc_col = c

        if pop_col and inc_col:
            # Area-weighted intersection to estimate pop/income per zone
            pop_estimates = []
            income_indices = []

            tract_utm = tract_gdf.to_crs(utm_crs)
            tract_utm["_tract_area"] = tract_utm.geometry.area

            for _, zone_row in zones_gdf.iterrows():
                zone_geom = zone_row.geometry
                zone_pop = 0.0
                zone_inc_weighted = 0.0
                zone_pop_for_inc = 0.0

                for _, tract_row in tract_gdf.iterrows():
                    if not zone_geom.intersects(tract_row.geometry):
                        continue
                    intersection = zone_geom.intersection(tract_row.geometry)
                    if intersection.is_empty:
                        continue

                    # Compute area fraction in UTM
                    int_utm = gpd.GeoSeries([intersection], crs=target_crs).to_crs(utm_crs)
                    tract_idx = tract_utm.index[tract_utm.index == tract_row.name]
                    if len(tract_idx) == 0:
                        continue
                    tract_area = tract_utm.loc[tract_idx[0], "_tract_area"]
                    if tract_area <= 0:
                        continue
                    frac = int_utm.area.iloc[0] / tract_area
                    frac = min(frac, 1.0)

                    t_pop = tract_row.get(pop_col, 0)
                    t_inc = tract_row.get(inc_col, 0)
                    if t_pop is None or np.isnan(t_pop):
                        t_pop = 0
                    if t_inc is None or np.isnan(t_inc) or t_inc < 0:
                        t_inc = 0

                    zone_pop += t_pop * frac
                    if t_inc > 0:
                        zone_inc_weighted += t_inc * (t_pop * frac)
                        zone_pop_for_inc += t_pop * frac

                pop_estimates.append(zone_pop)
                if zone_pop_for_inc > 0:
                    income_indices.append(zone_inc_weighted / zone_pop_for_inc)
                else:
                    income_indices.append(0)

            zones_gdf["pop_estimate"] = pop_estimates
            zones_gdf["income_index"] = income_indices
        else:
            print(f"  WARNING: missing pop/income columns in tracts — using area-based estimate")
            zones_gdf["pop_estimate"] = zones_gdf["area_km2"] * 1000  # rough fallback
            zones_gdf["income_index"] = 1.0
    else:
        print("  No demographic data — using area-based demand estimate")
        zones_gdf["pop_estimate"] = zones_gdf["area_km2"] * 1000
        zones_gdf["income_index"] = 1.0

    # Filter by minimum population
    before = len(zones_gdf)
    zones_gdf = zones_gdf[zones_gdf["pop_estimate"] >= min_population].copy()
    print(f"  {before - len(zones_gdf)} zones filtered (pop < {min_population})")
    zones_gdf["zone_id"] = range(1, len(zones_gdf) + 1)

    # Compute demand score: pop_density * income_index (normalized)
    zones_gdf["pop_density"] = zones_gdf["pop_estimate"] / zones_gdf["area_km2"].clip(lower=0.01)
    pd_max = zones_gdf["pop_density"].max()
    inc_max = zones_gdf["income_index"].max()
    zones_gdf["demand_score"] = (
        (zones_gdf["pop_density"] / pd_max if pd_max > 0 else 0)
        * (zones_gdf["income_index"] / inc_max if inc_max > 0 else 0)
        * 100
    )
    zones_gdf["demand_score"] = zones_gdf["demand_score"].round(1)
    zones_gdf = zones_gdf.sort_values("demand_score", ascending=False).reset_index(drop=True)
    zones_gdf["rank"] = range(1, len(zones_gdf) + 1)

    # Drop helper column
    zones_gdf = zones_gdf.drop(columns=["pop_density"], errors="ignore")

    # Build coverage surface for visualization
    coverage_rows = [{"geometry": covered_union, "status": "covered"}]
    for _, row in zones_gdf.iterrows():
        coverage_rows.append({
            "geometry": row.geometry,
            "status": "uncovered",
            "zone_id": row["zone_id"],
            "demand_score": row["demand_score"],
        })
    coverage_gdf = gpd.GeoDataFrame(coverage_rows, geometry="geometry", crs=target_crs)

    return zones_gdf, coverage_gdf


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="White space analysis — find underserved areas within a study area."
    )
    parser.add_argument("--trade-areas", required=True,
                        help="Input trade areas GeoPackage")
    parser.add_argument("--trade-area-layer", default=None,
                        help="Layer name within trade areas GeoPackage")
    parser.add_argument("--study-area", required=True,
                        help="Study area boundary GeoPackage")
    parser.add_argument("--study-area-layer", default=None,
                        help="Layer name within study area GeoPackage")
    parser.add_argument("--demographics", default=None,
                        help="Census tracts GeoPackage with pop/income columns")
    parser.add_argument("--demographics-layer", default=None,
                        help="Layer name within demographics GeoPackage")
    parser.add_argument("--min-population", type=int, default=5000,
                        help="Minimum population to keep a zone (default: 5000)")
    parser.add_argument("--output", "-o", required=True,
                        help="Output whitespace zones GeoPackage")
    parser.add_argument("--output-coverage", default=None,
                        help="Output coverage map GeoPackage (default: <output>_coverage.gpkg)")
    args = parser.parse_args()

    try:
        import geopandas as gpd
    except ImportError:
        print("ERROR: geopandas not installed. Run: pip install geopandas")
        return 1

    ta_path = Path(args.trade_areas).expanduser().resolve()
    sa_path = Path(args.study_area).expanduser().resolve()

    if not ta_path.exists():
        print(f"ERROR: trade areas not found: {ta_path}")
        return 1
    if not sa_path.exists():
        print(f"ERROR: study area not found: {sa_path}")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    coverage_path = (
        Path(args.output_coverage).expanduser().resolve()
        if args.output_coverage
        else out_path.with_name(out_path.stem + "_coverage.gpkg")
    )

    print("White space analysis")
    print(f"  Trade areas: {ta_path}")
    print(f"  Study area: {sa_path}")

    # Load inputs
    ta_kwargs = {"layer": args.trade_area_layer} if args.trade_area_layer else {}
    sa_kwargs = {"layer": args.study_area_layer} if args.study_area_layer else {}
    trade_areas = gpd.read_file(ta_path, **ta_kwargs)
    study_area = gpd.read_file(sa_path, **sa_kwargs)

    print(f"  Loaded {len(trade_areas)} trade areas, {len(study_area)} study area polygons")

    # Load demographics if provided
    tract_gdf = None
    if args.demographics:
        demo_path = Path(args.demographics).expanduser().resolve()
        if demo_path.exists():
            dk = {"layer": args.demographics_layer} if args.demographics_layer else {}
            tract_gdf = gpd.read_file(demo_path, **dk)
            print(f"  Loaded {len(tract_gdf)} demographic tracts")
        else:
            print(f"  WARNING: demographics file not found: {demo_path}")

    t0 = time.time()

    whitespace, coverage = compute_whitespace(
        trade_areas, study_area, tract_gdf,
        min_population=args.min_population,
    )

    elapsed = round(time.time() - t0, 2)

    # Write outputs
    if len(whitespace) > 0:
        whitespace.to_file(out_path, driver="GPKG")
        print(f"  Output: {out_path} ({len(whitespace)} zones)")
    else:
        print("  WARNING: no white space zones found — writing empty output")
        whitespace.to_file(out_path, driver="GPKG")

    coverage.to_file(coverage_path, driver="GPKG")
    print(f"  Coverage: {coverage_path}")
    print(f"  Elapsed: {elapsed}s")

    # JSON log
    log = {
        "step": "compute_whitespace",
        "input_trade_areas": str(ta_path),
        "input_study_area": str(sa_path),
        "input_demographics": str(args.demographics) if args.demographics else None,
        "n_trade_areas": len(trade_areas),
        "n_whitespace_zones": len(whitespace),
        "min_population": args.min_population,
        "top_zone_demand": float(whitespace["demand_score"].max()) if len(whitespace) > 0 else 0,
        "total_uncovered_km2": round(float(whitespace["area_km2"].sum()), 2) if len(whitespace) > 0 else 0,
        "output": str(out_path),
        "output_coverage": str(coverage_path),
        "elapsed_s": elapsed,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".whitespace.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
