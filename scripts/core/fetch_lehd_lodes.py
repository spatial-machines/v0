#!/usr/bin/env python3
"""Fetch LEHD/LODES employment data (workplace, residence, origin-destination).

Downloads Census LEHD LODES CSV files by state.

Usage:
    python scripts/core/fetch_lehd_lodes.py ne --type wac \
        -o data/raw/ne_workplace.csv

    python scripts/core/fetch_lehd_lodes.py ks --type rac --year 2021 \
        -o data/raw/ks_residence.csv

    python scripts/core/fetch_lehd_lodes.py ne --type od \
        -o data/raw/ne_commute_od.csv
"""
from __future__ import annotations

import csv
import gzip
import io
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE_URL = "https://lehd.ces.census.gov/data/lodes/LODES8"

URL_PATTERNS = {
    "wac": "{base}/{state}/wac/{state}_wac_S000_JT00_{year}.csv.gz",
    "rac": "{base}/{state}/rac/{state}_rac_S000_JT00_{year}.csv.gz",
    "od": "{base}/{state}/od/{state}_od_main_JT00_{year}.csv.gz",
}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch LEHD/LODES employment data.")
    parser.add_argument("state", help="State abbreviation (lowercase, e.g. ne, ks)")
    parser.add_argument("--type", default="wac", choices=["wac", "rac", "od"],
                        help="Data type: wac (workplace), rac (residence), od (origin-destination)")
    parser.add_argument("--year", default="2021", help="Year (default: 2021)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    state = args.state.lower()
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    url = URL_PATTERNS[args.type].format(base=BASE_URL, state=state, year=args.year)
    type_names = {"wac": "Workplace Area", "rac": "Residence Area", "od": "Origin-Destination"}
    print(f"Fetching LEHD LODES {type_names[args.type]} for {state.upper()} ({args.year})")
    print(f"  from: {url}")

    try:
        with urlopen(url, timeout=120) as response:
            compressed = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            print(f"ERROR: Data not available for {state.upper()} {args.year}")
            print("  Try a different year (LODES data typically lags 2-3 years)")
            return 1
        print(f"Error: {exc}")
        return 1
    except URLError as exc:
        print(f"Network error: {exc}")
        return 1

    print(f"  downloaded {len(compressed):,} bytes (compressed)")
    raw = gzip.decompress(compressed).decode("utf-8")
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    header = rows[0]
    data_rows = rows[1:]

    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_rows)

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "direct-download",
        "source_name": f"Census LEHD LODES8 {args.type.upper()} {args.year}",
        "source_type": "census-download",
        "source_url": url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"state={state}", f"type={args.type}", f"rows={len(data_rows)}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  decompressed {len(data_rows):,} rows")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
