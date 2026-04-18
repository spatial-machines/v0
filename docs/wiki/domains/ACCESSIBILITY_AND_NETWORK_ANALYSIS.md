# Accessibility and Network Analysis Domain

Purpose:
provide a navigation and cross-linking page for geocoding, buffering, within-distance enrichment, and network-based service-area analysis
help analysts and agents route location-access, coverage, and catchment questions to the correct workflow family
define the current reusable canon coverage for Euclidean and network-based accessibility analysis

## Domain Scope

This domain covers location-based access, distance, catchment, and coverage analysis.

It includes:
- geocoding and site-point preparation
- Euclidean buffer-based enrichment
- network-based service-area analysis and isochrone generation
- site comparison and accessibility context analysis
- routing to demographic and POI enrichment workflows that operate inside those distance zones

It does not include:
- POI extraction as a source family in its own right (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- demographic source ownership and tract aggregation logic (see `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`)
- general QA and processing conventions shared across all analyses (see `domains/DATA_ENGINEERING_AND_QA.md`)
- delivery and packaging workflows (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)

## Common Questions

- what is within 1, 3, or 5 miles of a site?
- how many people or facilities are within a 10-minute drive?
- where are the gaps in service coverage?
- when should a project use Euclidean distance versus a true network-based service area?
- what review steps are needed before accessibility claims are shared externally?

## Common Workflow Sequences

### Sequence 1: address-to-buffer enrichment

1. confirm the working CRS with `standards/CRS_SELECTION_STANDARD.md`
2. run `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
3. if reusable enrichment logic is needed across many targets, use `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. if the output supports client claims, review with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: drive-time or travel-distance accessibility

1. validate site points or addresses with `workflows/GEOCODE_BUFFER_ENRICHMENT.md` Phase 1 if needed
2. confirm that the project requires network travel rather than Euclidean distance
3. run `workflows/SERVICE_AREA_ANALYSIS.md`
4. enrich with demographic or POI context using the approved layers
5. validate structure with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
6. continue into `domains/CARTOGRAPHY_AND_DELIVERY.md` for packaging and publication if needed

### Sequence 3: accessibility + market or POI context

1. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. prepare POI context through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
3. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` or `workflows/SERVICE_AREA_ANALYSIS.md` as appropriate
4. validate narrative claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

## Key Standards for This Domain

- `standards/CRS_SELECTION_STANDARD.md` — projected-CRS and unit discipline
- `standards/SOURCE_READINESS_STANDARD.md` — readiness and source-tier rules for enrichment layers
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling partial overlaps and mixed metrics
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack routing and enrichment tools

## Key Workflows for This Domain

- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — address-to-buffer enrichment workflow
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — reusable Euclidean distance enrichment workflow
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based service-area workflow
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — general analytical packaging this domain specializes

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of service areas and summaries
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — claims review for accessibility findings
- `qa-review/MAP_QA_CHECKLIST.md` — map review when accessibility outputs are turned into deliverables

## Key Data Sources for This Domain

- `data-sources/OSM.md` — road and open geodata context for routing-adjacent work
- `data-sources/LOCAL_POSTGIS.md` — local spatial database support for enrichment and network-adjacent analysis
- `data-sources/CENSUS_ACS.md` — demographic enrichment source
- `data-sources/TIGER_GEOMETRY.md` — tract / boundary support for enrichment and rollup

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — database-native enrichment and spatial selection support
- `toolkits/GEOPANDAS_TOOLKIT.md` — geocoded point handling, spatial joins, and summary prep
- `toolkits/GDAL_OGR_TOOLKIT.md` — format conversion and packaging support

## Domain-Specific Caveats

- Euclidean buffers and network service areas answer different questions and are not interchangeable
- accessibility outputs can appear authoritative even when the routing engine, network vintage, or allocation method is weakly documented
- enrichment method matters as much as distance threshold, especially for partial-tract demographic summaries
- walking, biking, and transit analysis have different data-quality risks than simple driving isochrones

## Known Gaps in Current Canon

- there is no dedicated workflow yet for route analysis, corridor analysis, or transit accessibility
- no domain page exists yet for public health access or public facility coverage, even though this domain will often support them
- network QA is still embedded in workflows rather than expressed as a standalone QA page
- travel-time benchmarking against proprietary reference tools is not yet formalized as canon

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/DATA_ENGINEERING_AND_QA.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
