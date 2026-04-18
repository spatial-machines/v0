# Data Engineering and QA Domain

Purpose:
provide a navigation and cross-linking page for the firm's reusable retrieval, processing, provenance, validation, and QA canon
help analysts and agents find the cross-cutting execution rules that apply before any domain-specific analysis is treated as trustworthy
define the current reusable canon coverage for source intake, standardization, handoffs, and validation

## Domain Scope

This domain covers the cross-cutting data-engineering and QA layer that supports every analytical domain.

It includes:
- source intake and provenance
- general processing and standardization
- CRS discipline and source-readiness checks
- structural QA, interpretive review, and publishing readiness
- handoff artifacts between pipeline stages
- general validation-stage sequencing

It does not include:
- domain-specific analytical interpretation rules owned by demographic, POI, hydrology, cartography, or spatial-stats canon
- role authority, delegation, or escalation governance owned by role docs
- project-specific decisions and client-specific methodology notes

## Common Questions

- is this source ready for analysis?
- how should a newly retrieved dataset be normalized and joined before downstream use?
- what provenance and handoff fields must survive each stage?
- which QA checklist applies before a result is packaged or published?
- what is the difference between structural QA, interpretive review, and publishing readiness?

## Common Workflow Sequences

### Sequence 1: source intake to processed output

1. read `standards/SOURCE_READINESS_STANDARD.md`
2. run `workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md`
3. run `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
4. record handoff requirements from `standards/PROVENANCE_AND_HANDOFF_STANDARD.md`
5. validate with `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: analysis to validation to delivery readiness

1. complete the relevant domain workflow
2. follow `workflows/VALIDATION_AND_QA_STAGE.md`
3. apply `qa-review/STRUCTURAL_QA_CHECKLIST.md`
4. apply the relevant domain QA page
5. apply `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` when the output supports client-facing claims
6. confirm `standards/PUBLISHING_READINESS_STANDARD.md` before delivery or publication

### Sequence 3: cross-domain handoff discipline

1. confirm CRS and processing rules via `standards/CRS_SELECTION_STANDARD.md` and `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`
2. confirm stage-specific handoff expectations with `standards/PROVENANCE_AND_HANDOFF_STANDARD.md`
3. pass outputs into the next workflow only after the producing stage's QA checks are complete
4. continue into the relevant domain page for interpretation and delivery

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness tiers and intake discipline
- `standards/CRS_SELECTION_STANDARD.md` — CRS selection and verification rules
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — cross-stage provenance and handoff requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — structural QA policy
- `standards/INTERPRETIVE_REVIEW_STANDARD.md` — human-judgment review policy
- `standards/PUBLISHING_READINESS_STANDARD.md` — delivery gate before publishing or client handoff
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred execution stack and portability rules

## Key Workflows for This Domain

- `workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md` — reusable retrieval and provenance workflow
- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — cleaning, normalization, and joining workflow
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — general analysis-stage workflow
- `workflows/VALIDATION_AND_QA_STAGE.md` — general validation-stage workflow
- `workflows/LEAD_ANALYST_ORCHESTRATION.md` — downstream orchestration consumer of stage handoffs

## Key QA Pages for This Domain

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural review baseline for all outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative and claim review
- `qa-review/MAP_QA_CHECKLIST.md` — delivery-map review when outputs become cartographic products
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — higher-rigor gate for legal or challenge-prone work

## Key Data Sources for This Domain

- `data-sources/LOCAL_FILES.md` — local-file intake pattern
- `data-sources/REMOTE_FILES.md` — remote-file intake pattern
- `data-sources/LOCAL_POSTGIS.md` — local database intake pattern
- `data-sources/CENSUS_ACS.md` and `data-sources/TIGER_GEOMETRY.md` — example high-value source family pages

## Key Toolkits for This Domain

- `toolkits/GEOPANDAS_TOOLKIT.md` — shaping, joins, and packaging
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion, CRS inspection, and format handling
- `toolkits/POSTGIS_TOOLKIT.md` — large-scale spatial processing and query workflows

## Domain-Specific Caveats

- the same analysis can fail for purely structural reasons before any interpretation is attempted
- provenance and handoff discipline matter most when work crosses workflow boundaries
- QA should not be treated as a final cosmetic pass; it is part of the pipeline method
- a domain workflow can be correct in concept and still fail because the engineering or handoff layer was weak

## Known Gaps in Current Canon

- there is no standalone research-intake lane yet under `docs/wiki/research-notes/`
- project templates and reusable methodology-note templates are not yet first-class wiki sections
- some advanced cross-link and link-resolution hardening remains deferred in the build layer
- a future uncertainty / MOE standard is still needed for certain advanced analytical domains

## Adjacent Domains

- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/HYDROLOGY_AND_TERRAIN.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
