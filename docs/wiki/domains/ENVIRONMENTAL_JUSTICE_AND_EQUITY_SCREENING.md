# Environmental Justice and Equity Screening Domain

Purpose:
provide a navigation and cross-linking page for environmental justice, equity-screening, and community-burden questions built from demographic context, exposure proxies, and delivery-ready spatial summaries
help analysts and agents route EJ-style work into the correct demographic, hydrology, accessibility, QA, and delivery canon
define the current reusable canon coverage for environmental justice screening without inventing a dedicated firm-wide EJ scoring methodology that does not yet exist in the repo

## Domain Scope

This domain covers screening-oriented work where the question is how environmental burden, access, or hazard exposure overlaps with population vulnerability and community inequity.

It includes:
- equity-screening and burden-screening framing
- demographic vulnerability context
- environmental or hazard proxy overlays when supported by live canon
- map and review routing for EJ-oriented findings
- cross-routing to hazard, heat, hydrology, and demographic canon

It does not include:
- a formal firm-wide EJ index or weighting framework
- causal public-health methodology
- a dedicated pollution-model workflow that the wiki does not yet contain
- regulatory or legal conclusions beyond what the underlying workflows support

## Common Questions

- where do environmental or access burdens overlap with vulnerable populations?
- how should tract-level demographic context be paired with hazard or infrastructure layers?
- what can be screened defensibly with the current canon, and what remains outside it?
- how should EJ-style findings be reviewed before public delivery?
- when is the output a screening product rather than a final policy conclusion?

## Common Workflow Sequences

### Sequence 1: demographic vulnerability + spatial burden screening

1. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. prepare the relevant burden or hazard layer through `domains/HYDROLOGY_AND_TERRAIN.md` or another live domain workflow when available
3. use `workflows/TRACT_JOIN_AND_ENRICHMENT.md` or `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` to assemble the working layer
4. validate structure with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretive framing with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: access-oriented equity screening

1. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. prepare facilities or destinations through `domains/POI_AND_BUSINESS_LANDSCAPE.md` or `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
3. use `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md` for service areas or within-distance analysis
4. route final outputs through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: heat or flood-related equity screening

1. prepare vulnerability context through `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
2. prepare environmental surface or watershed-related outputs through `domains/HYDROLOGY_AND_TERRAIN.md`
3. assemble and review the screening output with `qa-review/STRUCTURAL_QA_CHECKLIST.md` and `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
4. escalate when the work is being used for legal, regulatory, or highly consequential claims

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — source-tier discipline before combining burden and demographic layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlays and spatial joins
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed counts, rates, and medians in screening summaries
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential interpretive claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for challenge-prone work

## Key Workflows for This Domain

- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic vulnerability context
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level enrichment and assembly
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — cross-domain analysis packaging
- `workflows/TERRAIN_DERIVATIVES.md` — environmental surface support when terrain proxies matter
- `workflows/WATERSHED_DELINEATION.md` — watershed-related burden context when appropriate
- `workflows/SERVICE_AREA_ANALYSIS.md` — access-oriented inequity screening

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural review of assembled screening outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of claims, narrative framing, and overreach risk
- `qa-review/MAP_QA_CHECKLIST.md` — review of public-facing screening maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — high-rigor review when outputs support consequential arguments

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — demographic context and tract-level indicators
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for screening layers
- `data-sources/USGS_ELEVATION.md` — terrain and hydrologic surface support when relevant
- `data-sources/LOCAL_FILES.md` — intake path for client or agency environmental layers
- `data-sources/REMOTE_FILES.md` — intake path for downloadable burden or context layers

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and packaging
- `toolkits/POSTGIS_TOOLKIT.md` — scale and spatial summarization support
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion, raster/vector handling, and delivery support

## Domain-Specific Caveats

- screening outputs are not the same as final regulatory, causal, or legal conclusions
- vulnerability framing can overreach quickly if the workflow does not support the implied policy claim
- mixed burden layers often have very different source quality and readiness levels
- environmental justice work requires especially careful interpretive review because maps can appear more definitive than they are

## Known Gaps in Current Canon

- there is no dedicated EJ screening standard, index, or weighting methodology yet
- no first-class pollution, emissions, or air-quality workflow exists yet
- there is no dedicated EJ review checklist beyond the general interpretive, structural, map, and legal-grade layers
- several adjacent domains in this space remain routing-first rather than method-rich

## Adjacent Domains

- `domains/URBAN_HEAT_AND_HEAT_VULNERABILITY.md`
- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
