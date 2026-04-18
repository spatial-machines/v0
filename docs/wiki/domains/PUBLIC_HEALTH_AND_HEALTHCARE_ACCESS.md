# Public Health and Healthcare Access Domain

Purpose:
provide a navigation and cross-linking page for healthcare access, service coverage, demographic vulnerability, and facility-context analysis
help analysts and agents move from public-health questions to the right accessibility, demographic, POI, and delivery canon
define the current reusable canon coverage for healthcare access work without inventing domain-specific health methodology the firm has not yet formalized

## Domain Scope

This domain covers recurring public-health and healthcare-access work where the core analytical question is about who can reach what care, where service coverage is weak, and how facility context relates to population need.

It includes:
- healthcare access and coverage framing
- clinic, provider, and facility accessibility analysis
- demographic context for healthcare need and inequity
- service-area and within-distance analysis for health-serving facilities
- health-oriented delivery and review routing

It does not include:
- formal epidemiology or disease-model methodology
- medical quality or claims-based healthcare analytics
- facility inventory extraction as a standalone POI domain (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- general accessibility method ownership (see `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`)

## Common Questions

- which populations are underserved by existing healthcare facilities?
- how many people fall inside or outside a drive-time or distance threshold for care?
- where do facility locations and demographic vulnerability overlap?
- what is the cleanest way to combine healthcare facilities, service areas, and tract-level demographic context?
- what review steps are needed before healthcare-access findings are delivered externally?

## Common Workflow Sequences

### Sequence 1: healthcare access baseline

1. confirm source readiness with `standards/SOURCE_READINESS_STANDARD.md`
2. prepare facility locations through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
3. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
4. run `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md` as appropriate
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md` and `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: site-based healthcare context analysis

1. geocode or validate site points with `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. prepare surrounding healthcare POIs with `workflows/POSTGIS_POI_LANDSCAPE.md`
3. enrich with demographic context using `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
4. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` or `workflows/SERVICE_AREA_ANALYSIS.md`
5. continue into `domains/CARTOGRAPHY_AND_DELIVERY.md` for reporting and review-site delivery

### Sequence 3: provider network review

1. intake provider or facility source data through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. standardize and validate with `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
3. use `workflows/SERVICE_AREA_ANALYSIS.md` for travel-based coverage where needed
4. review narrative claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — source-tier and reuse readiness
- `standards/CRS_SELECTION_STANDARD.md` — projected CRS discipline for buffering and access work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed summary metrics
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based healthcare access workflow
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean access and coverage enrichment
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site and address preparation
- `workflows/POSTGIS_POI_LANDSCAPE.md` — facility and provider landscape extraction
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic context enrichment
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — general analysis-stage framing this domain specializes

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of facilities, service areas, and summaries
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of access claims and narrative framing
- `qa-review/MAP_QA_CHECKLIST.md` — delivery-map review when outputs become public-facing artifacts

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — demographic context and tract-level indicators
- `data-sources/TIGER_GEOMETRY.md` — tract and boundary geometry for enrichment and delivery
- `data-sources/LOCAL_POSTGIS.md` — local facility and open geodata support
- `data-sources/OSM.md` — OSM-backed facility context and road-network-adjacent support
- `data-sources/LOCAL_FILES.md` — provider lists or client-supplied facility inventories
- `data-sources/REMOTE_FILES.md` — downloadable provider or facility tables

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — facility extraction, spatial summaries, and larger-scale joins
- `toolkits/GEOPANDAS_TOOLKIT.md` — geocoded point handling, joins, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and delivery support

## Domain-Specific Caveats

- healthcare access questions often mix facility supply, population need, and travel assumptions, so workflow choice matters
- Euclidean and network travel measures answer different questions and should not be treated as interchangeable
- public-health framing can drift into policy or causal claims unless interpretation stays bounded by the actual workflow outputs
- provider lists and facility inventories often require strong standardization before they are trustworthy enough for access analysis

## Known Gaps in Current Canon

- there is no healthcare-specific review checklist yet beyond the general structural and interpretive layers
- there is no dedicated workflow yet for provider capacity, utilization, or medical specialty differentiation
- transit-based healthcare access is not yet first-class canon
- public-health-specific uncertainty and disparity framing is still routed through broader demographic and accessibility canon rather than a dedicated standard

## Adjacent Domains

- `domains/PROVIDER_NETWORK_AND_CLINIC_ACCESS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/EMERGENCY_MEDICAL_SERVICE_COVERAGE.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
