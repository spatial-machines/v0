# TOOLS.md — Data Retrieval

Approved operational tools for the Data Retrieval role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`
- `docs/architecture/DATA_REUSE_POLICY.md`

## Primary Tool Classes

- `retrieval`
- `inspection`

## Approved Production Tools

### Census & Demographics
- `fetch_acs_data.py` — ACS 5-year (B/S/DP tables) by tract/county
- `fetch_census_population.py` — Decennial population counts
- `retrieve_tiger.py` — TIGER/Line boundary shapefiles
- `fetch_lehd_lodes.py` — LEHD/LODES employment (workplace/residence/OD)

### Points of Interest & Places
- `fetch_poi.py` — OpenStreetMap POI via Overpass API
- `fetch_overture.py` — Overture Maps (buildings, places, roads)

### Health & Environment
- `fetch_cdc_places.py` — CDC PLACES health outcomes by tract/county
- `fetch_ejscreen.py` — EPA EJScreen environmental justice indicators
- `fetch_usda_food_access.py` — USDA food desert indicators

### Hazards & Climate
- `fetch_fema_nfhl.py` — FEMA flood zone polygons
- `fetch_noaa_climate.py` — NOAA weather station observations
- `fetch_openweather.py` — OpenWeatherMap current/forecast

### Economic & Housing
- `fetch_bls_employment.py` — BLS employment/unemployment time series
- `fetch_hud_data.py` — HUD Fair Market Rents, income limits
- `fetch_fbi_crime.py` — FBI crime statistics by state

### Terrain
- `fetch_usgs_elevation.py` — USGS DEM elevation data

### Transit
- `fetch_gtfs.py` — GTFS transit feeds (routes, stops, schedules)

### Open Data & Generic
- `fetch_socrata.py` — Any Socrata-powered data portal
- `retrieve_remote.py` — Generic HTTP file download
- `retrieve_local.py` — Local file ingestion

### Geocoding
- `geocode_addresses.py` — Batch geocode addresses to point geometries

### Inventory & Inspection
- `search_project_inventory.py` — Search prior project data for reuse
- `build_project_inventory.py` — Build inventory for a project
- `inspect_dataset.py` — Inspect a dataset's schema and metadata

## Conditional / Secondary Tools

Use only when the workflow requires them:
- `fetch_poi_postgis.py` — PostGIS-backed POI queries (requires local PostGIS)

## Experimental Tools

These exist but are not default choices:
- geocoding fallbacks
- local database retrieval helpers (require PostGIS infrastructure)

If you need them, escalate first.

## Inputs You Depend On

- project brief
- retrieval instructions
- source handbooks
- data inventories and existing artifacts

## Outputs You Are Expected To Produce

- raw datasets
- manifests
- inspection summaries where needed
- retrieval provenance

## Operational Rules

- never skip the reuse-first check
- never treat reference-method docs as execution approval
- never store secrets or auth tokens in role-local files
- never present experimental routes as guaranteed capabilities
- when running Python tooling through the runtime exec surface, call the script directly
- do not use `cd ... && python ...`; use the correct working directory and a direct script command instead
- search prior project inventories before any new remote retrieval
- if a strong reuse candidate lacks `inventory.json`, build it before concluding it cannot be reused
- when reuse is chosen, record the reused source path and project origin in the retrieval provenance

## Reuse-First Command Pattern

Use direct commands such as:
- `python scripts/core/search_project_inventory.py --analyses-dir analyses --query "libraries"`
- `python scripts/core/build_project_inventory.py --project-dir analyses/<project-id>`

Use these before remote fetches unless the lead explicitly documents why a fresh pull is required.
