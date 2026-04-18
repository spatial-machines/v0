from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
import sys

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def tiger_tract_url(year: str, state_fips: str) -> str:
    return f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/tl_{year}_{state_fips}_tract.zip"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Download Census TIGER tract data.")
    parser.add_argument("year", help="TIGER vintage year (e.g. 2024)")
    parser.add_argument("state_fips", help="State FIPS code (e.g. 31 for Nebraska)")
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory (default: data/raw/)"
    )
    args = parser.parse_args()

    year = args.year
    state_fips = args.state_fips.zfill(2)
    url = tiger_tract_url(year, state_fips)

    raw_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = f"tl_{year}_{state_fips}_tract.zip"
    dest = raw_dir / filename

    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with dest.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

    manifest = {
        "dataset_id": dest.stem,
        "retrieval_method": "tiger-download",
        "source_name": "US Census TIGER/Line",
        "source_type": "census-tiger",
        "source_url": url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(dest.resolve().relative_to(PROJECT_ROOT)),
        "format": "zip",
        "geography_level": "tract",
        "vintage": year,
        "notes": [f"state_fips: {state_fips}"],
        "warnings": [],
    }

    out = raw_dir / f"{dest.stem}.manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"downloaded {url} -> {dest}")
    print(f"manifest {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
