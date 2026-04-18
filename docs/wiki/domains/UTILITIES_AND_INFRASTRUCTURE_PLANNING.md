# Utilities and Infrastructure Planning Domain

Purpose:
provide a navigation and cross-linking page for utility infrastructure mapping, service-territory analysis, and infrastructure planning context
help analysts and agents route utility and infrastructure questions into the correct reusable accessibility, demographic, land-use, and delivery workflows
define the current reusable canon coverage for infrastructure planning without inventing engineering design, capacity modeling, or utility-specific methodology the repo does not yet contain

## Domain Scope

This domain covers work where the main question is where utility infrastructure exists, what populations or areas it serves, and how infrastructure context supports planning, investment, or siting decisions.

It includes:
- utility infrastructure inventory and service-territory mapping
- infrastructure coverage and access analysis using demographic and spatial context
- infrastructure-context assembly for siting, development, and planning work
- cross-routing to energy, broadband, public asset, and resilience domains
- delivery routing for infrastructure planning outputs

It does not include:
- engineering design, capacity modeling, or load analysis
- energy-specific siting methodology (see `domains/ENERGY_INFRASTRUCTURE_AND_RENEWABLE_SITING.md`)
- broadband and telecommunications as a primary focus (see `domains/BROADBAND_AND_TELECOMMUNICATIONS_ACCESS.md`)
- critical facility resilience screening (see `domains/CRITICAL_FACILITY_RESILIENCE.md`)
- general site-suitability scoring (see `domains/SITE_SELECTION_AND_SUITABILITY.md`)

## Common Questions

- where is existing utility infrastructure located, and what areas does it serve?
- which populations or geographies are underserved by current infrastructure?
- how should infrastructure context be combined with demographic and land-use layers for planning?
- what infrastructure constraints or opportunities affect development or siting decisions?
- how should infrastructure planning outputs be reviewed and delivered?

## Common Workflow Sequences

### Sequence 1: infrastructure inventory and coverage baseline

1. intake infrastructure data through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. prepare demographic context through `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. assess coverage with `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: infrastructure context for development planning

1. assemble land-use and parcel context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
2. add zoning constraints through `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
3. add infrastructure coverage and proximity layers
4. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: infrastructure gap screening

1. prepare demographic and equity context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. overlay infrastructure coverage against population distribution
3. identify underserved areas using `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
4. if equity framing is needed, cross-route into `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
5. validate and deliver through `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of infrastructure and utility data inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlay and proximity work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed metrics in infrastructure summaries
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for infrastructure planning claims

## Key Workflows for This Domain

- `workflows/SERVICE_AREA_ANALYSIS.md` — coverage and access analysis for infrastructure
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — proximity enrichment for infrastructure context
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation for infrastructure proximity
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment for coverage analysis
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — population context for infrastructure planning
- `workflows/POSTGIS_POI_LANDSCAPE.md` — facility and infrastructure asset extraction
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — infrastructure output packaging

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of infrastructure analysis outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of infrastructure planning claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of infrastructure maps and delivery outputs

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client-supplied utility, infrastructure, or service-territory data
- `data-sources/REMOTE_FILES.md` — downloadable infrastructure and utility layers
- `data-sources/CENSUS_ACS.md` — demographic context for coverage analysis
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support
- `data-sources/LOCAL_POSTGIS.md` — contextual layer support at scale
- `data-sources/OSM.md` — open geodata for infrastructure and utility context

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and summarization for infrastructure layers
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- infrastructure data is often proprietary, incomplete, or provided under restricted use terms
- service-territory boundaries may not reflect actual service delivery or infrastructure condition
- infrastructure planning outputs often invite engineering or capacity conclusions the spatial analysis alone cannot support
- utility and infrastructure data formats vary widely and may require significant intake and normalization work

## Known Gaps in Current Canon

- there is no dedicated utility or infrastructure planning standard or methodology page yet
- capacity modeling, load analysis, and engineering-grade infrastructure assessment are not represented in the repo
- utility-specific data intake and normalization workflows are not yet wiki-standardized
- infrastructure condition, age, and maintenance context are not yet first-class data layers
- there is no dedicated infrastructure QA page beyond the general structural, interpretive, and map layers

## Adjacent Domains

- `domains/ENERGY_INFRASTRUCTURE_AND_RENEWABLE_SITING.md`
- `domains/BROADBAND_AND_TELECOMMUNICATIONS_ACCESS.md`
- `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
- `domains/CRITICAL_FACILITY_RESILIENCE.md`
- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
