# Disaster Response and Recovery Support Domain

Purpose:
provide a navigation and cross-linking page for spatial analysis supporting disaster response operations, damage assessment context, and recovery planning
help analysts and agents route disaster response and recovery questions into the correct reusable hazard, demographic, infrastructure, accessibility, and delivery workflows
define the current reusable canon coverage for disaster support work without inventing incident command methodology, damage-assessment scoring, or recovery-prioritization formulas the repo does not yet contain

## Domain Scope

This domain covers work where the main question is how spatial analysis can support response operations during or after a disaster, and how recovery planning benefits from demographic, infrastructure, and hazard context.

It includes:
- post-event context mapping using demographic, infrastructure, and hazard layers
- affected-area and affected-population estimation using live accessibility and demographic canon
- damage-context assembly combining facility, population, and hazard information
- recovery-planning context for housing, infrastructure, and community services
- delivery routing for disaster response and recovery outputs

It does not include:
- incident command operations, dispatch, or real-time emergency management
- structural damage assessment or engineering inspection
- insurance loss estimation or financial impact modeling
- pre-event hazard screening as a primary focus (see `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`)
- emergency service coverage planning (see `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`)

## Common Questions

- what populations and communities are in the affected area?
- which critical facilities and public assets are within the disaster zone?
- how should affected-area boundaries be defined and communicated?
- what demographic and economic context supports recovery prioritization?
- how should disaster response maps be reviewed before distribution to officials or the public?

## Common Workflow Sequences

### Sequence 1: affected-area population and context assessment

1. define affected-area boundary through `data-sources/LOCAL_FILES.md` or event-specific geometry
2. enrich with demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` and `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
3. identify critical facilities within the area through `workflows/POSTGIS_POI_LANDSCAPE.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 2: recovery-planning context assembly

1. prepare demographic and vulnerability baseline through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. add infrastructure context through `domains/UTILITIES_AND_INFRASTRUCTURE_PLANNING.md` or `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
3. add hazard-exposure context through `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md` or `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
4. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. review with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: rapid-turnaround disaster response map

1. assemble available layers from live data sources
2. apply cartographic standards through `standards/CARTOGRAPHY_STANDARD.md`
3. design maps using `workflows/CHOROPLETH_DESIGN.md` or `workflows/POINT_OVERLAY_DESIGN.md`
4. review with `qa-review/MAP_QA_CHECKLIST.md`
5. note data currency limitations clearly — disaster context changes rapidly and static maps can become outdated quickly

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of event-specific and contextual inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlay and affected-area work
- `standards/CARTOGRAPHY_STANDARD.md` — cartographic conventions for disaster response products
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for affected-area and recovery claims
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — provenance discipline for disaster data products

## Key Workflows for This Domain

- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment for affected areas
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — population context for impact estimation
- `workflows/POSTGIS_POI_LANDSCAPE.md` — facility and asset identification in affected areas
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — disaster context output packaging
- `workflows/SERVICE_AREA_ANALYSIS.md` — accessibility and coverage context
- `workflows/CHOROPLETH_DESIGN.md` — thematic map design for disaster products
- `workflows/POINT_OVERLAY_DESIGN.md` — facility and incident point mapping
- `workflows/REPORTING_AND_DELIVERY.md` — report and delivery packaging

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of disaster context outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of affected-area and impact claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of disaster response and recovery maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when outputs support funding or policy decisions

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — event-specific boundaries, damage reports, and situation data
- `data-sources/REMOTE_FILES.md` — downloadable hazard, FEMA, and post-event layers
- `data-sources/CENSUS_ACS.md` — demographic and community context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for affected-area analysis
- `data-sources/LOCAL_POSTGIS.md` — facility and contextual layer support
- `data-sources/OSM.md` — open geodata for infrastructure and facility context

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and rapid output preparation
- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and summarization at scale
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion, raster/vector handling, and packaging

## Domain-Specific Caveats

- disaster response analysis operates under time pressure, which increases the risk of source-quality shortcuts and interpretive overreach
- affected-area boundaries are often approximate and change as events evolve — maps should state their currency and limitations
- population and infrastructure estimates within disaster zones are based on pre-event Census and facility data, not real-time conditions
- recovery-planning context is valuable but should not be presented as damage assessment or loss estimation without engineering or insurance methodology

## Known Gaps in Current Canon

- there is no dedicated disaster response analysis standard or rapid-assessment methodology yet
- damage assessment, loss estimation, and post-event validation workflows are not represented in the repo
- real-time and near-real-time data intake for disaster support is not yet wiki-standardized
- shelter, evacuation, and temporary housing planning workflows are not yet first-class canon
- there is no dedicated disaster-response QA page beyond the general structural, interpretive, map, and legal-grade layers

## Adjacent Domains

- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/CRITICAL_FACILITY_RESILIENCE.md`
- `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`
- `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
