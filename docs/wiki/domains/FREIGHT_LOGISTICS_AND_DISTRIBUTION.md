# Freight, Logistics, and Distribution Domain

Purpose:
provide a navigation and cross-linking page for freight-oriented site context, distribution reach, and logistics-support questions built from the live parcel, access, demographic, and POI canon
help analysts and agents route freight and distribution questions into the correct reusable workflows without inventing a dedicated logistics optimization methodology that does not yet exist in the repo
define the current reusable canon coverage for freight and distribution as a routing and context layer rather than a full operations model

## Domain Scope

This domain covers analysis where the question is how freight-serving sites, logistics locations, or distribution footprints relate to parcels, access, destinations, and surrounding context.

It includes:
- freight-oriented site context and access framing
- distribution and logistics location screening
- parcel, access, and amenity context around logistics sites
- delivery routing for freight-oriented maps and summaries
- cross-routing to site-selection and development-context canon

It does not include:
- route optimization or fleet operations modeling
- freight network assignment or travel-demand methodology
- warehouse underwriting or industrial valuation methodology
- engineering design or transportation operations analysis

## Common Questions

- how should a freight or logistics site be contextualized spatially?
- which access and parcel-context factors can the current canon support for distribution questions?
- how should candidate logistics sites be compared using live workflows?
- what can be said defensibly about freight context without implying a full logistics model?
- how should freight-oriented outputs be reviewed before delivery?

## Common Workflow Sequences

### Sequence 1: logistics site baseline

1. assemble parcel or site geometry through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
2. prepare access context through `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md` or `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
3. add surrounding POI and facility context through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. route final outputs through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: freight candidate-site comparison

1. prepare candidate sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. add parcel and zoning context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md` and `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
3. use `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md` as appropriate
4. package outputs through `domains/SITE_SELECTION_AND_SUITABILITY.md`
5. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: freight-supporting demographic context

1. prepare site and access outputs through the sequences above
2. add demographic or labor-context support through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md` when appropriate
3. state clearly when the result is contextual support rather than full labor-shed or freight-demand analysis

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of parcel, access, and contextual layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for site, buffer, and overlay work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — mixed summary handling in freight context outputs
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential site and logistics claims
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation from address or named location inputs
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based site and distribution reach workflow
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearby context screening around freight sites
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — packaging freight-context outputs

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of freight-context outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of logistics and distribution claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of freight-oriented site maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — site, parcel, and freight-related layers supplied by client or analyst
- `data-sources/REMOTE_FILES.md` — downloadable industrial, freight, or policy layers
- `data-sources/LOCAL_POSTGIS.md` — local contextual extraction and summarization support
- `data-sources/OSM.md` — open geodata context for facilities, roads, and destinations
- `data-sources/CENSUS_ACS.md` — demographic or labor-context support when appropriate
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — contextual extraction and spatial summarization at scale
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support

## Domain-Specific Caveats

- freight and logistics outputs can look operational even when they are really contextual screening products
- access context does not automatically equal freight performance or suitability for operations
- parcel, zoning, and access layers often need to be interpreted together, but the current canon does not yet formalize that as a dedicated scoring method
- the strongest current use of this domain is site and context framing, not full logistics optimization

## Known Gaps in Current Canon

- there is no dedicated freight workflow, route-optimization workflow, or logistics standard yet
- labor-shed and distribution-demand analysis remain future canon gaps
- there is no freight-specific QA page beyond the general structural, interpretive, and map layers
- industrial and warehouse-specific development methodology is not yet a signed-off standards stack

## Adjacent Domains

- `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
