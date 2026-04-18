# Critical Facility Resilience Domain

Purpose:
provide a navigation and cross-linking page for resilience screening of critical facilities, infrastructure vulnerability assessment, and hazard-exposure context for essential public and private assets
help analysts and agents route critical facility resilience questions into the correct reusable hazard, demographic, accessibility, and delivery workflows
define the current reusable canon coverage for critical facility resilience without inventing structural vulnerability scoring, operational continuity modeling, or resilience-index methodology the repo does not yet contain

## Domain Scope

This domain covers work where the main question is which critical facilities are exposed to hazards, how resilient the essential asset base is, and what spatial context supports resilience planning.

It includes:
- critical facility inventory and spatial context mapping (hospitals, fire stations, power substations, water treatment plants, emergency shelters, schools)
- hazard-exposure screening for essential facilities using flood, heat, and other live hazard layers
- demographic vulnerability context around critical facilities
- cross-routing to hazard, infrastructure, emergency, and public asset domains
- delivery routing for critical facility resilience outputs

It does not include:
- structural vulnerability scoring, building-level assessment, or engineering resilience grading
- operational continuity or backup-capacity modeling
- general hazard screening not focused on critical facilities (see `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`)
- general public asset inventory (see `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`)
- emergency dispatch or response-time modeling (see `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`)

## Common Questions

- which critical facilities are located within known hazard zones?
- how many people depend on facilities that are exposed to flood, heat, or other hazards?
- what demographic and community context surrounds at-risk critical infrastructure?
- how should critical facility resilience findings be framed for planning or policy audiences?
- which facilities should be prioritized for further assessment based on spatial exposure?

## Common Workflow Sequences

### Sequence 1: critical facility hazard-exposure screening

1. intake or retrieve critical facility locations through `data-sources/LOCAL_FILES.md` or `workflows/POSTGIS_POI_LANDSCAPE.md`
2. prepare hazard context through `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md` or `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
3. overlay facilities against hazard layers with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretation with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: critical facility population-dependence context

1. inventory critical facilities and generate service areas with `workflows/SERVICE_AREA_ANALYSIS.md`
2. enrich with demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. identify population counts and vulnerability within each facility's service area
4. route into `domains/CLIMATE_RISK_AND_RESILIENCE.md` for broader resilience framing
5. deliver through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: resilience-context delivery

1. complete facility screening and population-dependence analysis
2. review maps with `qa-review/MAP_QA_CHECKLIST.md`
3. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the output supports high-stakes planning or funding decisions
4. avoid implying facility-level resilience grades the spatial analysis alone cannot support

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of facility, hazard, and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlay and proximity work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed metrics in facility resilience summaries
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for resilience and vulnerability claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for consequential outputs

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — critical facility extraction
- `workflows/SERVICE_AREA_ANALYSIS.md` — facility coverage and population-dependence analysis
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — proximity enrichment around facilities
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic vulnerability context
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — population context for dependence analysis
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — resilience screening output packaging
- `workflows/TERRAIN_DERIVATIVES.md` — terrain support when relevant to hazard exposure

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of resilience screening outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of resilience and vulnerability claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of facility resilience maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review for consequential outputs

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client or agency-supplied critical facility inventories
- `data-sources/REMOTE_FILES.md` — downloadable hazard, FEMA, and facility layers
- `data-sources/LOCAL_POSTGIS.md` — facility and hazard layer extraction at scale
- `data-sources/OSM.md` — open geodata for facility and infrastructure context
- `data-sources/CENSUS_ACS.md` — demographic vulnerability context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support
- `data-sources/USGS_ELEVATION.md` — terrain support for hazard context

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and overlay for facility-hazard screening
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and output preparation
- `toolkits/GDAL_OGR_TOOLKIT.md` — raster/vector conversion and packaging support

## Domain-Specific Caveats

- spatial exposure screening identifies which facilities are in hazard zones but does not assess structural resilience, operational continuity, or backup capacity
- critical facility lists vary by jurisdiction and project scope — there is no universal critical facility definition
- population-dependence analysis relies on service-area modeling assumptions that may not reflect actual usage patterns
- resilience framing can overstate what spatial analysis alone demonstrates if not bounded by interpretive review

## Known Gaps in Current Canon

- there is no dedicated critical facility resilience standard, vulnerability scoring model, or resilience index methodology yet
- structural and operational vulnerability assessment workflows are not represented in the repo
- facility-priority ranking for resilience investment is not yet a first-class workflow
- multi-hazard facility exposure synthesis is not yet a dedicated workflow
- there is no dedicated critical facility QA page beyond the general structural, interpretive, map, and legal-grade layers

## Adjacent Domains

- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/UTILITIES_AND_INFRASTRUCTURE_PLANNING.md`
- `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
- `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
