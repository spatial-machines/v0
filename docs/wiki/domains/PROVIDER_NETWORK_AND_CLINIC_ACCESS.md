# Provider Network and Clinic Access Domain

Purpose:
provide a navigation and cross-linking page for clinic-network, provider-distribution, and care-access routing questions
help analysts and agents organize facility inventories, service coverage, and demographic context into a coherent provider-access workflow family
define the current reusable canon coverage for clinic and provider access without claiming network-capacity or payer-specific methodology the firm has not yet formalized

## Domain Scope

This domain covers facility and provider access work where the unit of analysis is a provider network, clinic fleet, or service footprint.

It includes:
- clinic and provider location inventory work
- network-coverage and service-area questions
- access comparison across sites or service footprints
- provider-context enrichment with demographic and tract-level indicators
- packaging clinic-access findings for review and delivery

It does not include:
- broader public-health framing as a top-level domain (see `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`)
- general POI extraction ownership (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- emergency-response coverage planning (see `domains/EMERGENCY_MEDICAL_SERVICE_COVERAGE.md`)
- provider capacity, claims, or utilization modeling

## Common Questions

- where are the existing clinics or providers in the study geography?
- how far do populations need to travel to reach a clinic or provider site?
- where are the gaps between provider presence and demographic need?
- how should clinic inventories be standardized before analysis?
- what is the cleanest route from provider list to defensible access maps and summaries?

## Common Workflow Sequences

### Sequence 1: clinic network baseline

1. intake the clinic or provider inventory through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. standardize and document the facility list with `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
3. geocode or validate site points with `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
4. run `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: clinic access + demographic need

1. build the clinic inventory and access layer through Sequence 1
2. prepare tract-level context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. use `workflows/TRACT_JOIN_AND_ENRICHMENT.md` where tract context must be joined to output geography
4. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
5. continue into `domains/CARTOGRAPHY_AND_DELIVERY.md` for review and reporting

### Sequence 3: provider landscape extraction from open sources

1. retrieve candidate facility points through `workflows/POSTGIS_POI_LANDSCAPE.md`
2. normalize categories through `workflows/POI_CATEGORY_NORMALIZATION.md` if needed
3. run access analysis with `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. review extraction plausibility with `qa-review/POI_EXTRACTION_QA.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — source readiness before provider reuse
- `standards/CRS_SELECTION_STANDARD.md` — projected CRS requirements for distance and service areas
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling when access outputs are aggregated
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — standardization and handoff preparation for provider lists
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — address and site-point preparation
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based access workflow
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean access workflow
- `workflows/POSTGIS_POI_LANDSCAPE.md` — open-source provider/facility extraction support
- `workflows/POI_CATEGORY_NORMALIZATION.md` — provider/facility category cleanup
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract context enrichment

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structure and field integrity checks
- `qa-review/POI_EXTRACTION_QA.md` — extraction review when open-source facility retrieval is used
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of provider-access claims and narratives
- `qa-review/MAP_QA_CHECKLIST.md` — delivery-map review when outputs are shared externally

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client or analyst-supplied provider inventories
- `data-sources/REMOTE_FILES.md` — downloadable provider or clinic tables
- `data-sources/LOCAL_POSTGIS.md` — local open geodata and facility extraction support
- `data-sources/OSM.md` — OSM-backed provider and clinic context
- `data-sources/CENSUS_ACS.md` — demographic need and service-area context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — geocoding support, joins, and packaging
- `toolkits/POSTGIS_TOOLKIT.md` — facility retrieval, scale, and spatial summarization
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and handoff support

## Domain-Specific Caveats

- provider inventories are often dirtier and more duplicated than they first appear
- category normalization can change the meaning of the network if handled loosely
- network access outputs can overstate service adequacy if provider capacity or specialty fit is not part of the workflow
- provider access should be framed as spatial access evidence, not a full healthcare system evaluation

## Known Gaps in Current Canon

- there is no dedicated workflow yet for provider capacity, specialty coverage, or network adequacy scoring
- payer-network and claims-based analysis are not first-class canon
- there is no provider-specific QA page yet beyond general structural, POI, and interpretive review
- internal provider-network maintenance and deduplication conventions are not yet a dedicated standard

## Adjacent Domains

- `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/EMERGENCY_MEDICAL_SERVICE_COVERAGE.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`

## Trust Level

Validated Domain Page
