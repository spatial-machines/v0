#!/usr/bin/env python3
"""Fetch GTFS transit feed data.

Supports direct URL download or searching the Mobility Database for feeds.

Usage:
    python scripts/core/fetch_gtfs.py \
        --url https://cdn.mbta.com/MBTA_GTFS.zip \
        -o data/raw/mbta_gtfs.zip

    python scripts/core/fetch_gtfs.py --search "Kansas City" \
        -o data/raw/kc_gtfs.zip
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request
from urllib.parse import urlencode

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_mobility_token() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "MOBILITY_DB_TOKEN" and value.strip():
            return value.strip()
    return None


def _parse_gtfs_stats(zip_path: Path) -> dict:
    """Extract basic stats from a GTFS ZIP."""
    stats = {}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            stats["files"] = len(names)

            if "agency.txt" in names:
                with zf.open("agency.txt") as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    agencies = list(reader)
                    stats["agencies"] = [a.get("agency_name", "unknown") for a in agencies]

            if "routes.txt" in names:
                with zf.open("routes.txt") as f:
                    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    stats["route_count"] = sum(1 for _ in reader) - 1

            if "stops.txt" in names:
                with zf.open("stops.txt") as f:
                    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    stats["stop_count"] = sum(1 for _ in reader) - 1

            if "calendar.txt" in names:
                with zf.open("calendar.txt") as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    dates = []
                    for row in reader:
                        dates.append(row.get("start_date", ""))
                        dates.append(row.get("end_date", ""))
                    dates = [d for d in dates if d]
                    if dates:
                        stats["date_range"] = f"{min(dates)} to {max(dates)}"
    except Exception as exc:
        stats["parse_error"] = str(exc)
    return stats


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch GTFS transit feed data.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Direct URL to a GTFS ZIP file")
    group.add_argument("--search", help="Search for feeds by agency/city name")
    parser.add_argument("--limit", type=int, default=5, help="Max search results (default: 5)")
    parser.add_argument("-o", "--output", required=True, help="Output ZIP path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    download_url = args.url

    if args.search:
        token = _load_mobility_token()
        search_url = f"https://api.mobilitydatabase.org/v1/gtfs_feeds?provider_search={args.search}&limit={args.limit}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        print(f"Searching Mobility Database for '{args.search}'")
        req = Request(search_url, headers=headers)
        try:
            with urlopen(req, timeout=30) as response:
                feeds = json.load(response)
        except (HTTPError, URLError) as exc:
            print(f"Search error: {exc}")
            print("  You can also provide a direct --url to a GTFS ZIP")
            return 1

        if not feeds:
            print(f"No feeds found for '{args.search}'")
            return 1

        print(f"  found {len(feeds)} feeds:")
        for i, feed in enumerate(feeds):
            provider = feed.get("provider", "")
            dl = feed.get("latest_dataset", {}).get("hosted_url", "N/A")
            print(f"    [{i}] {provider} — {dl}")

        download_url = feeds[0].get("latest_dataset", {}).get("hosted_url")
        if not download_url:
            download_url = feeds[0].get("source_info", {}).get("producer_url")
        if not download_url:
            print("ERROR: No download URL found for first result")
            return 1

    print(f"Downloading GTFS feed")
    print(f"  from: {download_url}")

    try:
        with urlopen(download_url, timeout=120) as response:
            content = response.read()
    except (HTTPError, URLError) as exc:
        print(f"Download error: {exc}")
        return 1

    out_path.write_bytes(content)
    print(f"  downloaded {len(content):,} bytes")

    stats = _parse_gtfs_stats(out_path)
    if stats.get("agencies"):
        print(f"  agencies: {', '.join(stats['agencies'])}")
    if stats.get("route_count"):
        print(f"  routes: {stats['route_count']}")
    if stats.get("stop_count"):
        print(f"  stops: {stats['stop_count']}")
    if stats.get("date_range"):
        print(f"  date range: {stats['date_range']}")

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "gtfs-download",
        "source_name": "GTFS Transit Feed",
        "source_type": "transit-feed",
        "source_url": download_url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "gtfs-zip",
        "notes": [f"size={len(content):,} bytes"] + [f"{k}={v}" for k, v in stats.items() if k != "parse_error"],
        "warnings": [stats["parse_error"]] if "parse_error" in stats else [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
