# Data Source Integration Benchmark

**Purpose:** Validate that all 20 data source fetch scripts work correctly — connecting to live APIs, downloading real data, producing valid output files and manifest sidecars.

**When to run:** After any changes to fetch scripts, API endpoint updates, or as part of a full benchmark round.

## Test Protocol

For each script:
1. Run with minimal valid arguments
2. Verify output file was created and is non-empty
3. Verify manifest JSON sidecar was created
4. Verify the output can be read (CSV parses, JSON parses, GeoJSON has features, etc.)
5. Score 0-3: 0=broken, 1=connects but bad output, 2=works with warnings, 3=clean pass

## Test Cases

### No-Auth Sources (should pass on any machine with internet)

| ID | Script | Test Command | Expected |
|---|---|---|---|
| DS-01 | `fetch_acs_data.py` | `--state 31 --variables B01001_001E --year 2022 -o /tmp/test_acs.csv` | CSV with GEOID + population |
| DS-02 | `retrieve_tiger.py` | `56 --year 2024 -o /tmp/test_tiger/` | ZIP with Wyoming tract shapefile |
| DS-03 | `fetch_census_population.py` | `31 -o /tmp/test_pop.csv` | CSV with Nebraska tract populations |
| DS-04 | `fetch_poi.py` | `--state NE --amenity hospital -o /tmp/test_poi.gpkg` | GeoPackage with hospital points |
| DS-05 | `fetch_ejscreen.py` | `--lat 41.26 --lon -95.94 --distance 1 -o /tmp/test_ej.json` | JSON with EJ indicators |
| DS-06 | `fetch_cdc_places.py` | `31 --measure DIABETES -o /tmp/test_cdc.csv` | CSV with diabetes rates by tract |
| DS-07 | `fetch_fema_nfhl.py` | `--bbox -96.1,41.2,-95.9,41.3 -o /tmp/test_flood.geojson` | GeoJSON with flood zones |
| DS-08 | `fetch_usda_food_access.py` | `--state-fips 31 -o /tmp/test_food.csv` | CSV with food access indicators |
| DS-09 | `fetch_lehd_lodes.py` | `ne --type wac --year 2021 -o /tmp/test_lehd.csv` | CSV with workplace employment |
| DS-10 | `fetch_usgs_elevation.py` | `--bbox -96.0,41.2,-95.9,41.3 -o /tmp/test_dem.tif` | GeoTIFF DEM tile |
| DS-11 | `fetch_gtfs.py` | `--url https://cdn.mbta.com/MBTA_GTFS.zip -o /tmp/test_gtfs.zip` | GTFS ZIP with stats |
| DS-12 | `fetch_socrata.py` | `--domain data.cdc.gov --dataset swc5-untb --where "stateabbr='NE'" --limit 100 -o /tmp/test_socrata.csv` | CSV with 100 records |
| DS-13 | `retrieve_remote.py` | Any public URL with a CSV/GeoJSON | Downloaded file + manifest |
| DS-14 | `retrieve_local.py` | A local file path | Copied file + manifest |

### Auth-Required Sources (need API keys in .env)

| ID | Script | Test Command | Expected | Key |
|---|---|---|---|---|
| DS-15 | `fetch_noaa_climate.py` | `--location FIPS:31 --start-date 2023-01-01 --end-date 2023-01-31 --datatypes TMAX,TMIN -o /tmp/test_noaa.csv` | CSV with weather data | NOAA_API_TOKEN |
| DS-16 | `fetch_bls_employment.py` | `--series LAUST310000000000003 --start-year 2022 --end-year 2023 -o /tmp/test_bls.csv` | CSV with unemployment rate | BLS_API_KEY (optional) |
| DS-17 | `fetch_fbi_crime.py` | `NE --offense violent-crime --start-year 2020 --end-year 2022 -o /tmp/test_fbi.csv` | CSV with crime stats | FBI_API_KEY |
| DS-18 | `fetch_openweather.py` | `--lat 41.26 --lon -95.94 -o /tmp/test_weather.json` | JSON with current weather | OPENWEATHER_API_KEY |
| DS-19 | `fetch_hud_data.py` | `--dataset fmr --state NE -o /tmp/test_hud.csv` | CSV with Fair Market Rents | HUD_API_KEY (optional) |
| DS-20 | `fetch_overture.py` | `--help-themes` (basic test) or direct URL download | Overture data | None |

## Scoring

| Score | Total | Result |
|---|---|---|
| 48-60 (80%+) | Strong pass — data layer is production-ready |
| 36-47 (60-79%) | Acceptable — most sources work, some need fixes |
| Below 36 | Needs work — significant API failures or broken scripts |

## Notes

- Auth-required tests should be skipped (not failed) when keys are missing
- Rate limiting may cause intermittent failures — retry once before scoring as failed
- Some APIs may be temporarily down — note in results, don't count as permanent failure
- USDA Food Access downloads a large file (~50MB) — may be slow on limited bandwidth
