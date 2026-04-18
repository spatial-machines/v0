# Parcel and Cadastral Data Source Page

Source Summary:
Parcel data (also called cadastral data) provides the property-level geographic layer for land ownership, land use, and development analysis.
Unlike Census or federal data, parcel data in the United States has no single authoritative national source. It is maintained at the county level by assessors, recorders, and GIS offices, making it one of the most fragmented and variable major data families in GIS work.
Parcel data is the foundation for land-use analysis, zoning constraint work, site selection, real estate context, and development planning.

Owner / Publisher:
primary: county assessors, county recorders, and county/municipal GIS offices
aggregated sources: several vendors and public initiatives aggregate county-level parcel data into regional or national datasets

Geography Support:
parcel-level: individual property boundaries with associated attributes
coverage is county-by-county: availability, quality, vintage, and attribute completeness vary dramatically
urban and suburban counties generally have better parcel GIS data than rural counties
some states have statewide parcel aggregation programs; others do not
no single download covers the entire U.S. at uniform quality

Time Coverage:
update frequency varies by county: some counties publish annually, others irregularly
assessment rolls typically reflect a specific tax year or assessment date
parcel boundaries may change due to subdivision, consolidation, annexation, or survey corrections
always confirm the vintage and update frequency for the specific county

Access Method:
county GIS open data portals: many counties publish parcel shapefiles or geodatabases
state GIS clearinghouses: some states aggregate county parcel data (e.g., Wisconsin, Minnesota, North Carolina)
regrid.com (formerly Loveland Technologies): national parcel aggregation with standardized schema (free tier available, premium tiers for bulk access)
CAMA (Computer-Assisted Mass Appraisal) databases: county assessor databases with detailed property attributes, sometimes available as open data
CoreLogic, ATTOM, Precisely (formerly Pitney Bowes): commercial parcel and property data with nationwide coverage, standardized attributes, and regular updates (licensing required)
direct request to county GIS office for jurisdictions without open data portals

File Formats:
shapefile and geodatabase are the most common distribution formats
GeoJSON and GeoPackage from some modern portals
CSV or DBF for attribute-only exports (requires join to geometry)
some counties distribute through ArcGIS Online or web map services only

Key Attribute Fields (vary by county):
- **APN / PIN / Parcel ID:** unique parcel identifier (format varies by county)
- **Owner name and mailing address:** from the assessment roll
- **Land use code:** county-assigned use classification (residential, commercial, industrial, agricultural, etc.)
- **Zoning designation:** may or may not be included in parcel data (sometimes in a separate zoning layer)
- **Assessed value (land and improvement):** from the assessment roll, not market value
- **Acreage / lot size:** parcel area from the GIS boundary or assessment record
- **Year built:** for improved parcels
- **Sale date and sale price:** from recorded transfers (availability and recency vary)
- **Legal description:** metes and bounds or subdivision reference

Licensing / Usage Notes:
varies by source: county open data is generally free for use but check each county's terms
commercial aggregators (CoreLogic, ATTOM, regrid premium) have licensing terms that restrict redistribution and may limit derived-product use
client-supplied parcel data retains the client's original usage terms
some counties restrict commercial use of their parcel data even when it is publicly downloadable — check the license
do not assume that open access equals unrestricted use

Known Caveats:
parcel data is fundamentally local — schema, attribute naming, land-use codes, and quality are not standardized across counties
land-use codes are county-defined: "commercial" in one county may include categories that another county splits into separate codes
parcel geometry may not align precisely with other layers (roads, buildings, imagery) due to different survey origins, datums, or digitization methods
assessment roll data reflects the assessor's records, which may lag behind real conditions (recent demolitions, new construction, ownership changes)
condominiums, stacked parcels, and common-area parcels create geometry and ownership complications that are not always resolved cleanly
parcel boundaries are legal constructs based on survey descriptions — GIS parcel geometry is an approximation of the legal boundary, not a substitute for a legal survey
some jurisdictions have parcel GIS data that is significantly out of date or has never been fully digitized
multi-county or multi-state projects require harmonizing different schemas, codes, and attribute conventions — this is often the most time-consuming part of parcel-based analysis
tax-exempt parcels (government, nonprofit, religious) may have incomplete attribute information

Best-Fit Workflows:
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md (parcel context assembly)
workflows/TRACT_JOIN_AND_ENRICHMENT.md (demographic context for parcel-adjacent analysis)
workflows/GEOCODE_BUFFER_ENRICHMENT.md (site-level parcel context)
workflows/WITHIN_DISTANCE_ENRICHMENT.md (proximity enrichment around parcels or sites)

Best-Fit Domains:
domains/LAND_USE_AND_PARCEL_ANALYSIS.md
domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md
domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md
domains/SITE_SELECTION_AND_SUITABILITY.md
domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md

Alternatives:
Microsoft Building Footprints: open building footprint data derived from imagery (geometry only, no ownership or assessment attributes)
OSM land-use and building layers: community-mapped, variable completeness, no assessment data
county zoning layers: sometimes published separately from parcel data, with different geometry
state tax databases: some states publish statewide assessment rolls without GIS geometry
USDA CropScape / CDL for agricultural land-use classification (not parcel-based, satellite-derived)

Sources:
county assessor and GIS office websites (varies by jurisdiction)
regrid.com (national parcel aggregation)
state GIS clearinghouse websites
CoreLogic, ATTOM, Precisely (commercial aggregators)
National Parcels Dataset concept — note that no single authoritative national parcel dataset exists yet, though federal efforts have been discussed

Trust Level:
Validated Source Page
Needs Source Validation (quality, vintage, and attribute completeness vary by county)
