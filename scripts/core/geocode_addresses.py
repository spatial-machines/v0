#!/usr/bin/env python3
"""Batch geocode addresses to point geometries.

Supports:
  - US Census Geocoder (free, US-only, no key required)
  - Nominatim/OpenStreetMap (free, global, rate-limited to 1 req/sec)

Outputs:
  - GeoPackage with lat/lon + match status
  - CSV with match rate summary
  - JSON handoff log

Usage:
    python geocode_addresses.py \\
        --input data/raw/facilities.csv \\
        --address-col address \\
        --city-col city \\
        --state-col state \\
        --zip-col zip \\
        --provider census \\
        [--output data/processed/facilities_geocoded.gpkg] \\
        [--benchmark Current_Traditional] \\
        [--fallback-nominatim]  # fall back to Nominatim for Census failures

    # Single-column full address:
    python geocode_addresses.py \\
        --input data/raw/facilities.csv \\
        --full-address-col full_address \\
        --provider nominatim
"""
import argparse
import json
import sys
import time
from io import StringIO
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).parent.parent

CENSUS_GEOCODE_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def build_full_address(row, addr_col=None, city_col=None, state_col=None, zip_col=None, full_col=None):
    if full_col and full_col in row.index and pd.notna(row[full_col]):
        return str(row[full_col])
    parts = []
    if addr_col and addr_col in row.index and pd.notna(row[addr_col]):
        parts.append(str(row[addr_col]))
    if city_col and city_col in row.index and pd.notna(row[city_col]):
        parts.append(str(row[city_col]))
    if state_col and state_col in row.index and pd.notna(row[state_col]):
        parts.append(str(row[state_col]))
    if zip_col and zip_col in row.index and pd.notna(row[zip_col]):
        parts.append(str(row[zip_col]))
    return ", ".join(parts) if parts else ""


def geocode_census_batch(df, addr_col, city_col, state_col, zip_col, full_col, benchmark="Current_Traditional"):
    """
    US Census Geocoder batch API — up to 10,000 addresses per request.
    Returns df with lat, lon, match_status, match_type columns.
    """
    print(f"Geocoding {len(df)} addresses via US Census Geocoder (batch)...")

    results = {i: {"lat": None, "lon": None, "match_status": "Unmatched",
                   "match_type": None, "matched_address": None}
               for i in df.index}

    # Census batch: max 10k rows per call
    chunk_size = 9999
    chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

    for chunk_num, chunk in enumerate(chunks):
        print(f"  Chunk {chunk_num+1}/{len(chunks)} ({len(chunk)} rows)...")

        # Build CSV for Census API
        csv_rows = []
        for idx, row in chunk.iterrows():
            address = ""
            city = ""
            state = ""
            zipcode = ""
            if full_col and full_col in row.index and pd.notna(row.get(full_col)):
                # Try to parse full address (best effort)
                address = str(row[full_col])
            else:
                if addr_col and addr_col in row.index:
                    address = str(row.get(addr_col, "") or "")
                if city_col and city_col in row.index:
                    city = str(row.get(city_col, "") or "")
                if state_col and state_col in row.index:
                    state = str(row.get(state_col, "") or "")
                if zip_col and zip_col in row.index:
                    zipcode = str(row.get(zip_col, "") or "")

            csv_rows.append(f'{idx},"{address}","{city}","{state}","{zipcode}"')

        csv_content = "\n".join(csv_rows)

        try:
            response = requests.post(
                CENSUS_GEOCODE_URL,
                data={
                    "benchmark": benchmark,
                    "vintage": "Current_CurrentYear",
                },
                files={"addressFile": ("addresses.csv", csv_content, "text/csv")},
                timeout=120,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Census API error: {e}")
            continue

        # Parse response CSV
        # Format: ID,Input Address,Match,Match Type,Matched Address,Coordinates,Tiger Line ID,Side
        lines = response.text.strip().splitlines()
        for line in lines:
            parts = line.split(",")
            if len(parts) < 4:
                continue
            try:
                idx = int(parts[0].strip('"'))
            except ValueError:
                continue

            match_status = parts[2].strip('"').strip() if len(parts) > 2 else "Unmatched"
            match_type = parts[3].strip('"').strip() if len(parts) > 3 else None
            matched_addr = parts[4].strip('"').strip() if len(parts) > 4 else None
            coords = parts[5].strip('"').strip() if len(parts) > 5 else None

            lat, lon = None, None
            if coords and "," in coords:
                try:
                    lon_str, lat_str = coords.split(",")
                    lon = float(lon_str.strip())
                    lat = float(lat_str.strip())
                except ValueError:
                    pass

            results[idx] = {
                "lat": lat,
                "lon": lon,
                "match_status": match_status,
                "match_type": match_type,
                "matched_address": matched_addr,
            }

    return results


def geocode_nominatim_single(address, country_codes=None, delay=1.1):
    """Geocode a single address via Nominatim. Returns (lat, lon) or (None, None)."""
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }
    if country_codes:
        params["countrycodes"] = country_codes

    headers = {"User-Agent": "GIS-ConsultingFirm/1.0 (research use)"}
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name")
    except Exception:
        pass
    return None, None, None


