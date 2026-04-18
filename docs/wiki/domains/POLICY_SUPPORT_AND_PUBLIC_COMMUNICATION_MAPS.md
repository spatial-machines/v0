# Policy Support and Public Communication Maps Domain

Purpose:
provide a navigation and cross-linking page for policy-support mapping, public-facing communication products, and civic data visualization
help analysts and agents route policy communication and public outreach questions into the correct reusable cartographic, demographic, QA, and delivery workflows
define the current reusable canon coverage for policy-support mapping without inventing policy analysis methodology or advocacy framing the repo does not yet contain

## Domain Scope

This domain covers work where the main output is a map, data product, or spatial summary intended to support policy decisions, inform elected officials, or communicate findings to the public.

It includes:
- policy-support maps and data visualizations for government audiences
- public-facing communication maps designed for general audiences
- summary and dashboard products built from live demographic, access, and environmental canon
- publication and review routing for high-visibility public outputs
- cross-routing to cartography, delivery, and equity domains

It does not include:
- policy analysis, advocacy framing, or political recommendation
- legislative or regulatory interpretation
- general cartographic production not focused on policy communication (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)
- general demographic analysis not framed for policy audiences (see `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`)

## Common Questions

- how should spatial findings be presented for policy makers or elected officials?
- what cartographic conventions support clear public communication without overstating findings?
- what review process should apply to maps intended for public distribution or media use?
- how should equity, access, or environmental findings be framed for civic and policy audiences?
- when does a policy map need higher-rigor review before release?

## Common Workflow Sequences

### Sequence 1: policy-support map production

1. prepare the analytical foundation through the relevant domain (demographics, access, equity, environment)
2. apply cartographic standards through `standards/CARTOGRAPHY_STANDARD.md`
3. design maps using `workflows/CHOROPLETH_DESIGN.md`, `workflows/POINT_OVERLAY_DESIGN.md`, or `workflows/BIVARIATE_CHOROPLETH_DESIGN.md`
4. review maps with `qa-review/MAP_QA_CHECKLIST.md`
5. review interpretive framing with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
6. publish or package through `workflows/REPORTING_AND_DELIVERY.md`

### Sequence 2: public communication product with equity framing

1. prepare equity context through `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
2. add demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. design maps and summaries for public audiences
4. apply publishing readiness with `standards/PUBLISHING_READINESS_STANDARD.md`
5. route through `workflows/REVIEW_SITE_PUBLISHING.md` if web publication is needed
6. escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` when outputs are high-stakes

### Sequence 3: dashboard-style civic data product

1. assemble data layers from relevant domain workflows
2. package with `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`
3. apply cartographic and structural standards
4. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`
5. deliver through `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Key Standards for This Domain

- `standards/CARTOGRAPHY_STANDARD.md` — cartographic conventions for public-facing maps
- `standards/PUBLISHING_READINESS_STANDARD.md` — readiness gates for public release
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — review policy for interpretive claims in public products
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — higher-rigor expectations for consequential policy outputs
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — provenance discipline for public-facing data

## Key Workflows for This Domain

- `workflows/CHOROPLETH_DESIGN.md` — thematic map design for policy audiences
- `workflows/POINT_OVERLAY_DESIGN.md` — point-based map design for facility and asset products
- `workflows/BIVARIATE_CHOROPLETH_DESIGN.md` — two-variable map design for equity and access framing
- `workflows/HOTSPOT_MAP_DESIGN.md` — spatial pattern maps for policy narrative
- `workflows/REPORTING_AND_DELIVERY.md` — report and delivery packaging
- `workflows/REVIEW_SITE_PUBLISHING.md` — web publication workflow
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — analysis output packaging

## Key QA Pages for This Domain

- `qa-review/MAP_QA_CHECKLIST.md` — review of public-facing maps
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of claims and narrative framing
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor review for consequential policy outputs
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity of underlying data products

## Key Data Sources for This Domain

- `data-sources/CENSUS_ACS.md` — demographic context for policy framing
- `data-sources/TIGER_GEOMETRY.md` — tract and geography support for public maps
- `data-sources/LOCAL_FILES.md` — client or agency-supplied policy context layers
- `data-sources/REMOTE_FILES.md` — downloadable context and boundary layers
- `data-sources/LOCAL_POSTGIS.md` — contextual layer support at scale

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — data preparation and output support
- `toolkits/POSTGIS_TOOLKIT.md` — scale and summarization support
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and packaging support

## Domain-Specific Caveats

- policy maps carry higher interpretive weight than internal analysis products — what they show is often taken as what is true
- public communication products need especially careful review because aesthetic clarity can mask analytical uncertainty
- maps intended for elected officials, media, or public comment often need the highest level of QA and interpretive review
- policy support is not the same as policy advocacy — the canon should support clear communication, not directive framing

## Known Gaps in Current Canon

- there is no dedicated policy communication standard or public-map design guide yet
- dashboard and interactive map delivery workflows are not yet wiki-standardized
- audience-specific cartographic conventions (elected officials vs. general public vs. technical staff) are not yet differentiated
- there is no dedicated policy-map QA page beyond the general map, interpretive, and legal-grade layers
- narrative and caption writing guidance for public products is not yet first-class canon

## Adjacent Domains

- `domains/CARTOGRAPHY_AND_DELIVERY.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
- `domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md`
- `domains/DATA_ENGINEERING_AND_QA.md`

## Trust Level

Validated Domain Page
