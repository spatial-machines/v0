# NOAA Climate Data Source Page

Source Summary:
NOAA's Climate Data Online (CDO) provides weather station observations including temperature, precipitation, wind, snowfall, and other meteorological variables. Covers thousands of U.S. and global weather stations.

Owner / Publisher:
National Oceanic and Atmospheric Administration (NOAA), National Centers for Environmental Information (NCEI)

Geography Support:
Weather station locations (point data). Can be queried by state FIPS, county FIPS, ZIP code, or city ID.

Time Coverage:
Historical daily data (GHCND) from 1890s+. Monthly summaries (GSOM) and annual summaries (GSOY) also available.

Access Method:
REST API with token authentication. Use `fetch_noaa_climate.py` for retrieval.

Fetch Script:
`scripts/core/fetch_noaa_climate.py`

Example:
```bash
python scripts/core/fetch_noaa_climate.py --location FIPS:20 \
    --start-date 2023-01-01 --end-date 2023-12-31 \
    --datatypes TMAX,TMIN,PRCP -o data/raw/ks_climate_2023.csv

python scripts/core/fetch_noaa_climate.py --location CITY:US130077 \
    --dataset GSOM --start-date 2023-01-01 --end-date 2023-12-31 \
    -o data/raw/atlanta_monthly_2023.csv
```

Credentials:
Required — free token from https://www.ncdc.noaa.gov/cdo-web/token (NOAA_API_TOKEN in .env). Token is emailed instantly.

Licensing / Usage Notes:
Public federal data.

Known Caveats:
- Not all stations report all variables — coverage varies by location and time
- Daily data (GHCND) can be very large for state-level queries over long periods
- Temperature values are in tenths of degrees Celsius in raw GHCND (the API returns standard units)
- Station metadata changes over time (relocations, equipment upgrades)
- API has a 1000-record page limit — pagination required for large queries

Key Datasets:
- **GHCND** — Global Historical Climatology Network Daily: daily station observations
- **GSOM** — Global Summary of the Month: monthly aggregates
- **GSOY** — Global Summary of the Year: annual aggregates

Key Data Types:
- TMAX, TMIN — daily max/min temperature
- PRCP — daily precipitation
- SNOW — daily snowfall
- SNWD — snow depth
- AWND — average daily wind speed

Best-Fit Workflows:
- domains/CLIMATE_RISK.md
- domains/ENVIRONMENTAL_JUSTICE.md
- workflows/TEMPORAL_PATTERN_ANALYSIS.md

Alternatives:
- OpenWeatherMap (current/forecast, not historical)
- PRISM Climate Group (gridded interpolated data)
- ERA5 reanalysis (global gridded, via Copernicus)

Sources:
- https://www.ncei.noaa.gov/cdo-web/
- API docs: https://www.ncdc.noaa.gov/cdo-web/webservices/v2

Trust Level:
High — NOAA NCEI is the authoritative source for U.S. climate observations.
