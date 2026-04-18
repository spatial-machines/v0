#!/usr/bin/env python3
"""Fetch FBI Crime Data Explorer statistics by state.

Requires a free API key from https://api.data.gov/signup/

Usage:
    python scripts/core/fetch_fbi_crime.py NE --offense violent-crime \
        --start-year 2018 --end-year 2022 -o data/raw/ne_violent_crime.csv

    python scripts/core/fetch_fbi_crime.py KS --offense property-crime \
        -o data/raw/ks_property_crime.csv

Offense types: violent-crime, property-crime, homicide, robbery, aggravated-assault,
    burglary, larceny, motor-vehicle-theft, arson, human-trafficking
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_URL = "https://api.usa.gov/crime/fbi/sapi/api"


def _load_api_key() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "FBI_API_KEY" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch FBI crime statistics by state.")
    parser.add_argument("state", help="State abbreviation (e.g. NE, KS)")
    parser.add_argument("--offense", default="violent-crime",
                        help="Offense type (default: violent-crime)")
    parser.add_argument("--start-year", default="2018", help="Start year")
    parser.add_argument("--end-year", default="2022", help="End year")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    api_key = _load_api_key()
    if not api_key:
        print("ERROR: FBI API key required. Set FBI_API_KEY in .env")
        print("  Get a free key at: https://api.data.gov/signup/")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    state = args.state.upper()
    url = (f"{BASE_URL}/summarized/state/{state}/{args.offense}"
           f"/{args.start_year}/{args.end_year}?API_KEY={api_key}")

    print(f"Fetching FBI {args.offense} for {state} ({args.start_year}-{args.end_year})")

    try:
        with urlopen(url, timeout=60) as response:
            data = json.load(response)
    except HTTPError as exc:
        if exc.code == 403:
            print("ERROR: Invalid API key")
            return 1
        print(f"Error: {exc}")
        return 1
    except URLError as exc:
        print(f"Network error: {exc}")
        return 1

    results = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results, list):
        results = [results] if results else []

    if not results:
        print("WARNING: No data returned")
        return 1

    fieldnames = ["year", "state_abbr", "offense", "actual", "cleared", "population"]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "year": r.get("data_year", r.get("year", "")),
                "state_abbr": state,
                "offense": args.offense,
                "actual": r.get("actual", r.get("value", "")),
                "cleared": r.get("cleared", ""),
                "population": r.get("population", ""),
            })

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "fbi-cde-api",
        "source_name": "FBI Crime Data Explorer",
        "source_type": "federal-api",
        "source_url": f"{BASE_URL}/summarized/state/{state}/{args.offense}",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"state={state}", f"offense={args.offense}", f"records={len(results)}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  retrieved {len(results)} records")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
