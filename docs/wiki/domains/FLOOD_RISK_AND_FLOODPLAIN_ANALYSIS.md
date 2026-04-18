# Flood Risk and Floodplain Analysis Domain

Purpose:
provide a navigation and cross-linking page for flood-oriented screening, floodplain context, and hydrology-linked risk review
help analysts and agents route flood questions into the correct hydrology, demographic, QA, and delivery canon
define the current reusable canon coverage for flood-related work without inventing a dedicated floodplain model, hydraulic workflow, or regulatory determination method the repo does not yet contain

## Domain Scope

This domain covers flood-related spatial analysis where the question is about flood exposure, floodplain context, watershed-linked risk review, and public-facing flood screening outputs.

It includes:
- floodplain and flood-risk screening framing
- watershed and terrain support for flood-related context
- demographic overlays for vulnerable populations in flood-exposed geographies
- review and delivery routing for flood-oriented outputs
- cross-routing to broader hazard, EJ, and resilience domains

It does not include:
- hydraulic modeling or stormwater engineering methodology
- regulatory flood determinations or permitting conclusions
- a dedicated floodplain-standard workflow not already present in the wiki
- full drainage-system design or stormwater network analysis

## Common Questions

- which people or geographies appear exposed to flood-related risk under the available screening layers?
- how should watershed and terrain workflows support flood-oriented screening?
- what can the current canon support defensibly, and what remains outside it?
- how should flood-oriented maps and summaries be reviewed before delivery?
- when should a project escalate from screening to higher-rigor legal or engineering review?

## Common Workflow Sequences

### Sequence 1: flood screening baseline

1. intake the flood-related layer through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. prepare terrain and watershed support through `domains/HYDROLOGY_AND_TERRAIN.md`
3. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
4. assemble outputs through `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md` and `qa-review/HYDROLOGY_OUTPUT_QA.md`

### Sequence 2: watershed-informed flood context

1. run `workflows/WATERSHED_DELINEATION.md` when watershed support is required
2. use `workflows/TERRAIN_DERIVATIVES.md` where slope, aspect, or related terrain context matters
3. combine with flood screening layers and demographic context
4. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: high-stakes flood review

1. complete the screening or context workflow
2. review with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
3. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the work is challenge-prone or approaching legal/regulatory use
4. state plainly when the output is a screening artifact rather than a regulatory flood determination

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of flood-related, terrain, and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for overlays, watersheds, and joins
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for challenge-prone or legal use
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential claims
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling across mixed metrics

## Key Workflows for This Domain

- `workflows/WATERSHED_DELINEATION.md` — watershed context and hydrologic support
- `workflows/TERRAIN_DERIVATIVES.md` — terrain-support workflow
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — flood-screening assembly and packaging
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic overlay support
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic vulnerability context

## Key QA Pages for This Domain

- `qa-review/HYDROLOGY_OUTPUT_QA.md` — hydrology-specific output review
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of flood-risk claims and framing
- `qa-review/MAP_QA_CHECKLIST.md` — flood-map delivery review
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when needed

## Key Data Sources for This Domain

- `data-sources/USGS_ELEVATION.md` — terrain and hydrologic support data
- `data-sources/CLIENT_SUPPLIED_DEMS.md` — client-supplied terrain support where relevant
- `data-sources/CENSUS_ACS.md` — demographic vulnerability context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for overlays and delivery
- `data-sources/LOCAL_FILES.md` — intake path for floodplain or flood-related context layers
- `data-sources/REMOTE_FILES.md` — downloadable flood-related layer intake

## Key Toolkits for This Domain

- `toolkits/GDAL_OGR_TOOLKIT.md` — raster/vector conversion and support
- `toolkits/GEOPANDAS_TOOLKIT.md` — overlays, joins, and packaging
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale spatial summarization support

## Domain-Specific Caveats

- the live canon supports flood-oriented screening and contextualization more than a full engineering or regulatory flood workflow
- flood maps can invite stronger conclusions than the available inputs and workflows justify
- higher-stakes flood work may need legal-grade or engineering review even when the spatial assembly is sound
- floodplain context, watershed context, and actual modeled inundation are not interchangeable

## Known Gaps in Current Canon

- there is no dedicated flood-risk standard or floodplain modeling workflow yet
- stormwater and drainage analysis remain separate future gaps
- there is no flood-specific QA page beyond the hydrology, structural, interpretive, map, and legal-grade layers
- regulatory floodplain determination remains outside current wiki method coverage

## Adjacent Domains

- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
