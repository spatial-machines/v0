# Transportation Safety and Crash Analysis Domain

Purpose:
provide a navigation and cross-linking page for transportation-safety, crash-context, and roadway-risk screening questions built from the live accessibility, demographic, and delivery canon
help analysts and agents route safety-oriented transportation questions into the correct reusable workflows while preserving clear method boundaries
define the current reusable canon coverage for transportation safety as a routing and screening layer rather than a full crash-analysis methodology

## Domain Scope

This domain covers spatial analysis where the question is how transportation safety issues, crash context, or roadway-risk concerns should be screened and presented spatially.

It includes:
- transportation-safety and crash-context screening
- demographic and community context around safety concerns
- site and corridor context assembly using live general workflows
- delivery routing for transportation-safety outputs
- cross-routing to access, community, and resilience domains when appropriate

It does not include:
- a dedicated crash-database workflow or safety-performance standard
- causal crash modeling, exposure normalization, or corridor engineering methodology
- route design or traffic operations modeling
- enforcement, behavioral, or policy evaluation beyond the live canon

## Common Questions

- how should transportation-safety concerns be represented spatially with the current canon?
- what demographic or community context can be paired with crash or roadway-risk layers?
- when is the output a screening artifact rather than a full safety analysis?
- how should transportation-safety outputs be reviewed before delivery?
- which adjacent domain should own the underlying access or site methodology?

## Common Workflow Sequences

### Sequence 1: crash-context screening baseline

1. intake crash or roadway-risk layers through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. assemble outputs using `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` and `workflows/TRACT_JOIN_AND_ENRICHMENT.md` where appropriate
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: site or corridor safety context

1. prepare sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` to assemble nearby safety context when appropriate
3. route access and mobility framing through `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
4. review maps with `qa-review/MAP_QA_CHECKLIST.md`

### Sequence 3: safety within broader public-service context

1. prepare transportation-safety screening outputs through this domain
2. route community-serving asset implications through `domains/COMMUNITY_FACILITY_PLANNING.md` when relevant
3. state clearly when the result is screening context rather than a formal safety-performance analysis

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of crash, roadway, and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for joins, overlays, and proximity work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — mixed summary handling when safety outputs are aggregated
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential safety claims
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations when the work becomes challenge-prone

## Key Workflows for This Domain

- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — screening assembly and packaging
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic context enrichment
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation for corridor or intersection context
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — nearby safety-context enrichment support

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of safety outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of crash and safety claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of public-facing safety maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review when the output is challenge-prone or consequential

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — local crash, corridor, or roadway-risk layers
- `data-sources/REMOTE_FILES.md` — downloadable crash or transportation context layers
- `data-sources/CENSUS_ACS.md` — demographic and equity context
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for summaries and delivery
- `data-sources/OSM.md` — roadway and contextual open geodata support when relevant

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale contextual summarization and support

## Domain-Specific Caveats

- the current canon supports transportation-safety screening more than full crash analysis
- crash maps and risk maps can appear more definitive than the underlying workflow actually justifies
- safety conclusions often require stronger exposure, normalization, or engineering method than the live canon currently contains
- high-stakes safety outputs may need legal-grade or domain-expert review beyond the base workflow

## Known Gaps in Current Canon

- there is no dedicated crash-analysis workflow, safety standard, or transportation-safety QA page yet
- exposure-normalized crash metrics and corridor prioritization are not live canon
- traffic operations, roadway design, and engineering methodology remain future gaps
- transportation safety is currently routing-rich but method-light

## Adjacent Domains

- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`
- `domains/PEDESTRIAN_AND_BICYCLE_ACCESS.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
