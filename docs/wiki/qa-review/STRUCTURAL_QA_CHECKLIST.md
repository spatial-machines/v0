# Structural QA Checklist

This checklist is one component of the broader [Validation and QA Stage Workflow](../workflows/VALIDATION_AND_QA_STAGE.md). Use that workflow for stage order, final readiness classification, and validation handoff expectations.

Purpose:
provide a reusable structural validation checklist for GIS outputs
Use When
Use this page before treating a workflow as complete.
Core Checks
required files exist
geometry is present and valid
CRS is stated and consistent
key join fields are present
row counts are plausible
nulls are understood
derived fields were actually written
outputs match the approved scope
handoffs exist where required
publish outputs exist where required
For Trend Outputs
endpoint years are explicit
units are explicit
inflation handling is documented where needed
current snapshot and trend outputs are not mixed carelessly
For ZIP / ZCTA Outputs
delivery geography is named explicitly
rollup method is documented
shares were not averaged blindly
medians were not rolled up naively
For Maps
legend is understandable
title reflects the actual metric
units are visible
caveats are not hidden if they materially affect interpretation
Escalate When
geometry or CRS problems remain unresolved
a join appears materially incomplete
trend logic looks stronger than the source support
ZIP-level metrics look mathematically suspicious
Governing Standard
standards/STRUCTURAL_QA_STANDARD.md
— defines the firm's policy on when structural QA is mandatory, failure thresholds, and escalation rules
Relationship to Other QA Pages
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
— run after structural QA for narrative and interpretive checks
standards/PUBLISHING_READINESS_STANDARD.md
— Gate 1 requires this checklist to pass
Trust Level
Validated QA Page Needs Testing
