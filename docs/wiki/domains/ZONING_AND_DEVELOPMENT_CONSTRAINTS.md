# Zoning and Development Constraints Domain

Purpose:
provide a navigation and cross-linking page for zoning-context, development-constraint, and site-feasibility framing questions
help analysts and agents route zoning and constraint questions into the correct parcel, accessibility, demographic, and delivery canon
define the current reusable canon coverage for zoning and development constraints without inventing a formal zoning interpretation standard or entitlement methodology that does not yet exist in the repo

## Domain Scope

This domain covers site and development-context work where zoning, constraints, or allowed-use questions shape the interpretation of a parcel or candidate site.

It includes:
- zoning and development-constraint framing
- parcel and site-context assembly
- access, neighborhood, and facility context around constrained sites
- delivery routing for development-constraint maps and summaries
- escalation guidance when a site question approaches legal or entitlement interpretation

It does not include:
- a dedicated zoning-code parsing or entitlement workflow
- legal interpretation of development rights
- engineering or environmental permitting methodology
- full multi-criteria site-suitability scoring as a signed-off method

## Common Questions

- what spatial constraints appear to affect this site or parcel?
- how should parcel context, surrounding uses, and accessibility be assembled for a development review?
- what can the current canon support defensibly without overclaiming legal or zoning certainty?
- how should zoning-oriented outputs be reviewed before delivery?
- when should the work be described as screening rather than definitive entitlement guidance?

## Common Workflow Sequences

### Sequence 1: zoning and constraint context baseline

1. intake parcel, zoning, or constraint layers through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. standardize geometry and fields with `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
3. assemble parcel context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
4. add surrounding access or facility context through `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md` or `domains/POI_AND_BUSINESS_LANDSCAPE.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: candidate-site development review

1. prepare sites with `workflows/GEOCODE_BUFFER_ENRICHMENT.md` if needed
2. assemble parcel and land-use context through `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
3. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` or `workflows/SERVICE_AREA_ANALYSIS.md` when nearby context matters
4. package outputs with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. route delivery through `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: high-stakes constraint review

1. complete the screening or context workflow
2. review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
3. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the work approaches legal, permitting, or challenge-prone use
4. state clearly when the output is contextual screening rather than final zoning or entitlement advice

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of zoning, parcel, and contextual layers
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for site overlays and joins
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling for mixed site-context metrics
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for challenge-prone use cases
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — zoning and constraint layer cleanup
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation from addresses or named locations
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearby context analysis around candidate sites
- `workflows/SERVICE_AREA_ANALYSIS.md` — access-oriented development context when network travel matters
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — packaging development-context outputs

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structure and geometry integrity checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of zoning and development-constraint claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of site and zoning maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when outputs become consequential

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client-supplied parcel, zoning, and constraint layers
- `data-sources/REMOTE_FILES.md` — downloadable zoning or policy layers
- `data-sources/LOCAL_POSTGIS.md` — local contextual layer support and summarization
- `data-sources/CENSUS_ACS.md` — demographic context around candidate sites
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — overlays, joins, and site-context packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — format conversion and CRS support
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale site-context summarization and support

## Domain-Specific Caveats

- zoning and development constraints are easy to overstate if the workflow is treated as legal interpretation rather than spatial context
- local zoning and land-use layers often carry jurisdiction-specific semantics that the current canon does not normalize automatically
- site screening can be useful without being definitive, and the page should preserve that distinction
- high-stakes development questions often need stronger review and human judgment than the base workflow alone provides

## Known Gaps in Current Canon

- there is no dedicated zoning standard, entitlement workflow, or land-use-classification standard yet
- no dedicated zoning QA page exists beyond the general structural, interpretive, map, and legal-grade layers
- parcel-policy joins and constraint ranking are not yet first-class canon
- development-constraint work is currently routing-rich but method-light

## Adjacent Domains

- `domains/LAND_USE_AND_PARCEL_ANALYSIS.md`
- `domains/REAL_ESTATE_AND_DEVELOPMENT_CONTEXT.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
