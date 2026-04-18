# Workforce and Labor-Shed Analysis Domain

Purpose:
provide a navigation and cross-linking page for workforce geography, labor-shed delineation, and commute-based labor availability analysis
help analysts and agents route workforce and labor market questions into the correct reusable demographic, accessibility, drive-time, and delivery workflows
define the current reusable canon coverage for workforce analysis without inventing a dedicated labor-shed methodology or commute model that does not yet exist in the repo

## Domain Scope

This domain covers work where the main question is where workers come from, how labor availability varies across geographies, and how commute patterns shape workforce access for employers or economic development planning.

It includes:
- labor-shed delineation using drive-time and service-area methods
- workforce demographic profiling within commute-accessible geographies
- employer-site workforce availability assessment
- labor market context assembly for economic development and site selection
- delivery routing for workforce analysis outputs

It does not include:
- formal labor-force forecasting, wage modeling, or employment projection
- economic impact or fiscal analysis (see `domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md`)
- general demographic inventory not tied to workforce questions (see `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`)
- site-level suitability scoring (see `domains/SITE_SELECTION_AND_SUITABILITY.md`)
- transit-specific network methodology as a first-class workflow (see `domains/TRANSIT_ACCESS_AND_COVERAGE.md`)

## Common Questions

- how many working-age residents live within a commutable distance of this employer or site?
- what are the demographic and occupational characteristics of the available workforce?
- how does labor availability compare across candidate sites or corridors?
- what commute-time thresholds are reasonable for this geography and industry?
- how should workforce context be presented alongside demographic and accessibility findings?

## Common Workflow Sequences

### Sequence 1: drive-time labor-shed baseline

1. prepare employer or site locations through `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or validated existing geometry
2. generate commute-time service areas with `workflows/SERVICE_AREA_ANALYSIS.md`
3. enrich labor-shed areas with demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` and `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: workforce comparison across candidate sites

1. generate labor sheds for each candidate through `workflows/SERVICE_AREA_ANALYSIS.md`
2. enrich each area with `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. compare workforce profiles across candidate sites
4. route into `domains/SITE_SELECTION_AND_SUITABILITY.md` for broader comparison framing
5. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: workforce context for economic development

1. define study area through `domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md`
2. generate labor-shed areas with `workflows/SERVICE_AREA_ANALYSIS.md`
3. add trend context with `workflows/DECADE_TREND_ANALYSIS.md`
4. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. review with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` and `qa-review/TREND_OUTPUT_REVIEW.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of demographic and commute inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for service areas and overlay work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling population counts and rate metrics in workforce summaries
- `standards/TREND_ANALYSIS_STANDARD.md` — comparability rules when workforce trends are included
- `standards/DEMOGRAPHIC_SHIFT_STANDARD.md` — shift interpretation for workforce change framing
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based labor-shed generation
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — employer or site preparation before labor-shed generation
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean enrichment when network travel is not required
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment within labor-shed areas
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic inventory for workforce context
- `workflows/DECADE_TREND_ANALYSIS.md` — long-horizon workforce change context
- `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md` — shift and comparative change framing
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — workforce output packaging

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of workforce analysis outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of labor availability and workforce claims
- `qa-review/TREND_OUTPUT_REVIEW.md` — review of workforce trend outputs
- `qa-review/MAP_QA_CHECKLIST.md` — review of labor-shed maps and delivery outputs

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — demographic, employment, and commute-related variables
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery
- `data-sources/LOCAL_FILES.md` — client-supplied employer sites, facility lists, or workforce data
- `data-sources/REMOTE_FILES.md` — downloadable economic or workforce context layers
- `data-sources/LOCAL_POSTGIS.md` — contextual layer support at scale
- `data-sources/OSM.md` — open geodata for employment and infrastructure context

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and summarization for labor-shed work
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, aggregation, and workforce output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- labor-shed boundaries are modeled estimates, not administrative or natural market edges
- ACS commute and employment data describe residential location and general industry, not employer-specific recruitment pools
- commute-time thresholds vary significantly by industry, role type, and geography — no single default threshold applies universally
- workforce availability claims should separate what the demographic data shows from what the actual labor market conditions are
- confidentiality and suppression rules in Census employment data may limit granularity at small geographies

## Known Gaps in Current Canon

- there is no dedicated labor-shed standard or commute-modeling methodology yet
- occupation-level and industry-level workforce profiling workflows are not yet first-class wiki pages
- LEHD (LODES) origin-destination employment data intake is not yet wiki-standardized
- commute-mode split analysis and multi-modal commute-shed methods are not yet represented
- there is no dedicated workforce QA page beyond the general structural, interpretive, and trend layers

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
- `domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
