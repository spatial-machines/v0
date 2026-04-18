# Trend Analysis Standard

Purpose:
define how the firm handles current snapshot, 10-year trend, and selective extended-history analysis
reduce fake confidence in long-run comparisons
make trend claims consistent across projects
Use When
Use this standard whenever a workflow includes:
time-series framing
multi-vintage ACS or Census comparisons
change metrics such as growth or CAGR
Do Not Use When
Do not use this standard to force every variable into a trend line. Some variables should remain snapshot only.
Approved Rule
Default client-facing trend lane:
10-year
Selective extended-history lane:
20-year only for indicators with defended source continuity and geography handling
Trend readiness categories:
current snapshot only
10-year trend-ready
selective extended-history
Inputs
Required inputs:
approved indicator list
approved endpoint vintages
approved geography level
approved inflation handling where relevant
Method Notes
Start with endpoint-based trend analysis, not maximal year collection.
Use tract as the default upstream geography for demographic trend work.
Treat ACS 5-year endpoints as the default recent trend lane.
Use decennial anchors where they materially improve long-horizon context.
Apply inflation normalization before presenting multi-year income trend comparisons.
Do not present a trend if variable definitions or category structures are too unstable.
Validation Rules
A trend claim should fail validation if:
endpoint years are not explicit
inflation handling is missing for income comparisons
geography changes are ignored
the variable was not approved as trend-ready
a 20-year claim is made without a documented comparability note
Human Review Gates
Escalate when:
choosing 20-year framing for a variable
endpoint selection materially changes interpretation
inflation method is ambiguous
the geography used for the trend is unstable
Common Failure Modes
collecting more years than the method can defend
equating ACS availability with comparability
mixing geography levels across years
showing long-run income change in nominal dollars
letting charts imply confidence that the methods do not support
Related Workflows
workflows/DECADE_TREND_ANALYSIS.md
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
standards/SPATIAL_STATS_STANDARD.md
— for spatially-explicit analysis of trend variables (e.g., where is poverty growing in clustered patterns)
qa-review/TREND_OUTPUT_REVIEW.md
Sources
U.S. Census ACS 5-year documentation
decennial Census reference materials
firm LA trend methodology notes
Trust Level
Production Standard Human Review Required
