#!/usr/bin/env python3
"""Enrich trade area polygons with Census ACS demographic data.

Performs spatial join between trade area polygons and census tract data
to compute area-weighted demographic averages for each trade area.

Usage:
    python scripts/core/enrich_points.py \
        --trade-areas data/processed/trade_areas.gpkg \
        --layer trade_area_3mi \
        --state MO \
        --output data/processed/enriched.gpkg
"""
from __future__ import annotations

import csv
import json
import time
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]

STATE_ABBREV_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11",
}

# Default ACS variables
DEFAULT_VARIABLES = {
    "B19013_001E": "median_income",
    "B01003_001E": "total_population",
    # Age groups for pct_under_35
    "B01001_003E": "male_under_5",
    "B01001_004E": "male_5_9",
    "B01001_005E": "male_10_14",
    "B01001_006E": "male_15_17",
    "B01001_007E": "male_18_19",
    "B01001_008E": "male_20",
    "B01001_009E": "male_21",
    "B01001_010E": "male_22_24",
    "B01001_011E": "male_25_29",
    "B01001_012E": "male_30_34",
    "B01001_027E": "female_under_5",
    "B01001_028E": "female_5_9",
    "B01001_029E": "female_10_14",
    "B01001_030E": "female_15_17",
    "B01001_031E": "female_18_19",
    "B01001_032E": "female_20",
    "B01001_033E": "female_21",
    "B01001_034E": "female_22_24",
    "B01001_035E": "female_25_29",
    "B01001_036E": "female_30_34",
}

AGE_UNDER_35_VARS = [
    "B01001_003E", "B01001_004E", "B01001_005E", "B01001_006E",
    "B01001_007E", "B01001_008E", "B01001_009E", "B01001_010E",
    "B01001_011E", "B01001_012E",
    "B01001_027E", "B01001_028E", "B01001_029E", "B01001_030E",
    "B01001_031E", "B01001_032E", "B01001_033E", "B01001_034E",
    "B01001_035E", "B01001_036E",
]


def _load_api_key() -> str | None:
    """Read CENSUS_API_KEY from the project .env file."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "CENSUS_API_KEY" and value.strip():
            return value.strip()
    return None


def _fetch_acs_tracts(state_fips: str, variables: list[str], year: str,
                       api_key: str | None) -> "pd.DataFrame":
    """Fetch ACS tract-level data from Census API. Returns DataFrame with GEOID + variables."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError("Missing pandas. Install: pip install pandas") from exc

    get_vars = ",".join(variables)
    url = (
        f"https://api.census.gov/data/{year}/acs/acs5"
        f"?get={get_vars}&for=tract:*&in=state:{state_fips}&in=county:*"
    )
    if api_key:
        url += f"&key={api_key}"

    print(f"  Fetching ACS {year} for state FIPS {state_fips}...")
    print(f"    Variables: {len(variables)}")

    max_retries = 3
    rows = None
    for attempt in range(max_retries):
        try:
            with urlopen(url, timeout=60) as response:
                rows = json.load(response)
            break
        except HTTPError as exc:
            if exc.code == 429 and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited, retrying in {wait}s...")
                import time as _time
                _time.sleep(wait)
                continue
            if exc.code == 400:
                body = exc.read().decode("utf-8", errors="replace")
                print(f"    API error (400): {body}")
                raise
            raise
        except URLError as exc:
            print(f"    Network error: {exc.reason}")
            raise

    if not rows or len(rows) < 2:
        print("    WARNING: no data returned from Census API")
        return pd.DataFrame()

    header = rows[0]
    data = rows[1:]

    df = pd.DataFrame(data, columns=header)

    # Build GEOID from state + county + tract
    df["GEOID"] = df["state"] + df["county"] + df["tract"]

    # Convert variable columns to numeric
    for var in variables:
        if var in df.columns:
            df[var] = pd.to_numeric(df[var], errors="coerce")

    print(f"    Retrieved {len(df)} tracts")
    return df


