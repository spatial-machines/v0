#!/usr/bin/env python3
"""Fetch data from any Socrata-powered open data portal.

Works with thousands of city/county/state data portals (Chicago, NYC, LA, etc.).

Usage:
    python scripts/core/fetch_socrata.py --domain data.cityofchicago.org \
        --dataset ijzp-q8t2 --limit 10000 -o data/raw/chicago_crimes.csv

    python scripts/core/fetch_socrata.py --domain data.cdc.gov \
        --dataset swc5-untb --where "stateabbr='KS'" \
        --select "locationid,measureid,data_value" \
        -o data/raw/cdc_ks.csv
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


def _load_app_token() -> str | None:
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
        description="Fetch data from any Socrata open data portal."
    )
    parser.add_argument("--domain", required=True, help="Socrata domain (e.g. data.cityofchicago.org)")
    parser.add_argument("--dataset", required=True, help="Dataset identifier (4x4, e.g. ijzp-q8t2)")
    parser.add_argument("--where", help="SoQL $where filter (e.g. \"year=2023\")")
    parser.add_argument("--select", help="SoQL $select columns (e.g. \"date,type,latitude,longitude\")")
    parser.add_argument("--order", help="SoQL $order clause")
    parser.add_argument("--limit", type=int, default=50000, help="Max records (default: 50000)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    token = _load_app_token()
    all_rows = []
    offset = 0
    page_size = min(args.limit, 50000)

    print(f"Fetching from {args.domain} dataset {args.dataset}")
    if args.where:
        print(f"  filter: {args.where}")

    while offset < args.limit:
        params: dict = {"$limit": min(page_size, args.limit - offset), "$offset": offset}
        if args.where:
            params["$where"] = args.where
        if args.select:
            params["$select"] = args.select
        if args.order:
            params["$order"] = args.order

        url = f"https://{args.domain}/resource/{args.dataset}.json?{urlencode(params)}"
        headers = {}
        if token:
            headers["X-App-Token"] = token

        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=120) as response:
                data = json.load(response)
        except HTTPError as exc:
            if exc.code == 429:
                print("  rate limited — add SOCRATA_APP_TOKEN to .env for higher limits")
                break
            print(f"Error: {exc}")
            return 1
        except URLError as exc:
            print(f"Network error: {exc}")
            return 1

        if not data:
            break

        all_rows.extend(data)
        print(f"  page: {len(data)} records (total: {len(all_rows)})")

        if len(data) < page_size:
            break
        offset += len(data)

    if not all_rows:
        print("WARNING: No data returned")
        return 1

    fieldnames = list(all_rows[0].keys())
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "socrata-soda-api",
        "source_name": f"Socrata: {args.domain}/{args.dataset}",
        "source_type": "open-data-portal",
        "source_url": f"https://{args.domain}/resource/{args.dataset}",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"domain={args.domain}", f"rows={len(all_rows)}"],
        "warnings": [] if token else ["No app token — may be rate limited"],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  total: {len(all_rows)} records")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
