# Cartography and Delivery Domain

Purpose:
provide a navigation and cross-linking page for the firm's delivery-oriented standards, workflows, and QA pages
help analysts and agents find the right page for map production, package handoff, review-site publication, and client delivery
define the domain scope and common workflow sequences for the cartography and delivery family

## Domain Scope

This domain covers the final stages of the analysis pipeline: turning validated analytical outputs into client-ready deliverables.

It includes:
- map design and cartographic quality
- review-site building and publication
- QGIS project packaging for offline handoff
- delivery format selection and preparation
- publishing readiness assessment
- attribution, licensing, and metadata for client outputs

It does not include:
- analytical workflows that produce the underlying data
- data source selection or retrieval as a primary domain
- structural or interpretive QA of the underlying analysis except as delivery gates
- role governance or project-specific client handling

## Common Questions

- what map design workflow fits this deliverable?
- when should a deliverable be a review site versus a QGIS package versus a data-only handoff?
- which QA pages must be run before publishing or client delivery?
- what provenance and metadata must travel with the output?
- which design rules are mandatory for the relevant map family?

## Common Workflow Sequences

### Sequence 1: review-site delivery

1. complete the upstream analytical workflow and validation checks
2. run `qa-review/STRUCTURAL_QA_CHECKLIST.md`
3. run the relevant domain QA page such as `qa-review/TREND_OUTPUT_REVIEW.md`, `qa-review/ZIP_ROLLUP_REVIEW.md`, `qa-review/POI_EXTRACTION_QA.md`, or `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md`
4. run `qa-review/MAP_QA_CHECKLIST.md`
5. run `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
6. confirm provenance with `standards/PROVENANCE_AND_HANDOFF_STANDARD.md`
7. build and publish with `workflows/REVIEW_SITE_PUBLISHING.md`
8. confirm `standards/PUBLISHING_READINESS_STANDARD.md`

### Sequence 2: QGIS package delivery

1. complete the upstream analytical workflow and validation checks
2. run `qa-review/STRUCTURAL_QA_CHECKLIST.md`
3. run `qa-review/MAP_QA_CHECKLIST.md` for any styled outputs
4. confirm provenance with `standards/PROVENANCE_AND_HANDOFF_STANDARD.md`
5. package with `workflows/QGIS_HANDOFF_PACKAGING.md`
6. confirm `standards/PUBLISHING_READINESS_STANDARD.md`

### Sequence 3: cartographic workflow selection

1. read `standards/CARTOGRAPHY_STANDARD.md`
2. select the relevant workflow:
   - `workflows/CHOROPLETH_DESIGN.md`
   - `workflows/POINT_OVERLAY_DESIGN.md`
   - `workflows/HOTSPOT_MAP_DESIGN.md`
   - `workflows/BIVARIATE_CHOROPLETH_DESIGN.md`
3. run `qa-review/MAP_QA_CHECKLIST.md`
4. continue to publication or package delivery as required

## Key Standards for This Domain

- `standards/CARTOGRAPHY_STANDARD.md` — firm-wide design rules and map-family taxonomy
- `standards/PUBLISHING_READINESS_STANDARD.md` — delivery gate for client outputs
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — handoff and metadata requirements
- `standards/CRS_SELECTION_STANDARD.md` — delivery CRS requirements
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — delivery format and tool preferences

## Key Workflows for This Domain

- `workflows/CHOROPLETH_DESIGN.md` — single-variable choropleth method
- `workflows/POINT_OVERLAY_DESIGN.md` — point-on-base thematic design method
- `workflows/HOTSPOT_MAP_DESIGN.md` — hotspot and LISA output rendering workflow
- `workflows/BIVARIATE_CHOROPLETH_DESIGN.md` — bivariate map design workflow
- `workflows/REVIEW_SITE_PUBLISHING.md` — web-based delivery workflow
- `workflows/QGIS_HANDOFF_PACKAGING.md` — offline GIS package delivery workflow

## Key QA Pages for This Domain

- `qa-review/MAP_QA_CHECKLIST.md` — cartographic quality review
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — data integrity before packaging
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative and claims review
- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — spatial-stats-specific review before hotspot or LISA delivery

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — common thematic data source for choropleths and dashboards
- `data-sources/TIGER_GEOMETRY.md` — common polygon geometry source for delivery products
- `data-sources/LOCAL_POSTGIS.md` — common local-source path for POI and contextual mapping
- `data-sources/OSM.md` — common contextual and POI source for delivery products

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — data shaping and export support
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support
- QGIS for project assembly, styling, and export
- Leaflet / Mapbox for interactive web maps used in `workflows/REVIEW_SITE_PUBLISHING.md`

## Domain-Specific Caveats

- maps are interpretive products, not raw data, and visual choices affect conclusions
- open, portable delivery formats are preferred unless the client explicitly requires a proprietary format
- OSM-derived content in deliverables requires ODbL attribution
- Census-derived deliverables should cite source and vintage clearly
- agent-generated maps, narratives, and dashboards require human review before client delivery

## Known Gaps in Current Canon

- there is not yet a dedicated domain page for policy communication, public-facing storytelling, or dashboard strategy
- reusable delivery templates are not yet first-class wiki content
- broader reporting-and-memo packaging still depends partly on workflow pages rather than a template library

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DATA_ENGINEERING_AND_QA.md`

## Trust Level

Validated Domain Page
