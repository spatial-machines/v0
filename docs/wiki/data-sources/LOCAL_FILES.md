# Local Files Source Page

Source Summary:
covers any data file already present in the project workspace or provided directly by the user
this is a category-level source page, not a named external data provider
local files are the most variable source class: format, schema, CRS, and quality are unknown until inspection
prefer this page when the input is already on disk; prefer `data-sources/REMOTE_FILES.md` when the file must first be downloaded

Owner / Publisher:
varies: client, user, another pipeline stage, or an external download already completed
provenance must be reconstructed from whatever the supplier provided

Geography Support:
determined per dataset after inspection
no assumptions about coverage, level, or projection are valid until the file has been opened

Time Coverage:
determined per dataset
must be documented during intake; do not infer vintage from filename alone

Access Method:
Fetch Script:
`scripts/core/retrieve_local.py` — ingest a local file with manifest and provenance
Usage:
validate that the file exists at the declared path
if the file is outside the project directory, copy it into `data/raw/` before any further work
if the file is already in `data/raw/`, validate in place and do not move it
never modify files in `data/raw/`; write any cleaned or reprojected version to `data/interim/` per `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`

Supported Formats:
CSV
XLSX / XLS (may require sheet selection)
Parquet
GeoJSON
GeoPackage (.gpkg)
Shapefile (.shp, typically zipped; requires sidecar files)
JSON
other formats on a case-by-case basis after toolchain confirmation

Licensing / Usage Notes:
depends entirely on the source; document any known restrictions
client-supplied files may have distribution restrictions and must not be loaded into the firm's shared PostGIS database
files arriving without a license note should be treated as restricted until clarified

QA Checks (source-specific):
1. file exists at the declared path
2. extension and format are recognized by the expected library
3. file is readable: not corrupt, not password-protected, not truncated
4. if spatial: geometry column is present, CRS is inspected and the EPSG code is recorded per `standards/CRS_SELECTION_STANDARD.md`
5. if tabular: column names, types, and row count are recorded
6. if zipped: archive extracts cleanly and contents are inventoried
7. character encoding is confirmed (UTF-8 unless documented otherwise)

Known Pitfalls:
shapefiles require .shx, .dbf, and .prj sidecar files; missing sidecars cause silent failures or unprojected geometry
CSVs may lack explicit geography metadata; do not assume spatial intent without a geometry column
Excel files may contain multiple sheets; always confirm which sheet to use and record that decision
file encoding issues (non-UTF-8) can corrupt field names or values without raising errors
ad hoc files placed outside `data/raw/` break reproducibility; copy them in first, then work from the canonical path
files supplied without a sidecar README or column dictionary should be queried with the supplier before being treated as production-ready
filenames are not provenance — do not infer vintage, units, or geography from a filename

Source Readiness Tier Guidance:
if provenance is fully documented and quality has been confirmed: Tier 1 or Tier 2
if provenance is partial or quality is unverified: Tier 3 (Provisional)
if nothing is known about the file beyond its bytes: Tier 4 (Unreviewed); escalate before using
see `standards/SOURCE_READINESS_STANDARD.md` for tier definitions and their consequences

Retrieval Contract:
this page covers source-specific intake for local files
for the general retrieval workflow (manifest writing, run provenance, handoff to processing), see `workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md`
do not redefine manifest or provenance schema on this page

Best-Fit Workflows:
any workflow that accepts user-supplied or pre-staged data
`workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` for cleaning, normalization, and join preparation after intake
`workflows/TRACT_JOIN_AND_ENRICHMENT.md` when the local file is a CSV or GeoPackage to be joined to Census tract geometry
`workflows/GEOCODE_BUFFER_ENRICHMENT.md` when the local file is an address list

Alternatives:
if the file is a known Census product (ACS table, TIGER shapefile), prefer `data-sources/CENSUS_ACS.md` or `data-sources/TIGER_GEOMETRY.md` for retrieval guidance instead of treating it as a generic local file
if the file is a client-supplied DEM, prefer `data-sources/CLIENT_SUPPLIED_DEMS.md` for the specialized intake validation process
if the file must be downloaded from a URL first, prefer `data-sources/REMOTE_FILES.md`
if the data lives in the firm's spatial warehouse, prefer `data-sources/LOCAL_POSTGIS.md`

Sources:
firm intake methodology notes
GDAL / OGR vector driver documentation (https://gdal.org/drivers/vector/)
GeoPandas read_file documentation
pandas read_csv and read_excel documentation

Trust Level:
Validated Source Page
Needs Source Validation (quality, provenance, and format vary per file)
