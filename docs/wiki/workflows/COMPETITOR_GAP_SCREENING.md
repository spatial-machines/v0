# Competitor Gap Screening Workflow

Purpose:
define a repeatable process for identifying geographic gaps in competitor or category coverage
produce screening outputs that show where demand indicators are present but competitor or service density is low
support white-space identification, market opportunity framing, and downstream site-selection or trade-area work

Typical Use Cases
- where are there potential customers but few or no competitors in this category?
- which areas have high population density or favorable demographics but low business presence?
- how does competitor density vary across a set of trade areas or study geographies?
- where should the next location go based on competitive context?

Inputs
- study area boundary or set of study geographies (tracts, ZCTAs, trade areas, custom zones)
- competitor or category POI layer (extracted and normalized)
- demand indicator layers (demographic variables, population counts, household income, or other approved proxies)
- project-approved working CRS
- approved category definitions for competitor classification

Preconditions
- POI extraction is complete and validated per `qa-review/POI_EXTRACTION_QA.md`
- category normalization is complete per `workflows/POI_CATEGORY_NORMALIZATION.md`
- demand indicators are available and source-ready per `standards/SOURCE_READINESS_STANDARD.md`
- the CRS has been confirmed per `standards/CRS_SELECTION_STANDARD.md`
- the project lead has approved the competitor category definition and the demand proxy variables

Preferred Tools
- PostGIS for scale and spatial query work (`toolkits/POSTGIS_TOOLKIT.md`)
- GeoPandas for in-memory analysis and output prep (`toolkits/GEOPANDAS_TOOLKIT.md`)
- GDAL/OGR for conversion and packaging (`toolkits/GDAL_OGR_TOOLKIT.md`)

Execution Order

## Phase 1: Competitor Layer Preparation

1. Extract competitor POIs using `workflows/POSTGIS_POI_LANDSCAPE.md`.
2. Normalize categories using `workflows/POI_CATEGORY_NORMALIZATION.md`.
3. Validate extraction with `qa-review/POI_EXTRACTION_QA.md`.
4. Confirm the final competitor category definition is documented.

## Phase 2: Demand Layer Preparation

1. Prepare demographic demand indicators using `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md`.
2. Select the approved demand proxy variables (e.g., total population, households, median income, target demographic segment).
3. Confirm demand data is at the appropriate geography (tract, ZCTA, or custom zone).

## Phase 3: Competitor Density Calculation

1. Define the analysis geography: tracts, ZCTAs, trade-area polygons, hex grids, or other approved zones.
2. Count competitor POIs within each zone using spatial joins.
3. Calculate competitor density: POI count per zone, per capita, per household, or per approved denominator.
4. Document the density metric and denominator used.

## Phase 4: Gap Identification

1. For each zone, compare competitor density against demand indicators.
2. Flag zones where demand indicators are above a project-defined threshold but competitor density is below a project-defined threshold (the "white-space" zones).
3. If no explicit thresholds are provided, present the data as a continuous comparison (demand vs. density) rather than a binary classification.
4. Do not invent thresholds — if the project has not defined what constitutes "underserved" or "high opportunity," present the spatial pattern and escalate the threshold question.

## Phase 5: Contextual Enrichment

1. Add accessibility context through `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md` if the project requires it.
2. Add additional business-landscape context through `workflows/POSTGIS_POI_LANDSCAPE.md` (complementary businesses, anchor tenants, etc.).
3. If trade-area framing is needed, route through `workflows/TRADE_AREA_DELINEATION.md`.

## Phase 6: Validation and Output

1. Validate structural integrity with `qa-review/STRUCTURAL_QA_CHECKLIST.md`.
2. Review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — low competitor density does not automatically mean high opportunity.
3. Generate map-ready layers showing demand-density comparison.
4. Package outputs: zone-level comparison table, gap-flagged zones, methodology documentation.
5. Route maps through `domains/CARTOGRAPHY_AND_DELIVERY.md`.

Validation Checks
- competitor category definition is documented and matches the project-approved scope
- demand proxy variables are documented and appropriate for the question
- density metric and denominator are documented
- gap identification thresholds are project-approved (not analyst-invented)
- zones with low competitor counts are checked for plausibility (could reflect source coverage gaps rather than real white space)
- the output distinguishes between "low competition" and "low competition plus high demand"

Common Failure Modes
- using POI source data with coverage gaps and interpreting missing data as white space
- inventing gap thresholds without project approval
- treating low competitor density as proof of market opportunity without examining demand indicators
- not normalizing competitor counts by population or appropriate denominator (raw counts favor dense areas)
- confusing absence from the POI source with absence from the market (OSM may undercount, especially for newer or smaller businesses)
- presenting continuous density data as a binary gap/no-gap classification without discussing the threshold choice
- not documenting the competitor category definition, making the analysis non-reproducible
- double-counting competitors that appear under multiple categories after normalization

Escalate When
- the client requires a specific competitive scoring or ranking methodology not yet in the wiki canon
- the POI source has obvious coverage gaps that would create false white-space signals
- the project requires gravity-model or demand-allocation methods for competitive analysis
- the gap screening output will be used for investment, real estate, or franchise decisions
- the competitor category is ambiguous and the resolution could materially change the results
- the client provides proprietary competitor data with licensing restrictions

Outputs
- zone-level comparison table (demand indicators, competitor counts, density metrics)
- gap-flagged zones (if thresholds are approved)
- competitor density map
- demand vs. density comparison map
- methodology documentation
- map-ready layers

Related Standards
- `standards/SOURCE_READINESS_STANDARD.md`
- `standards/CRS_SELECTION_STANDARD.md`
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`
- `standards/OPEN_EXECUTION_STACK_STANDARD.md`
- `standards/INTERPRETIVE_REVIEW_STANDARD.md`

Related Workflows
- `workflows/POSTGIS_POI_LANDSCAPE.md`
- `workflows/POI_CATEGORY_NORMALIZATION.md`
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
- `workflows/SERVICE_AREA_ANALYSIS.md`
- `workflows/TRADE_AREA_DELINEATION.md`
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`

Related QA
- `qa-review/POI_EXTRACTION_QA.md`
- `qa-review/STRUCTURAL_QA_CHECKLIST.md`
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
- `qa-review/MAP_QA_CHECKLIST.md`

Trust Level
Draft Workflow Needs Testing
