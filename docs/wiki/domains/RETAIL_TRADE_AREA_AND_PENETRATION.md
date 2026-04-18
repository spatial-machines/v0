# Retail Trade Area and Penetration Domain

Purpose:
provide a navigation and cross-linking page for retail trade-area delineation, market penetration estimation, and catchment-based retail analysis
help analysts and agents route trade-area questions into the correct reusable demographic, POI, accessibility, and delivery workflows
define the current reusable canon coverage for trade-area work without inventing a dedicated trade-area methodology or penetration formula that does not yet exist in the repo

## Domain Scope

This domain covers work where the main question is how a retail location, brand, or category draws customers from a surrounding geography and how deeply it penetrates that market.

It includes:
- trade-area delineation using drive-time, distance, or demographic boundaries
- market penetration framing using demographic and POI context
- catchment comparison across candidate or existing retail sites
- demographic and business-landscape enrichment within delineated trade areas
- delivery routing for trade-area outputs

It does not include:
- formal site-suitability scoring or weighted ranking (see `domains/SITE_SELECTION_AND_SUITABILITY.md`)
- competitor gap detection and white-space mapping as a primary focus (see `domains/COMPETITOR_AND_WHITE_SPACE_ANALYSIS.md`)
- general demographic inventory not tied to a trade-area question (see `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`)
- final map packaging and publication (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)

## Common Questions

- what is the primary trade area for this retail location or proposed site?
- how many people live within the trade area, and what are their demographic characteristics?
- what competing or complementary businesses operate within the same trade area?
- how does trade-area coverage differ across candidate sites?
- what share of the surrounding market does a location realistically serve?

## Common Workflow Sequences

### Sequence 1: drive-time trade-area baseline

1. prepare site locations through `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or validated existing geometry
2. generate service areas with `workflows/SERVICE_AREA_ANALYSIS.md`
3. enrich trade areas with demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` and `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
4. add POI context through `workflows/POSTGIS_POI_LANDSCAPE.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
6. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: distance-based trade-area enrichment

1. prepare target geometry with `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. run `workflows/WITHIN_DISTANCE_ENRICHMENT.md` when Euclidean distance is approved
3. enrich with demographic and POI context
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md` and `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: trade-area comparison across sites

1. generate trade areas for each candidate through `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
2. enrich each area with `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. add business-landscape context through `workflows/POSTGIS_POI_LANDSCAPE.md`
4. compare results and route into `domains/SITE_SELECTION_AND_SUITABILITY.md` for broader comparison framing
5. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

## Key Standards for This Domain

- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for buffers, service areas, and overlay work
- `standards/SOURCE_READINESS_STANDARD.md` — readiness of demographic, POI, and facility inputs
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed metrics in trade-area summaries
- `standards/ZIP_ZCTA_AGGREGATION_STANDARD.md` — when trade-area delivery is ZIP-oriented
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based trade-area generation
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean trade-area enrichment
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation before trade-area generation
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment within trade areas
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic inventory for trade-area context
- `workflows/POSTGIS_POI_LANDSCAPE.md` — business and competitor context within trade areas
- `workflows/POI_CATEGORY_NORMALIZATION.md` — category cleanup for retail and competitor POIs
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — trade-area output packaging

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of trade-area outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of penetration and market-share claims
- `qa-review/POI_EXTRACTION_QA.md` — validation of retail and competitor POI within trade areas
- `qa-review/MAP_QA_CHECKLIST.md` — review of trade-area maps and delivery outputs

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — demographic context for trade-area enrichment
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery
- `data-sources/LOCAL_POSTGIS.md` — POI and contextual layer support at scale
- `data-sources/OSM.md` — open geodata for retail, amenity, and competitor context
- `data-sources/LOCAL_FILES.md` — client-supplied site lists, customer files, or transaction data
- `data-sources/REMOTE_FILES.md` — downloadable context and boundary layers

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — scale and spatial query work for trade-area generation and enrichment
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, shaping, and trade-area output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- trade-area delineation is a modeling choice, not a fact — the boundary reflects the method used, not a natural market edge
- penetration and market-share claims require careful framing because the wiki does not yet contain a signed-off penetration formula or market-share methodology
- drive-time trade areas and Euclidean buffers answer different questions and should not be treated as interchangeable
- customer-origin data (when available) provides the strongest trade-area evidence, but intake and privacy handling are project-level rather than wiki-standardized

## Known Gaps in Current Canon

- there is no dedicated trade-area delineation standard or methodology page yet
- market penetration calculation is not yet a first-class workflow with defined formulas or review criteria
- customer-origin and transaction-data intake workflows are not yet wiki-standardized
- gravity-model and Huff-model trade-area methods are not yet represented in the repo
- there is no dedicated trade-area QA page beyond the general structural, interpretive, and POI layers

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/COMPETITOR_AND_WHITE_SPACE_ANALYSIS.md`
- `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
