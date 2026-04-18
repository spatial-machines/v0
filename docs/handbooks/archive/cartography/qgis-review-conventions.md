# Cartography Conventions — QGIS Review Packages

See also: [QGIS Project Contract](../../docs/QGIS_PROJECT_CONTRACT.md) for the full
review spec schema, field role taxonomy, and generation pipeline.

## Layer Naming
- use human-readable names: "South Dakota Census Tracts", not "sd_tracts_joined"
- include the geographic scope and data type in the name
- suffix with "(Demo Subset)" for partial/demo data layers

## Layer Roles
- **primary_analysis** — the main review layer; gets thematic styling
- **secondary_review** — supporting layers for cross-checking
- **reference** — context layers (boundaries, basemaps, labels)

## Layer Grouping
- **Review Layers**: primary and secondary analysis layers
- **Reference Layers**: context layers
- group names match layer roles; do not create ad-hoc groups

## Field Roles
Fields are auto-classified by `build_review_spec.py` from column names and types:
- **id**: identifiers (GEOID, FIPS) — not styled
- **label**: names (NAME, tract_name) — used for map labels when < 100 features
- **count**: population/totals (total_pop) — graduated, natural breaks, YlGnBu
- **percent**: rates/percentages (water_pct) — graduated, quantile, YlOrRd
- **area**: area metrics (land_area_sqm) — graduated, equal interval, Greens
- **measure**: other numeric fields — graduated, equal interval, Greens

## Thematic Styling
- the primary thematic field is auto-selected: percent > count > measure
- graduated renderer with 5 classes by default
- semi-transparent fill (alpha=200) with visible outlines (80,80,80)
- outline width: 0.26mm
- reviewers can restyle in QGIS; the initial map is a starting point, not final

## CRS Conventions
- set the project CRS to match the primary data layer (typically EPSG:4269 for Census data)
- do not reproject data during packaging — preserve the original CRS
- note the CRS in the review notes

## File Format Preferences
- GeoPackage (.gpkg) preferred for spatial data in review packages
- CSV for tabular summaries
- PNG for static maps and charts
- Markdown and HTML for reports

## Review Notes Requirements
Every review package must include:
- validation status (PASS / PASS WITH WARNINGS / REWORK NEEDED)
- list of all warnings with plain-language explanations
- data coverage notes (what percentage of features have full data per field)
- instructions for opening the package in QGIS
- suggested review order (which layers to inspect first)
- thematic field and symbology method used
