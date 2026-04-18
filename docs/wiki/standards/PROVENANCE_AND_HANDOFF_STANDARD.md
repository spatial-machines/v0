# Provenance and Handoff Standard

Purpose:
define what must accompany an analysis output when it moves between analysts, agents, projects, or to a client
prevent downstream users from working with undocumented outputs
make every handoff reviewable and reproducible
Use When
Use this standard whenever:
an output will be consumed by a different analyst or agent than the one who produced it
an output is being packaged for client delivery
an output is being archived for future reuse or audit
a project is being handed off between team members
Do Not Use When
Do not use this standard for scratch or intermediate files that are consumed and discarded within a single workflow step by the same analyst.
Approved Rule
Every handoff output must include provenance metadata sufficient for the recipient to:
understand what the output contains
trace it back to its sources
assess its quality and limitations
reproduce it or update it with new inputs
Required Provenance Fields
For every handoff output, document:
Output name and description
: what this file or layer contains
Source family
: which upstream data sources contributed (e.g., ACS 5-year 2022, TIGER 2022, firm PostGIS OSM extract 2024-09)
Source readiness tier
: per
standards/SOURCE_READINESS_STANDARD.md
Geography
: the geographic scope and level (e.g., tracts within Los Angeles County)
CRS
: EPSG code of the output, per
standards/CRS_SELECTION_STANDARD.md
Time coverage
: vintage or date range of the underlying data
Key fields
: list of critical attribute fields and their definitions
Method summary
: one-paragraph plain-English description of how the output was produced
Known limitations
: caveats, approximations, or gaps
Producer
: who or what created the output (analyst name, agent ID, script name)
Date produced
: when the output was generated
Validation status
: whether the output has passed structural QA, interpretive review, or other checks
Workflow-Specific Handoff Subschemas
The Required Provenance Fields above apply to every handoff output, regardless of which pipeline stage produced it. Beyond those universal fields, each pipeline stage produces a handoff with stage-specific informational fields. Those stage-specific fields are documented below.
This section names the informational fields each stage's handoff conveys. It does not define a JSON schema; the on-disk shape (field names, types, file format) is owned by ARCHITECTURE.md § Handoff Contracts and the canonical core scripts under scripts/core/. The intent of this section is to give wiki workflow pages a single canonical reference for what their handoff communicates, so each workflow page can defer here without re-inventing the field list.
Retrieval handoff
Produced by:
workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md
Stage-specific fields:
list of retrieved datasets with their file paths in
data/raw/
references to each per-dataset manifest sidecar
source readiness tier per
standards/SOURCE_READINESS_STANDARD.md
warnings raised during retrieval (HTTP failures, partial coverage, vintage gaps, license restrictions)
run provenance reference (the per-run JSON in
runs/
that lists every dataset retrieved during the run)
readiness state for the processing stage
Processing handoff
Produced by:
workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md
and its domain specializations (
workflows/TRACT_JOIN_AND_ENRICHMENT.md
,
workflows/POI_CATEGORY_NORMALIZATION.md
,
workflows/GEOCODE_BUFFER_ENRICHMENT.md
)
Stage-specific fields:
per-step summary covering extraction, normalization, join diagnostics, derived fields, output paths
join diagnostics: match rate, unmatched geometry counts, unmatched tabular counts
key normalization decisions: type casts, zero-padding rules, whitespace handling, field renames
derived field formulas (the rates, shares, densities, area metrics computed during processing)
coercion failures and how they were handled
schema notes: field renames, drops, type changes
references to per-step processing logs in
runs/
or
outputs/qa/
structural QA result per
standards/STRUCTURAL_QA_STANDARD.md
warnings raised during processing
upstream retrieval handoff reference
readiness state for the analysis stage
Analysis handoff
Produced by:
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md
and its domain specializations (
workflows/DECADE_TREND_ANALYSIS.md
,
workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md
,
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
,
workflows/HOTSPOT_ANALYSIS.md
,
workflows/LISA_CLUSTER_ANALYSIS.md
)
Stage-specific fields:
list of analytical output paths and the field names they contain
classification choices per field (method, class count, break values)
null-handling decisions per metric (full-coverage / filtered-subset / both)
ranking exclusions and tie-breaking rules
derived analytical field formulas (beyond the processing-level rates and shares)
references to per-step analysis logs
warnings raised during analysis
spatial stats handoff entry per
standards/SPATIAL_STATS_STANDARD.md
when the analysis includes spatial autocorrelation, hotspot, or LISA results
upstream processing handoff reference
readiness state for the validation stage
Validation handoff
Produced by:
workflows/VALIDATION_AND_QA_STAGE.md
Stage-specific fields:
per-check QA artifacts (structural QA, map QA, interpretive review, domain-specific QA)
overall outcome: PASS, PASS WITH WARNINGS, or REWORK NEEDED (the firm's three-level outcome vocabulary)
warning list (warnings that must remain visible downstream)
rework list (when status is REWORK NEEDED)
ready_for: reporting when status is PASS or PASS WITH WARNINGS
ready_for: review when status is REWORK NEEDED
upstream analysis handoff reference
gate status against
standards/PUBLISHING_READINESS_STANDARD.md
Reporting handoff
Produced by:
workflows/REPORTING_AND_DELIVERY.md
Stage-specific fields:
report file paths (markdown and HTML)
referenced asset paths (maps, tables, supporting files)
key findings summary
caveats and warnings carried forward from upstream stages
upstream validation handoff reference
readiness state for synthesis or site publishing
Lead orchestration handoff
Produced by:
workflows/LEAD_ANALYST_ORCHESTRATION.md
Stage-specific fields:
run plan reference
pipeline status (which stages completed, which are missing)
synthesis summary (key findings, validation outcome, caveats)
list of key output artifacts across all stages
recommendation for the human reviewer
warning list aggregated across all upstream stages
ready_for: human-review when the run is complete
ready_for: rework when an upstream issue prevents completion
references to every upstream stage handoff
How wiki workflow pages reference this section
A wiki workflow page that produces a handoff should reference this standard once and rely on the section above for the field list. The workflow page describes the procedure that fills the handoff; this standard describes what the handoff conveys; ARCHITECTURE.md describes the JSON shape. The three layers complement each other and should not duplicate.
Handoff Package Contents
A handoff package should include:
the output file(s)
a methodology note or README covering the provenance fields above
any supporting reference files needed to interpret or reproduce the output (e.g., crosswalk tables, variable dictionaries, classification schemes)
Inputs
the output being handed off
the workflow that produced it
the relevant standards applied during production
the QA results
Method Notes
Provenance metadata should be recorded as the output is produced, not reconstructed after the fact.
For GIS outputs, prefer GeoPackage metadata fields or a sidecar README over embedding provenance only in file names.
When an agent produces an output, the agent should write the provenance fields into the methodology note automatically.
If the handoff is internal (analyst to analyst), the methodology note can be brief but must exist.
If the handoff is external (to client), the methodology note should be reviewed against
standards/PUBLISHING_READINESS_STANDARD.md
.
Validation Rules
A handoff should fail validation if:
no provenance metadata accompanies the output
the source family is unidentified
the CRS is undocumented
the output has not been checked against
qa-review/STRUCTURAL_QA_CHECKLIST.md
key fields are unnamed or undefined
the recipient cannot determine the vintage or geography of the data from the provided documentation
Human Review Gates
Escalate when:
the output will be used for legal or regulatory purposes
the source readiness tier is Tier 3 (Provisional) or below
the output crosses project boundaries (one project's output feeding another project)
the handoff involves sensitive or client-confidential data
provenance reconstruction is required because documentation was not maintained during production
Common Failure Modes
delivering a shapefile with no data dictionary or README
losing track of which ACS vintage produced a specific table
handing off a derived layer without noting the derivation method
archiving outputs with opaque file names and no supporting documentation
assuming the next analyst will know what CRS or geography level a layer uses
agent-produced outputs with no provenance because the agent was not instructed to document
Related Workflows
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
workflows/REVIEW_SITE_PUBLISHING.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
Sources
firm project methodology notes
Federal Geographic Data Committee (FGDC) metadata guidance
ISO 19115 geographic information metadata concepts (as reference, not as a required format)
Trust Level
Production Standard