def _fetch_tract_geometries(state_fips: str, year: str) -> "gpd.GeoDataFrame":
    """Fetch census tract boundaries from Census TIGER API."""
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise ImportError("Missing geopandas. Install: pip install geopandas") from exc

    url = (
        f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS{year}"
        f"/MapServer/8/query"
        f"?where=STATE%3D%27{state_fips}%27"
        f"&outFields=GEOID,AREALAND"
        f"&outSR=4326&f=geojson&resultRecordCount=10000"
    )

    print(f"  Fetching tract boundaries from TIGER...")
    try:
        gdf = gpd.read_file(url)
        print(f"    Retrieved {len(gdf)} tract boundaries")
        return gdf
    except Exception as exc:
        print(f"    TIGER API failed: {exc}")
        # Fallback: try cartographic boundary files
        cb_url = (
            f"https://www2.census.gov/geo/tiger/GENZ{year}/shp/"
            f"cb_{year}_{state_fips}_tract_500k.zip"
        )
        print(f"    Trying cartographic boundaries...")
        try:
            gdf = gpd.read_file(cb_url)
            print(f"    Retrieved {len(gdf)} tract boundaries (cartographic)")
            return gdf
        except Exception as exc2:
            print(f"    Cartographic boundaries also failed: {exc2}")
            raise


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Enrich trade area polygons with Census ACS demographic data."
    )
    parser.add_argument("--trade-areas", required=True, help="Input trade areas GeoPackage")
    parser.add_argument("--layer", help="Layer name to enrich (default: largest radius layer)")
    parser.add_argument("--census-year", default="2022", help="ACS vintage year (default: 2022)")
    parser.add_argument("--state", required=True, help="State FIPS code or abbreviation")
    parser.add_argument("--variables", nargs="+",
                        default=["median_income", "population_density", "pct_under_35"],
                        help="Variables to compute (default: median_income population_density pct_under_35)")
    parser.add_argument("--competitors", default="",
                        help="Comma-separated competitor GeoPackage paths for density/gap computation")
    parser.add_argument("--output", "-o", required=True, help="Output enriched GeoPackage")
    args = parser.parse_args()

    try:
        import geopandas as gpd
        import pandas as pd
        import numpy as np
    except ImportError as exc:
        print(f"ERROR: missing dependency: {exc.name}. Install: pip install geopandas pandas numpy")
        return 1

    src = Path(args.trade_areas).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: input not found: {src}")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Resolve state FIPS
    state = args.state.upper()
    if len(state) == 2 and state.isalpha():
        state_fips = STATE_ABBREV_TO_FIPS.get(state)
        if not state_fips:
            print(f"ERROR: unknown state abbreviation: {state}")
            return 1
    else:
        state_fips = state.zfill(2)

    # Determine which layer to use
    import fiona
    available_layers = fiona.listlayers(str(src))
    print(f"  Available layers: {available_layers}")

    if args.layer:
        layer = args.layer
    else:
        # Pick the largest radius layer
        layer = available_layers[-1] if available_layers else None
        print(f"  Auto-selected layer: {layer}")

    if not layer or layer not in available_layers:
        print(f"ERROR: layer '{layer}' not found. Available: {available_layers}")
        return 1

    print(f"Enriching trade areas with ACS demographics")
    print(f"  Input: {src} (layer: {layer})")
    print(f"  State: {state} (FIPS {state_fips})")
    print(f"  Census year: {args.census_year}")

    t0 = time.time()

    # Load trade areas
    trade_areas = gpd.read_file(src, layer=layer)
    if trade_areas.crs is None:
        trade_areas = trade_areas.set_crs("EPSG:4326")
    trade_areas = trade_areas.to_crs("EPSG:4326")
    print(f"  Loaded {len(trade_areas)} trade areas")

    # Fetch ACS data
    api_key = _load_api_key()
    acs_vars = list(DEFAULT_VARIABLES.keys())
    acs_df = _fetch_acs_tracts(state_fips, acs_vars, args.census_year, api_key)

    if acs_df.empty:
        print("ERROR: no ACS data retrieved")
        return 1

    # Compute derived fields on tract data
    # pct_under_35
    for var in AGE_UNDER_35_VARS:
        if var not in acs_df.columns:
            acs_df[var] = 0
    acs_df["pop_under_35"] = sum(acs_df[v] for v in AGE_UNDER_35_VARS if v in acs_df.columns)
    acs_df["pct_under_35"] = np.where(
        acs_df["B01003_001E"] > 0,
        (acs_df["pop_under_35"] / acs_df["B01003_001E"]) * 100,
        np.nan,
    )

    # Rename core fields
    acs_df["median_income"] = acs_df.get("B19013_001E", np.nan)
    acs_df["total_population"] = acs_df.get("B01003_001E", np.nan)

    # Strip Census sentinel values (-666666666 means suppressed/missing data)
    CENSUS_SENTINEL = -666666666
    for col in ["median_income", "total_population", "B19013_001E", "B01003_001E"]:
        if col in acs_df.columns:
            acs_df[col] = acs_df[col].where(acs_df[col] != CENSUS_SENTINEL, np.nan)
            # Also catch any large negative values from weighted averaging artifacts
            if col in ("median_income", "B19013_001E"):
                acs_df[col] = acs_df[col].where(acs_df[col] >= 0, np.nan)

    # Fetch tract geometries for spatial join
    tracts_gdf = _fetch_tract_geometries(state_fips, args.census_year)
    if tracts_gdf.empty:
        print("ERROR: no tract geometries retrieved")
        return 1

    # Merge ACS data onto tract geometries
    tracts_gdf = tracts_gdf.to_crs("EPSG:4326")

    # Normalize GEOID column name
    geoid_col = None
    for c in tracts_gdf.columns:
        if c.upper() == "GEOID":
            geoid_col = c
            break
    if geoid_col and geoid_col != "GEOID":
        tracts_gdf = tracts_gdf.rename(columns={geoid_col: "GEOID"})

    # Merge
    keep_cols = ["GEOID", "median_income", "total_population", "pct_under_35"]
    acs_subset = acs_df[[c for c in keep_cols if c in acs_df.columns]].copy()
    tracts_gdf = tracts_gdf.merge(acs_subset, on="GEOID", how="left")

    # Compute tract area in sq km for density
    tracts_utm = tracts_gdf.to_crs(tracts_gdf.estimate_utm_crs())
    tracts_gdf["area_sqkm"] = tracts_utm.geometry.area / 1e6
    tracts_gdf["population_density"] = np.where(
        tracts_gdf["area_sqkm"] > 0,
        tracts_gdf["total_population"] / tracts_gdf["area_sqkm"],
        np.nan,
    )

    print(f"  Performing area-weighted spatial join...")

    # Area-weighted intersection: for each trade area, intersect with tracts,
    # weight by intersection area / tract area
    enriched_records = []
    trade_areas_utm = trade_areas.to_crs(tracts_utm.crs)
    tracts_utm_joined = tracts_gdf.to_crs(tracts_utm.crs)

    joined_count = 0
    for idx, ta_row in trade_areas_utm.iterrows():
        ta_geom = ta_row.geometry
        if ta_geom is None or ta_geom.is_empty:
            continue

        # Find intersecting tracts
        candidates = tracts_utm_joined[tracts_utm_joined.geometry.intersects(ta_geom)]

        if len(candidates) == 0:
            # No tracts intersect — keep POI attributes with NaN demographics
            rec = {c: ta_row[c] for c in trade_areas.columns if c != "geometry"}
            rec["median_income"] = np.nan
            rec["population_density"] = np.nan
            rec["pct_under_35"] = np.nan
            rec["n_tracts_intersected"] = 0
            enriched_records.append(rec)
            continue

        joined_count += 1

        # Compute intersection areas as weights
        intersections = candidates.geometry.intersection(ta_geom)
        intersection_areas = intersections.area
        tract_areas = candidates.geometry.area
        weights = intersection_areas / tract_areas.replace(0, np.nan)
        weights = weights.fillna(0)
        weight_sum = weights.sum()

        rec = {c: ta_row[c] for c in trade_areas.columns if c != "geometry"}

        # Area-weighted average for each demographic variable
        for demo_var in ["median_income", "population_density", "pct_under_35"]:
            if demo_var in candidates.columns:
                vals = pd.to_numeric(candidates[demo_var], errors="coerce")
                valid_mask = vals.notna() & (weights > 0)
                if valid_mask.any():
                    rec[demo_var] = float(
                        (vals[valid_mask] * weights[valid_mask]).sum() / weights[valid_mask].sum()
                    )
                else:
                    rec[demo_var] = np.nan
            else:
                rec[demo_var] = np.nan

        rec["n_tracts_intersected"] = len(candidates)
        enriched_records.append(rec)

    # Build enriched GeoDataFrame
    enriched = gpd.GeoDataFrame(
        enriched_records,
        geometry=trade_areas.geometry.values,
        crs="EPSG:4326",
    )

    # Compute competitor density and gap_to_nearest if competitor GeoPackages provided
    competitor_paths = [p.strip() for p in args.competitors.split(",") if p.strip()]
    if competitor_paths:
        print(f"  Computing competitor density from {len(competitor_paths)} file(s)...")
        comp_gdfs = []
        for cp in competitor_paths:
            cp_path = Path(cp).expanduser().resolve()
            if cp_path.exists():
                try:
                    cg = gpd.read_file(str(cp_path))
                    if cg.crs is None:
                        cg = cg.set_crs("EPSG:4326")
                    cg = cg.to_crs("EPSG:4326")
                    comp_gdfs.append(cg)
                    print(f"    Loaded {len(cg)} competitors from {cp_path.name}")
                except Exception as exc:
                    print(f"    WARNING: could not load {cp}: {exc}")
            else:
                print(f"    WARNING: competitor file not found: {cp}")

        if comp_gdfs:
            all_competitors = gpd.GeoDataFrame(
                pd.concat(comp_gdfs, ignore_index=True), crs="EPSG:4326"
            )
            # Reproject to UTM for area/distance calculations
            utm_crs = enriched.estimate_utm_crs()
            enriched_utm = enriched.to_crs(utm_crs)
            comp_utm = all_competitors.to_crs(utm_crs)

            competitor_density_vals = []
            gap_to_nearest_vals = []
            for idx, ta_row in enriched_utm.iterrows():
                ta_geom = ta_row.geometry
                if ta_geom is None or ta_geom.is_empty:
                    competitor_density_vals.append(np.nan)
                    gap_to_nearest_vals.append(np.nan)
                    continue
                # Count competitors inside trade area
                inside = comp_utm[comp_utm.geometry.within(ta_geom)]
                ta_area_sqkm = ta_geom.area / 1e6
                density = len(inside) / ta_area_sqkm if ta_area_sqkm > 0 else 0.0
                competitor_density_vals.append(round(density, 4))
                # Gap to nearest competitor (km)
                centroid = ta_geom.centroid
                distances = comp_utm.geometry.distance(centroid) / 1000.0  # metres → km
                gap = float(distances.min()) if len(distances) > 0 else np.nan
                gap_to_nearest_vals.append(round(gap, 3) if not np.isnan(gap) else np.nan)

            enriched["competitor_density"] = competitor_density_vals
            enriched["gap_to_nearest"] = gap_to_nearest_vals
            print(f"    Competitor density range: {min(v for v in competitor_density_vals if v is not None and not np.isnan(v)):.4f} – {max(v for v in competitor_density_vals if v is not None and not np.isnan(v)):.4f} per sq km")
        else:
            print("  WARNING: no valid competitor files loaded — skipping competitor columns")
    else:
        print("  No competitors specified — competitor_density and gap_to_nearest will be absent")

    coverage_pct = round(joined_count / max(len(trade_areas), 1) * 100, 1)

    enriched.to_file(out_path, driver="GPKG")
    elapsed = round(time.time() - t0, 2)

    print(f"  Enriched {len(enriched)} trade areas")
    print(f"  Join coverage: {coverage_pct}% ({joined_count}/{len(trade_areas)} matched tracts)")
    print(f"  Output: {out_path}")
    print(f"  Elapsed: {elapsed}s")

    # JSON log
    log = {
        "step": "enrich_points",
        "input": str(src),
        "layer": layer,
        "state_fips": state_fips,
        "census_year": args.census_year,
        "n_trade_areas": len(enriched),
        "variables_fetched": list(DEFAULT_VARIABLES.values()),
        "join_coverage_pct": coverage_pct,
        "output": str(out_path),
        "elapsed_s": elapsed,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".enrich.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
