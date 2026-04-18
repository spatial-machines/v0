# Public Asset Inventory and Service Coverage Domain

Purpose:
provide a navigation and cross-linking page for public asset cataloging, civic facility service coverage analysis, and public infrastructure accessibility mapping
help analysts and agents route public asset and service coverage questions into the correct reusable POI, accessibility, demographic, and delivery workflows
define the current reusable canon coverage for public asset work without inventing asset-management methodology or facility-priority scoring the repo does not yet contain

## Domain Scope

This domain covers work where the main question is what publicly owned or publicly serving assets exist, how well they cover the population, and where service gaps appear.

It includes:
- public asset inventory and mapping (libraries, schools, civic centers, fire stations, parks, public facilities)
- service coverage analysis using accessibility and demographic context
- public facility gap screening and underserved-area identification
- cross-routing to community facility, infrastructure, and emergency service domains
- delivery routing for public asset and coverage outputs

It does not include:
- sector-specific healthcare facility analysis (see `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`)
- emergency medical service response-time coverage (see `domains/EMERGENCY_MEDICAL_SERVICE_COVERAGE.md`)
- critical facility resilience screening (see `domains/CRITICAL_FACILITY_RESILIENCE.md`)
- asset condition assessment, maintenance scheduling, or capital improvement modeling
- parks and recreation as a primary focus (see `domains/PARKS_RECREATION_AND_OPEN_SPACE_ACCESS.md`)

## Common Questions

- what public facilities and civic assets exist in the study area?
- which populations are well-served or underserved by current public facility locations?
- how should public asset coverage be measured — by distance, drive-time, or population within reach?
- how do facility service areas overlap or leave gaps?
- how should public asset findings be reviewed and delivered for planning audiences?

## Common Workflow Sequences

### Sequence 1: public asset inventory and coverage baseline

1. intake or retrieve public facility locations through `workflows/POSTGIS_POI_LANDSCAPE.md` or `data-sources/LOCAL_FILES.md`
2. normalize facility categories with `workflows/POI_CATEGORY_NORMALIZATION.md`
3. generate coverage areas with `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. enrich with demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
6. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: service gap screening

1. prepare public asset coverage areas through the baseline sequence
2. overlay population distribution from `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
3. identify underserved areas and populations with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
4. if equity framing is needed, route through `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
5. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: multi-facility coverage comparison

1. inventory multiple asset types through `workflows/POSTGIS_POI_LANDSCAPE.md`
2. generate overlapping service areas with `workflows/SERVICE_AREA_ANALYSIS.md`
3. assemble comparison outputs with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
4. review maps with `qa-review/MAP_QA_CHECKLIST.md`
5. deliver through `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of facility inventories and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for coverage and accessibility work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed metrics in coverage summaries
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for service gap and coverage claims

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — public asset and facility extraction
- `workflows/POI_CATEGORY_NORMALIZATION.md` — facility category cleanup
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based coverage analysis
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean coverage analysis
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — facility location preparation
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment for coverage
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — population context for gap screening
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — coverage output packaging

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of coverage analysis outputs
- `qa-review/POI_EXTRACTION_QA.md` — validation of facility extraction and categorization
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of service gap and coverage claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of public asset and coverage maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — local facility and open geodata extraction
- `data-sources/OSM.md` — OSM-backed public facility and amenity context
- `data-sources/LOCAL_FILES.md` — client or agency-supplied facility inventories
- `data-sources/REMOTE_FILES.md` — downloadable public facility and asset tables
- `data-sources/CENSUS_ACS.md` — demographic context for coverage analysis
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and summarization for asset and coverage layers
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- public facility inventories are often incomplete, outdated, or inconsistently categorized across agencies
- service coverage measured by distance or drive-time does not guarantee service capacity, quality, or availability
- gap screening can overstate underservice if the facility inventory misses relevant assets or if the chosen coverage threshold is too narrow
- multi-facility coverage overlaps can create visual complexity that obscures rather than clarifies actual service patterns

## Known Gaps in Current Canon

- there is no dedicated public asset management standard or facility-priority methodology yet
- capacity analysis, utilization measurement, and condition assessment are not represented in the repo
- no dedicated facility coverage QA page exists beyond the general structural, POI, interpretive, and map layers
- asset categorization and cross-agency normalization workflows are not yet wiki-standardized
- level-of-service standards for different facility types are not yet first-class canon

## Adjacent Domains

- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/UTILITIES_AND_INFRASTRUCTURE_PLANNING.md`
- `domains/CRITICAL_FACILITY_RESILIENCE.md`
- `domains/PARKS_RECREATION_AND_OPEN_SPACE_ACCESS.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
