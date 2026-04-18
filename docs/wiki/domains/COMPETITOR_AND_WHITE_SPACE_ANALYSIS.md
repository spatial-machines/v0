# Competitor and White-Space Analysis Domain

Purpose:
provide a navigation and cross-linking page for competitive landscape mapping, market gap detection, and white-space identification work
help analysts and agents route competitor and under-served market questions into the correct reusable POI, demographic, accessibility, and delivery workflows
define the current reusable canon coverage for competitor analysis without inventing a dedicated competitive-scoring methodology or gap-detection formula that does not yet exist in the repo

## Domain Scope

This domain covers work where the main question is where competitors operate, where gaps exist in market coverage, and where unmet demand may create opportunity.

It includes:
- competitor inventory and landscape mapping using POI extraction
- white-space identification based on POI density, demographic context, and accessibility
- competitive context enrichment for trade areas and candidate sites
- category-level gap detection across study geographies
- delivery routing for competitive landscape and white-space outputs

It does not include:
- trade-area delineation and penetration estimation as a primary focus (see `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`)
- formal site-suitability scoring or weighted ranking (see `domains/SITE_SELECTION_AND_SUITABILITY.md`)
- general POI extraction and normalization not framed around competition (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- brand-level financial performance or sales forecasting

## Common Questions

- who are the competitors in this market, and where are they located?
- which areas have high demand indicators but low competitor presence?
- how does the competitive landscape differ across candidate trade areas?
- are there category gaps that suggest under-served market segments?
- how should competitive context be presented alongside demographic and access findings?

## Common Workflow Sequences

### Sequence 1: competitor landscape baseline

1. confirm source readiness with `standards/SOURCE_READINESS_STANDARD.md`
2. read `data-sources/LOCAL_POSTGIS.md` and `data-sources/OSM.md`
3. run `workflows/POSTGIS_POI_LANDSCAPE.md` with competitor-relevant category filters
4. normalize categories with `workflows/POI_CATEGORY_NORMALIZATION.md`
5. validate with `qa-review/POI_EXTRACTION_QA.md` and `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: white-space screening

1. prepare competitor POI layer through `workflows/POSTGIS_POI_LANDSCAPE.md`
2. add demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` and `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
3. overlay demand indicators and competitor density within study geographies
4. enrich with accessibility context through `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
5. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
6. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: competitive context for site comparison

1. generate trade areas through `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md` or `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
2. extract competitor POIs within each trade area through `workflows/POSTGIS_POI_LANDSCAPE.md`
3. normalize and summarize through `workflows/POI_CATEGORY_NORMALIZATION.md`
4. feed into `domains/SITE_SELECTION_AND_SUITABILITY.md` for broader comparison framing
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of POI and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlay, buffer, and enrichment work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling counts and densities in competitive summaries
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for competitive and market-gap claims

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — competitor and category-level POI extraction
- `workflows/POI_CATEGORY_NORMALIZATION.md` — category cleanup for competitor taxonomy
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean enrichment for competitor density
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based enrichment for competitor coverage
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation for competitive context
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic demand context
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic inventory for demand indicators
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — competitive landscape output packaging

## Key QA Pages for This Domain

- `qa-review/POI_EXTRACTION_QA.md` — validation of competitor POI extraction
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of competitive analysis outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of white-space and competitive gap claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of competitive landscape maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — POI and contextual layer support at scale
- `data-sources/OSM.md` — open geodata for competitor, retail, and amenity context
- `data-sources/CENSUS_ACS.md` — demographic demand indicators
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment
- `data-sources/LOCAL_FILES.md` — client-supplied competitor lists or proprietary brand data
- `data-sources/REMOTE_FILES.md` — downloadable competitor or industry context layers

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query, density, and competitor extraction at scale
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, aggregation, and competitive summary preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- white-space detection is an analytical framing, not a guaranteed market opportunity — low competitor density may reflect low demand rather than unmet demand
- competitor landscape quality depends heavily on POI source completeness, category accuracy, and currency
- OSM and open POI sources may undercount certain categories or miss recent openings and closures
- competitive claims should stay bounded by source quality and avoid overreach beyond what the data supports
- branded-chain identification and proprietary competitor classification remain project-level rather than wiki-standardized

## Known Gaps in Current Canon

- there is no dedicated white-space analysis workflow or standard yet
- competitor ranking and scoring methodology is not yet a first-class workflow
- no dedicated competitive density or saturation metric exists in the current canon
- gravity-model and demand-allocation methods for competitive analysis are not yet represented
- there is no dedicated competitor QA page beyond the general POI, structural, and interpretive layers

## Adjacent Domains

- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
