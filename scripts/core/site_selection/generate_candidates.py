#!/usr/bin/env python3
"""Generate candidate site locations within white space zones.

Places candidates at population-weighted centroids of each zone,
enforces minimum separation distance, and ranks by demand score.

Usage:
    python scripts/core/site_selection/generate_candidates.py \
        --whitespace outputs/spatial_stats/whitespace_zones.gpkg \
        --demographics data/processed/tracts.gpkg \
        --output outputs/spatial_stats/candidate_sites.gpkg

    python scripts/core/site_selection/generate_candidates.py \
        --whitespace outputs/spatial_stats/whitespace_zones.gpkg \
        --exclusions data/raw/existing_locations.gpkg \
        --min-separation 0.75 \
        --output outputs/spatial_stats/candidate_sites.gpkg
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


def _population_weighted_centroid(zone_geom, tract_gdf, pop_col, utm_crs):
    """Compute population-weighted centroid of a zone from intersecting tracts.

    Falls back to geometric centroid if no tracts intersect or no population data.
    """
    import geopandas as gpd
    import numpy as np

    target_crs = "EPSG:4326"
    weighted_x = 0.0
    weighted_y = 0.0
    total_weight = 0.0

    for _, tract in tract_gdf.iterrows():
        if not zone_geom.intersects(tract.geometry):
            continue
        intersection = zone_geom.intersection(tract.geometry)
        if intersection.is_empty:
            continue

        # Area fraction
        int_utm = gpd.GeoSeries([intersection], crs=target_crs).to_crs(utm_crs)
        tract_utm = gpd.GeoSeries([tract.geometry], crs=target_crs).to_crs(utm_crs)
        tract_area = tract_utm.area.iloc[0]
        if tract_area <= 0:
            continue
        frac = min(int_utm.area.iloc[0] / tract_area, 1.0)

        t_pop = tract.get(pop_col, 0)
        if t_pop is None or np.isnan(t_pop) or t_pop <= 0:
            continue

        weight = t_pop * frac
        centroid = intersection.centroid
        weighted_x += centroid.x * weight
        weighted_y += centroid.y * weight
        total_weight += weight

    if total_weight > 0:
        from shapely.geometry import Point
        return Point(weighted_x / total_weight, weighted_y / total_weight)

    # Fallback to geometric centroid
    return zone_geom.centroid


def generate_candidates(
    whitespace_gdf,
    tract_gdf=None,
    exclusion_gdf=None,
    competitor_gdf=None,
    min_separation_mi: float = 0.5,
):
    """Generate candidate sites at population-weighted centroids of white space zones.

    Parameters
    ----------
    whitespace_gdf : GeoDataFrame
        White space zones from compute_whitespace.
    tract_gdf : GeoDataFrame or None
        Census tracts with population/income for weighted centroids.
    exclusion_gdf : GeoDataFrame or None
        Existing locations to exclude candidates near.
    competitor_gdf : GeoDataFrame or None
        Competitor locations for competitor_count column.
    min_separation_mi : float
        Minimum distance between candidates (miles).

    Returns
    -------
    GeoDataFrame of candidate sites.
    """
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import Point

    target_crs = "EPSG:4326"
    utm_crs = _get_utm_crs(whitespace_gdf)
    min_sep_m = min_separation_mi * MILES_TO_METERS

    # Identify pop/income columns
    pop_col = None
    inc_col = None
    if tract_gdf is not None:
        for c in tract_gdf.columns:
            cl = c.lower()
            if "total_population" in cl or c == "B01003_001E" or cl == "population":
                pop_col = c
            if "median_income" in cl or c == "B19013_001E":
                inc_col = c

    candidates = []

    for _, zone in whitespace_gdf.iterrows():
        zone_id = zone.get("zone_id", 0)
        zone_geom = zone.geometry

        # Compute population-weighted centroid
        if tract_gdf is not None and pop_col:
            pt = _population_weighted_centroid(zone_geom, tract_gdf, pop_col, utm_crs)
        else:
            pt = zone_geom.centroid

        # Ensure point is inside zone (representative_point fallback)
        if not zone_geom.contains(pt):
            pt = zone_geom.representative_point()

        candidates.append({
            "zone_id": zone_id,
            "geometry": pt,
            "pop_estimate": zone.get("pop_estimate", 0),
            "income_index": zone.get("income_index", 0),
            "area_km2": zone.get("area_km2", 0),
            "demand_score": zone.get("demand_score", 0),
        })

    if not candidates:
        print("  WARNING: no candidates generated — no white space zones")
        return gpd.GeoDataFrame(
            columns=["zone_id", "geometry", "pop_within_1mi", "income_index",
                      "competitor_count", "demand_score", "rank"],
            geometry="geometry", crs=target_crs,
        )

    cand_gdf = gpd.GeoDataFrame(candidates, geometry="geometry", crs=target_crs)

    # Enforce minimum separation distance
    print(f"  Enforcing {min_separation_mi}-mile minimum separation...")
    cand_utm = cand_gdf.to_crs(utm_crs)
    keep = []
    kept_pts = []
    for idx, row in cand_utm.iterrows():
        pt = row.geometry
        too_close = False
        for kept_pt in kept_pts:
            if pt.distance(kept_pt) < min_sep_m:
                too_close = True
                break
        if not too_close:
            keep.append(idx)
            kept_pts.append(pt)

    removed = len(cand_gdf) - len(keep)
    cand_gdf = cand_gdf.loc[keep].copy()
    if removed > 0:
        print(f"  Removed {removed} candidates (too close together)")

    # Enforce exclusion zones
    if exclusion_gdf is not None and len(exclusion_gdf) > 0:
        print("  Applying exclusion zones...")
        excl_utm = exclusion_gdf.to_crs(utm_crs)
        cand_utm = cand_gdf.to_crs(utm_crs)
        keep = []
        for idx, row in cand_utm.iterrows():
            pt = row.geometry
            dists = excl_utm.geometry.distance(pt)
            if dists.min() >= min_sep_m:
                keep.append(idx)
        removed_excl = len(cand_gdf) - len(keep)
        cand_gdf = cand_gdf.loc[keep].copy()
        if removed_excl > 0:
            print(f"  Removed {removed_excl} candidates (too close to existing locations)")

    # Compute competitor count within 1 mile
    cand_gdf["competitor_count"] = 0
    if competitor_gdf is not None and len(competitor_gdf) > 0:
        print("  Computing competitor counts within 1 mile...")
        comp_utm = competitor_gdf.to_crs(utm_crs)
        cand_utm = cand_gdf.to_crs(utm_crs)
        one_mile_m = 1 * MILES_TO_METERS
        counts = []
        for _, row in cand_utm.iterrows():
            dists = comp_utm.geometry.distance(row.geometry)
            counts.append(int((dists <= one_mile_m).sum()))
        cand_gdf["competitor_count"] = counts

    # Compute pop within 1 mile from tracts
    cand_gdf["pop_within_1mi"] = cand_gdf["pop_estimate"]  # zone pop as proxy
    if tract_gdf is not None and pop_col:
        print("  Estimating population within 1 mile of each candidate...")
        one_mile_m = 1 * MILES_TO_METERS
        cand_utm = cand_gdf.to_crs(utm_crs)
        tract_utm = tract_gdf.to_crs(utm_crs)
        tract_utm["_tract_area"] = tract_utm.geometry.area

        pop_1mi = []
        for _, cand_row in cand_utm.iterrows():
            buf = cand_row.geometry.buffer(one_mile_m)
            pop_sum = 0.0
            for _, tract_row in tract_utm.iterrows():
                if not buf.intersects(tract_row.geometry):
                    continue
                intersection = buf.intersection(tract_row.geometry)
                if intersection.is_empty:
                    continue
                frac = min(intersection.area / tract_row["_tract_area"], 1.0) if tract_row["_tract_area"] > 0 else 0
                t_pop = tract_row.get(pop_col, 0)
                if t_pop is None or np.isnan(t_pop):
                    t_pop = 0
                pop_sum += t_pop * frac
            pop_1mi.append(round(pop_sum))
        cand_gdf["pop_within_1mi"] = pop_1mi

    # Rename and sort
    cand_gdf = cand_gdf.sort_values("demand_score", ascending=False).reset_index(drop=True)
    cand_gdf["rank"] = range(1, len(cand_gdf) + 1)

    # Keep final columns
    keep_cols = ["zone_id", "geometry", "pop_within_1mi", "income_index",
                 "competitor_count", "demand_score", "rank"]
    for c in keep_cols:
        if c not in cand_gdf.columns:
            cand_gdf[c] = 0
    cand_gdf = cand_gdf[keep_cols]

    return cand_gdf


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate candidate site locations within white space zones."
    )
    parser.add_argument("--whitespace", required=True,
                        help="Whitespace zones GeoPackage from compute_whitespace")
    parser.add_argument("--demographics", default=None,
                        help="Census tracts GeoPackage with pop/income columns")
    parser.add_argument("--demographics-layer", default=None,
                        help="Layer name within demographics GeoPackage")
    parser.add_argument("--exclusions", default=None,
                        help="Existing locations GeoPackage (exclusion zones)")
    parser.add_argument("--competitors", default=None,
                        help="Competitor locations GeoPackage")
    parser.add_argument("--min-separation", type=float, default=0.5,
                        help="Minimum separation between candidates in miles (default: 0.5)")
    parser.add_argument("--output", "-o", required=True,
                        help="Output candidate sites GeoPackage")
    args = parser.parse_args()

    try:
        import geopandas as gpd
    except ImportError:
        print("ERROR: geopandas not installed. Run: pip install geopandas")
        return 1

    ws_path = Path(args.whitespace).expanduser().resolve()
    if not ws_path.exists():
        print(f"ERROR: whitespace zones not found: {ws_path}")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Candidate site generation")
    print(f"  Whitespace zones: {ws_path}")

    whitespace = gpd.read_file(ws_path)
    print(f"  Loaded {len(whitespace)} white space zones")

    # Load optional inputs
    tract_gdf = None
    if args.demographics:
        dp = Path(args.demographics).expanduser().resolve()
        if dp.exists():
            dk = {"layer": args.demographics_layer} if args.demographics_layer else {}
            tract_gdf = gpd.read_file(dp, **dk)
            print(f"  Loaded {len(tract_gdf)} demographic tracts")

    exclusion_gdf = None
    if args.exclusions:
        ep = Path(args.exclusions).expanduser().resolve()
        if ep.exists():
            exclusion_gdf = gpd.read_file(ep)
            print(f"  Loaded {len(exclusion_gdf)} exclusion locations")

    competitor_gdf = None
    if args.competitors:
        cp = Path(args.competitors).expanduser().resolve()
        if cp.exists():
            competitor_gdf = gpd.read_file(cp)
            print(f"  Loaded {len(competitor_gdf)} competitor locations")

    t0 = time.time()

    candidates = generate_candidates(
        whitespace,
        tract_gdf=tract_gdf,
        exclusion_gdf=exclusion_gdf,
        competitor_gdf=competitor_gdf,
        min_separation_mi=args.min_separation,
    )

    elapsed = round(time.time() - t0, 2)

    # Write output
    candidates.to_file(out_path, driver="GPKG")
    print(f"  Output: {out_path} ({len(candidates)} candidates)")
    print(f"  Elapsed: {elapsed}s")

    # JSON log
    log = {
        "step": "generate_candidates",
        "input_whitespace": str(ws_path),
        "input_demographics": str(args.demographics) if args.demographics else None,
        "input_exclusions": str(args.exclusions) if args.exclusions else None,
        "input_competitors": str(args.competitors) if args.competitors else None,
        "n_whitespace_zones": len(whitespace),
        "n_candidates": len(candidates),
        "min_separation_mi": args.min_separation,
        "top_demand_score": float(candidates["demand_score"].max()) if len(candidates) > 0 else 0,
        "output": str(out_path),
        "elapsed_s": elapsed,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".candidates.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
