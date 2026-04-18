#!/usr/bin/env python3
"""Fetch CDC PLACES health outcome estimates by tract or county.

Uses the Socrata-powered CDC data API. Supports measures like DIABETES,
OBESITY, BPHIGH, MHLTH, ACCESS2, CHECKUP, etc.

Usage:
    python scripts/core/fetch_cdc_places.py 20 --measure DIABETES \
        -o data/raw/ks_diabetes.csv

    python scripts/core/fetch_cdc_places.py 13 --measure OBESITY \
        --geo-level county -o data/raw/ga_obesity_county.csv
"""
from __future__ import annotations

import csv
import json
import io
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request
from urllib.parse import urlencode

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FIPS_TO_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}

# Socrata endpoints for CDC PLACES
ENDPOINTS = {
    "tract": "https://data.cdc.gov/resource/swc5-untb.json",
    "county": "https://data.cdc.gov/resource/swc5-untb.json",
    "place": "https://data.cdc.gov/resource/swc5-untb.json",
}


def _load_socrata_token() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "SOCRATA_APP_TOKEN" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch CDC PLACES health data by tract or county."
    )
    parser.add_argument("state_fips", help="State FIPS code (e.g. 20 for Kansas)")
    parser.add_argument("--measure", required=True, help="Health measure (e.g. DIABETES, OBESITY, BPHIGH)")
    parser.add_argument("--geo-level", default="tract", choices=["tract", "county", "place"],
                        help="Geography level (default: tract)")
    parser.add_argument("--year", default="2023", help="Data year (default: 2023)")
    parser.add_argument("--limit", type=int, default=50000, help="Max records (default: 50000)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    state_fips = args.state_fips.zfill(2)
    state_abbr = FIPS_TO_ABBR.get(state_fips)
    if not state_abbr:
        print(f"ERROR: Unknown state FIPS: {state_fips}")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    token = _load_socrata_token()
    endpoint = ENDPOINTS[args.geo_level]

    params = urlencode({
        "$where": f"stateabbr='{state_abbr}' AND measureid='{args.measure.upper()}' AND data_value_type_id='AgeAdjPrv'",
        "$select": "locationid,locationname,measureid,measure,data_value,low_confidence_limit,high_confidence_limit,totalpopulation,geolocation",
        "$limit": args.limit,
    })
    url = f"{endpoint}?{params}"

    print(f"Fetching CDC PLACES {args.measure} for {state_abbr} ({args.geo_level} level)")

    headers = {}
    if token:
        headers["X-App-Token"] = token

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=120) as response:
            data = json.load(response)
    except (HTTPError, URLError) as exc:
        print(f"Error: {exc}")
        return 1

    if not data:
        print(f"WARNING: No data returned for {args.measure} in {state_abbr}")
        return 1

    fieldnames = ["GEOID", "location_name", "measure_id", "measure", "data_value",
                  "low_ci", "high_ci", "total_population"]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({
                "GEOID": row.get("locationid", ""),
                "location_name": row.get("locationname", ""),
                "measure_id": row.get("measureid", ""),
                "measure": row.get("measure", ""),
                "data_value": row.get("data_value", ""),
                "low_ci": row.get("low_confidence_limit", ""),
                "high_ci": row.get("high_confidence_limit", ""),
                "total_population": row.get("totalpopulation", ""),
            })

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "socrata-api",
        "source_name": f"CDC PLACES {args.year}",
        "source_type": "federal-api",
        "source_url": endpoint,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "geography_level": args.geo_level,
        "notes": [f"state={state_abbr}", f"measure={args.measure}", f"rows={len(data)}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  retrieved {len(data)} rows")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
