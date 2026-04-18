# Crime, Public Safety, and Incident Mapping Domain

Purpose:
provide a navigation and cross-linking page for crime mapping, public safety analysis, and incident-pattern spatial work
help analysts and agents route public safety and crime-pattern questions into the correct reusable spatial statistics, demographic, POI, and delivery workflows
define the current reusable canon coverage for crime and incident mapping without inventing predictive policing methodology, risk scoring, or public safety standards the repo does not yet contain

## Domain Scope

This domain covers work where the main question is where crimes or public safety incidents concentrate, how incident patterns relate to demographic and spatial context, and how findings should be mapped for planning or policy audiences.

It includes:
- crime and incident mapping using point-pattern and areal methods
- spatial statistics applied to incident data (hotspot, clustering, autocorrelation)
- demographic and neighborhood context for public safety analysis
- cross-routing to spatial statistics, policy communication, and equity domains
- delivery routing for public safety maps and products

It does not include:
- predictive policing or recidivism modeling
- law enforcement operational planning or dispatch optimization
- individual-level risk scoring or criminal justice recommendation
- emergency response coverage modeling (see `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`)
- general spatial statistics not applied to public safety (see the spatial statistics canon directly)

## Common Questions

- where do crimes or incidents concentrate geographically?
- are observed spatial patterns statistically significant or could they be random?
- how does crime incidence relate to demographic, economic, or land-use context?
- how should public safety maps be reviewed to avoid misleading or stigmatizing presentation?
- what spatial methods are supported by the current canon for incident-pattern analysis?

## Common Workflow Sequences

### Sequence 1: incident hotspot analysis

1. intake incident data through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. confirm source readiness with `standards/SOURCE_READINESS_STANDARD.md`
3. run `workflows/HOTSPOT_ANALYSIS.md`
4. validate with `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md`
5. design maps with `workflows/HOTSPOT_MAP_DESIGN.md`
6. review with `qa-review/MAP_QA_CHECKLIST.md` and `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: incident clustering and spatial autocorrelation

1. prepare incident data at appropriate geography
2. run `workflows/SPATIAL_AUTOCORRELATION_TEST.md`
3. if local clusters are needed, run `workflows/LISA_CLUSTER_ANALYSIS.md`
4. validate with `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md`
5. review claims about pattern significance and interpretation

### Sequence 3: incident context with demographic framing

1. prepare incident spatial analysis through sequences above
2. add demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md` and `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`
3. add POI or facility context through `workflows/POSTGIS_POI_LANDSCAPE.md` if relevant
4. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
5. review carefully with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — correlation with demographics must not be presented as causation
6. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when the output could influence policy or enforcement decisions

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of incident and demographic inputs
- `standards/SPATIAL_STATS_STANDARD.md` — spatial statistics rigor for pattern detection
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for point-pattern and areal work
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for enforcement or policy outputs
- `standards/CARTOGRAPHY_STANDARD.md` — cartographic conventions for sensitive public safety maps

## Key Workflows for This Domain

- `workflows/HOTSPOT_ANALYSIS.md` — spatial hotspot detection
- `workflows/SPATIAL_AUTOCORRELATION_TEST.md` — global spatial autocorrelation testing
- `workflows/LISA_CLUSTER_ANALYSIS.md` — local cluster identification
- `workflows/HOTSPOT_MAP_DESIGN.md` — hotspot map design and presentation
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic context enrichment
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — demographic inventory for context
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — output packaging
- `workflows/CHOROPLETH_DESIGN.md` — areal map design for rate-based presentation

## Key QA Pages for This Domain

- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — review of spatial statistics outputs
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of analysis outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of claims about crime patterns and context
- `qa-review/MAP_QA_CHECKLIST.md` — review of public safety maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review for consequential outputs

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client or agency-supplied incident, crime, and call-for-service data
- `data-sources/REMOTE_FILES.md` — downloadable crime and incident datasets
- `data-sources/CENSUS_ACS.md` — demographic context for neighborhood-level framing
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support
- `data-sources/LOCAL_POSTGIS.md` — contextual layer support at scale
- `data-sources/OSM.md` — open geodata for facility and infrastructure context

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — spatial joins, aggregation, and output preparation
- `toolkits/POSTGIS_TOOLKIT.md` — spatial query and summarization at scale
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- crime and incident data reflects reporting and recording practices, not objective ground truth — underreporting, classification differences, and jurisdictional boundaries all shape the data
- spatial patterns in crime data can appear significant but may reflect patrol allocation, reporting bias, or demographic proxies rather than true incidence variation
- correlating crime incidence with demographic characteristics requires extreme interpretive caution to avoid stigmatizing communities or implying causation
- public safety maps carry unusually high interpretive weight and can directly influence enforcement, investment, and community perception
- this domain requires the highest level of interpretive and legal-grade review before public release

## Known Gaps in Current Canon

- there is no dedicated crime mapping standard, incident data intake methodology, or public safety analysis workflow yet
- address geocoding and incident data normalization for crime mapping are not yet wiki-standardized
- temporal pattern analysis (time-of-day, day-of-week, seasonal) is not yet a first-class workflow
- there is no dedicated public safety QA page beyond the general spatial statistics, interpretive, map, and legal-grade layers
- source-policy guidance for sensitive incident data (CJIS, privacy, redaction) is not yet first-class canon

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/POLICY_SUPPORT_AND_PUBLIC_COMMUNICATION_MAPS.md`
- `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`
- `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
