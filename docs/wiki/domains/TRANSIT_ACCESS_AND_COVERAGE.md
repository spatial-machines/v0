# Transit Access and Coverage Domain

Purpose:
provide a navigation and cross-linking page for transit-access, coverage, and public-transport reachability questions built from the live accessibility and demographic canon
help analysts and agents route transit-oriented questions into the correct reusable workflows while preserving clear method boundaries
define the current reusable canon coverage for transit-access framing without inventing a dedicated transit-network or schedule-based analysis methodology that does not yet exist in the repo

## Domain Scope

This domain covers spatial analysis where the question is how people, sites, or facilities relate to transit access and public-transport coverage.

It includes:
- transit-access framing and screening
- demographic context for transit coverage questions
- site and facility context around transit reachability
- delivery routing for transit-oriented maps and summaries
- cross-routing to accessibility, community-facility, and development-context canon

It does not include:
- schedule-based transit travel-time modeling
- GTFS-driven accessibility workflows not already present in the repo
- transit service planning or route optimization methodology
- causal mobility or ridership analysis beyond the live canon

## Common Questions

- which populations appear well-served or underserved by transit access?
- how should transit context be paired with demographic and facility layers?
- what can the current canon support defensibly for transit screening today?
- when should a transit-oriented project stay a screening exercise rather than a full network model?
- how should transit-access outputs be reviewed before delivery?

## Common Workflow Sequences

### Sequence 1: transit-oriented access screening

1. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
2. intake or validate transit-related geography through `data-sources/LOCAL_FILES.md` or `data-sources/REMOTE_FILES.md`
3. use `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md` for the nearest live access workflow that matches the question
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review interpretation with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: site and transit context review

1. prepare candidate sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. assemble surrounding demographic context through `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` when the question is a simple proximity screen
4. route outputs into `domains/CARTOGRAPHY_AND_DELIVERY.md`

### Sequence 3: transit within broader planning context

1. prepare transit-access screening outputs through this domain
2. route public-serving asset questions into `domains/COMMUNITY_FACILITY_PLANNING.md`
3. route site comparison questions into `domains/SITE_SELECTION_AND_SUITABILITY.md`
4. state clearly when the result is transit screening rather than full network-performance analysis

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of transit and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for joins, overlays, and proximity analysis
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — handling mixed summary metrics
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for consequential accessibility claims

## Key Workflows for This Domain

- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation for transit-context studies
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — simple transit-proximity screening support
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — packaging transit-oriented outputs
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic context enrichment
- `workflows/SERVICE_AREA_ANALYSIS.md` — adjacent workflow when a network-based access proxy is used

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of transit-access outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of transit-access and equity claims
- `qa-review/MAP_QA_CHECKLIST.md` — review of public-facing transit-access maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — client or analyst-supplied transit layers
- `data-sources/REMOTE_FILES.md` — downloadable transit, stop, or service-area layers
- `data-sources/CENSUS_ACS.md` — demographic context for access screening
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for enrichment and delivery
- `data-sources/OSM.md` — open geodata context for station and street support where relevant

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, overlays, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support
- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale contextual summarization and support

## Domain-Specific Caveats

- the current canon supports transit-access screening more than full transit-network analysis
- transit accessibility can overreach quickly if schedule quality or service frequency are implied without a real method
- proximity to transit does not automatically equal useful mobility access
- transit questions often need explicit distinction between screening, planning context, and full operational modeling

## Known Gaps in Current Canon

- there is no dedicated transit-access workflow, GTFS workflow, or transit QA page yet
- schedule-based travel-time and transfer modeling are not live canon
- no transit-specific standard exists yet for service-quality or access interpretation
- transit work is currently routing-rich but method-light

## Adjacent Domains

- `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md`
- `domains/PEDESTRIAN_AND_BICYCLE_ACCESS.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
