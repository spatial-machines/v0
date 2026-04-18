# Reporting and Delivery Workflow

Purpose

Define the standard reporting stage that converts validated analysis outputs into clear, reviewable deliverables for synthesis, publishing, and client-facing use.

Typical Use Cases

- tract-level demographic analysis reports
- hotspot and trend analysis reporting
- market and site-selection reporting
- technical appendices for review-site publication
- executive brief plus technical report delivery bundles

Inputs

- validated analysis outputs
- validation handoff
- upstream analysis and processing handoffs as needed for traceability
- project brief and scope constraints
- maps, tables, web outputs, and source citations generated upstream

Preconditions

- validation stage is complete
- structural and interpretive issues are resolved or explicitly carried as warnings
- output files are written to expected project locations
- provenance and source references are available

Preferred Tools

- canonical reporting scripts for asset collection and report generation
- markdown-first authoring
- self-contained HTML output for review and delivery
- REVIEW_SITE_PUBLISHING as the downstream packaging workflow

Execution Order

1. confirm validated scope and reporting objective
2. collect approved assets and references
3. draft the reporting structure
4. write the markdown report and executive framing
5. generate self-contained HTML deliverables
6. surface QA, caveats, and provenance explicitly
7. prepare delivery handoff for synthesis or publishing

Step Details

### 1. Confirm validated scope and reporting objective

Read the project brief and validation handoff first.

Confirm:

- what question the report must answer
- which findings are in scope
- which outputs are approved for reporting
- which warnings must remain visible in the final narrative
- whether the deliverable is primarily an executive brief, technical memo, or review bundle

The reporting stage should never silently expand scope beyond what validation approved.

### 2. Collect approved assets and references

Gather only validated and relevant materials:

- final maps
- tables and ranked outputs
- web map links or files
- data catalogs and citations
- validation findings
- caveat notes from upstream handoffs

This is the point where reporting decides what belongs in the final package by analytic relevance and readiness, not by aesthetics alone.

### 3. Draft the reporting structure

Build the report around the answer first.

Recommended structure:

1. title and scope
2. executive answer or key finding
3. study area and question framing
4. methods summary
5. main findings
6. QA and confidence notes
7. caveats and limitations
8. sources and provenance
9. appendix or supporting materials when needed

For technical reports, expand methods and artifact references. For executive briefs, compress detail while preserving caveats.

### 4. Write the markdown report and executive framing

The markdown version should be the clearest expression of the reporting logic.

Reporting principles:

- lead with the answer
- keep claims proportional to evidence
- connect each major finding to a visible output or cited artifact
- surface uncertainty instead of hiding it
- distinguish measured results from interpretation

Do not treat the report as decoration for maps. The report is the narrative handoff between validated analysis and decision-making.

### 5. Generate self-contained HTML deliverables

Convert the reporting package into self-contained HTML suitable for:

- local review
- review-site inclusion
- archival delivery bundles

HTML outputs should:

- render cleanly without external dependencies when possible
- preserve headings, tables, links, and image references
- remain readable outside the review site

### 6. Surface QA, caveats, and provenance explicitly

Every reporting package should make visible:

- whether the run passed cleanly or passed with warnings
- the most material limitations
- source constraints and vintage issues
- any unresolved uncertainty the reader must understand

This prevents the reporting stage from laundering technical warnings into polished but misleading prose.

### 7. Prepare delivery handoff for synthesis or publishing

The reporting stage should produce a compact handoff that includes:

- report file paths
- referenced assets
- key findings summary
- carried-forward warnings
- readiness state for synthesis or site publishing

If the reporting package is incomplete or dependent on unresolved assets, it should not advance as if it were publication-ready.

Validation Checks

Before reporting is considered complete, confirm:

- all referenced assets exist
- filenames and paths resolve correctly
- report claims match validated findings
- caveats are present and visible
- source references are attached
- HTML outputs open cleanly
- deliverables are internally consistent across markdown, HTML, and linked assets

Common Failure Modes

- report leads with methods instead of the answer
- narrative omits the strongest caveat from validation
- report references maps or tables that were never validated
- HTML output breaks or drops embedded assets
- findings overstate confidence or imply causation unsupported by analysis
- citations or provenance are missing from the final bundle
- executive summary diverges from the validated outputs

Escalate When

- validation outcome is REWORK NEEDED
- warnings materially change the interpretation of the result
- key assets are missing, broken, or contradictory
- the project brief requires client-facing language that could overstate the evidence
- legal, policy, or high-stakes delivery requires stricter review than the standard reporting path

Outputs

- markdown report
- self-contained HTML report
- asset manifest or equivalent reporting handoff
- summary of key findings and carried-forward warnings
- delivery-ready references for site publishing or lead-analyst synthesis

Related Standards

- PUBLISHING_READINESS_STANDARD
- INTERPRETIVE_REVIEW_STANDARD
- PROVENANCE_AND_HANDOFF_STANDARD

Related Workflows

- VALIDATION_AND_QA_STAGE
- REVIEW_SITE_PUBLISHING
- QGIS_HANDOFF_PACKAGING

Trust Level

Validated Workflow
