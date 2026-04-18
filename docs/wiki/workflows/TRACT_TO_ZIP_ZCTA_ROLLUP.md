# Tract to ZIP / ZCTA Rollup Workflow

Purpose:
convert tract-based results into ZIP-oriented outputs without hiding aggregation risk
Typical Use Cases
ZIP-based client app delivery
market comparison at ZIP scale
tract-first demographic analysis with ZIP-facing summaries
Inputs
approved tract layer with joined attributes
approved ZIP or ZCTA delivery layer
approved crosswalk or allocation logic
metric classification
Preconditions
tract-level joins and derived metrics are complete
project has chosen the delivery geography representation
human review has approved the rollup method for non-additive metrics
Preferred Tools
GeoPandas
PostGIS
QGIS-compatible Python workflows
Execution Order
Confirm the ZIP / ZCTA representation.
Classify each metric as:
additive count
share or rate
non-additive metric
Apply the defended crosswalk or allocation method.
Roll up additive counts.
Recompute shares and rates from rolled-up numerators and denominators where possible.
Handle medians and other non-additive metrics with explicit method notes or keep them out of the rollup.
Validate the rolled-up layer.
Document the rollup method in plain English.
Validation Checks
ZIP layer is explicitly named
counts reconcile reasonably
rates were recomputed rather than naively averaged
non-additive metrics are documented or withheld
Common Failure Modes
using a casual spatial join with no method note
averaging medians
hiding whether the output is ZIP or ZCTA
mixing tract and ZIP logic in the same metric without explanation
Escalate When
medians are requested at ZIP level
the crosswalk materially changes client interpretation
there is disagreement over the delivery geography choice
Outputs
ZIP / ZCTA-level output layer
rollup method note
validation summary
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
standards/TREND_ANALYSIS_STANDARD.md
qa-review/ZIP_ROLLUP_REVIEW.md
data-sources/ZCTA_AND_ZIP_NOTE.md
Sources
Census ZCTA geography guidance
firm LA ZIP aggregation notes
Trust Level
Draft Workflow Needs Testing
