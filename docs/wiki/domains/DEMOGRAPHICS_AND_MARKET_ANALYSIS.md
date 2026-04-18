# Demographics and Market Analysis Domain

Purpose:
provide a navigation and cross-linking page for demographic, market-context, trend, and shift-analysis canon
help analysts and agents start from common client questions rather than from isolated workflow names
define the current reusable canon coverage for demographic inventory, tract enrichment, trend analysis, and ZIP-oriented delivery

## Domain Scope

This domain covers recurring demographic and market-context analysis built from Census-style tabular data, tract geometry, aggregations, and comparative summaries.

It includes:
- first-wave demographic inventory
- tract-level joins and enrichment
- ZIP / ZCTA-oriented delivery from tract-based source geographies
- decade trend analysis
- demographic shift analysis
- market-context framing for client-facing analysis

It does not include:
- POI extraction and competitor landscape work (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- accessibility or drive-time analysis (see `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`)
- cartographic delivery and publication (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)
- source-family intake rules (see `data-sources/CENSUS_ACS.md` and `data-sources/TIGER_GEOMETRY.md`)

## Common Questions

- what does the study area look like demographically right now?
- which variables are safe for current snapshot versus long-term trend claims?
- how should tract-level demographic data be prepared for ZIP-oriented delivery?
- where is the population growing, declining, or shifting?
- which demographic changes matter enough to interpret for a client audience?

## Common Workflow Sequences

### Sequence 1: first-wave demographic inventory

1. read `standards/SOURCE_READINESS_STANDARD.md`
2. read `data-sources/CENSUS_ACS.md`
3. read `data-sources/TIGER_GEOMETRY.md`
4. run `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
5. if tract geometry needs enrichment, run `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
6. validate structure with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: trend-oriented demographic analysis

1. prepare inventory with `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
2. follow `standards/TREND_ANALYSIS_STANDARD.md`
3. run `workflows/DECADE_TREND_ANALYSIS.md`
4. review outputs with `qa-review/TREND_OUTPUT_REVIEW.md`
5. if packaging for delivery, continue into `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: demographic shift analysis

1. prepare tract-level enriched data with `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
2. read `standards/DEMOGRAPHIC_SHIFT_STANDARD.md`
3. run `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md`
4. validate interpretation with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
5. if ZIP-oriented delivery is required, apply `standards/ZIP_ZCTA_AGGREGATION_STANDARD.md` and review with `qa-review/ZIP_ROLLUP_REVIEW.md`

## Key Standards for This Domain

- `standards/TREND_ANALYSIS_STANDARD.md` — comparability and trend-claim rules
- `standards/DEMOGRAPHIC_SHIFT_STANDARD.md` — framing and interpretation rules for shift analysis
- `standards/ZIP_ZCTA_AGGREGATION_STANDARD.md` — tract-to-ZIP / ZCTA delivery rules
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — additive vs rate vs median handling
- `standards/SOURCE_READINESS_STANDARD.md` — source-tier assignment before reuse

## Key Workflows for This Domain

- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — first-wave inventory and retrieval planning
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract geometry + ACS-style tabular enrichment
- `workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md` — ZIP-oriented delivery workflow
- `workflows/DECADE_TREND_ANALYSIS.md` — long-horizon trend workflow
- `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md` — shift and comparative change workflow
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — general analysis conventions this domain specializes

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural checks before interpretation
- `qa-review/TREND_OUTPUT_REVIEW.md` — trend-specific output review
- `qa-review/ZIP_ROLLUP_REVIEW.md` — ZIP / ZCTA delivery review
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative and claim review

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — ACS demographic tabular source guidance
- `data-sources/TIGER_GEOMETRY.md` — Census geometry guidance
- `data-sources/LOCAL_FILES.md` — intake path for client-supplied demographic extracts
- `data-sources/REMOTE_FILES.md` — intake path for downloadable source tables

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, shaping, aggregation, and output prep
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale joins and geographic summarization
- `toolkits/GDAL_OGR_TOOLKIT.md` — format conversion and CRS-safe packaging

## Domain-Specific Caveats

- tract is often the real working geography even when the delivery is ZIP-oriented
- trend claims require stricter comparability discipline than current-snapshot summaries
- rates, shares, and medians cannot be rolled up with the same rules as additive counts
- demographic interpretation should stay bounded by source readiness, geography, and time coverage

## Known Gaps in Current Canon

- market ranking and peer-geography comparison do not yet have a dedicated workflow page
- trade-area penetration analysis is not yet a first-class workflow family
- uncertainty / MOE handling for advanced derived metrics is still a separate future standards gap
- there is no dedicated domain page yet for housing, affordability, or workforce analysis

## Adjacent Domains

- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DATA_ENGINEERING_AND_QA.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
