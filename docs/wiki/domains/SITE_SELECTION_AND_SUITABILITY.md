# Site Selection and Suitability Domain

Purpose:
provide a navigation and cross-linking page for candidate-site comparison, suitability framing, and location-screening work built from live parcel, access, demographic, POI, and environmental canon
help analysts and agents route site-selection questions into the correct reusable workflows without inventing a dedicated multi-criteria suitability standard the repo does not yet contain
define the current reusable canon coverage for site selection as a routing and synthesis layer rather than a formal scoring methodology

## Domain Scope

This domain covers work where the main question is how candidate sites compare across context, access, demographics, facilities, and environmental or parcel constraints.

It includes:
- candidate-site comparison framing
- suitability-oriented screening using live adjacent canon
- parcel, demographic, POI, access, and environmental context assembly
- delivery and review routing for site-selection outputs
- escalation guidance when suitability claims become too strong for the underlying workflow

It does not include:
- a dedicated multi-criteria decision model or weighting framework
- financial underwriting or investment scoring
- legal entitlement or permitting conclusions
- a signed-off site-suitability standard with thresholds or scoring rules

## Common Questions

- how should multiple candidate sites be compared using the current live canon?
- which site-context factors are supported today, and which remain a future method gap?
- what is the cleanest route from candidate-site list to reviewable suitability output?
- when should site selection stay a screening exercise rather than a ranked recommendation?
- how should suitability-style outputs be reviewed before external delivery?

## Common Workflow Sequences

### Sequence 1: candidate-site baseline

1. prepare candidate sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or parcel intake via `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
2. add demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. add POI context through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
4. add access context through `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: parcel and constraint-aware site screening

1. assemble parcel and site context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
2. add zoning or policy constraints through `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
3. add environmental or terrain support through `domains/HYDROLOGY_AND_TERRAIN.md` when relevant
4. package outputs with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. route final maps and deliverables through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: high-stakes suitability presentation

1. complete the screening workflow with live adjacent canon only
2. review claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
3. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the output may support challenge-prone or consequential decisions
4. state clearly when the result is a screening comparison rather than a final site recommendation

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness across mixed candidate-site inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for site comparisons, buffers, and overlays
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — mixed-metric handling in site comparison outputs
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential suitability claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for challenge-prone outputs

## Key Workflows for This Domain

- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — candidate-site preparation from addresses or named locations
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearby context enrichment for site comparison
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based access comparison when travel matters
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — cross-domain site-comparison packaging
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic context assembly

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of site comparison outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of suitability claims and overreach risk
- `qa-review/MAP_QA_CHECKLIST.md` — review of site-selection maps and comparison exhibits
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when the output is consequential

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — candidate-site, parcel, and client-supplied layers
- `data-sources/REMOTE_FILES.md` — downloadable constraint and contextual layers
- `data-sources/CENSUS_ACS.md` — demographic and neighborhood context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery
- `data-sources/LOCAL_POSTGIS.md` — contextual extraction and summarization support
- `data-sources/OSM.md` — amenity and facility context support
- `data-sources/USGS_ELEVATION.md` — environmental or terrain support when relevant

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, comparison layers, and packaging
- `toolkits/POSTGIS_TOOLKIT.md` — contextual extraction and site-comparison summarization at scale
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support

## Domain-Specific Caveats

- site selection work becomes misleading quickly if screening outputs are presented as formal ranking or guaranteed suitability
- candidate-site comparisons often combine layers with very different trust levels and intended uses
- the strongest current use of this canon is comparative context, not definitive scoring
- consequential site decisions may need much more review, legal input, or engineering support than the public workflow alone provides

## Known Gaps in Current Canon

- there is no dedicated site-suitability standard, scoring model, or weighting framework yet
- no first-class parcel-constraint ranking or tradeoff workflow exists yet
- there is no site-selection-specific QA page beyond the general structural, interpretive, map, and legal-grade layers
- site selection currently depends on assembling adjacent canon rather than following a dedicated signed-off method stack

## Adjacent Domains

- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
