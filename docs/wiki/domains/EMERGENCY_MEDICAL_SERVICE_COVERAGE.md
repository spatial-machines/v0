# Emergency Medical Service Coverage Domain

Purpose:
provide a navigation and cross-linking page for emergency medical service coverage, response-area context, and high-stakes facility access routing
help analysts and agents route EMS coverage questions into the correct accessibility, demographic, facility, QA, and delivery canon
define the current reusable canon coverage for EMS-oriented spatial access work without inventing dispatch, travel-time standard, or emergency-response methodology the firm has not yet formalized

## Domain Scope

This domain covers spatial coverage questions involving emergency medical services, urgent response geographies, and high-stakes facility access.

It includes:
- EMS coverage and service-area framing
- facility and response-zone access analysis
- demographic context around emergency coverage gaps
- packaging EMS-oriented maps and summaries for review
- routing to the shared accessibility and facility canon that currently supports this work

It does not include:
- dispatch optimization or operational EMS modeling
- incident prediction, call-volume modeling, or ambulance deployment optimization
- formal response-time standards or service-level thresholds not already present in the repo
- broader healthcare-access work that is not response-oriented (see `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`)

## Common Questions

- which populations fall inside or outside existing EMS coverage zones?
- how should emergency coverage be represented when the underlying workflow is a service-area analysis?
- what demographic context matters when reviewing response-area inequities?
- how should high-stakes emergency coverage findings be reviewed before delivery?
- where does EMS coverage analysis end and operational dispatch modeling begin?

## Common Workflow Sequences

### Sequence 1: EMS coverage baseline

1. intake or validate EMS facility locations through `data-sources/LOCAL_FILES.md`, `data-sources/REMOTE_FILES.md`, or `domains/POI_AND_BUSINESS_LANDSCAPE.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. run `workflows/SERVICE_AREA_ANALYSIS.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review narrative and delivery risk with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: site and response-zone review

1. geocode or validate anchor locations through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. standardize facility and service inputs with `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
3. run `workflows/SERVICE_AREA_ANALYSIS.md`
4. route maps through `qa-review/MAP_QA_CHECKLIST.md`
5. continue into `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: community-risk context for EMS coverage

1. prepare demographic and neighborhood context through `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
2. overlay with EMS service areas or coverage outputs
3. review claims carefully with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
4. escalate to higher-stakes review framing when the output supports consequential planning or legal arguments

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of facility, demographic, and geography inputs
- `standards/CRS_SELECTION_STANDARD.md` — projected CRS discipline for service areas and joins
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling when coverage outputs are aggregated
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations when the work is challenge-prone or high-stakes
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/SERVICE_AREA_ANALYSIS.md` — core network-based EMS coverage workflow
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — address and site preparation when needed
- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — source cleanup and handoff preparation
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic context inventory
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level enrichment for coverage review

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of service areas and summaries
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of high-stakes coverage claims
- `qa-review/MAP_QA_CHECKLIST.md` — EMS map delivery review
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review gate when needed

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — analyst or client-supplied EMS facility inventories
- `data-sources/REMOTE_FILES.md` — downloadable public EMS facility tables
- `data-sources/CENSUS_ACS.md` — demographic context for service populations
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery
- `data-sources/LOCAL_POSTGIS.md` — local spatial support for facility and contextual layers
- `data-sources/OSM.md` — OSM-backed contextual geodata support

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, enrichment, and packaging
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale facility and spatial summary support
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and delivery support

## Domain-Specific Caveats

- EMS coverage questions are higher stakes than many other access analyses and can invite overclaiming if the workflow is treated as a proxy for operational performance
- service-area outputs do not automatically equal actual dispatch or real-world response performance
- high-stakes outputs may need legal-grade review or additional human judgment even when the base workflow is sound
- the current canon supports spatial coverage framing, not full emergency operations modeling

## Known Gaps in Current Canon

- there is no dedicated EMS-specific standard yet for response thresholds, dispatch assumptions, or operational service levels
- no incident prediction, station optimization, or ambulance deployment workflow exists yet
- there is no dedicated EMS QA page beyond the general structural, interpretive, map, and legal-grade layers
- public-safety and emergency-operations domains more broadly are still research-first areas in the taxonomy

## Adjacent Domains

- `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
- `domains/PROVIDER_NETWORK_AND_CLINIC_ACCESS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`
- `domains/DATA_ENGINEERING_AND_QA.md`

## Trust Level

Validated Domain Page
