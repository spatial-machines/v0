# OpenWeatherMap Source Page

Source Summary:
OpenWeatherMap provides current weather conditions, 5-day forecasts, and historical weather data for any location worldwide. Useful for climate context in spatial analyses, urban heat studies, and event-based analysis.

Owner / Publisher:
OpenWeather Ltd (commercial, with free tier)

Geography Support:
Point (lat/lon), city name. Global coverage.

Time Coverage:
Current conditions (real-time), 5-day/3-hour forecast (free tier), historical data (paid tiers).

Access Method:
REST API with API key. Use `fetch_openweather.py` for retrieval.

Fetch Script:
`scripts/core/fetch_openweather.py`

Example:
```bash
python scripts/core/fetch_openweather.py --lat 41.26 --lon -95.94 \
    -o data/raw/omaha_weather.json

python scripts/core/fetch_openweather.py --city "Atlanta,US" \
    --mode forecast -o data/raw/atlanta_forecast.json

python scripts/core/fetch_openweather.py --lat 39.1 --lon -94.6 \
    --mode forecast --units imperial -o data/raw/kc_forecast.json
```

Credentials:
Required — free tier API key from https://openweathermap.org/api (OPENWEATHER_API_KEY in .env). Free tier allows 1000 calls/day.

Licensing / Usage Notes:
Freemium service. Free tier is sufficient for contextual weather queries. Historical data and higher rate limits require paid plans. Attribution required per terms of service.

Known Caveats:
- Free tier limited to current weather and 5-day forecast — no historical
- Weather data is point-based, not area-based — represents conditions at or near the queried location
- Forecast accuracy degrades beyond 2-3 days
- Temperature units depend on the --units flag (metric=Celsius, imperial=Fahrenheit)
- Not a replacement for NOAA for rigorous climate analysis

Best-Fit Workflows:
- domains/CLIMATE_RISK.md (weather context)
- Contextual weather overlay for any spatial analysis
- Event-based analysis (weather on a specific date)

Alternatives:
- NOAA CDO (free, authoritative, historical — preferred for analysis)
- Weather.gov API (free, U.S. only, forecast-focused)
- Visual Crossing (commercial, historical)

Sources:
- https://openweathermap.org/api
- https://openweathermap.org/current
- https://openweathermap.org/forecast5

Trust Level:
Medium — commercial aggregator, useful for context but not authoritative for research.
