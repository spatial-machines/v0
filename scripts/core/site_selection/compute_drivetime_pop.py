#!/usr/bin/env python3
"""Population within drive-time rings.

For each location, computes ring-differenced demographics at 5/10/15 minute
drive-time rings: population, households, median income, daytime population,
and business count.

Usage:
    python scripts/core/site_selection/compute_drivetime_pop.py \
        --locations data/raw/locations.gpkg \
        --isochrones data/processed/trade_areas.gpkg \
        --state CO \
        --output outputs/spatial_stats/drivetime_demographics.gpkg

    python scripts/core/site_selection/compute_drivetime_pop.py \
        --locations data/raw/locations.gpkg \
        --isochrones data/processed/trade_areas.gpkg \
        --state CO \
        --travel-times 5 10 15 \
        --output outputs/spatial_stats/drivetime_demographics.gpkg
"""
from __future__ import annotations

import json
import time
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[3]

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

# ACS variables for drive-time enrichment
DRIVETIME_VARS = {
    "B01003_001E": "total_population",
    "B11001_001E": "total_households",
    "B19013_001E": "median_household_income",
    "B23025_002E": "in_labor_force",
    "B23025_005E": "employed_civilian",
}

DAYTIME_MULTIPLIER = 1.3  # Estimate: commercial tracts have ~1.3x residential pop during daytime


