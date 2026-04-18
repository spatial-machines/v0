#!/usr/bin/env python3
"""Fetch data from the Census American Community Survey (ACS) API.

Supports detail tables (B-tables), subject tables (S-tables), and
data profiles (DP-tables) via the --dataset flag.

Usage:
    python scripts/fetch_acs_data.py 20 \
        --dataset acs/acs5 --variables B17001_001E,B17001_002E \
        --year 2022 -o data/raw/ks_poverty.csv

    python scripts/fetch_acs_data.py 20 \
        --dataset acs/acs5/subject --variables S2701_C04_001E,S2701_C05_001E \
        -o data/raw/ks_uninsured.csv
"""
from __future__ import annotations

import csv
import json
import time
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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


def build_url(
    state_fips: str,
    dataset: str,
    variables: list[str],
    year: str,
    api_key: str | None,
    for_clause: str | None,
    in_clause: str | None,
    label_field: bool,
) -> str:
    get_vars = list(variables)
    if label_field and "NAME" not in get_vars:
        get_vars.insert(0, "NAME")
    get_str = ",".join(get_vars)

    for_part = for_clause or f"tract:*"
    in_part = in_clause or f"state:{state_fips}&in=county:*"

    url = (
        f"https://api.census.gov/data/{year}/{dataset}"
        f"?get={get_str}&for={for_part}&in={in_part}"
    )
    if api_key:
        url += f"&key={api_key}"
    return url


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch ACS data from the Census API for any table type."
    )
    parser.add_argument("state_fips", help="State FIPS code (e.g. 20 for Kansas)")
    parser.add_argument(
        "--dataset", default="acs/acs5",
        help="ACS dataset endpoint: acs/acs5, acs/acs5/subject, acs/acs5/profile (default: acs/acs5)",
    )
    parser.add_argument(
        "--variables", required=True,
        help="Comma-separated Census variable codes (e.g. B17001_001E,B17001_002E)",
    )
    parser.add_argument(
        "--year", default="2022",
        help="ACS vintage year (default: 2022)",
    )
    parser.add_argument(
        "--api-key",
        help="Census API key (default: reads CENSUS_API_KEY from .env)",
    )
    parser.add_argument(
        "--label-field", action="store_true",
        help="Include the NAME field as a human-readable label",
    )
    parser.add_argument(
        "--for", dest="for_clause",
        help="Override the 'for' geography clause (default: tract:*)",
    )
    parser.add_argument(
        "--in", dest="in_clause",
        help="Override the 'in' geography clause (default: state:XX&in=county:*)",
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="Output CSV path",
    )
    args = parser.parse_args()

    state_fips = args.state_fips.zfill(2)
    variables = [v.strip() for v in args.variables.split(",") if v.strip()]
    api_key = args.api_key or _load_api_key()

    if not api_key:
        print("WARNING: no Census API key found; requests may be rate-limited")

    url = build_url(
        state_fips, args.dataset, variables, args.year,
        api_key, args.for_clause, args.in_clause, args.label_field,
    )

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching ACS {args.dataset} ({args.year}) for state FIPS {state_fips}")
    print(f"  variables: {', '.join(variables)}")
    print(f"  fetching: {url}")

    # Fetch with retry for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urlopen(url, timeout=60) as response:
                rows = json.load(response)
            break
        except HTTPError as exc:
            if exc.code == 429 and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  rate limited, retrying in {wait}s...")
                time.sleep(wait)
                continue
            if exc.code == 400:
                body = exc.read().decode("utf-8", errors="replace")
                print(f"API error (400): {body}")
                print("Check that variable codes are valid for the dataset and year.")
                return 1
            raise
        except URLError as exc:
            print(f"Network error: {exc.reason}")
            return 1

    header = rows[0]
    data_rows = rows[1:]

    col_index = {name: idx for idx, name in enumerate(header)}

    # Determine geography columns present in the response
    geo_cols = [c for c in ("state", "county", "tract", "block group", "place") if c in col_index]

    # Build output fieldnames
    fieldnames = ["GEOID"]
    if args.label_field and "NAME" in col_index:
        fieldnames.append("NAME")
    fieldnames.extend(variables)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(data_rows, key=lambda r: "".join(r[col_index[g]] for g in geo_cols)):
            geoid = "".join(row[col_index[g]] for g in geo_cols)
            record = {"GEOID": geoid}
            if args.label_field and "NAME" in col_index:
                record["NAME"] = row[col_index["NAME"]]
            for var in variables:
                record[var] = row[col_index[var]]
            writer.writerow(record)

    warnings = []

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "census-api",
        "source_name": f"US Census ACS {args.dataset} {args.year}",
        "source_type": "census-api",
        "source_url": url.split("&key=")[0],  # strip API key from log
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "geography_level": "tract",
        "vintage": args.year,
        "variables": variables,
        "notes": [f"state_fips: {state_fips}", f"rows: {len(data_rows)}"],
        "warnings": warnings,
    }

    manifest_path = out_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"  retrieved {len(data_rows)} rows")
    print(f"  wrote {out_path}")
    print(f"  manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
