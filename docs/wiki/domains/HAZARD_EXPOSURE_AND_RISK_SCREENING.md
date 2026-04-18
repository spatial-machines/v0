# Hazard Exposure and Risk Screening Domain

Purpose:
provide a navigation and cross-linking page for spatial hazard screening, exposure mapping, and risk-context analysis built from live environmental, demographic, and QA canon
help analysts and agents route hazard-oriented questions into the correct hydrology, demographic, interpretive, and delivery workflows
define the current reusable canon coverage for hazard screening without inventing dedicated wildfire, industrial, seismic, or probabilistic risk methodology the repo does not yet contain

## Domain Scope

This domain covers screening-style hazard work where the goal is to identify where people, assets, or geographies overlap with environmental or spatial hazard context.

It includes:
- hazard exposure screening
- demographic vulnerability overlays
- environmental and terrain-support routing
- review and delivery routing for hazard-oriented outputs
- cross-routing to flood, heat, EJ, and resilience domains

It does not include:
- a firm-wide probabilistic risk standard
- specialized hazard-model workflows that are not yet in the wiki
- dispatch, operational emergency management, or incident-response modeling
- legal or regulatory hazard determinations beyond what the underlying workflows support

## Common Questions

- where do hazards and vulnerable populations overlap?
- what can be screened defensibly with the live canon today?
- when is the analysis a screening product rather than a full risk model?
- how should hazard-oriented outputs be reviewed before delivery?
- which adjacent hazard-specific domain should handle the question in more detail?

## Common Workflow Sequences

### Sequence 1: hazard exposure baseline

1. intake the hazard or context layer through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. assemble and summarize with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md` where needed
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretation with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: terrain- or watershed-informed hazard screening

1. prepare environmental support layers through `domains/HYDROLOGY_AND_TERRAIN.md`
2. combine with tract or site context through the general analysis workflow
3. if the hazard is flood-oriented, route into `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
4. route final outputs into `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: hazard + resilience framing

1. prepare the screening output through this domain
2. route broader adaptation or resilience interpretation into `domains/CLIMATE_RISK_AND_RESILIENCE.md`
3. escalate to higher-rigor review if the output will support high-stakes planning or challenge-prone decisions

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness and provenance discipline for hazard layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlays and joins
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling across mixed metrics
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for challenge-prone use cases

## Key Workflows for This Domain

- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — cross-domain hazard screening assembly
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic enrichment and assembly
- `workflows/TERRAIN_DERIVATIVES.md` — terrain-support routing when relevant
- `workflows/WATERSHED_DELINEATION.md` — hydrologic support when relevant
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic vulnerability context

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity checks for assembled hazard layers
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of hazard framing and overclaim risk
- `qa-review/MAP_QA_CHECKLIST.md` — review of public-facing hazard maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when needed

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — intake path for hazard and exposure layers
- `data-sources/REMOTE_FILES.md` — downloadable hazard or context layer intake
- `data-sources/CENSUS_ACS.md` — demographic context for vulnerability overlays
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for overlays and delivery
- `data-sources/USGS_ELEVATION.md` — terrain and hydrologic support when relevant

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — raster/vector conversion and support
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale spatial summarization and support

## Domain-Specific Caveats

- screening outputs are not substitutes for detailed hazard models or operational risk analysis
- hazard layers often come from mixed-quality sources with different intended uses and update cycles
- risk language can overstate what the underlying workflow actually demonstrates
- higher-stakes hazard work often needs stronger review than the base workflow alone implies

## Known Gaps in Current Canon

- there is no dedicated hazard-risk standard or probabilistic risk methodology yet
- wildfire, industrial, seismic, and other hazard families do not yet have their own workflow pages
- there is no hazard-specific QA page beyond the general structural, interpretive, map, and legal-grade layers
- most hazard subdomains remain routing-first rather than method-rich

## Adjacent Domains

- `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
- `domains/URBAN_HEAT_AND_HEAT_VULNERABILITY.md`
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