def _load_api_key() -> str | None:
    """Read CENSUS_API_KEY from the project .env file."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("CENSUS_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def _get_utm_crs(gdf):
    """Determine the best UTM CRS for a GeoDataFrame based on centroid."""
    centroid = gdf.geometry.unary_union.centroid
    lon = centroid.x
    lat = centroid.y
    zone = int((lon + 180) / 6) + 1
    hemisphere = "north" if lat >= 0 else "south"
    epsg = 32600 + zone if hemisphere == "north" else 32700 + zone
    return f"EPSG:{epsg}"


def _fetch_tracts_with_demographics(state_fips: str, api_key: str | None):
    """Fetch Census tracts with demographics and geometry for a state.

    Returns a GeoDataFrame with tract geometries and demographic columns.
    """
    import geopandas as gpd
    import pandas as pd
    import numpy as np

    # Fetch ACS data
    var_list = ",".join(DRIVETIME_VARS.keys())
    url = (
        f"https://api.census.gov/data/2022/acs/acs5"
        f"?get=NAME,{var_list}"
        f"&for=tract:*&in=state:{state_fips}"
    )
    if api_key:
        url += f"&key={api_key}"

    print(f"  Fetching ACS demographics for state {state_fips}...")
    for attempt in range(3):
        try:
            resp = urlopen(url, timeout=30)
            data = json.loads(resp.read().decode())
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt < 2:
                print(f"    Retry {attempt + 1}/3: {exc}")
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  ERROR: Census API failed after 3 attempts: {exc}")
                return None

    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)

    # Build GEOID
    df["GEOID"] = df["state"] + df["county"] + df["tract"]

    # Convert numeric columns
    for acs_var in DRIVETIME_VARS:
        if acs_var in df.columns:
            df[acs_var] = pd.to_numeric(df[acs_var], errors="coerce")
            # Strip Census sentinel
            df.loc[df[acs_var] == -666666666, acs_var] = np.nan

    # Rename to friendly names
    rename = {k: v for k, v in DRIVETIME_VARS.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Fetch tract geometries
    print(f"  Fetching tract geometries...")
    tiger_url = (
        f"https://www2.census.gov/geo/tiger/TIGER2022/TRACT/"
        f"tl_2022_{state_fips}_tract.zip"
    )
    try:
        tracts = gpd.read_file(tiger_url)
    except Exception:
        # Try cartographic boundary
        cb_url = (
            f"https://www2.census.gov/geo/tiger/GENZ2022/shp/"
            f"cb_2022_{state_fips}_tract_500k.zip"
        )
        try:
            tracts = gpd.read_file(cb_url)
        except Exception as exc:
            print(f"  ERROR: could not fetch tract geometries: {exc}")
            return None

    tracts = tracts.to_crs("EPSG:4326")
    tracts["GEOID"] = tracts["GEOID"].astype(str)
    df["GEOID"] = df["GEOID"].astype(str)

    merged = tracts.merge(df[["GEOID"] + list(DRIVETIME_VARS.values())],
                          on="GEOID", how="left")
    return merged


def compute_ring_demographics(location_gdf, isochrone_layers, tract_gdf):
    """Compute ring-differenced demographics for each location at each ring.

    Parameters
    ----------
    location_gdf : GeoDataFrame
        Point locations to analyze.
    isochrone_layers : dict
        {ring_name: GeoDataFrame} — e.g., {"5min": gdf, "10min": gdf, "15min": gdf}.
        Each must have the same number of rows as location_gdf (one polygon per location).
    tract_gdf : GeoDataFrame
        Census tracts with demographic columns.

    Returns
    -------
    list[dict] — one dict per location with nested ring stats.
    """
    import geopandas as gpd
    import numpy as np

    target_crs = "EPSG:4326"
    utm_crs = _get_utm_crs(tract_gdf)

    tract_gdf = tract_gdf.to_crs(target_crs)
    tract_utm = tract_gdf.to_crs(utm_crs)
    tract_utm["_tract_area"] = tract_utm.geometry.area

    # Sort rings by time
    sorted_rings = sorted(isochrone_layers.keys(),
                           key=lambda k: int("".join(c for c in k if c.isdigit()) or "0"))

    results = []

    for loc_idx, loc_row in location_gdf.iterrows():
        loc_name = loc_row.get("name", loc_row.get("brand", f"Location {loc_idx}"))
        loc_result = {
            "location_id": loc_idx,
            "name": str(loc_name),
            "lat": float(loc_row.geometry.y),
            "lon": float(loc_row.geometry.x),
            "rings": {},
        }

        prev_geom = None

        for ring_name in sorted_rings:
            ring_gdf = isochrone_layers[ring_name]
            if loc_idx >= len(ring_gdf):
                continue

            ring_geom = ring_gdf.iloc[loc_idx].geometry

            # Ring-differenced: subtract previous ring
            if prev_geom is not None:
                from shapely.validation import make_valid
                ring_area = make_valid(ring_geom).difference(make_valid(prev_geom))
            else:
                ring_area = ring_geom

            # Area-weighted intersection with tracts
            pop = 0.0
            hh = 0.0
            inc_weighted = 0.0
            pop_for_inc = 0.0
            labor = 0.0
            employed = 0.0

            for t_idx, tract_row in tract_gdf.iterrows():
                if not ring_area.intersects(tract_row.geometry):
                    continue
                intersection = ring_area.intersection(tract_row.geometry)
                if intersection.is_empty:
                    continue

                int_utm = gpd.GeoSeries([intersection], crs=target_crs).to_crs(utm_crs)
                t_area = tract_utm.loc[t_idx, "_tract_area"] if t_idx in tract_utm.index else 0
                if t_area <= 0:
                    continue
                frac = min(int_utm.area.iloc[0] / t_area, 1.0)

                t_pop = tract_row.get("total_population", 0)
                t_hh = tract_row.get("total_households", 0)
                t_inc = tract_row.get("median_household_income", 0)
                t_labor = tract_row.get("in_labor_force", 0)
                t_emp = tract_row.get("employed_civilian", 0)

                for v in [t_pop, t_hh, t_inc, t_labor, t_emp]:
                    pass  # type check below
                t_pop = 0 if (t_pop is None or (isinstance(t_pop, float) and np.isnan(t_pop))) else t_pop
                t_hh = 0 if (t_hh is None or (isinstance(t_hh, float) and np.isnan(t_hh))) else t_hh
                t_inc = 0 if (t_inc is None or (isinstance(t_inc, float) and np.isnan(t_inc)) or t_inc < 0) else t_inc
                t_labor = 0 if (t_labor is None or (isinstance(t_labor, float) and np.isnan(t_labor))) else t_labor
                t_emp = 0 if (t_emp is None or (isinstance(t_emp, float) and np.isnan(t_emp))) else t_emp

                pop += t_pop * frac
                hh += t_hh * frac
                if t_inc > 0:
                    inc_weighted += t_inc * (t_pop * frac)
                    pop_for_inc += t_pop * frac
                labor += t_labor * frac
                employed += t_emp * frac

            median_inc = int(inc_weighted / pop_for_inc) if pop_for_inc > 0 else 0
            daytime_pop = int(pop * DAYTIME_MULTIPLIER) if employed > pop * 0.4 else int(pop)

            loc_result["rings"][ring_name] = {
                "population": int(round(pop)),
                "households": int(round(hh)),
                "median_household_income": median_inc,
                "daytime_population": daytime_pop,
                "employed_civilian": int(round(employed)),
                "in_labor_force": int(round(labor)),
            }

            prev_geom = ring_geom

        results.append(loc_result)

    return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Population within drive-time rings for site locations."
    )
    parser.add_argument("--locations", required=True,
                        help="Point locations GeoPackage")
    parser.add_argument("--isochrones", required=True,
                        help="Trade areas GeoPackage (with layers per travel time)")
    parser.add_argument("--state", required=True,
                        help="State abbreviation (for Census data)")
    parser.add_argument("--travel-times", nargs="+", type=int, default=[5, 10, 15],
                        help="Travel times in minutes (default: 5 10 15)")
    parser.add_argument("--output", "-o", required=True,
                        help="Output GeoPackage")
    parser.add_argument("--output-json", default=None,
                        help="Output JSON (default: same path with .json)")
    args = parser.parse_args()

    try:
        import geopandas as gpd
    except ImportError:
        print("ERROR: geopandas not installed. Run: pip install geopandas")
        return 1

    loc_path = Path(args.locations).expanduser().resolve()
    iso_path = Path(args.isochrones).expanduser().resolve()

    if not loc_path.exists():
        print(f"ERROR: locations not found: {loc_path}")
        return 1
    if not iso_path.exists():
        print(f"ERROR: isochrones not found: {iso_path}")
        return 1

    state = args.state.upper()
    if state not in STATE_ABBREV_TO_FIPS:
        print(f"ERROR: unknown state: {state}")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = (
        Path(args.output_json).expanduser().resolve()
        if args.output_json
        else out_path.with_suffix(".json")
    )

    print("Drive-time population analysis")
    print(f"  Locations: {loc_path}")
    print(f"  Isochrones: {iso_path}")
    print(f"  State: {state}")
    print(f"  Travel times: {args.travel_times}")

    locations = gpd.read_file(loc_path)
    print(f"  Loaded {len(locations)} locations")

    # Load isochrone layers
    import fiona
    available_layers = fiona.listlayers(iso_path)
    print(f"  Available isochrone layers: {available_layers}")

    iso_layers = {}
    for tt in args.travel_times:
        # Try common naming patterns
        candidates = [
            f"trade_area_{tt}min",
            f"trade_area_{tt}mi",
            f"isochrone_{tt}min",
        ]
        found = False
        for cand in candidates:
            if cand in available_layers:
                iso_layers[f"{tt}min"] = gpd.read_file(iso_path, layer=cand)
                print(f"  Loaded layer: {cand} ({len(iso_layers[f'{tt}min'])} features)")
                found = True
                break
        if not found:
            # Use first available buffer layer as fallback for this time
            for layer in available_layers:
                if str(tt) in layer:
                    iso_layers[f"{tt}min"] = gpd.read_file(iso_path, layer=layer)
                    print(f"  Loaded layer: {layer} (fallback for {tt}min)")
                    found = True
                    break
        if not found:
            print(f"  WARNING: no isochrone layer found for {tt} minutes")

    if not iso_layers:
        print("ERROR: no isochrone layers matched travel times")
        return 1

    # Fetch Census data
    api_key = _load_api_key()
    state_fips = STATE_ABBREV_TO_FIPS[state]
    tract_gdf = _fetch_tracts_with_demographics(state_fips, api_key)

    if tract_gdf is None or len(tract_gdf) == 0:
        print("ERROR: could not fetch Census tract data")
        return 1

    print(f"  Loaded {len(tract_gdf)} Census tracts")

    t0 = time.time()

    results = compute_ring_demographics(locations, iso_layers, tract_gdf)

    elapsed = round(time.time() - t0, 2)

    # Write JSON output
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(results, indent=2))
    print(f"  JSON output: {json_path}")

    # Build GeoPackage output — one row per location with summary stats
    import pandas as pd
    rows = []
    for r in results:
        row = {
            "location_id": r["location_id"],
            "name": r["name"],
            "lat": r["lat"],
            "lon": r["lon"],
        }
        cumulative_pop = 0
        for ring_name, stats in r["rings"].items():
            prefix = ring_name.replace("min", "min_")
            for k, v in stats.items():
                row[f"{prefix}{k}"] = v
            cumulative_pop += stats["population"]
        row["total_pop_all_rings"] = cumulative_pop
        rows.append(row)

    from shapely.geometry import Point
    if rows:
        summary_gdf = gpd.GeoDataFrame(
            rows,
            geometry=[Point(r["lon"], r["lat"]) for r in rows],
            crs="EPSG:4326",
        )
        summary_gdf.to_file(out_path, driver="GPKG")
        print(f"  GeoPackage output: {out_path} ({len(summary_gdf)} locations)")
    else:
        print("  WARNING: no results — writing empty output")

    print(f"  Elapsed: {elapsed}s")

    # JSON log
    log = {
        "step": "compute_drivetime_pop",
        "input_locations": str(loc_path),
        "input_isochrones": str(iso_path),
        "state": state,
        "travel_times": args.travel_times,
        "n_locations": len(locations),
        "n_rings": len(iso_layers),
        "n_tracts": len(tract_gdf),
        "output": str(out_path),
        "output_json": str(json_path),
        "elapsed_s": elapsed,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".drivetime_pop.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
