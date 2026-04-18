#!/usr/bin/env python3
"""Fetch points-of-interest (POIs) from OpenStreetMap via Overpass API.

Generic POI fetcher for any tag query — grocery stores, transit stops,
healthcare facilities, schools, banks, etc. Results are cached locally
so repeated runs don't re-hit the API.

Usage:
    # Grocery stores in Cook County
    python scripts/core/fetch_osm_pois.py \\
        --bbox -88.26,41.47,-87.52,42.15 \\
        --query 'shop=supermarket|shop=grocery' \\
        -o data/raw/cook_grocery.gpkg

    # CTA/Metra/Pace transit stops
    python scripts/core/fetch_osm_pois.py \\
        --bbox -88.26,41.47,-87.52,42.15 \\
        --query 'public_transport=stop_position|highway=bus_stop|railway=station' \\
        -o data/raw/cook_transit.gpkg

Supported query syntax (piped OR):
    key=value | key2=value2 | key3=*
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import shapely.geometry as sg

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "osm_pois"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _cache_key(bounds: tuple, query: str) -> str:
    s = json.dumps({"bounds": bounds, "query": query}, sort_keys=True)
    return hashlib.md5(s.encode()).hexdigest()[:12]


def _build_overpass_query(bbox: tuple, filters: list[str]) -> str:
    """Build an Overpass QL query from a list of tag filters.

    Each filter is "key=value" or "key=*".
    """
    south, west, north, east = bbox[1], bbox[0], bbox[3], bbox[2]
    bbox_str = f"{south},{west},{north},{east}"

    clauses = []
    for f in filters:
        if "=" not in f:
            continue
        key, value = f.split("=", 1)
        if value == "*":
            clauses.append(f'node["{key}"]({bbox_str});')
            clauses.append(f'way["{key}"]({bbox_str});')
        else:
            clauses.append(f'node["{key}"="{value}"]({bbox_str});')
            clauses.append(f'way["{key}"="{value}"]({bbox_str});')

    return f"[out:json][timeout:90];\n(\n{chr(10).join(clauses)}\n);\nout center;"


def fetch(bbox: tuple, query: str, use_cache: bool = True) -> gpd.GeoDataFrame:
    """Fetch OSM POIs matching the query within the bounding box.

    Args:
        bbox: (minlon, minlat, maxlon, maxlat) in WGS84
        query: Pipe-separated filters, e.g. "shop=supermarket|shop=grocery"
        use_cache: Use local cache if available
    """
    import requests

    filters = [f.strip() for f in query.split("|") if f.strip()]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"osm_{_cache_key(bbox, query)}.gpkg"

    if use_cache and cache_path.exists():
        return gpd.read_file(cache_path)

    ql = _build_overpass_query(bbox, filters)
    resp = requests.post(OVERPASS_URL, data={"data": ql}, timeout=180)
    resp.raise_for_status()
    payload = resp.json()

    features = []
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        if el["type"] == "node":
            lon, lat = el["lon"], el["lat"]
        elif el["type"] == "way" and "center" in el:
            lon, lat = el["center"]["lon"], el["center"]["lat"]
        else:
            continue

        features.append({
            "geometry": sg.Point(lon, lat),
            "osm_id": el.get("id"),
            "osm_type": el["type"],
            "name": tags.get("name", ""),
            "brand": tags.get("brand", ""),
            "shop": tags.get("shop", ""),
            "amenity": tags.get("amenity", ""),
            "public_transport": tags.get("public_transport", ""),
            "highway": tags.get("highway", ""),
            "railway": tags.get("railway", ""),
            "operator": tags.get("operator", ""),
        })

    if not features:
        return gpd.GeoDataFrame({"geometry": []}, crs="EPSG:4326")

    gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")

    if use_cache:
        gdf.to_file(cache_path, driver="GPKG")

    return gdf


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch OSM POIs via Overpass API.")
    p.add_argument("--bbox", required=True,
                   help="Bounding box as minlon,minlat,maxlon,maxlat (WGS84)")
    p.add_argument("--query", required=True,
                   help="Pipe-separated tag filters, e.g. 'shop=supermarket|shop=grocery'")
    p.add_argument("-o", "--output", required=True, help="Output GeoPackage path")
    p.add_argument("--no-cache", action="store_true", help="Skip local cache")
    args = p.parse_args()

    bbox = tuple(float(x) for x in args.bbox.split(","))
    if len(bbox) != 4:
        print("ERROR: --bbox must be minlon,minlat,maxlon,maxlat")
        return 1

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching OSM POIs")
    print(f"  bbox: {bbox}")
    print(f"  query: {args.query}")

    gdf = fetch(bbox, args.query, use_cache=not args.no_cache)
    print(f"  features: {len(gdf)}")

    if gdf.empty:
        print("WARNING: no features found")
        return 1

    gdf.to_file(out, driver="GPKG")

    manifest = {
        "dataset_id": out.stem,
        "retrieval_method": "overpass-api",
        "source_name": "OpenStreetMap via Overpass API",
        "source_type": "community-database",
        "source_url": OVERPASS_URL,
        "query": args.query,
        "bbox": list(bbox),
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out),
        "format": "gpkg",
        "notes": [f"features={len(gdf)}"],
        "warnings": [],
    }
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
