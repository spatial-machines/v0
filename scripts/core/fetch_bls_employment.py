#!/usr/bin/env python3
"""Fetch Bureau of Labor Statistics employment/unemployment time series.

Optional API key increases rate limits. Register free at
https://data.bls.gov/registrationEngine/

Usage:
    python scripts/core/fetch_bls_employment.py \
        --series LAUST200000000000003,LAUST200000000000004 \
        --start-year 2019 --end-year 2023 -o data/raw/ks_employment.csv

Series ID examples:
    LAUST{fips}0000000000003 = unemployment rate for state
    LAUST{fips}0000000000004 = unemployment count for state
    LAUCN{fips}0000000003    = county unemployment rate
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_api_key() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "BLS_API_KEY" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch BLS employment time series data.")
    parser.add_argument("--series", required=True, help="Comma-separated BLS series IDs")
    parser.add_argument("--start-year", required=True, help="Start year (YYYY)")
    parser.add_argument("--end-year", required=True, help="End year (YYYY)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    series_ids = [s.strip() for s in args.series.split(",")]
    api_key = _load_api_key()

    print(f"Fetching BLS data for {len(series_ids)} series ({args.start_year}-{args.end_year})")

    payload = {
        "seriesid": series_ids,
        "startyear": args.start_year,
        "endyear": args.end_year,
    }
    if api_key:
        payload["registrationkey"] = api_key
    else:
        print("  WARNING: No BLS_API_KEY — limited to 25 requests/day")

    data_bytes = json.dumps(payload).encode("utf-8")
    req = Request(
        "https://api.bls.gov/publicAPI/v2/timeseries/data/",
        data=data_bytes,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(req, timeout=60) as response:
            data = json.load(response)
    except (HTTPError, URLError) as exc:
        print(f"Error: {exc}")
        return 1

    if data.get("status") != "REQUEST_SUCCEEDED":
        print(f"API error: {data.get('message', 'Unknown error')}")
        for msg in data.get("message", []):
            print(f"  {msg}")
        return 1

    all_rows = []
    for series in data.get("Results", {}).get("series", []):
        sid = series.get("seriesID", "")
        for record in series.get("data", []):
            all_rows.append({
                "series_id": sid,
                "year": record.get("year", ""),
                "period": record.get("period", ""),
                "period_name": record.get("periodName", ""),
                "value": record.get("value", ""),
                "footnotes": "; ".join(fn.get("text", "") for fn in record.get("footnotes", []) if fn.get("text")),
            })

    fieldnames = ["series_id", "year", "period", "period_name", "value", "footnotes"]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "bls-api",
        "source_name": "Bureau of Labor Statistics",
        "source_type": "federal-api",
        "source_url": "https://api.bls.gov/publicAPI/v2/timeseries/data/",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"series={len(series_ids)}", f"rows={len(all_rows)}"],
        "warnings": [] if api_key else ["No API key — rate limited"],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  retrieved {len(all_rows)} records across {len(series_ids)} series")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
