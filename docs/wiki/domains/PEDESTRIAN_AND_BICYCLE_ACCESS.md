# Pedestrian and Bicycle Access Domain

Purpose:
provide a navigation and cross-linking page for walkability, bicycle access, and non-motorized reachability questions built from the live accessibility and community-context canon
help analysts and agents route pedestrian and bicycle questions into the correct reusable workflows while preserving clear method boundaries
define the current reusable canon coverage for pedestrian and bicycle access without inventing a dedicated pedestrian-network, bike-network, or level-of-traffic-stress methodology that does not yet exist in the repo

## Domain Scope

This domain covers spatial analysis where the question is how people reach places by walking or biking, or how non-motorized access should be framed in a site or community context.

It includes:
- pedestrian and bicycle access screening
- non-motorized proximity framing around sites and facilities
- demographic context for active-transport access questions
- routing to delivery and review for active-access outputs
- cross-routing to community-facility, parks, and development-context canon

It does not include:
- a dedicated walk-network or bike-network analysis workflow
- safety-stress scoring, comfort scoring, or route-quality methodology
- schedule-based multimodal travel modeling
- engineering design or streetscape design methodology

## Common Questions

- what destinations appear walkable or bike-accessible from this site?
- how should active-transport context be represented using the current canon?
- what can the live workflows support today without implying a full network model?
- how should pedestrian or bicycle access outputs be reviewed before delivery?
- when should a project describe the result as screening instead of definitive active-transport analysis?

## Common Workflow Sequences

### Sequence 1: active-access screening baseline

1. prepare sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` for simple proximity-based screening
3. add destination or facility context through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
4. add demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: parks, schools, or civic access framing

1. prepare relevant destinations through `domains/COMMUNITY_FACILITY_PLANNING.md` or `domains/PARKS_RECREATION_AND_OPEN_SPACE_ACCESS.md`
2. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` as the nearest live active-access proxy when appropriate
3. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
4. route outputs through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: candidate-site active mobility context

1. assemble parcel or site baseline through `domains/SITE_SELECTION_AND_SUITABILITY.md`
2. add nearby amenities and destinations through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
3. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` for non-motorized screening context
4. state clearly when the output is proximity screening rather than a full pedestrian or bicycle network analysis

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of destination, demographic, and contextual layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for distance and overlay work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — mixed summary handling in active-access outputs
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential access claims

## Key Workflows for This Domain

- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation from addresses or named locations
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearest live workflow for active-access proximity screening
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — packaging active-access outputs
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic enrichment when needed

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of active-access outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of walkability/bike-access claims and overreach risk
- `qa-review/MAP_QA_CHECKLIST.md` — review of pedestrian and bicycle access maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — site, path, or destination layers supplied by client or analyst
- `data-sources/REMOTE_FILES.md` — downloadable path, destination, or corridor layers
- `data-sources/OSM.md` — open geodata context for destinations and street-adjacent features
- `data-sources/CENSUS_ACS.md` — demographic context for access and equity framing
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support
- `toolkits/POSTGIS_TOOLKIT.md` — contextual summarization support at scale

## Domain-Specific Caveats

- the current canon supports walk/bike screening more than full pedestrian or bicycle network analysis
- simple proximity does not equal safe, comfortable, or realistic active-transport access
- active-mobility claims can overreach if the workflow does not model the actual network conditions people experience
- this domain should preserve the distinction between screening context and formal transportation design or operations analysis

## Known Gaps in Current Canon

- there is no dedicated pedestrian-network or bicycle-network workflow yet
- no walkability, bike-stress, or streetscape standard exists yet
- there is no active-mobility-specific QA page beyond the general structural, interpretive, and map layers
- route quality, comfort, and safety methodology remain live gaps

## Adjacent Domains

- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
- `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/PARKS_RECREATION_AND_OPEN_SPACE_ACCESS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
