# Trend Output Review Checklist

Purpose:
provide a dedicated review checklist for outputs that include time-series comparisons, growth metrics, or trend narratives
catch the specific errors that arise from multi-vintage analysis, which are distinct from general structural or interpretive QA
enforce the firm's Trend Analysis Standard in review
Use When
Use this checklist when reviewing any output that includes:
multi-vintage ACS or Census comparisons
absolute or percent change metrics
CAGR or annualized growth rates
trend narratives or change-over-time claims
inflation-adjusted income comparisons
Do Not Use When
Do not use this checklist if:
the output contains only current-snapshot data with no time-series element
the output is a data inventory that classifies variables by trend readiness but does not yet present trend results
Core Review Checks
Endpoint Integrity
both endpoint years are explicitly stated in every table, chart, and narrative claim
the endpoint vintages match the approved project specification
the same ACS product type is used at both endpoints (e.g., both are 5-year estimates)
decennial Census anchors are identified as such and not conflated with ACS estimates
Geography Consistency
the same geography level is used at both endpoints (e.g., both are tracts)
if tract boundaries changed between endpoints (e.g., post-2020 redistricting), the impact is documented
the geographic scope is identical at both endpoints (same county, same set of tracts)
Variable Comparability
each variable presented as a trend was approved as trend-ready per
standards/TREND_ANALYSIS_STANDARD.md
variables that are snapshot-only are not shown with change metrics
any variables with known category or definition changes between endpoints are caveated
race and ethnicity variables follow the comparability guidance in
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
Inflation and Unit Handling
income, rent, home-value, and other currency variables are inflation-adjusted before comparison
the inflation source and base year are documented (e.g., CPI-U, adjusted to 2022 dollars)
the output distinguishes nominal from real (inflation-adjusted) values
units are consistent across endpoints (not mixing counts with rates, or dollars with percentages)
Derived Metric Accuracy
absolute change = endpoint 2 value minus endpoint 1 value
percent change = (endpoint 2 - endpoint 1) / endpoint 1, with handling for zero or near-zero denominators
CAGR formulas are correctly applied with the right time span
derived metrics reconcile with the source endpoint values (spot-check at least 3 rows)
Narrative Alignment
the narrative does not claim a trend for a variable classified as snapshot-only
the narrative correctly describes the direction of change (increase vs. decrease)
the narrative does not overclaim based on small absolute changes or changes within the margin of error
20-year or extended-history claims are accompanied by a documented comparability note
the narrative does not conflate current composition with change over time
Visualization Check
chart axes clearly label endpoints with years
chart titles specify the time period and geography
trend lines or bar comparisons are visually proportionate to the actual change
no misleading axis truncation that exaggerates change
maps showing change use a diverging color scale, not a sequential one
Escalate When
a key trend reverses direction or changes magnitude depending on endpoint choice
race or ethnicity category definitions shifted materially between endpoints
inflation handling is ambiguous or produces counter-intuitive results
the client requests a 20-year trend for variables that are only approved for 10-year use
margin of error overlap makes a trend claim statistically weak
the trend narrative could be commercially or politically sensitive
Common Failure Modes
presenting nominal income change as real growth
using different geography levels at each endpoint without noting it
showing 20-year trends for variables with known category breaks
computing percent change from zero or near-zero baselines without flagging
labeling ACS 5-year estimates with a single year (e.g., "2022") instead of the estimate period (2018-2022)
copying trend language from a prior project without re-checking the numbers
missing the fact that tract boundaries changed after 2020
Relationship to Other QA Pages
standards/TREND_ANALYSIS_STANDARD.md
— the governing standard for trend methodology
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
— governs how demographic change is framed
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first for general structural integrity
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
— run after for narrative-level claims
workflows/DECADE_TREND_ANALYSIS.md
— the workflow this review validates
Trust Level
Validated QA Page Needs Testing
