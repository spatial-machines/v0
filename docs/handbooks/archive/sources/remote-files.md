# Source Handbook — Remote Files

## Purpose
Retrieve directly downloadable files from URLs.

## Coverage
- geography levels: varies by file
- temporal coverage: varies by source
- subject matter: varies by source

## Access
- auth required: usually no for public files
- credential location: if required, use environment/config rather than hardcoding
- rate limits: source-specific
- base URL or access path: varies

## Retrieval Method
- preferred method: HTTP GET with streamed download into `data/raw/`
- fallback method: manual download and placement into `data/raw/`
- expected formats:
  - csv
  - geojson
  - json
  - zip
  - gpkg
  - parquet

## Key Fields / Schema Notes
- primary identifiers: source-specific
- important columns: source-specific
- geometry notes: inspect after download
- CRS notes: inspect after download

## Example Requests
- Download a zipped shapefile from a URL
- Download a CSV from a public GitHub raw URL

## QA Checks
- HTTP status is 200-range
- file saved successfully
- content length recorded when available
- readable after download
- provenance recorded with URL and timestamp

## Known Pitfalls
- some servers block direct remote reads by geospatial libraries
- zip archives may contain nested directories
- filename may need to be inferred from URL
- remote source may change or disappear

## Notes / Lessons
- Prefer downloading first, then loading locally rather than reading directly from remote URLs.
