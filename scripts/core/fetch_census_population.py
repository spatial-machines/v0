#!/usr/bin/env python3
"""Fetch total population for all census tracts in a state from the Census API.

Uses the 2020 Decennial Census (PL 94-171 Redistricting Data) endpoint.
No API key required for this public dataset.

Usage:
    python scripts/fetch_census_population.py 46 \
        -o analyses/sd-tracts-demo/data/reference/sd_tract_population.csv
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_url(state_fips: str, year: str = "2020") -> str:
    return (
        f"https://api.census.gov/data/{year}/dec/pl"
        f"?get=P1_001N,NAME&for=tract:*&in=state:{state_fips}&in=county:*"
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch full tract population coverage from Census PL 2020 API."
    )
    parser.add_argument("state_fips", help="State FIPS code (e.g. 46 for South Dakota)")
    parser.add_argument(
        "--year", default="2020",
        help="Census dataset year (default: 2020, PL redistricting data)",
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="Output CSV path",
    )
    args = parser.parse_args()

    state_fips = args.state_fips.zfill(2)
    url = build_url(state_fips, args.year)

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching 2020 Census total population for state FIPS {state_fips}")
    print(f"  fetching: {url}")

    with urlopen(url, timeout=60) as response:
        rows = json.load(response)

    header = rows[0]
    data_rows = rows[1:]

    # Census returns: P1_001N, NAME, state, county, tract
    col_index = {name: idx for idx, name in enumerate(header)}

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["geoid", "tract_name", "total_pop"])
        writer.writeheader()
        for row in sorted(data_rows, key=lambda r: r[col_index["state"]] + r[col_index["county"]] + r[col_index["tract"]]):
            geoid = row[col_index["state"]] + row[col_index["county"]] + row[col_index["tract"]]
            writer.writerow({
                "geoid": geoid,
                "tract_name": row[col_index["NAME"]],
                "total_pop": row[col_index["P1_001N"]],
            })

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "census-api",
        "source_name": "US Census PL 2020",
        "source_type": "census-api",
        "source_url": url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "geography_level": "tract",
        "vintage": args.year,
        "notes": [f"state_fips: {state_fips}", f"rows: {len(data_rows)}"],
        "warnings": [],
    }

    manifest_path = out_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"  retrieved {len(data_rows)} tracts")
    print(f"  wrote {out_path}")
    print(f"  manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
