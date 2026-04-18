# Real Estate and Development Context Domain

Purpose:
provide a navigation and cross-linking page for market-facing site context, development framing, and location intelligence around parcels and candidate sites
help analysts and agents route real-estate and development questions into the correct parcel, demographic, POI, access, and delivery canon
define the current reusable canon coverage for development context without inventing underwriting, valuation, or brokerage methodology the repo does not yet contain

## Domain Scope

This domain covers site and development work where the central question is how a parcel or location sits within its market, access, and community context.

It includes:
- development-context framing for parcels and candidate sites
- demographic and neighborhood context around sites
- nearby amenity, facility, and access context
- map and review routing for real-estate and development presentations
- cross-routing to parcel, zoning, site-selection, and POI canon

It does not include:
- valuation, underwriting, absorption, or appraisal methodology
- legal entitlement interpretation
- brokerage comps, pricing models, or investment scoring
- a dedicated market-ranking or site-scoring workflow not already present in the wiki

## Common Questions

- what kind of demographic, amenity, and access context surrounds this site?
- how should site and parcel work be framed for a development or market audience?
- what nearby resources, destinations, and facilities matter for development context?
- what can the current canon support as location intelligence without implying financial advice?
- how should development-context outputs be reviewed before external delivery?

## Common Workflow Sequences

### Sequence 1: development context baseline

1. assemble parcel or site geometry through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. prepare amenities and destinations through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
4. add access context through `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: candidate site review

1. prepare sites with `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. enrich surrounding context with `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
3. add tract-level demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
4. package analysis through `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: development presentation workflow

1. complete site-context assembly using parcel, demographic, POI, and access canon
2. review narrative claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
3. review public-facing maps with `qa-review/MAP_QA_CHECKLIST.md`
4. state clearly when the output is contextual rather than financial or entitlement advice

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of parcel, demographic, POI, and access layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for site and parcel context assembly
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling across mixed site-context metrics
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential narrative claims

## Key Workflows for This Domain

- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation from address or named location inputs
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearby context enrichment around sites
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic context enrichment
- `workflows/POSTGIS_POI_LANDSCAPE.md` — destination and amenity context extraction
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — packaging development-context outputs

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structure and field integrity checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of development-context claims and overreach risk
- `qa-review/MAP_QA_CHECKLIST.md` — review of market-facing site and development maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — parcel, site, and client-supplied development layers
- `data-sources/REMOTE_FILES.md` — downloadable parcel, policy, or contextual layers
- `data-sources/CENSUS_ACS.md` — demographic and neighborhood context
- `data-sources/TIGER_GEOMETRY.md` — tract and boundary support for delivery and enrichment
- `data-sources/LOCAL_POSTGIS.md` — open geodata and contextual extraction support
- `data-sources/OSM.md` — amenity and POI context support

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, enrichment, and site-context packaging
- `toolkits/POSTGIS_TOOLKIT.md` — contextual extraction and spatial summarization at scale
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support

## Domain-Specific Caveats

- development-context work can drift into valuation or entitlement claims that the current canon does not support
- site intelligence is strongest when it stays explicit about what is contextual, what is demographic, and what is access-related
- polished maps can imply more certainty than the underlying workflow actually provides
- parcel, market, and amenity layers often come from different vintages and need careful provenance handling

## Known Gaps in Current Canon

- there is no dedicated site-scoring, underwriting, or valuation workflow yet
- no first-class comps, absorption, or financial analysis canon exists yet
- there is no real-estate-specific QA page beyond the general structural, interpretive, and map layers
- development context is currently assembled from adjacent canon rather than owned by a dedicated standards stack

## Adjacent Domains

- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
