#!/usr/bin/env python3
"""Fetch POI (Point of Interest) data from a local OSM PostGIS database.

Opens an SSH tunnel to the OSM database, queries planet_osm_point for
brand/name matches, and outputs a GeoPackage. Falls back to Overpass API
if --fallback-overpass is set and the local DB is unreachable.

Usage:
    python scripts/core/fetch_poi.py \
        --brand Chipotle \
        --tag amenity=fast_food \
        --state MO \
        --output data/raw/chipotles_mo.gpkg \
        --competitors "McDonald's,Taco Bell,Qdoba" \
        --fallback-overpass
"""
from __future__ import annotations

import json
import random
import subprocess
import time
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# State FIPS → abbreviation mapping (for --state lookup)
STATE_ABBREV_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11",
}

# Rough state bounding boxes (EPSG:4326) for --state filtering
# Format: (minx, miny, maxx, maxy)
STATE_BBOXES = {
    "MO": (-95.774, 35.995, -89.098, 40.614),
    "KS": (-102.051, 36.993, -94.588, 40.003),
    "IL": (-91.513, 36.970, -87.019, 42.509),
    "NE": (-104.053, 39.999, -95.308, 43.002),
    "IA": (-96.639, 40.375, -90.140, 43.501),
    "TX": (-106.646, 25.837, -93.508, 36.501),
    "CA": (-124.409, 32.534, -114.131, 42.009),
    "NY": (-79.762, 40.496, -71.856, 45.016),
    "FL": (-87.634, 24.396, -79.974, 31.001),
    "OH": (-84.820, 38.403, -80.518, 41.978),
    "GA": (-85.605, 30.356, -80.840, 35.001),
    "PA": (-80.519, 39.720, -74.689, 42.270),
}


