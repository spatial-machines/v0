# Validation and QA Stage Workflow

Purpose

Define the standard validation stage between analysis or cartography and reporting.

Typical Use Cases

- tract-level demographic analysis
- choropleth and hotspot outputs
- web map and report readiness review
- any deliverable moving from production to reporting

Inputs

- analysis handoff JSON
- output files in outputs/maps, outputs/web, and outputs/tables
- processed datasets referenced by the upstream handoff
- relevant project brief constraints

Preconditions

- upstream analysis stage is complete
- outputs are written to expected locations
- provenance and handoff fields are present

Preferred QA Components

- STRUCTURAL_QA_CHECKLIST
- MAP_QA_CHECKLIST
- INTERPRETIVE_REVIEW_CHECKLIST
- project- or domain-specific QA pages when applicable

Execution Order

1. intake and scope confirmation
2. structural QA pass
3. map and presentation QA pass
4. interpretive QA pass
5. readiness classification
6. validation handoff writing

Step Details

### 1. Intake and scope confirmation

Read the upstream analysis handoff and project brief to confirm:

- what outputs are expected
- what analytic method was used
- which outputs are in scope for this validation pass
- whether any project-specific caveats change the review bar

This prevents reviewers from applying the wrong checklist to the wrong deliverable.

### 2. Structural QA pass

Use STRUCTURAL_QA_CHECKLIST first.

This is the non-negotiable technical integrity gate. It should answer:

- are the files present and readable?
- is CRS consistent?
- are geometry and schema structurally sound?
- are joins complete enough to support interpretation?
- are nulls and coverage gaps disclosed?

If structural issues materially undermine the dataset, the workflow should stop here and classify the run as REWORK NEEDED.

### 3. Map and presentation QA pass

Use MAP_QA_CHECKLIST for any visual output.

This pass focuses on communication accuracy rather than raw data integrity:

- title accuracy
- legend clarity
- classification readability
- color choice and accessibility
- annotation and layout issues
- obvious visual artifacts or misleading presentation

If structural QA passed but map QA finds issues, the run may still be PASS WITH WARNINGS or REWORK NEEDED depending on severity.

### 4. Interpretive QA pass

Use INTERPRETIVE_REVIEW_CHECKLIST for reports, summaries, or any human-facing claims.

This pass checks:

- whether claims are supported by outputs
- whether uncertainty and caveats are surfaced
- whether ranking or comparison language overstates confidence
- whether domain framing stays within the evidence

This is the bridge between technical correctness and honest delivery.

### 5. Readiness classification

After the three passes, assign one of the standard outcomes:

- PASS: fit to move forward to reporting with no material blockers
- PASS WITH WARNINGS: usable, but warnings must stay visible downstream
- REWORK NEEDED: material issue blocks reporting or publication

### 6. Validation handoff writing

Write the aggregated validation handoff with:

- referenced QA artifacts
- overall status
- warning list
- rework list if applicable
- ready_for: reporting when status is PASS or PASS WITH WARNINGS
- ready_for: review when status is REWORK NEEDED

Validation Checks

Before validation is considered complete, confirm:

- all expected outputs exist
- file paths resolve correctly
- geometry and CRS checks are satisfied
- joins, nulls, and counts are within acceptable tolerance or flagged clearly
- map presentation issues are either resolved or called out
- interpretive claims are proportional to evidence
- caveats remain visible in downstream artifacts

Common Failure Modes

- structural QA passes are skipped because maps look fine
- reviewers apply the wrong checklist sequence
- warnings are buried instead of carried forward
- validation artifacts exist but are not summarized in the handoff
- reports proceed even though validation found blocking issues

Escalate When

- join coverage or geometry problems threaten validity
- map design could materially mislead interpretation
- narrative claims overstate evidence
- publishing readiness is blocked by unresolved issues

Outputs

- per-check QA JSON or structured artifacts
- aggregated validation handoff
- ready_for flag
- warning list and rework list

Related Standards

- STRUCTURAL_QA_STANDARD
- PUBLISHING_READINESS_STANDARD
- INTERPRETIVE_REVIEW_STANDARD

Related QA Pages

- STRUCTURAL_QA_CHECKLIST
- MAP_QA_CHECKLIST
- INTERPRETIVE_REVIEW_CHECKLIST

Trust Level

Validated Workflow
