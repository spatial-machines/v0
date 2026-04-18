#!/usr/bin/env python3
"""Fetch weather data from OpenWeatherMap API.

Requires a free API key from https://openweathermap.org/api

Usage:
    python scripts/core/fetch_openweather.py --lat 41.26 --lon -95.94 \
        -o data/raw/omaha_weather.json

    python scripts/core/fetch_openweather.py --city "Atlanta,US" \
        --mode forecast -o data/raw/atlanta_forecast.json

    python scripts/core/fetch_openweather.py --lat 39.1 --lon -94.6 \
        --mode forecast --units imperial -o data/raw/kc_forecast.json
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlencode

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENDPOINTS = {
    "current": "https://api.openweathermap.org/data/2.5/weather",
    "forecast": "https://api.openweathermap.org/data/2.5/forecast",
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
        if key.strip() == "OPENWEATHER_API_KEY" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch weather data from OpenWeatherMap."
    )
    loc = parser.add_mutually_exclusive_group(required=True)
    loc.add_argument("--city", help="City name (e.g. 'Atlanta,US', 'London,UK')")
    loc.add_argument("--lat", type=float, help="Latitude (use with --lon)")
    parser.add_argument("--lon", type=float, help="Longitude (required with --lat)")
    parser.add_argument("--mode", default="current", choices=["current", "forecast"],
                        help="Weather mode (default: current)")
    parser.add_argument("--units", default="metric", choices=["metric", "imperial", "standard"],
                        help="Units (default: metric)")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    if args.lat is not None and args.lon is None:
        print("ERROR: --lon required when using --lat")
        return 1

    api_key = _load_api_key()
    if not api_key:
        print("ERROR: OpenWeather API key required. Set OPENWEATHER_API_KEY in .env")
        print("  Sign up at: https://openweathermap.org/api")
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    params: dict = {"appid": api_key, "units": args.units}
    if args.city:
        params["q"] = args.city
        location_desc = args.city
    else:
        params["lat"] = args.lat
        params["lon"] = args.lon
        location_desc = f"({args.lat}, {args.lon})"

    endpoint = ENDPOINTS[args.mode]
    url = f"{endpoint}?{urlencode(params)}"

    print(f"Fetching {args.mode} weather for {location_desc}")

    try:
        with urlopen(url, timeout=30) as response:
            data = json.load(response)
    except HTTPError as exc:
        if exc.code == 401:
            print("ERROR: Invalid API key")
            return 1
        print(f"Error: {exc}")
        return 1
    except URLError as exc:
        print(f"Network error: {exc}")
        return 1

    out_path.write_text(json.dumps(data, indent=2))

    # Print summary
    if args.mode == "current":
        main_data = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        unit_sym = "°C" if args.units == "metric" else "°F"
        print(f"  conditions: {weather.get('description', 'unknown')}")
        print(f"  temperature: {main_data.get('temp', 'N/A')}{unit_sym}")
        print(f"  humidity: {main_data.get('humidity', 'N/A')}%")
        print(f"  wind: {data.get('wind', {}).get('speed', 'N/A')} {'m/s' if args.units == 'metric' else 'mph'}")
    elif args.mode == "forecast":
        entries = data.get("list", [])
        print(f"  forecast entries: {len(entries)}")
        if entries:
            print(f"  range: {entries[0].get('dt_txt', '')} to {entries[-1].get('dt_txt', '')}")

    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "openweather-api",
        "source_name": "OpenWeatherMap",
        "source_type": "weather-api",
        "source_url": endpoint,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "json",
        "notes": [f"location={location_desc}", f"mode={args.mode}", f"units={args.units}"],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
