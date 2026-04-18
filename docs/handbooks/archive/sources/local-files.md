# Source Handbook — Local Files

## Purpose
Use local files already present in the project workspace or explicitly provided by the user.

## Coverage
- geography levels: any, depending on supplied data
- temporal coverage: varies by file
- subject matter: varies by file

## Access
- auth required: no
- credential location: n/a
- rate limits: none
- base path: project workspace or user-supplied path

## Retrieval Method
- preferred method: validate path and inspect file format in place
- fallback method: copy file into `data/raw/` if source is external to project structure
- expected formats:
  - csv
  - xlsx/xls
  - parquet
  - geojson
  - gpkg
  - shp (or zipped shapefile)
  - json

## Key Fields / Schema Notes
- primary identifiers: determined per dataset
- important columns: determined per dataset
- geometry notes: inspect if spatial
- CRS notes: inspect if spatial

## Example Requests
- Load the CSV at `data/raw/example.csv`
- Inspect the GeoPackage in `data/raw/parcels.gpkg`

## QA Checks
- file exists
- extension/type recognized
- readable by appropriate library
- geometry and CRS inspected when spatial

## Known Pitfalls
- shapefiles often require sidecar files
- CSVs may not include explicit geography metadata
- Excel sheets may require sheet selection

## Notes / Lessons
- Prefer copying ad hoc source files into `data/raw/` for reproducibility.
