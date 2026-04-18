# Drive-Time and Service-Area Planning Domain

Purpose:
provide a navigation and cross-linking page for drive-time, travel-distance, and service-area planning questions built from the live accessibility and network canon
help analysts and agents route facility coverage, catchment, and reachability questions into the correct reusable workflows
define the current reusable canon coverage for service-area planning without inventing a dedicated routing-engine standard or travel-model methodology that does not yet exist in the repo

## Domain Scope

This domain covers planning work where the main question is how far people, sites, or facilities can reach over a travel network.

It includes:
- drive-time and travel-distance service areas
- facility catchment and coverage framing
- site comparison using network reachability
- demographic and POI enrichment within network-based access zones
- delivery routing for service-area outputs

It does not include:
- full route optimization or dispatch modeling
- transit-specific network methodology as a first-class workflow
- walking or biking network standards not already present in the repo
- proprietary routing-engine comparisons as a signed-off method layer

## Common Questions

- how many people are within a 10-minute drive of this facility?
- which areas fall outside current service coverage?
- how should multiple candidate sites be compared using drive-time coverage?
- when is a service area required instead of a simple Euclidean buffer?
- how should service-area outputs be reviewed before delivery?

## Common Workflow Sequences

### Sequence 1: facility coverage baseline

1. prepare facility locations through `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or validated existing geometry
2. run `workflows/SERVICE_AREA_ANALYSIS.md`
3. enrich with demographic or POI context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md` or `domains/POI_AND_BUSINESS_LANDSCAPE.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: candidate-site comparison

1. prepare candidate sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. run `workflows/SERVICE_AREA_ANALYSIS.md`
3. compare results in `domains/SITE_SELECTION_AND_SUITABILITY.md`
4. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: service-area plus facility context

1. run `workflows/SERVICE_AREA_ANALYSIS.md`
2. retrieve or normalize surrounding facilities through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
3. assemble outputs through `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
4. review maps with `qa-review/MAP_QA_CHECKLIST.md`

## Key Standards for This Domain

- `standards/CRS_SELECTION_STANDARD.md` — CRS and unit discipline for supporting geometry work
- `standards/SOURCE_READINESS_STANDARD.md` — readiness of facility, demographic, and contextual inputs
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling for service-area aggregates
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/SERVICE_AREA_ANALYSIS.md` — core network-based service-area workflow
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — facility/site preparation before service-area generation
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — service-area packaging and synthesis
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — comparison workflow when Euclidean distance is sufficient instead

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of service-area outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of coverage and reachability claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of service-area maps and delivery outputs

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client or analyst-supplied facility and site inputs
- `data-sources/REMOTE_FILES.md` — downloadable facility or context layers
- `data-sources/CENSUS_ACS.md` — demographic enrichment context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for summaries and delivery
- `data-sources/LOCAL_POSTGIS.md` — contextual layer support at scale
- `data-sources/OSM.md` — open geodata context for network-adjacent analysis

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — site prep, joins, and packaging
- `toolkits/POSTGIS_TOOLKIT.md` — scale and contextual summarization support
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support

## Domain-Specific Caveats

- service areas and Euclidean buffers answer different questions and should not be treated as interchangeable
- network outputs can appear more precise than the underlying routing assumptions justify
- service coverage does not automatically equal service adequacy or operational performance
- high-stakes coverage claims may need stronger review than the workflow alone implies

## Known Gaps in Current Canon

- there is no dedicated routing-engine standard or travel-time QA page yet
- transit, walking, and biking network analysis remain broader gaps beyond the core service-area workflow
- no route optimization or schedule-based accessibility workflow exists yet
- network-method comparison against proprietary tools is not yet a signed-off standard

## Adjacent Domains

- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
- `domains/PEDESTRIAN_AND_BICYCLE_ACCESS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
