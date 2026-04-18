#!/usr/bin/env python3
"""Fetch FEMA National Flood Hazard Layer (NFHL) flood zone polygons.

Queries the FEMA ArcGIS REST service for flood zone boundaries.

Usage:
    python scripts/core/fetch_fema_nfhl.py --bbox -84.5,33.6,-84.2,33.9 \
        -o data/raw/atlanta_flood_zones.geojson

    python scripts/core/fetch_fema_nfhl.py --state-fips 31 --county-fips 055 \
        -o data/raw/douglas_ne_flood.geojson
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlencode

NFHL_URL = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"


def _fetch_page(where: str, geometry: str | None, offset: int, count: int) -> dict:
    params: dict = {
        "where": where,
        "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE,DEPTH,DFIRM_ID",
        "f": "geojson",
        "resultOffset": offset,
        "resultRecordCount": count,
        "outSR": "4326",
    }
    if geometry:
        params["geometry"] = geometry
        params["geometryType"] = "esriGeometryEnvelope"
        params["inSR"] = "4326"
        params["spatialRel"] = "esriSpatialRelIntersects"
    url = f"{NFHL_URL}?{urlencode(params)}"
    with urlopen(url, timeout=120) as resp:
        return json.load(resp)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch FEMA NFHL flood zone polygons.")
    parser.add_argument("--bbox", help="Bounding box: minx,miny,maxx,maxy")
    parser.add_argument("--state-fips", help="State FIPS code")
    parser.add_argument("--county-fips", help="County FIPS code (requires --state-fips)")
    parser.add_argument("--max-records", type=int, default=10000, help="Max records (default: 10000)")
    parser.add_argument("-o", "--output", required=True, help="Output GeoJSON path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    geometry = None
    if args.bbox:
        parts = [float(x) for x in args.bbox.split(",")]
        geometry = f"{parts[0]},{parts[1]},{parts[2]},{parts[3]}"
        where = "1=1"
        print(f"Fetching FEMA NFHL for bbox {args.bbox}")
    elif args.state_fips:
        fips = args.state_fips.zfill(2)
        if args.county_fips:
            dfirm_id = fips + args.county_fips.zfill(3)
            where = f"DFIRM_ID='{dfirm_id}'"
        else:
            where = f"DFIRM_ID LIKE '{fips}%'"
        print(f"Fetching FEMA NFHL for DFIRM filter: {where}")
    else:
        print("ERROR: Provide --bbox or --state-fips")
        return 1

    all_features = []
    offset = 0
    page_size = 2000

    while offset < args.max_records:
        try:
            data = _fetch_page(where, geometry, offset, page_size)
        except (HTTPError, URLError) as exc:
            print(f"Error at offset {offset}: {exc}")
            break

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        print(f"  fetched {len(features)} features (total: {len(all_features)})")

        exceeded = data.get("exceededTransferLimit", False) or data.get("properties", {}).get("exceededTransferLimit", False)
        if not exceeded or len(features) < page_size:
            break
        offset += len(features)

    result = {"type": "FeatureCollection", "features": all_features}
    out_path.write_text(json.dumps(result))

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "arcgis-rest",
        "source_name": "FEMA National Flood Hazard Layer",
        "source_type": "federal-api",
        "source_url": NFHL_URL,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "geojson",
        "notes": [f"features={len(all_features)}", f"where={where}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  total: {len(all_features)} flood zone features")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
