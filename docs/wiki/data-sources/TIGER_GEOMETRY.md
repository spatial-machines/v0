# TIGER / Census Geometry Source Page

Source Summary:
TIGER / Line shapefiles and related boundary files are the Census Bureau's official geographic framework for Census tabulations.
The firm uses TIGER geometry as the default boundary layer for tracts, block groups, counties, places, ZCTAs, and other Census geographies.
TIGER is not a data source for demographic attributes. It provides geometry only. Attributes come from ACS, decennial Census, or other tabular products joined to TIGER geometry.
Owner / Publisher:
U.S. Census Bureau, Geography Division
Geography Support:
nation, state, county, tract, block group, block, place, ZCTA, congressional district, school district, and many more
available for the full United States, Puerto Rico, and island areas
Time Coverage:
annual TIGER / Line releases aligned with ACS and Census vintage years
2020 TIGER reflects 2020 Census geography; 2022 TIGER reflects the 2022 ACS vintage
older vintages available back through 2007 for some geographies
tract and block-group boundaries can change between decennial cycles (boundary updates occur, especially post-2020)
Access Method:
direct download from Census Bureau FTP / web (https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)
Census Bureau cartographic boundary files (simplified, smaller, clipped to shoreline) as an alternative for mapping
Fetch Script:
`scripts/core/retrieve_tiger.py` — download TIGER tract/county shapefiles by state FIPS
File Formats:
shapefile (default TIGER / Line distribution)
cartographic boundary files also available as shapefile, GeoJSON, or KML
convert to GeoPackage or PostGIS on ingestion for firm use
Licensing / Usage Notes:
public domain federal data, no usage restrictions
attribution to U.S. Census Bureau is standard practice
Known Caveats:
TIGER geometry includes water-only areas and other non-populated features; filter as needed
TIGER boundaries are not clipped to shoreline by default; use cartographic boundary files if shoreline clipping matters for mapping
tract and block-group boundaries can change between vintages; always match geometry vintage to data vintage
ZCTA geometry is Census-defined and does not align perfectly with USPS ZIP code delivery routes
TIGER shapefiles use NAD83 (EPSG:4269) as the native CRS
large shapefiles (national-level tracts) can be slow to load; scope downloads to the relevant state or county FIPS
Key Identifier Fields:
TIGER attribute tables use a consistent set of FIPS-based identifier columns. Downstream join workflows need these by name:
GEOID
— the full FIPS string for the feature (11 characters for tract, 12 for block group, 5 for county, 2 for state); the canonical join key for merging with ACS or decennial tabular data
STATEFP
— 2-character state FIPS code
COUNTYFP
— 3-character county FIPS code
TRACTCE
— 6-character census tract code (within the parent county)
BLKGRPCE
— 1-character block group code (within the parent tract)
NAME
— human-readable name (varies by geography level)
Always cast GEOID to string and zero-pad before joining to tabular data per
workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md
and
workflows/TRACT_JOIN_AND_ENRICHMENT.md
Best-Fit Workflows:
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/DECADE_TREND_ANALYSIS.md
workflows/GEOCODE_BUFFER_ENRICHMENT.md
Alternatives:
cartographic boundary files: simplified geometry, clipped to shoreline, better for mapping but less precise for analysis
Census Bureau API geometry endpoints: limited geometry availability, useful for lightweight queries
third-party pre-processed Census geometry (use with caution; verify vintage and provenance)
Sources:
https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
Census Bureau TIGER / Line technical documentation
Census Bureau Geographic Areas Reference Manual
Trust Level:
Production Source Page
