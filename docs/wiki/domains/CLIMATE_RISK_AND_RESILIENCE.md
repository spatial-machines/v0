# Climate Risk and Resilience Domain

Purpose:
provide a navigation and cross-linking page for climate-risk framing, resilience-oriented screening, and cross-hazard synthesis built from live environmental, demographic, and delivery canon
help analysts and agents route broader resilience questions into the correct heat, flood, hazard, demographic, QA, and delivery workflows
define the current reusable canon coverage for climate-risk and resilience work without inventing climate-scenario, adaptation-planning, or resilience-scoring methodology the repo does not yet contain

## Domain Scope

This domain covers higher-level climate and resilience work where multiple environmental burdens, vulnerabilities, or infrastructure concerns are synthesized into one framing layer.

It includes:
- climate-risk framing and synthesis
- resilience-oriented screening built from live hazard and demographic canon
- cross-routing between heat, flood, EJ, and broader hazard domains
- packaging resilience-oriented maps and summaries for delivery
- escalation guidance when resilience claims exceed current method support

It does not include:
- climate scenario modeling or projection workflows not already present in the wiki
- adaptation-priority scoring or resilience-index methodology
- engineering design, infrastructure hardening, or operational continuity modeling
- formal regulatory climate-risk standards

## Common Questions

- how should multiple hazard or burden layers be brought together into one resilience-oriented framing?
- what can the current canon support today as screening or synthesis work?
- how should climate-risk outputs be reviewed before public delivery?
- when should the work be described as resilience framing rather than a predictive climate model?
- which more specific domain should own the underlying analytical method?

## Common Workflow Sequences

### Sequence 1: cross-hazard resilience screening

1. prepare the relevant hazard layers through `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`, `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`, or `domains/URBAN_HEAT_AND_HEAT_VULNERABILITY.md`
2. prepare vulnerability context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. assemble and summarize through `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretation with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: resilience-oriented EJ framing

1. prepare burden and vulnerability context through `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
2. prepare any hazard-specific supporting layers through the appropriate adjacent domain
3. route synthesis outputs through `domains/CARTOGRAPHY_AND_DELIVERY.md`
4. state clearly that the result is a resilience-screening or framing artifact if no stronger method exists

### Sequence 3: climate-risk delivery workflow

1. complete the synthesis workflow using only live hazard and demographic canon
2. review maps with `qa-review/MAP_QA_CHECKLIST.md`
3. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the output is challenge-prone or high-stakes
4. avoid implying predictive certainty or scenario rigor the workflow does not actually contain

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness and provenance discipline across mixed hazard inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for multi-layer overlays and synthesis
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling across mixed metric types
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential resilience claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for challenge-prone outputs

## Key Workflows for This Domain

- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — synthesis and packaging workflow
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — vulnerability context inventory
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level vulnerability and overlay support
- `workflows/TERRAIN_DERIVATIVES.md` — terrain support where relevant
- `workflows/WATERSHED_DELINEATION.md` — watershed support where relevant

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of assembled resilience outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of resilience framing and overclaim risk
- `qa-review/MAP_QA_CHECKLIST.md` — review of public-facing resilience maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when the use case is challenge-prone

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — vulnerability and demographic context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for synthesis and delivery
- `data-sources/USGS_ELEVATION.md` — terrain-support routing where relevant
- `data-sources/LOCAL_FILES.md` — intake path for climate or hazard context layers
- `data-sources/REMOTE_FILES.md` — downloadable climate or hazard layer intake

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — overlays, joins, and synthesis support
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale spatial summarization and support
- `toolkits/GDAL_OGR_TOOLKIT.md` — raster/vector conversion and delivery support

## Domain-Specific Caveats

- the current canon is better at resilience-oriented screening and synthesis than at full climate modeling
- climate-risk language can overstate certainty very quickly if the workflow is really a screening assemblage
- cross-hazard synthesis is only as strong as the weakest input layer and the weakest interpretation step
- resilience is often a planning frame rather than a directly measurable output in the current live canon

## Known Gaps in Current Canon

- there is no dedicated climate-risk standard, scenario workflow, or resilience-scoring method yet
- adaptation-priority and intervention-selection workflows are not yet live canon
- there is no resilience-specific QA page beyond the general structural, interpretive, map, and legal-grade layers
- much of the climate domain remains routing-first rather than method-rich at this stage

## Adjacent Domains

- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/URBAN_HEAT_AND_HEAT_VULNERABILITY.md`
- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
