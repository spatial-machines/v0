# Land Use and Parcel Analysis Domain

Purpose:
provide a navigation and cross-linking page for parcel-oriented analysis, land-use context, and site-level geographic assembly work
help analysts and agents route land-use and parcel questions into the correct processing, accessibility, demographic, and delivery canon
define the current reusable canon coverage for parcel and land-use work without inventing a dedicated parcel data model or zoning methodology that does not yet exist in the repo

## Domain Scope

This domain covers spatial analysis where parcels, land-use context, or site footprints are the primary unit of work.

It includes:
- parcel and site-level spatial context analysis
- land-use and development-context framing
- parcel-adjacent demographic and access enrichment
- parcel and site assembly workflows built from the general processing and analysis canon
- delivery routing for parcel and land-use outputs

It does not include:
- a dedicated parcel-source standard or cadastral workflow not already present in the wiki
- formal zoning-code interpretation as its own method layer
- appraisal, valuation, or financial underwriting methodology
- full engineering or survey-grade parcel boundary validation

## Common Questions

- what is around this parcel or site today?
- how should parcel-level geometry be combined with tract, POI, or access context?
- what is the cleanest route from parcel file intake to map-ready site context output?
- how should parcel summaries be reviewed before external delivery?
- when does a parcel analysis remain contextual versus becoming a higher-stakes development recommendation?

## Common Workflow Sequences

### Sequence 1: parcel context baseline

1. intake parcel or site geometry through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. standardize and validate structure with `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
3. enrich with nearby context using `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. add tract-level demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` where needed
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: parcel + demographic + access context

1. prepare parcel geometry and identifiers through the general processing workflow
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. prepare access context through `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
4. assemble outputs through `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: parcel support for development review

1. intake site or parcel geometry through local or remote files
2. assemble surrounding facility and POI context through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
3. use `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md` where site-based distance context is required
4. review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of parcel, tract, and contextual layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for parcel geometry, buffering, and joins
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed parcel-adjacent summaries
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations when parcel work becomes challenge-prone

## Key Workflows for This Domain

- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — cleanup, normalization, and join preparation
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearby parcel/site context enrichment
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation when targets start as addresses
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic and tract context enrichment
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — parcel-context packaging and analysis assembly

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structure and field integrity checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of land-use and site-context claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of parcel and site maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when parcel work becomes consequential

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — parcel shapefiles, geodatabases, and client site files
- `data-sources/REMOTE_FILES.md` — downloadable parcel or land-use layers
- `data-sources/LOCAL_POSTGIS.md` — local spatial database support for contextual layers
- `data-sources/CENSUS_ACS.md` — demographic context for parcel and site summaries
- `data-sources/TIGER_GEOMETRY.md` — tract and boundary support for enrichment and delivery

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — parcel joins, overlays, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — format conversion, CRS handling, and geometry support
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale parcel-context summarization and support

## Domain-Specific Caveats

- parcel work often looks simple while hiding geometry cleanliness, identifier drift, and source-vintage issues
- parcel context does not automatically equal development suitability or entitlement feasibility
- higher-stakes parcel outputs may need stronger review than the base contextual workflow suggests
- parcel and land-use layers often vary substantially in completeness and interpretation by jurisdiction

## Known Gaps in Current Canon

- there is no dedicated parcel-source page or cadastral standard yet
- no first-class parcel rollup, parcel topology, or ownership-analysis workflow exists yet
- there is no parcel-specific QA page beyond the general structural, interpretive, map, and legal-grade layers
- land-use classification conventions remain a current method gap rather than a signed-off standard

## Adjacent Domains

- `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md`
- `domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
