# Community Facility Planning Domain

Purpose:
provide a navigation and cross-linking page for planning-oriented analysis of civic, educational, health-serving, and everyday community facilities
help analysts and agents route community-facility questions into the right demographic, accessibility, POI, and delivery canon
define the current reusable canon coverage for facility planning without inventing sector-specific planning methodology the firm has not yet formalized

## Domain Scope

This domain covers recurring analysis of facilities that serve communities directly, such as clinics, libraries, schools, civic sites, and related public-serving assets.

It includes:
- facility inventory and service-coverage framing
- demographic and neighborhood context around facilities
- site comparison and access analysis for community-serving assets
- packaging community-facility findings for maps, reports, and review sites
- cross-routing to healthcare, accessibility, and POI canon

It does not include:
- sector-specific healthcare ownership (see `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`)
- emergency-response planning as its own domain (see `domains/EMERGENCY_MEDICAL_SERVICE_COVERAGE.md`)
- parcel, zoning, or full site-suitability methodology
- school-performance, library-program, or other non-spatial service-quality evaluation

## Common Questions

- where are community-serving facilities located today?
- which populations are well-served or underserved by the current facility pattern?
- how should facility access be measured for planning questions?
- how do we combine facility locations with tract-level demographic context?
- what is the right delivery format for a facility-planning analysis?

## Common Workflow Sequences

### Sequence 1: community facility baseline

1. retrieve or intake facility data through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` or `workflows/SERVICE_AREA_ANALYSIS.md`
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. review final claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 2: site comparison or candidate-facility review

1. prepare sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. retrieve surrounding facilities through `workflows/POSTGIS_POI_LANDSCAPE.md`
3. enrich with demographic context using `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
4. route outputs into `domains/CARTOGRAPHY_AND_DELIVERY.md` for presentation

### Sequence 3: community facility access mapping

1. clean facility categories through `workflows/POI_CATEGORY_NORMALIZATION.md` if needed
2. build access zones with `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
3. validate maps with `qa-review/MAP_QA_CHECKLIST.md`
4. publish or package through the delivery domain

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of facility inventories and demographic context
- `standards/CRS_SELECTION_STANDARD.md` — projected CRS discipline for access work
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling across mixed metrics
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — community-facility extraction support
- `workflows/POI_CATEGORY_NORMALIZATION.md` — facility category cleanup
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site and candidate location preparation
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean access and coverage analysis
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based coverage analysis
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic context enrichment

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural review of facility outputs and enrichment
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of planning claims and narrative framing
- `qa-review/MAP_QA_CHECKLIST.md` — review of community-facility maps and presentation products
- `qa-review/POI_EXTRACTION_QA.md` — extraction review when open-source facility retrieval is used

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — local open geodata and facility extraction support
- `data-sources/OSM.md` — OSM-backed community facility context
- `data-sources/CENSUS_ACS.md` — demographic and neighborhood context
- `data-sources/TIGER_GEOMETRY.md` — tract and boundary geometry for enrichment and delivery
- `data-sources/LOCAL_FILES.md` — client or analyst-supplied facility inventories
- `data-sources/REMOTE_FILES.md` — downloadable public facility tables

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — extraction, summarization, and spatial scale support
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, packaging, and spatial enrichment
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and delivery support

## Domain-Specific Caveats

- community-facility planning often blends access, demographics, and sector-specific judgment that the current canon does not fully formalize
- not every planning question needs a network model, but Euclidean distance can be misleading if used by default
- facility inventories can hide naming, category, and duplication problems that materially affect the output
- planning maps often invite stronger claims than the workflow itself supports, so interpretive review matters

## Known Gaps in Current Canon

- there is no dedicated domain page yet for schools, libraries, parks, or civic assets as separate sectors
- no full site-suitability or parcel-constrained facility-planning workflow exists yet
- facility-priority scoring and multi-criteria planning logic are not yet first-class canon
- there is no dedicated community-facility QA page beyond the general structural, interpretive, map, and POI layers

## Adjacent Domains

- `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
- `domains/PROVIDER_NETWORK_AND_CLINIC_ACCESS.md`
- `domains/PHARMACY_AND_FOOD_ACCESS.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
