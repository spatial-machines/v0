# Economic Development and Corridor Analysis Domain

Purpose:
provide a navigation and cross-linking page for economic development assessment, commercial corridor vitality analysis, and investment-zone framing
help analysts and agents route corridor, district, and economic-context questions into the correct reusable demographic, POI, land-use, accessibility, and delivery workflows
define the current reusable canon coverage for economic development analysis without inventing a dedicated corridor-scoring methodology or economic-impact formula that does not yet exist in the repo

## Domain Scope

This domain covers work where the main question is how an area, corridor, or district performs economically and what spatial context supports development planning, investment framing, or revitalization analysis.

It includes:
- commercial corridor vitality assessment using demographic, POI, and land-use context
- economic development district and zone framing
- investment-context assembly combining parcels, demographics, accessibility, and business landscape
- trend and shift analysis applied to economic development questions
- delivery routing for economic development outputs

It does not include:
- formal economic impact modeling, fiscal analysis, or multiplier estimation
- retail trade-area delineation and penetration as a primary focus (see `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`)
- competitor gap detection as a primary focus (see `domains/COMPETITOR_AND_WHITE_SPACE_ANALYSIS.md`)
- site-level suitability scoring (see `domains/SITE_SELECTION_AND_SUITABILITY.md`)
- workforce and labor-shed analysis as a primary focus (see `domains/WORKFORCE_AND_LABOR_SHED_ANALYSIS.md`)

## Common Questions

- what is the current economic and demographic profile of this corridor or district?
- how has this area changed over time, and what trends matter for development planning?
- what businesses and services are present, and where are the gaps?
- how accessible is this area by car, transit, and foot?
- what land-use, parcel, and zoning conditions shape development potential?

## Common Workflow Sequences

### Sequence 1: corridor demographic and business profile

1. define corridor or district geography through `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or validated boundary inputs
2. prepare demographic profile with `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. add trend context with `workflows/DECADE_TREND_ANALYSIS.md`
4. extract business landscape with `workflows/POSTGIS_POI_LANDSCAPE.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
6. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: corridor context assembly

1. prepare demographic baseline through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. add POI and business context through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
3. add land-use and parcel context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
4. add zoning and constraint context through `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
5. add accessibility context through `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md` or `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
6. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`

### Sequence 3: development-context delivery

1. assemble corridor context from relevant domain layers
2. add shift and change framing through `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md`
3. review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
4. if high-stakes delivery, escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md`
5. route final maps and deliverables through `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness across mixed economic development inputs
- `standards/TREND_ANALYSIS_STANDARD.md` — comparability and trend-claim rules for corridor change analysis
- `standards/DEMOGRAPHIC_SHIFT_STANDARD.md` — shift interpretation for development-context framing
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed metrics in corridor summaries
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for corridor geometry and overlay work
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for economic development claims

## Key Workflows for This Domain

- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic baseline for corridor or district
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level enrichment for corridor geography
- `workflows/DECADE_TREND_ANALYSIS.md` — long-horizon change context
- `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md` — shift and comparative change framing
- `workflows/POSTGIS_POI_LANDSCAPE.md` — business and amenity landscape extraction
- `workflows/POI_CATEGORY_NORMALIZATION.md` — category cleanup for corridor business context
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — corridor or district geometry preparation
- `workflows/SERVICE_AREA_ANALYSIS.md` — accessibility context for corridor analysis
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — corridor output packaging

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of corridor analysis outputs
- `qa-review/TREND_OUTPUT_REVIEW.md` — trend-specific output review for corridor change claims
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of economic development framing and narrative
- `qa-review/POI_EXTRACTION_QA.md` — validation of business landscape within corridor
- `qa-review/MAP_QA_CHECKLIST.md` — review of corridor maps and economic development exhibits
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review for consequential development outputs

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — demographic and economic context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support
- `data-sources/LOCAL_POSTGIS.md` — POI and contextual layer support at scale
- `data-sources/OSM.md` — open geodata for business, amenity, and infrastructure context
- `data-sources/LOCAL_FILES.md` — client-supplied corridor boundaries, parcel layers, or economic data
- `data-sources/REMOTE_FILES.md` — downloadable economic, land-use, or boundary layers

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query, summarization, and corridor-level extraction
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, shaping, aggregation, and output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- economic development analysis often combines layers with very different trust levels, time horizons, and intended uses
- corridor vitality claims should be grounded in observable spatial and demographic evidence rather than speculative economic forecasting
- trend and shift findings for corridors may reflect boundary effects or tract-level aggregation artifacts rather than real corridor-level change
- economic impact, multiplier, and fiscal analysis are not currently supported by the wiki canon and should not be presented as if they are

## Known Gaps in Current Canon

- there is no dedicated economic development standard, corridor vitality index, or economic scoring methodology yet
- economic impact modeling and fiscal analysis are not represented in the repo
- no dedicated corridor-specific QA page exists beyond the general structural, trend, interpretive, and legal-grade layers
- business vacancy, storefront activity, and real-time commercial vitality indicators are not yet wiki-standardized
- there is no dedicated workflow for assembling multi-layer economic development context from disparate domain sources

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md`
- `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`
- `domains/WORKFORCE_AND_LABOR_SHED_ANALYSIS.md`
- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
