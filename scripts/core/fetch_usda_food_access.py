#!/usr/bin/env python3
"""Fetch USDA Food Access Research Atlas data (food desert indicators by tract).

Downloads the Food Access Research Atlas CSV from USDA ERS.

Usage:
    python scripts/core/fetch_usda_food_access.py -o data/raw/food_access.csv

    python scripts/core/fetch_usda_food_access.py --state-fips 20 \
        -o data/raw/ks_food_access.csv
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pandas as pd

FOOD_ACCESS_URL = "https://www.ers.usda.gov/media/5626/food-access-research-atlas-data-download-2019.xlsx"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch USDA Food Access Research Atlas data."
    )
    parser.add_argument("--state-fips", help="Filter to state FIPS code (e.g. 20)")
    parser.add_argument("--url", default=FOOD_ACCESS_URL, help="Override download URL")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading USDA Food Access Research Atlas")
    print(f"  from: {args.url}")

    try:
        with urlopen(args.url, timeout=180) as response:
            raw = response.read()
    except (HTTPError, URLError) as exc:
        print(f"Error: {exc}")
        return 1

    # Parse Excel (USDA ships xlsx since 2024)
    # File has 3 sheets: Read Me, Variable Lookup, Food Access Research Atlas
    import io
    df = pd.read_excel(
        io.BytesIO(raw),
        sheet_name="Food Access Research Atlas",
        dtype={"CensusTract": str},
    )
    print(f"  downloaded {len(df)} tract records")

    if args.state_fips:
        state_fips = args.state_fips.zfill(2)
        df = df[df["CensusTract"].str[:2] == state_fips].copy()
        print(f"  filtered to {len(df)} tracts for state FIPS {state_fips}")

    if df.empty:
        print("WARNING: No data after filtering")
        return 1

    df.to_csv(out_path, index=False)

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "direct-download",
        "source_name": "USDA Food Access Research Atlas 2019",
        "source_type": "federal-download",
        "source_url": args.url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv",
        "notes": [f"rows={len(df)}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
