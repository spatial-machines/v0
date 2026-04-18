#!/usr/bin/env python3
"""Fetch POI data from the local PostGIS OSM planet extract.

Queries the Optiplex PostGIS database (osmdb) for points of interest
within a bounding box or polygon. Returns a GeoPackage with all matching
features and their OSM tags.

This is the preferred POI source over Overpass API:
  - 2-3x more complete for commercial chains
  - No rate limits or timeouts
  - 41.7M points indexed locally
  - Sub-second queries

Requires: SSH tunnel to Optiplex running on localhost:15432
  systemctl --user start postgis-tunnel.service

Usage:
    python fetch_poi_postgis.py \\
        --bbox -105.11,39.61,-104.60,39.91 \\
        --query "amenity='cafe' OR shop='coffee'" \\
        --output data/raw/denver_cafes.gpkg

    python fetch_poi_postgis.py \\
        --bbox -105.11,39.61,-104.60,39.91 \\
        --brand "Starbucks" \\
        --output data/raw/starbucks.gpkg

    python fetch_poi_postgis.py \\
        --bbox -105.11,39.61,-104.60,39.91 \\
        --amenity cafe \\
        --competitors "Dunkin,Dutch Bros,Peet's Coffee,Caribou Coffee" \\
        --output data/raw/competitors.gpkg
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Default connection string — SSH tunnel on Pi to Optiplex PostGIS
DEFAULT_CONN = "postgresql://osm@127.0.0.1:15432/osmdb"

# OSM planet data is in SRID 3857 (Web Mercator)
OSM_SRID = 3857

# Columns to always retrieve from planet_osm_point
BASE_COLS = [
    "osm_id", "name", "brand", "operator", "amenity", "shop",
    "\"addr:housenumber\"", "\"addr:street\"", "\"addr:city\"",
    "\"addr:state\"", "\"addr:postcode\"", "phone", "website",
    "opening_hours",
]

# Additional tag columns that might be useful
EXTRA_COLS = [
    "tourism", "leisure", "healthcare", "office",
]


def build_where_clause(args) -> str:
    """Build SQL WHERE clause from arguments."""
    conditions = []

    if args.brand:
        brands = [b.strip() for b in args.brand.split(",")]
        brand_conds = []
        for b in brands:
            brand_conds.append(f"name ILIKE '%{b}%'")
            brand_conds.append(f"brand ILIKE '%{b}%'")
            brand_conds.append(f"operator ILIKE '%{b}%'")
        conditions.append(f"({' OR '.join(brand_conds)})")

    if args.competitors:
        comps = [c.strip() for c in args.competitors.split(",")]
        comp_conds = []
        for c in comps:
            comp_conds.append(f"name ILIKE '%{c}%'")
            comp_conds.append(f"brand ILIKE '%{c}%'")
        conditions.append(f"({' OR '.join(comp_conds)})")

    if args.amenity:
        amenities = [a.strip() for a in args.amenity.split(",")]
        conditions.append(f"amenity IN ({','.join(repr(a) for a in amenities)})")

    if args.shop:
        shops = [s.strip() for s in args.shop.split(",")]
        conditions.append(f"shop IN ({','.join(repr(s) for s in shops)})")

    if args.query:
        conditions.append(f"({args.query})")

    if not conditions:
        print("Error: at least one of --brand, --competitors, --amenity, --shop, or --query is required")
        sys.exit(1)

    return " AND ".join(conditions) if not args.any_match else " OR ".join(conditions)


def parse_bbox(bbox_str: str) -> tuple:
    """Parse 'minx,miny,maxx,maxy' into tuple."""
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"bbox must have 4 values (minx,miny,maxx,maxy), got {len(parts)}")
    return tuple(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch POI from local PostGIS OSM planet extract."
    )
    parser.add_argument("--bbox", required=True,
                        help="Bounding box: minx,miny,maxx,maxy (EPSG:4326)")
    parser.add_argument("--brand", help="Brand name(s) to search (comma-separated)")
    parser.add_argument("--competitors", help="Competitor brand names (comma-separated)")
    parser.add_argument("--amenity", help="OSM amenity tag(s) (comma-separated)")
    parser.add_argument("--shop", help="OSM shop tag(s) (comma-separated)")
    parser.add_argument("--query", help="Raw SQL WHERE clause for planet_osm_point")
    parser.add_argument("--any-match", action="store_true",
                        help="OR conditions instead of AND (default: AND)")
    parser.add_argument("--exclude-brand", help="Exclude these brands (comma-separated)")
    parser.add_argument("-o", "--output", required=True,
                        help="Output GeoPackage path")
    parser.add_argument("--conn", default=DEFAULT_CONN,
                        help=f"PostgreSQL connection string (default: {DEFAULT_CONN})")
    parser.add_argument("--table", default="planet_osm_point",
                        choices=["planet_osm_point", "planet_osm_polygon"],
                        help="OSM table to query (default: planet_osm_point)")
    args = parser.parse_args()

    # Parse bbox
    minx, miny, maxx, maxy = parse_bbox(args.bbox)

    # Build spatial filter (transform 4326 bbox to 3857)
    bbox_sql = f"ST_Transform(ST_MakeEnvelope({minx}, {miny}, {maxx}, {maxy}, 4326), {OSM_SRID})"

    # Build WHERE
    where = build_where_clause(args)

    # Exclusion
    exclude_sql = ""
    if args.exclude_brand:
        excludes = [b.strip() for b in args.exclude_brand.split(",")]
        excl_parts = []
        for b in excludes:
            excl_parts.append(f"name NOT ILIKE '%{b}%'")
            excl_parts.append(f"COALESCE(brand,'') NOT ILIKE '%{b}%'")
        exclude_sql = " AND " + " AND ".join(excl_parts)

    # Build columns list
    cols = BASE_COLS + EXTRA_COLS
    cols_sql = ", ".join(cols)

    # Full query — transform geometry back to 4326 for output
    sql = f"""
        SELECT {cols_sql},
               ST_Transform(way, 4326) AS geometry
        FROM {args.table}
        WHERE ({where})
          AND ST_Within(way, {bbox_sql})
          {exclude_sql}
        ORDER BY osm_id
    """

    print(f"Querying {args.table} in PostGIS...")
    print(f"  Bbox: {minx},{miny},{maxx},{maxy}")
    print(f"  Filter: {where[:100]}...")

    try:
        from sqlalchemy import create_engine
        engine = create_engine(args.conn)
        gdf = gpd.read_postgis(sql, engine, geom_col="geometry", crs="EPSG:4326")
    except ImportError:
        # Fallback without sqlalchemy
        import psycopg2
        conn = psycopg2.connect(args.conn.replace("postgresql://", "").replace("@", " user=").replace("/", " dbname=").replace(":", " port="))
        gdf = gpd.read_postgis(sql, conn, geom_col="geometry", crs="EPSG:4326")
        conn.close()

    # Clean column names (remove quotes)
    gdf.columns = [c.replace('"', '').replace("addr:", "addr_") for c in gdf.columns]

    print(f"  Found: {len(gdf)} features")

    if len(gdf) == 0:
        print("  WARNING: No features found. Check your query and bbox.")

    # Drop empty geometry rows
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    # Output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    print(f"  Saved: {out_path} ({len(gdf)} features)")

    # Write sidecar log
    log = {
        "step": "fetch_poi_postgis",
        "source": "PostGIS osmdb (planet extract)",
        "table": args.table,
        "bbox": [minx, miny, maxx, maxy],
        "filter": where[:200],
        "features": len(gdf),
        "output": str(out_path),
        "connection": args.conn.split("@")[1] if "@" in args.conn else "local",
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "OSM data completeness varies by region. Commercial chain coverage is better than Overpass but still imperfect.",
    }
    log_path = out_path.with_suffix(".fetch_poi_postgis.json")
    log_path.write_text(json.dumps(log, indent=2))

    # Print brand breakdown
    if "brand" in gdf.columns or "name" in gdf.columns:
        brand_col = "brand" if "brand" in gdf.columns and gdf["brand"].notna().any() else "name"
        breakdown = gdf[brand_col].value_counts().head(15)
        if len(breakdown) > 0:
            print(f"\n  Brand/name breakdown:")
            for name, count in breakdown.items():
                print(f"    {name}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
