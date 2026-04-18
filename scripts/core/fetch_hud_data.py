#!/usr/bin/env python3
"""Fetch HUD housing data (Fair Market Rents, Income Limits).

Supports Fair Market Rents (FMR) and Income Limits via the HUD User API.

Usage:
    python scripts/core/fetch_hud_data.py --dataset fmr --state NE \
        -o data/raw/ne_fmr.csv

    python scripts/core/fetch_hud_data.py --dataset il --state KS --year 2024 \
        -o data/raw/ks_income_limits.csv
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENDPOINTS = {
    "fmr": "https://www.huduser.gov/hudapi/public/fmr/statedata/{state}",
    "il": "https://www.huduser.gov/hudapi/public/il/statedata/{state}",
}


def _load_api_key() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "HUD_API_KEY" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch HUD housing data.")
    parser.add_argument("--dataset", default="fmr", choices=["fmr", "il"],
                        help="Dataset: fmr (Fair Market Rents), il (Income Limits)")
    parser.add_argument("--state", required=True, help="State abbreviation (e.g. NE, KS)")
    parser.add_argument("--year", default="2024", help="Data year (default: 2024)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    api_key = _load_api_key()
    url = ENDPOINTS[args.dataset].format(state=args.state.upper())
    if args.year:
        url += f"?year={args.year}"

    print(f"Fetching HUD {args.dataset.upper()} for {args.state.upper()} ({args.year})")

    headers = {"User-Agent": "spatial-machines/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=60) as response:
            data = json.load(response)
    except HTTPError as exc:
        if exc.code == 401:
            print("ERROR: HUD API key required. Set HUD_API_KEY in .env")
            print("  Sign up at: https://www.huduser.gov/hudapi/public/register")
            return 1
        print(f"Error: {exc}")
        return 1
    except URLError as exc:
        print(f"Network error: {exc}")
        return 1

    # Extract the data section
    result_data = data.get("data", data)
    if isinstance(result_data, dict):
        # Single record — wrap in list
        if "basicdata" in result_data:
            records = result_data["basicdata"]
        elif "metroareas" in result_data:
            records = result_data["metroareas"]
        else:
            records = [result_data]
    elif isinstance(result_data, list):
        records = result_data
    else:
        print(f"WARNING: Unexpected response format")
        records = []

    if not records:
        print("WARNING: No records returned")
        out_path.write_text(json.dumps(data, indent=2))
        print(f"  wrote raw JSON to {out_path}")
        return 0

    # Write CSV
    fieldnames = list(records[0].keys()) if records else []
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "hud-api",
        "source_name": f"HUD {args.dataset.upper()} {args.year}",
        "source_type": "federal-api",
        "source_url": url.split("?")[0],
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"state={args.state}", f"records={len(records)}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  retrieved {len(records)} records")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
