#!/usr/bin/env python3
"""Fetch environmental justice indicators from EPA EJScreen.

Usage:
    python scripts/core/fetch_ejscreen.py --lat 33.749 --lon -84.388 \
        --distance 1 -o data/raw/ejscreen_atlanta.json

    python scripts/core/fetch_ejscreen.py --lat 41.878 --lon -87.629 \
        --distance 3 -o data/raw/ejscreen_chicago.json
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlencode


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch EPA EJScreen environmental justice indicators for a point+buffer."
    )
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument(
        "--distance", type=float, default=1,
        help="Buffer distance in miles (default: 1)",
    )
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    params = urlencode({
        "namestr": "",
        "geometry": json.dumps({"x": args.lon, "y": args.lat, "spatialReference": {"wkid": 4326}}),
        "distance": args.distance,
        "unit": "9035",
        "aession": "",
        "f": "json",
    })
    url = f"https://ejscreen.epa.gov/mapper/ejscreenRESTbroker.aspx?{params}"

    print(f"Fetching EJScreen for ({args.lat}, {args.lon}), {args.distance} mi buffer")

    try:
        with urlopen(url, timeout=60) as response:
            data = json.load(response)
    except (HTTPError, URLError) as exc:
        print(f"Error fetching EJScreen: {exc}")
        return 1

    out_path.write_text(json.dumps(data, indent=2))

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "ejscreen-api",
        "source_name": "EPA EJScreen",
        "source_type": "federal-api",
        "source_url": url.split("?")[0],
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "json",
        "notes": [f"lat={args.lat}", f"lon={args.lon}", f"distance={args.distance}mi"],
        "warnings": [],
    }
    manifest_path = out_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path}")
    print(f"  manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
