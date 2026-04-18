# Energy Infrastructure and Renewable Siting Domain

Purpose:
provide a navigation and cross-linking page for energy infrastructure mapping, renewable energy siting context, and energy-planning spatial analysis
help analysts and agents route energy and renewable siting questions into the correct reusable terrain, land-use, accessibility, environmental, and delivery workflows
define the current reusable canon coverage for energy siting work without inventing generation-capacity modeling, interconnection analysis, or energy-specific methodology the repo does not yet contain

## Domain Scope

This domain covers work where the main question is where energy infrastructure exists, where renewable energy facilities could be sited, and what spatial context supports energy planning decisions.

It includes:
- energy facility inventory and infrastructure context mapping
- renewable energy siting screening using terrain, land-use, and environmental context
- constraint and opportunity layer assembly for energy development
- demographic and community context for energy-planning projects
- delivery routing for energy siting and infrastructure outputs

It does not include:
- generation-capacity modeling, grid interconnection analysis, or power-flow modeling
- general utility infrastructure coverage (see `domains/UTILITIES_AND_INFRASTRUCTURE_PLANNING.md`)
- general site-suitability scoring not specific to energy (see `domains/SITE_SELECTION_AND_SUITABILITY.md`)
- environmental permitting or regulatory compliance conclusions

## Common Questions

- where are existing energy facilities and transmission infrastructure located?
- which areas have favorable terrain, land-use, and environmental conditions for renewable siting?
- what constraint layers should be screened before recommending potential energy development sites?
- what populations and communities are near proposed or existing energy infrastructure?
- how should energy siting context be reviewed and delivered?

## Common Workflow Sequences

### Sequence 1: renewable siting constraint screening

1. prepare terrain context through `workflows/TERRAIN_DERIVATIVES.md`
2. add land-use and parcel context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
3. add zoning or regulatory constraint layers through `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
4. add environmental context through `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md` or `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md` when relevant
5. assemble with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
6. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: energy facility context assembly

1. intake energy facility data through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. add demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. add accessibility context through `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. review with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: community impact context for energy projects

1. prepare demographic and equity context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. add environmental justice screening through `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
3. overlay with energy facility or proposed site locations
4. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the output supports consequential siting decisions
5. deliver through `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of energy, terrain, and constraint inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for siting overlays and terrain work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed metrics in siting summaries
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for siting and energy planning claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for consequential siting outputs

## Key Workflows for This Domain

- `workflows/TERRAIN_DERIVATIVES.md` — slope, aspect, and terrain context for siting
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — siting output packaging and synthesis
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment for energy facility context
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — population context for community impact
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — proximity enrichment around energy facilities
- `workflows/SERVICE_AREA_ANALYSIS.md` — access analysis for energy infrastructure

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of siting and energy outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of siting and energy planning claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of energy siting maps and delivery outputs
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review for consequential outputs

## Key Data Sources for This Domain

- `data-sources/USGS_ELEVATION.md` — terrain data for slope and aspect analysis
- `data-sources/LOCAL_FILES.md` — client-supplied energy facility, transmission, or constraint data
- `data-sources/REMOTE_FILES.md` — downloadable energy, land-use, and constraint layers
- `data-sources/CENSUS_ACS.md` — demographic context for community impact analysis
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support
- `data-sources/OSM.md` — open geodata for infrastructure and land-use context

## Key Toolkits for This Domain

- `toolkits/GDAL_OGR_TOOLKIT.md` — raster/vector handling for terrain and siting layers
- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and summarization at scale
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and output preparation

## Domain-Specific Caveats

- siting screening identifies spatial opportunity or constraint but does not replace engineering feasibility, interconnection, or financial analysis
- terrain suitability for renewables depends on resolution, currency, and the specific technology being assessed
- energy infrastructure data is often proprietary, restricted, or incomplete in open sources
- community impact and equity framing requires careful interpretive review to avoid overreach

## Known Gaps in Current Canon

- there is no dedicated renewable energy siting standard, solar/wind resource methodology, or generation-capacity workflow yet
- grid interconnection and transmission constraint analysis are not represented in the repo
- energy-specific data intake and normalization workflows are not yet wiki-standardized
- no dedicated energy siting QA page exists beyond the general structural, interpretive, map, and legal-grade layers
- environmental review and permitting workflow integration is not yet first-class canon

## Adjacent Domains

- `domains/UTILITIES_AND_INFRASTRUCTURE_PLANNING.md`
- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
