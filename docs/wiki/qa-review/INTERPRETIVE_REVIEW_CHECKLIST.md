# Interpretive Review Checklist

This checklist is one component of the broader [Validation and QA Stage Workflow](../workflows/VALIDATION_AND_QA_STAGE.md). Use that workflow for stage order, final readiness classification, and validation handoff expectations.

Purpose:
provide a reusable checklist for reviewing whether analysis outputs support the interpretive claims made about them
catch overstatement, missing context, and narrative errors before client delivery
complement the Structural QA Checklist, which covers data integrity; this page covers meaning and communication
Use When
Use this checklist after structural QA has passed and before:
writing or finalizing a client memo
publishing a review site or dashboard
presenting findings to a client or internal stakeholder
an agent generates summary text or narrative from analysis outputs
Do Not Use When
Do not use this checklist as a substitute for structural QA. If the data has not passed
qa-review/STRUCTURAL_QA_CHECKLIST.md
, fix structural issues first.
Core Interpretive Checks
Claims Match the Data
every numeric claim in the narrative can be traced to a specific output table or field
the direction of change (increase, decrease, stable) matches the data
magnitudes cited in text match the underlying values (no rounding errors that change the story)
comparisons are between the correct geographies and time periods
Context Is Present
the geography is named explicitly (not just "the area" or "the market")
the time period is stated for any trend or change claim
the data source is identified
margins of error or confidence caveats are noted where they materially affect interpretation (especially for small geographies or small populations)
Overclaiming Is Flagged
correlation is not presented as causation
demographic change is not described as displacement without evidence
small absolute changes in small populations are not presented as dramatic shifts
a single metric is not used to characterize an entire market or population
projections or forecasts are labeled as such, not presented as observed data
Category and Metric Integrity
rates and counts are not confused
shares are presented with their denominator context
medians and means are not conflated
aggregated metrics note the aggregation method
metrics from different vintages are not compared without a comparability note
Map and Chart Review
map titles accurately reflect the metric shown
legend categories do not mislead (e.g., equal-interval vs. quantile classification choice is deliberate)
color scales are appropriate (sequential for magnitude, diverging for change)
units are visible on all axes and legends
chart annotations do not exaggerate or editorialize
bivariate or multi-variable maps include clear explanatory notes
Sensitivity and Framing
race and ethnicity descriptions follow the firm's demographic shift standard
income and poverty framing does not editorialize
neighborhood or community characterizations are evidence-based, not stereotype-based
language is appropriate for the intended audience
Escalate When
a finding could be commercially or politically sensitive
the data supports multiple reasonable interpretations and the narrative picks one without noting alternatives
margins of error overlap materially for a key comparison
the analysis involves legal, regulatory, or equity claims
an agent-generated narrative has not been reviewed by a human
Common Failure Modes
writing the narrative before the data is final, then not updating it
copying trend language from a prior project without checking the new data
letting chart titles do the interpretive work without verifying they match
presenting ACS estimates for small areas as if they were precise counts
mixing current snapshot data with change-over-time language in the same paragraph
Relationship to Other QA Pages
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first; structural QA must pass before interpretive review
qa-review/ZIP_ROLLUP_REVIEW.md
— additional checks specific to ZIP-aggregated outputs
qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md
— additional checks for outputs with spatial autocorrelation, hotspot, or LISA results
standards/TREND_ANALYSIS_STANDARD.md
— governs whether a trend claim is methodologically valid
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
— governs demographic change framing
Trust Level
Validated QA Page Needs Testing