def _load_env() -> dict[str, str]:
    """Read key=value pairs from .env file."""
    env_path = PROJECT_ROOT / ".env"
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _open_ssh_tunnel(env: dict) -> tuple:
    """Open SSH tunnel to the OSM database. Returns (local_port, tunnel_object_or_process).

    Tries sshtunnel library first, falls back to subprocess ssh -L.
    """
    ssh_host = env.get("OSM_DB_SSH_HOST", "")
    ssh_user = env.get("OSM_DB_SSH_USER", "")
    ssh_key = env.get("OSM_DB_SSH_KEY", "")
    db_host = env.get("OSM_DB_HOST", "localhost")
    db_port = int(env.get("OSM_DB_PORT", "5432"))

    local_port = random.randint(15000, 15999)

    # Expand ~ in key path — try HOME, then /root for Docker containers
    if ssh_key.startswith("~"):
        expanded = str(Path(ssh_key).expanduser())
        if not Path(expanded).exists():
            # In Docker, HOME may differ; try /root
            expanded = ssh_key.replace("~", "/root")
        ssh_key = expanded

    # Try sshtunnel library first
    try:
        from sshtunnel import SSHTunnelForwarder
        tunnel = SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_user,
            ssh_pkey=ssh_key,
            remote_bind_address=(db_host, db_port),
            local_bind_address=("127.0.0.1", local_port),
        )
        tunnel.start()
        actual_port = tunnel.local_bind_port
        print(f"  SSH tunnel open (sshtunnel): localhost:{actual_port} -> {db_host}:{db_port}")
        return actual_port, tunnel
    except (ImportError, AttributeError) as exc:
        # AttributeError: paramiko compatibility issues (e.g. DSSKey removed)
        print(f"  sshtunnel unavailable ({exc}), trying subprocess SSH...")

    # Fallback: subprocess ssh -L
    cmd = [
        "ssh", "-N", "-L", f"{local_port}:{db_host}:{db_port}",
        "-i", ssh_key,
        "-F", "/dev/null",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        f"{ssh_user}@{ssh_host}",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    time.sleep(4)  # wait for tunnel to establish
    if proc.poll() is not None:
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        raise ConnectionError(f"SSH tunnel failed: {stderr}")
    print(f"  SSH tunnel open (subprocess): localhost:{local_port} -> {db_host}:{db_port}")
    return local_port, proc


def _close_tunnel(tunnel_obj):
    """Close SSH tunnel cleanly."""
    if tunnel_obj is None:
        return
    try:
        # sshtunnel object
        if hasattr(tunnel_obj, "stop"):
            tunnel_obj.stop()
        # subprocess
        elif hasattr(tunnel_obj, "terminate"):
            tunnel_obj.terminate()
            tunnel_obj.wait(timeout=5)
    except Exception:
        pass


def _query_local_db(brand: str, tags: list[tuple[str, str]], bbox: tuple | None,
                    limit: int | None, env: dict) -> "gpd.GeoDataFrame":
    """Query local OSM PostGIS database via SSH tunnel."""
    try:
        import geopandas as gpd
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise ImportError(
            f"Missing dependency: {exc.name}. Install: pip install geopandas sqlalchemy psycopg2-binary"
        ) from exc

    db_host = env.get("OSM_DB_HOST", "127.0.0.1")
    db_port = int(env.get("OSM_DB_PORT", "5432"))
    db_user = env.get("OSM_DB_USER", "osm")
    db_pass = env.get("OSM_DB_PASSWORD", "osm")
    db_name = env.get("OSM_DB_NAME", "osmdb")

    # Check if DB is already reachable (pre-established tunnel or direct access)
    tunnel = None
    local_port = db_port
    try:
        import socket
        s = socket.create_connection((db_host, db_port), timeout=3)
        s.close()
        print(f"  DB already reachable at {db_host}:{db_port} — skipping tunnel")
    except (OSError, ConnectionRefusedError):
        print(f"  DB not reachable at {db_host}:{db_port} — opening SSH tunnel...")
        local_port, tunnel = _open_ssh_tunnel(env)
        db_host = "127.0.0.1"

    try:
        url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{local_port}/{db_name}"
        engine = create_engine(url, connect_args={"connect_timeout": 10})

        # Build WHERE clause
        conditions = []
        params = {}

        # Brand / name match
        if brand:
            conditions.append("(brand ILIKE :brand_pat OR name ILIKE :brand_pat)")
            params["brand_pat"] = f"%{brand}%"

        # Tag filters
        for i, (tag_key, tag_val) in enumerate(tags):
            col = tag_key.replace("-", "_")
            pname = f"tag_{i}"
            conditions.append(f'"{col}" = :{pname}')
            params[pname] = tag_val

        # Bbox filter (way column is EPSG:3857)
        if bbox:
            conditions.append(
                "ST_Intersects(way, ST_Transform(ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326), 3857))"
            )
            params["minx"] = bbox[0]
            params["miny"] = bbox[1]
            params["maxx"] = bbox[2]
            params["maxy"] = bbox[3]

        where = " AND ".join(conditions) if conditions else "TRUE"
        limit_clause = f"LIMIT {limit}" if limit else ""

        sql = f"""
            SELECT
                osm_id,
                name,
                brand,
                amenity,
                shop,
                tags->'addr:street' AS addr_street,
                tags->'addr:city' AS addr_city,
                tags->'addr:state' AS addr_state,
                tags->'addr:postcode' AS addr_postcode,
                ST_Transform(way, 4326) AS geometry
            FROM planet_osm_point
            WHERE {where}
            {limit_clause}
        """

        print(f"  Querying local OSM DB...")
        gdf = gpd.read_postgis(text(sql), engine, geom_col="geometry", params=params)
        print(f"  Retrieved {len(gdf)} features from local DB")
        return gdf
    finally:
        _close_tunnel(tunnel)


def _query_overpass(brand: str, tags: list[tuple[str, str]], bbox: tuple | None,
                    limit: int | None) -> "gpd.GeoDataFrame":
    """Query Overpass API as fallback."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError as exc:
        raise ImportError(
            f"Missing dependency: {exc.name}. Install: pip install geopandas shapely"
        ) from exc

    # Build Overpass QL query
    filters = ""
    if brand:
        # Use exact match first — regex (~) is slower and may timeout on Overpass
        filters += f'["brand"="{brand}"]'
    for tag_key, tag_val in tags:
        filters += f'["{tag_key}"="{tag_val}"]'

    bbox_str = ""
    if bbox:
        # Overpass uses (south,west,north,east)
        bbox_str = f"({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]})"

    query = f'[out:json][timeout:60];node{filters}{bbox_str};out body;'

    print(f"  Querying Overpass API...")
    print(f"  Query: {query[:200]}...")

    # Try multiple Overpass endpoints
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    # Use subprocess curl with --data-urlencode for reliability
    max_retries = 4
    result = None
    for attempt in range(max_retries):
        for ep_url in endpoints:
            try:
                print(f"    Trying: {ep_url} (attempt {attempt + 1}/{max_retries})")
                proc = subprocess.run(
                    ["curl", "-s", "--max-time", "90",
                     "--data-urlencode", f"data={query}",
                     ep_url],
                    capture_output=True, text=True, timeout=100,
                )
                output = proc.stdout.strip()
                if proc.returncode == 0 and output.startswith("{"):
                    result = json.loads(output)
                    break
                elif "too busy" in output or "timeout" in output.lower():
                    print(f"    Server busy, will retry...")
                else:
                    print(f"    Non-JSON response (code {proc.returncode})")
            except FileNotFoundError:
                # No curl — fall back to urllib
                from urllib.parse import urlencode
                encoded_data = urlencode({"data": query}).encode("utf-8")
                try:
                    req = Request(ep_url, data=encoded_data, method="POST")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    req.add_header("User-Agent", "GIS-Agent-Pipeline/1.0")
                    with urlopen(req, timeout=120) as resp:
                        result = json.load(resp)
                    break
                except Exception as exc2:
                    print(f"    urllib also failed: {exc2}")
            except Exception as exc:
                print(f"    Failed: {exc}")
        if result is not None:
            break
        if attempt < max_retries - 1:
            wait = 15 * (attempt + 1)
            print(f"    Waiting {wait}s before retry...")
            time.sleep(wait)

    if result is None:
        raise ConnectionError("All Overpass endpoints failed after retries")

    elements = result.get("elements", [])
    print(f"  Retrieved {len(elements)} features from Overpass API")

    if not elements:
        return gpd.GeoDataFrame(
            columns=["osm_id", "name", "brand", "amenity", "shop",
                      "addr_street", "addr_city", "addr_state", "addr_postcode", "geometry"]
        )

    records = []
    for el in elements:
        t = el.get("tags", {})
        records.append({
            "osm_id": el.get("id"),
            "name": t.get("name", ""),
            "brand": t.get("brand", ""),
            "amenity": t.get("amenity", ""),
            "shop": t.get("shop", ""),
            "addr_street": t.get("addr:street", ""),
            "addr_city": t.get("addr:city", ""),
            "addr_state": t.get("addr:state", ""),
            "addr_postcode": t.get("addr:postcode", ""),
            "geometry": Point(el["lon"], el["lat"]),
        })

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    if limit:
        gdf = gdf.head(limit)
    return gdf


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch POI data from local OSM PostGIS database or Overpass API."
    )
    parser.add_argument("--brand", required=True, help="Brand or name to search (ILIKE match)")
    parser.add_argument("--tag", action="append", default=[],
                        help="OSM tag filter as key=value (can repeat)")
    parser.add_argument("--bbox", help="Bounding box: minx,miny,maxx,maxy (EPSG:4326)")
    parser.add_argument("--state", help="State abbreviation (e.g. MO) — uses built-in bbox")
    parser.add_argument("--output", "-o", required=True, help="Output GeoPackage path")
    parser.add_argument("--competitors", default="",
                        help="Comma-separated competitor brands (fetched and saved to --competitors-output)")
    parser.add_argument("--competitors-output", default="",
                        help="Output GeoPackage path for competitor POIs (default: <output>_competitors.gpkg)")
    parser.add_argument("--limit", type=int, help="Maximum number of features to return")
    parser.add_argument("--fallback-overpass", action="store_true",
                        help="Fall back to Overpass API if local DB fails")
    args = parser.parse_args()

    # Parse tags
    tags = []
    for t in args.tag:
        if "=" in t:
            k, _, v = t.partition("=")
            tags.append((k.strip(), v.strip()))
        else:
            print(f"WARNING: ignoring malformed tag filter: {t}")

    # Resolve bbox
    bbox = None
    if args.bbox:
        parts = [float(x.strip()) for x in args.bbox.split(",")]
        if len(parts) == 4:
            bbox = tuple(parts)
        else:
            print("ERROR: --bbox must have exactly 4 values: minx,miny,maxx,maxy")
            return 1
    elif args.state:
        st = args.state.upper()
        if st in STATE_BBOXES:
            bbox = STATE_BBOXES[st]
            print(f"  Using built-in bbox for {st}: {bbox}")
        else:
            print(f"WARNING: no built-in bbox for state '{st}' — querying without bbox (slow)")

    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    env = _load_env()
    source = "unknown"
    t0 = time.time()

    print(f"Fetching POIs: brand={args.brand}")
    if tags:
        print(f"  tag filters: {tags}")
    if bbox:
        print(f"  bbox: {bbox}")
    if competitors:
        print(f"  competitors: {competitors}")

    gdf = None

    # Try local DB first
    try:
        gdf = _query_local_db(args.brand, tags, bbox, args.limit, env)
        source = "local_osm_db"
    except Exception as exc:
        print(f"  Local DB failed: {exc}")
        if args.fallback_overpass:
            print("  Falling back to Overpass API...")
        else:
            print("ERROR: local DB unavailable and --fallback-overpass not set")
            return 1

    # Fallback to Overpass
    if gdf is None or (len(gdf) == 0 and args.fallback_overpass):
        try:
            gdf = _query_overpass(args.brand, tags, bbox, args.limit)
            source = "overpass_api"
        except Exception as exc:
            print(f"ERROR: Overpass API also failed: {exc}")
            return 1

    query_time = round(time.time() - t0, 2)

    if gdf is None or len(gdf) == 0:
        print("WARNING: no features found matching criteria")
        # Still write empty GeoPackage
        try:
            import geopandas as gpd
            gdf = gpd.GeoDataFrame(
                columns=["osm_id", "name", "brand", "amenity", "shop",
                          "addr_street", "addr_city", "addr_state", "addr_postcode", "geometry"]
            )
        except ImportError:
            pass

    # Set CRS if missing
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    # Write output
    gdf.to_file(out_path, driver="GPKG")
    print(f"  Source: {source}")
    print(f"  Features: {len(gdf)}")
    print(f"  Output: {out_path}")
    print(f"  Query time: {query_time}s")

    # Fetch competitor POIs if requested
    comp_out_path = None
    comp_count = 0
    if competitors:
        comp_out_str = args.competitors_output or str(out_path).replace(".gpkg", "_competitors.gpkg")
        comp_out_path = Path(comp_out_path or comp_out_str).expanduser().resolve()
        comp_out_path = Path(comp_out_str).expanduser().resolve()
        print(f"\nFetching {len(competitors)} competitor brand(s): {competitors}")
        comp_gdfs = []
        t_comp = time.time()
        for comp_brand in competitors:
            print(f"  Querying: {comp_brand}")
            try:
                cgdf = _query_overpass(comp_brand, [], bbox, args.limit)
                cgdf["queried_brand"] = comp_brand
                comp_gdfs.append(cgdf)
                print(f"    {len(cgdf)} locations found")
            except Exception as exc:
                print(f"    WARNING: could not fetch {comp_brand}: {exc}")
        if comp_gdfs:
            import pandas as pd
            import geopandas as gpd
            all_comps = gpd.GeoDataFrame(
                pd.concat(comp_gdfs, ignore_index=True), crs="EPSG:4326"
            )
            all_comps.to_file(comp_out_path, driver="GPKG")
            comp_count = len(all_comps)
            print(f"  Total competitors: {comp_count} → {comp_out_path}")
        else:
            print("  No competitor data retrieved")
            comp_out_path = None

    # JSON log
    log = {
        "step": "fetch_poi",
        "brand": args.brand,
        "tags": [f"{k}={v}" for k, v in tags],
        "bbox": list(bbox) if bbox else None,
        "state": args.state,
        "competitors": competitors,
        "competitors_output": str(comp_out_path) if comp_out_path else None,
        "competitors_count": comp_count,
        "source": source,
        "count": len(gdf),
        "crs": "EPSG:4326",
        "query_time_s": query_time,
        "output": str(out_path),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_suffix(".fetch_poi.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
