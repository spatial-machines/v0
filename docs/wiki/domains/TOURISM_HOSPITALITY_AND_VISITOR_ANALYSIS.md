# Tourism, Hospitality, and Visitor Analysis Domain

Purpose:
provide a navigation and cross-linking page for tourism context, hospitality landscape mapping, and visitor-pattern analysis
help analysts and agents route tourism and hospitality questions into the correct reusable POI, demographic, accessibility, and delivery workflows
define the current reusable canon coverage for tourism and hospitality work without inventing a dedicated visitor-modeling methodology or tourism-impact formula that does not yet exist in the repo

## Domain Scope

This domain covers work where the main question is how a geography functions as a tourism or hospitality market, what visitor-serving assets exist, and how visitor patterns intersect with demographic and accessibility context.

It includes:
- hospitality and lodging landscape mapping using POI extraction
- attraction, venue, and visitor-serving amenity inventory
- tourism-context assembly combining POI, demographic, and accessibility layers
- visitor-pattern framing using available spatial and demographic context
- delivery routing for tourism and hospitality outputs

It does not include:
- visitor volume estimation, spending modeling, or economic impact calculation
- retail trade-area delineation as a primary focus (see `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`)
- general POI extraction not framed around tourism or hospitality (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- parks and recreation access analysis (see `domains/PARKS_RECREATION_AND_OPEN_SPACE_ACCESS.md`)
- final map packaging and publication (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)

## Common Questions

- what is the hospitality and lodging landscape in this study area?
- where are the major attractions, venues, and visitor-serving amenities?
- how accessible are tourism assets by car, transit, and foot?
- what demographic and economic context surrounds a tourism district or corridor?
- how should tourism and hospitality findings be presented for planning or investment audiences?

## Common Workflow Sequences

### Sequence 1: hospitality landscape baseline

1. confirm source readiness with `standards/SOURCE_READINESS_STANDARD.md`
2. read `data-sources/LOCAL_POSTGIS.md` and `data-sources/OSM.md`
3. run `workflows/POSTGIS_POI_LANDSCAPE.md` with hospitality and tourism category filters
4. normalize categories with `workflows/POI_CATEGORY_NORMALIZATION.md`
5. validate with `qa-review/POI_EXTRACTION_QA.md` and `qa-review/STRUCTURAL_QA_CHECKLIST.md`
6. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: tourism context assembly

1. prepare hospitality POI layer through `workflows/POSTGIS_POI_LANDSCAPE.md`
2. add demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` and `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
3. add accessibility context through `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. review with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: tourism district profile

1. define district or corridor geography through `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or validated boundary inputs
2. prepare demographic profile through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. extract hospitality and attraction landscape through `workflows/POSTGIS_POI_LANDSCAPE.md`
4. add trend context if relevant through `workflows/DECADE_TREND_ANALYSIS.md`
5. add transit or pedestrian accessibility context through `domains/TRANSIT_ACCESS_AND_COVERAGE.md` or `domains/PEDESTRIAN_AND_BICYCLE_ACCESS.md`
6. validate and deliver through `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of POI, demographic, and contextual inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlay and enrichment work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling counts and summaries in hospitality context
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for tourism and visitor-context claims

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — hospitality, lodging, and attraction extraction
- `workflows/POI_CATEGORY_NORMALIZATION.md` — category cleanup for tourism and hospitality POIs
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean enrichment around tourism assets
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based accessibility for tourism sites
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — district or site preparation
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment for tourism areas
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic inventory for visitor-area context
- `workflows/DECADE_TREND_ANALYSIS.md` — long-horizon change context for tourism districts
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — tourism output packaging

## Key QA Pages for This Domain

- `qa-review/POI_EXTRACTION_QA.md` — validation of hospitality and attraction POI extraction
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of tourism analysis outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of tourism and visitor-context claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of tourism maps and delivery outputs

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — POI and contextual layer support at scale
- `data-sources/OSM.md` — open geodata for lodging, attractions, and amenity context
- `data-sources/CENSUS_ACS.md` — demographic context for tourism areas
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment
- `data-sources/LOCAL_FILES.md` — client-supplied tourism inventories, visitor data, or district boundaries
- `data-sources/REMOTE_FILES.md` — downloadable tourism, recreation, or cultural-asset layers

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and extraction for hospitality and attraction layers
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, aggregation, and tourism output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- OSM and open POI sources are strong for lodging and major attractions but may undercount smaller venues, seasonal operations, or recently opened businesses
- visitor volume, spending, and economic impact estimation are not supported by the current wiki canon and should not be presented as if they are
- tourism and hospitality POI categories overlap with general retail and food-service categories — category boundaries should be defined explicitly for each project
- seasonal and event-driven variation in tourism is real but not captured by static demographic or POI snapshots

## Known Gaps in Current Canon

- there is no dedicated tourism or hospitality analysis standard or methodology page yet
- visitor volume estimation, visitor origin analysis, and tourism spending workflows are not represented in the repo
- mobile-device movement data and anonymized visitor-tracking source intake are not yet wiki-standardized
- event and seasonal analysis methods for tourism contexts are not yet first-class workflow families
- there is no dedicated tourism QA page beyond the general POI, structural, and interpretive layers

## Adjacent Domains

- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`
- `domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md`
- `domains/PARKS_RECREATION_AND_OPEN_SPACE_ACCESS.md`
- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
- `domains/PEDESTRIAN_AND_BICYCLE_ACCESS.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
