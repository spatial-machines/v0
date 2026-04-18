# POI and Business Landscape Domain

Purpose:
provide a navigation and cross-linking page for point-of-interest extraction, category normalization, areal enrichment, and business-landscape analysis
help analysts and agents move from location-context questions to the right POI, enrichment, and delivery workflows
define the current reusable canon coverage for open-stack POI analysis using OSM and local PostGIS sources

## Domain Scope

This domain covers point-of-interest retrieval, cleaning, summarization, enrichment, and communication for business, amenity, competitor, and facility landscape work.

It includes:
- POI retrieval from local PostGIS / OSM-backed sources
- category normalization and taxonomy cleanup
- POI counts and summaries within study geographies, buffers, and service areas
- business landscape and competitor-context mapping
- areal enrichment of POI outputs for client-facing analysis

It does not include:
- Census demographic workflow ownership (see `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`)
- network-travel modeling and isochrones (see `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`)
- final delivery, map packaging, and publication (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)
- general processing conventions that apply to every dataset (see `domains/DATA_ENGINEERING_AND_QA.md`)

## Common Questions

- what businesses, amenities, or competitors are in the study area?
- how should OSM or PostGIS categories be normalized before analysis?
- how many relevant POIs fall within a tract, buffer, or service area?
- does the extracted POI landscape look plausible for the geography?
- what is the cleanest way to package POI outputs for review and delivery?

## Common Workflow Sequences

### Sequence 1: business landscape baseline

1. confirm source readiness with `standards/SOURCE_READINESS_STANDARD.md`
2. read `data-sources/LOCAL_POSTGIS.md` and `data-sources/OSM.md`
3. run `workflows/POSTGIS_POI_LANDSCAPE.md`
4. if category cleanup is required, run `workflows/POI_CATEGORY_NORMALIZATION.md`
5. validate with `qa-review/POI_EXTRACTION_QA.md` and `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: POI enrichment around candidate sites

1. prepare target geometry with `workflows/GEOCODE_BUFFER_ENRICHMENT.md` or use validated existing geometry
2. if Euclidean distance is approved, run `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
3. if network travel is required, run `workflows/SERVICE_AREA_ANALYSIS.md`
4. use cleaned POI outputs from `workflows/POSTGIS_POI_LANDSCAPE.md`
5. validate the extraction and counts with `qa-review/POI_EXTRACTION_QA.md`

### Sequence 3: POI + demographic context analysis

1. prepare POI layer with `workflows/POSTGIS_POI_LANDSCAPE.md`
2. prepare tract enrichment with `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
3. run `workflows/WITHIN_DISTANCE_ENRICHMENT.md` or `workflows/SERVICE_AREA_ANALYSIS.md` as appropriate
4. review structural integrity with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. continue into `domains/CARTOGRAPHY_AND_DELIVERY.md` for client-facing packaging

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — whether the source is fit for the requested use
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — how to handle areal summaries and mixed metric types
- `standards/CRS_SELECTION_STANDARD.md` — CRS requirements for joins, buffering, and enrichment
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — main POI retrieval and analysis workflow
- `workflows/POI_CATEGORY_NORMALIZATION.md` — category cleanup and normalization
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean enrichment around existing geometry
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — address-to-buffer enrichment workflow
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based service-area enrichment
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — general analysis conventions this domain specializes

## Key QA Pages for This Domain

- `qa-review/POI_EXTRACTION_QA.md` — POI-specific extraction review
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural output checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative review when POI findings support client claims

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — local POI and open geodata stack guidance
- `data-sources/OSM.md` — OSM source-family guidance
- `data-sources/LOCAL_FILES.md` — intake path for client-provided POI lists or facility inventories
- `data-sources/REMOTE_FILES.md` — intake path for downloadable POI or facility tables

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — preferred engine for scale and spatial query work
- `toolkits/GEOPANDAS_TOOLKIT.md` — extraction, shaping, joins, and light-weight enrichment
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- category logic is often the real analytical decision, not just a preprocessing detail
- OSM and local PostGIS sources are powerful but coverage can vary by geography and category
- POI counts can look precise while still hiding taxonomy ambiguity, duplicate handling decisions, or source staleness
- business landscape claims should separate raw extraction from cleaned and normalized analysis outputs

## Known Gaps in Current Canon

- there is no dedicated workflow yet for white-space analysis or competitor ranking
- formal trade-area penetration analysis is not yet a first-class workflow family
- there is no standalone domain page yet for retail, hospitality, or tourism analysis
- branded-chain normalization and advanced taxonomy governance remain handbook / project-level rather than wiki-standardized

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DATA_ENGINEERING_AND_QA.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