def geocode_nominatim_batch(df, addr_col, city_col, state_col, zip_col, full_col, country_codes=None):
    """Nominatim batch — rate-limited to 1 req/sec."""
    print(f"Geocoding {len(df)} addresses via Nominatim (1 req/sec — may be slow)...")
    results = {}
    for i, (idx, row) in enumerate(df.iterrows()):
        address = build_full_address(row, addr_col, city_col, state_col, zip_col, full_col)
        if not address.strip():
            results[idx] = {"lat": None, "lon": None, "match_status": "No address", "matched_address": None}
            continue

        lat, lon, matched = geocode_nominatim_single(address, country_codes)
        results[idx] = {
            "lat": lat,
            "lon": lon,
            "match_status": "Match" if lat is not None else "Unmatched",
            "match_type": "Nominatim",
            "matched_address": matched,
        }

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(df)} geocoded...")
        time.sleep(1.1)  # Nominatim ToS: max 1 req/sec

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input CSV or GeoPackage with addresses")
    parser.add_argument("--provider", default="census", choices=["census", "nominatim"],
                        help="Geocoding provider (default: census)")
    parser.add_argument("--address-col", help="Street address column")
    parser.add_argument("--city-col", help="City column")
    parser.add_argument("--state-col", help="State column")
    parser.add_argument("--zip-col", help="ZIP code column")
    parser.add_argument("--full-address-col", help="Single combined address column")
    parser.add_argument("--fallback-nominatim", action="store_true",
                        help="Fall back to Nominatim for Census mismatches")
    parser.add_argument("--country-codes", help="ISO country codes for Nominatim (e.g. 'us,ca')")
    parser.add_argument("--benchmark", default="Current_Traditional",
                        help="Census benchmark (default: Current_Traditional)")
    parser.add_argument("-o", "--output", help="Output GeoPackage path")
    parser.add_argument("--output-unmatched", help="Save unmatched rows to this CSV path")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    if src.suffix.lower() == ".csv":
        df = pd.read_csv(src, low_memory=False)
    else:
        df = gpd.read_file(src).drop(columns="geometry", errors="ignore")
        df = pd.DataFrame(df)

    print(f"Loaded {len(df)} rows")

    # Geocode
    if args.provider == "census":
        results = geocode_census_batch(
            df, args.address_col, args.city_col, args.state_col,
            args.zip_col, args.full_address_col, args.benchmark
        )

        # Nominatim fallback for unmatched
        if args.fallback_nominatim:
            unmatched_idx = [idx for idx, r in results.items() if r["lat"] is None]
            if unmatched_idx:
                print(f"\nFalling back to Nominatim for {len(unmatched_idx)} unmatched...")
                nom_results = geocode_nominatim_batch(
                    df.loc[unmatched_idx],
                    args.address_col, args.city_col, args.state_col,
                    args.zip_col, args.full_address_col, args.country_codes
                )
                for idx, r in nom_results.items():
                    if r["lat"] is not None:
                        results[idx] = r

    else:  # nominatim
        results = geocode_nominatim_batch(
            df, args.address_col, args.city_col, args.state_col,
            args.zip_col, args.full_address_col, args.country_codes
        )

    # Merge results back
    result_df = pd.DataFrame.from_dict(results, orient="index")
    result_df.index.name = df.index.name
    out_df = df.join(result_df)

    matched = int((out_df["lat"].notna() & out_df["lon"].notna()).sum())
    match_rate = matched / len(out_df) if len(out_df) > 0 else 0
    print(f"\nMatch rate: {matched}/{len(out_df)} ({match_rate:.1%})")

    # Build GeoDataFrame
    matched_df = out_df[out_df["lat"].notna() & out_df["lon"].notna()].copy()
    gdf = gpd.GeoDataFrame(
        matched_df,
        geometry=gpd.points_from_xy(matched_df["lon"], matched_df["lat"]),
        crs="EPSG:4326",
    )

    # Output
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "data" / "processed"
        out_path = out_dir / f"{src.stem}_geocoded.gpkg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    print(f"Saved {len(gdf)} geocoded features: {out_path}")

    # Save unmatched
    unmatched = out_df[out_df["lat"].isna()].copy()
    if len(unmatched) > 0:
        if args.output_unmatched:
            unmatched_path = Path(args.output_unmatched)
        else:
            unmatched_path = out_path.with_name(out_path.stem + "_unmatched.csv")
        unmatched.to_csv(unmatched_path, index=False)
        print(f"Saved {len(unmatched)} unmatched rows: {unmatched_path}")

    # Handoff log
    log = {
        "step": "geocode_addresses",
        "source": str(src),
        "provider": args.provider,
        "total": len(df),
        "matched": matched,
        "match_rate": round(match_rate, 4),
        "unmatched": int(len(unmatched)),
        "output": str(out_path),
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
