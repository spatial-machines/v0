# Source Handbook — US Census / TIGER

## Purpose
Retrieve Census Bureau geography files and associated tabular data for US geographic analysis.

## Coverage
- geography levels: nation, state, county, tract, block group, place, and more depending on endpoint/file
- temporal coverage: varies by vintage
- subject matter: boundaries and Census tabular attributes

## Access
- auth required: Census API key recommended for tabular API access
- credential location: environment variable `CENSUS_API_KEY`
- rate limits: Census API usage limits apply
- base URLs:
  - TIGER/Line: `https://www2.census.gov/geo/tiger/`
  - Census API: `https://api.census.gov/data/`

## Retrieval Method
- preferred method:
  - boundary files: download ZIP from TIGER/Line into `data/raw/`
  - tabular data: API request via Census API
- fallback method:
  - manual download into `data/raw/`
- expected formats:
  - zip (shapefile archives)
  - json/csv-style API responses

## Key Fields / Schema Notes
- primary identifiers:
  - GEOID
  - STATEFP
  - COUNTYFP
  - TRACTCE
  - BLKGRPCE
- important columns: geography-specific
- geometry notes: usually polygon boundaries in shapefile archives
- CRS notes: inspect downloaded geometries and reproject as needed for analysis

## Example Requests
- Download 2024 tract boundaries for Nebraska
- Retrieve ACS variables for county-level analysis

## QA Checks
- vintage recorded
- geography level recorded
- state/county filters recorded
- ZIP file readable after download
- join key strategy documented

## Known Pitfalls
- direct remote reads may fail; download first
- geography naming and FIPS construction must be handled carefully
- vintage mismatches between boundary and tabular data can break joins
- ACS variable selection needs explicit documentation

## Notes / Lessons
- Always record vintage and geography level. Avoid silent joins across mismatched vintages.
