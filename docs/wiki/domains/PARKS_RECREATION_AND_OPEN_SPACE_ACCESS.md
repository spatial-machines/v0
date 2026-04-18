# Parks, Recreation, and Open Space Access Domain

Purpose:
provide a navigation and cross-linking page for park access, recreation access, and open-space context analysis built from live accessibility, demographic, POI, and delivery canon
help analysts and agents route parks and open-space questions into the correct reusable workflows without inventing a dedicated parks-planning standard that does not yet exist in the repo
define the current reusable canon coverage for parks and open-space access as a routing layer for community-serving place analysis

## Domain Scope

This domain covers work where the question is how people reach parks, recreation assets, or open-space resources and how those resources are distributed relative to population context.

It includes:
- park and recreation access framing
- demographic context for open-space access questions
- location and facility context for community-serving open space
- map and review routing for park-access outputs
- cross-routing to accessibility, community-facility, and development-context canon

It does not include:
- park programming or service-quality evaluation
- ecological habitat or conservation methodology beyond access framing
- trail-network modeling or recreation-demand forecasting not already present in the wiki
- a dedicated parks-planning standard or level-of-service method

## Common Questions

- how far are people from parks or recreation assets?
- which populations appear underserved by current open-space access?
- how should park locations and demographic context be combined into one deliverable?
- when is a simple distance approach enough, and when is a network-based workflow better?
- how should park-access outputs be reviewed before public delivery?

## Common Workflow Sequences

### Sequence 1: park access baseline

1. retrieve or intake park and open-space locations through `domains/POI_AND_BUSINESS_LANDSCAPE.md` or `data-sources/LOCAL_FILES.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` or `workflows/SERVICE_AREA_ANALYSIS.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretation with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: candidate park or recreation site review

1. prepare sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. add nearby community context through `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
3. add tract-level demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
4. route final outputs through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: community-facility crossover

1. use this domain for park and open-space access framing
2. route broader public-serving asset questions into `domains/COMMUNITY_FACILITY_PLANNING.md`
3. use `qa-review/MAP_QA_CHECKLIST.md` for public-facing maps and access exhibits

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of park, tract, and contextual inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for distance and access workflows
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — mixed-metric handling in access summaries
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean park-access workflow
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based park-access workflow
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation for candidate access studies
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic context enrichment
- `workflows/POSTGIS_POI_LANDSCAPE.md` — open-source park and amenity extraction support

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structure and geometry integrity checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of access and equity claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of park and open-space maps
- `qa-review/POI_EXTRACTION_QA.md` — extraction review when open-source park locations are used

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — local contextual and amenity extraction support
- `data-sources/OSM.md` — OSM-backed parks and amenity context
- `data-sources/CENSUS_ACS.md` — demographic and vulnerability context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery
- `data-sources/LOCAL_FILES.md` — client or analyst-supplied park and open-space layers
- `data-sources/REMOTE_FILES.md` — downloadable parks, recreation, or open-space layers

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — park and amenity extraction support at scale
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, enrichment, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support

## Domain-Specific Caveats

- park access questions can overstate equity conclusions if the workflow treats all parks or open-space resources as equivalent
- Euclidean and network access measures answer different planning questions and should not be conflated
- OSM or open-source amenity data may need validation before it becomes a defensible park inventory
- parks and open-space access often intersects with community-facility and development questions, so domain boundaries should stay explicit

## Known Gaps in Current Canon

- there is no dedicated parks-planning or open-space standard yet
- no first-class trail-network, recreation-demand, or park level-of-service workflow exists yet
- there is no parks-specific QA page beyond the general structural, interpretive, map, and POI layers
- ecological and conservation-oriented open-space analysis remains a future gap

## Adjacent Domains

- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
