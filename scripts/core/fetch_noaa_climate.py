#!/usr/bin/env python3
"""Fetch NOAA Climate Data Online (CDO) observations.

Requires a free API token from https://www.ncdc.noaa.gov/cdo-web/token

Usage:
    python scripts/core/fetch_noaa_climate.py --location FIPS:20 \
        --start-date 2023-01-01 --end-date 2023-12-31 \
        --datatypes TMAX,TMIN,PRCP -o data/raw/ks_climate_2023.csv

    python scripts/core/fetch_noaa_climate.py --location CITY:US130077 \
        --dataset GHCND --start-date 2023-06-01 --end-date 2023-08-31 \
        -o data/raw/atlanta_summer_2023.csv
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request
from urllib.parse import urlencode

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_api_token() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "NOAA_API_TOKEN" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch NOAA Climate Data Online observations.")
    parser.add_argument("--dataset", default="GHCND", help="Dataset ID: GHCND, GSOM, GSOY (default: GHCND)")
    parser.add_argument("--location", required=True, help="Location ID (e.g. FIPS:20, CITY:US130077, ZIP:66044)")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--datatypes", default="TMAX,TMIN,PRCP", help="Comma-separated data types")
    parser.add_argument("--limit", type=int, default=1000, help="Records per page (default: 1000)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    token = _load_api_token()
    if not token:
        print("ERROR: NOAA API token required. Set NOAA_API_TOKEN in .env")
        print("  Get a free token at: https://www.ncdc.noaa.gov/cdo-web/token")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    datatypes = [d.strip() for d in args.datatypes.split(",")]
    print(f"Fetching NOAA {args.dataset} for {args.location}")
    print(f"  period: {args.start_date} to {args.end_date}")
    print(f"  types: {', '.join(datatypes)}")

    all_results = []
    offset = 1

    while True:
        params = urlencode({
            "datasetid": args.dataset,
            "locationid": args.location,
            "startdate": args.start_date,
            "enddate": args.end_date,
            "datatypeid": ",".join(datatypes),
            "limit": args.limit,
            "offset": offset,
            "units": "standard",
        })
        url = f"https://www.ncei.noaa.gov/cdo-web/api/v2/data?{params}"
        req = Request(url, headers={"token": token})

        try:
            with urlopen(req, timeout=60) as response:
                data = json.load(response)
        except HTTPError as exc:
            if exc.code == 429:
                print("  rate limited — try again in a few seconds")
                return 1
            print(f"Error: {exc}")
            return 1
        except URLError as exc:
            print(f"Network error: {exc}")
            return 1

        results = data.get("results", [])
        if not results:
            break

        all_results.extend(results)
        meta = data.get("metadata", {}).get("resultset", {})
        total = meta.get("count", 0)
        print(f"  page: {len(results)} records (total so far: {len(all_results)}/{total})")

        if len(all_results) >= total:
            break
        offset += args.limit

    if not all_results:
        print("WARNING: No data returned")
        return 1

    fieldnames = ["date", "station", "datatype", "value", "attributes"]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            writer.writerow({
                "date": r.get("date", "")[:10],
                "station": r.get("station", ""),
                "datatype": r.get("datatype", ""),
                "value": r.get("value", ""),
                "attributes": r.get("attributes", ""),
            })

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "noaa-cdo-api",
        "source_name": f"NOAA CDO {args.dataset}",
        "source_type": "federal-api",
        "source_url": "https://www.ncei.noaa.gov/cdo-web/api/v2/data",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"location={args.location}", f"records={len(all_results)}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  total: {len(all_results)} records")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
