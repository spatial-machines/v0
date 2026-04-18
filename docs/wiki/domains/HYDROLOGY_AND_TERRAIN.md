# Hydrology and Terrain Domain

Purpose:
provide a navigation and cross-linking page for DEM intake, terrain derivatives, watershed delineation, and hydrology-oriented QA canon
help analysts and agents route terrain and water-system questions to the correct workflow, source, and review pages
define the current reusable canon coverage for terrain and watershed work using an open, reproducible stack

## Domain Scope

This domain covers raster terrain preparation, terrain derivative generation, watershed delineation, and hydrology-oriented review.

It includes:
- DEM intake and source validation
- terrain derivatives such as slope, aspect, hillshade, curvature, TPI, and TWI
- watershed delineation and pour-point-driven hydrology workflows
- hydrology QA and legal-grade review routing
- packaging terrain and watershed outputs for review and delivery

It does not include:
- general delivery and map packaging as a domain (see `domains/CARTOGRAPHY_AND_DELIVERY.md`)
- general data-processing conventions shared by all workflows (see `domains/DATA_ENGINEERING_AND_QA.md`)
- transportation or service-area accessibility questions (see `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`)
- broader environmental justice or hazard screening domains that may later reuse these workflows

## Common Questions

- is the DEM good enough for the requested terrain or watershed task?
- which derivatives should be produced, and how should they be documented?
- how should a pour point be validated before delineation?
- when is a terrain output just analytical support, and when does it need legal-grade review?
- what QA should happen before hydrology outputs are treated as defensible?

## Common Workflow Sequences

### Sequence 1: terrain derivatives from a validated DEM

1. confirm source readiness with `standards/SOURCE_READINESS_STANDARD.md`
2. read `data-sources/USGS_ELEVATION.md` or `data-sources/CLIENT_SUPPLIED_DEMS.md`
3. confirm CRS with `standards/CRS_SELECTION_STANDARD.md`
4. run `workflows/TERRAIN_DERIVATIVES.md`
5. validate with `qa-review/HYDROLOGY_OUTPUT_QA.md` and `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: watershed delineation

1. validate DEM intake via `data-sources/USGS_ELEVATION.md` or `data-sources/CLIENT_SUPPLIED_DEMS.md`
2. confirm working CRS with `standards/CRS_SELECTION_STANDARD.md`
3. run `workflows/WATERSHED_DELINEATION.md`
4. if derivative surfaces are also needed, use `workflows/TERRAIN_DERIVATIVES.md`
5. review outputs with `qa-review/HYDROLOGY_OUTPUT_QA.md`
6. if the project is legal-grade or challenge-prone, route through `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md`

### Sequence 3: terrain support for downstream analysis

1. produce slope, aspect, or hillshade with `workflows/TERRAIN_DERIVATIVES.md`
2. use `standards/OPEN_EXECUTION_STACK_STANDARD.md` and `standards/CRS_SELECTION_STANDARD.md` to document reproducibility
3. pass outputs into the downstream analytical workflow
4. continue into `domains/CARTOGRAPHY_AND_DELIVERY.md` when review or publication is required

## Key Standards for This Domain

- `standards/CRS_SELECTION_STANDARD.md` — projected-CRS requirements for raster analysis
- `standards/SOURCE_READINESS_STANDARD.md` — source-tier assignment for DEMs and supporting inputs
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md` — additional rigor for legal or regulatory work
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred reproducible toolchain

## Key Workflows for This Domain

- `workflows/TERRAIN_DERIVATIVES.md` — slope, aspect, hillshade, curvature, TPI, and TWI generation
- `workflows/WATERSHED_DELINEATION.md` — watershed delineation and hydrologic context workflow
- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — general preparation conventions this domain inherits when raster / vector inputs need standardization before analysis

## Key QA Pages for This Domain

- `qa-review/HYDROLOGY_OUTPUT_QA.md` — hydrology-specific output review
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural checks on outputs and packaging
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — review gate for higher-stakes use cases

## Key Data Sources for This Domain

- `data-sources/USGS_ELEVATION.md` — USGS elevation source guidance
- `data-sources/CLIENT_SUPPLIED_DEMS.md` — client-supplied DEM intake and caveats
- `data-sources/LOCAL_FILES.md` — general local raster intake pattern
- `data-sources/REMOTE_FILES.md` — downloadable raster intake pattern

## Key Toolkits for This Domain

- `toolkits/GDAL_OGR_TOOLKIT.md` — raster conversion, inspection, and CRS support
- `toolkits/GEOPANDAS_TOOLKIT.md` — vector overlays, packaging, and QA support around hydrology outputs

## Domain-Specific Caveats

- DEM quality and resolution can limit the usefulness of every downstream product
- many hydrology outputs look plausible even when CRS, pour-point logic, or conditioning decisions are wrong
- legal or regulatory use cases require a higher review bar than exploratory terrain support
- terrain derivatives and watershed outputs should preserve enough provenance to survive later challenge or reproduction

## Known Gaps in Current Canon

- floodplain and flood-risk analysis do not yet have a dedicated domain or workflow family
- stormwater, drainage, wetlands, and groundwater analysis are not yet first-class canon areas
- there is no standalone toolkit page yet for WhiteboxTools or Rasterio even though the workflows depend on them conceptually
- hazard and resilience domain pages have not yet been created to absorb hydrology-derived work

## Adjacent Domains

- `domains/DATA_ENGINEERING_AND_QA.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`

## Trust Level

Validated Domain Page
