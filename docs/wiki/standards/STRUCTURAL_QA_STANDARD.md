# Structural QA Standard

This standard defines the firm's structural QA policy. Use [Validation and QA Stage Workflow](../workflows/VALIDATION_AND_QA_STAGE.md) for the validation-stage sequence and final outcome classification, and [Structural QA Checklist](../qa-review/STRUCTURAL_QA_CHECKLIST.md) for the operational checks this standard governs.

Purpose:
define the firm's policy on structural quality assurance for GIS outputs
specify when structural QA is mandatory, what constitutes a structural failure, and what thresholds apply
provide the governing rules that the
qa-review/STRUCTURAL_QA_CHECKLIST.md
operationalizes
This standard defines rules. The
qa-review/STRUCTURAL_QA_CHECKLIST.md
is the operational tool that implements them.
Use When
Use this standard to determine:
whether an output requires structural QA before it can move forward
what level of rigor the QA must meet
what constitutes a passing or failing result
when QA must escalate to human review
Do Not Use When
Do not use this standard for:
interpretive or narrative review (use
standards/INTERPRETIVE_REVIEW_STANDARD.md
)
domain-specific review of map cartography, trend logic, or POI extraction (use the dedicated QA pages)
internal scratch files that will not be consumed by another analyst, agent, or client
Approved Rule
When Structural QA Is Required
Structural QA is mandatory before any output:
is handed off to a different analyst or agent
enters a downstream workflow as an input
is packaged for client delivery
is published to a review site or dashboard
is archived for future reuse
What Structural QA Covers
Structural QA validates that the output is physically correct and internally consistent. It does not validate interpretation, narrative, or cartographic quality.
Required checks:
file existence: all expected output files are present
geometry validity: no null, empty, or corrupt geometries in spatial layers
CRS consistency: the output CRS matches the documented working or delivery CRS
field presence: all required attribute fields exist and are populated
join integrity: row counts match expectations; no silent row loss or duplication
null handling: null values are understood and documented, not silently propagated
derived field correctness: computed fields contain values, not blanks or formula residuals
scope alignment: the output covers the approved geography and time period
format compliance: the output is in the approved delivery format
Failure Definition
An output fails structural QA if:
any required file is missing
geometry is null, invalid, or in the wrong CRS
a required attribute field is missing or entirely null
row count deviates more than 5% from the expected count without explanation
derived fields are blank or contain obvious formula errors
the output geography or time period does not match the approved scope
Acceptable Tolerance
row-count mismatches of less than 5% may pass if explained (e.g., water-only tracts filtered)
minor null values in optional fields may pass if documented
CRS discrepancies between NAD83 geographic and WGS 84 geographic may pass for CONUS work if documented per
standards/CRS_SELECTION_STANDARD.md
Inputs
the output to be validated
the workflow that produced it
the expected output specification (field list, row count, CRS, format)
any relevant project scope documentation
Method Notes
Structural QA should be run immediately after the producing workflow completes, not deferred to delivery time.
Agents should run structural QA automatically at the end of every producing workflow and log the result.
Structural QA results should be recorded in the handoff package per
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
.
If structural QA fails, the producing workflow must fix the issue before the output moves forward.
Structural QA does not require domain expertise. It is a mechanical check that any analyst or agent can run.
Validation Rules
The structural QA process itself should fail validation if:
the checklist was not run at all
the QA was run against the wrong output version
failures were overridden without documentation
the QA result was not recorded in the handoff metadata
Human Review Gates
Escalate when:
structural QA reveals unexpected row loss exceeding 5%
geometry validity problems cannot be resolved programmatically
the CRS of the output is unknown or undocumented
a join produced duplicate rows that inflate the output
the agent reports a pass but the output looks implausible to a human reviewer
Common Failure Modes
skipping structural QA because "the data looks fine"
running structural QA once and not re-running after modifications
treating structural QA as optional for internal outputs
overriding failures without documenting why
confusing structural QA (data integrity) with interpretive review (meaning)
agents passing outputs that have correct structure but implausible values (structural QA does not catch interpretation errors)
Related Workflows
qa-review/STRUCTURAL_QA_CHECKLIST.md
— the operational checklist this standard governs
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
— requires QA status in handoff metadata
standards/PUBLISHING_READINESS_STANDARD.md
— Gate 1 requires structural QA to pass
all producing workflows (tract join, rollup, enrichment, POI extraction, etc.)
Sources
firm QA methodology notes
firm project review processes
Trust Level
Production Standard
