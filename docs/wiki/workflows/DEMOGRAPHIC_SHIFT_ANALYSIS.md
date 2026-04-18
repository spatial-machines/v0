# Demographic Shift Analysis Workflow

Purpose:
produce a defendable summary of demographic change over time for a defined geography
implement the framing rules in
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
as an operational workflow
give analysts and agents a repeatable process for turning trend data into demographic-change narrative outputs
Typical Use Cases
describing how a neighborhood's racial and ethnic composition has changed over 10 years
summarizing age-structure shifts for a market area
reporting changes in educational attainment, homeownership, or income distribution
producing the "demographic change" section of a market analysis or community profile
Inputs
validated trend output from
workflows/DECADE_TREND_ANALYSIS.md
(endpoint datasets with change metrics)
approved indicator package classified by trend readiness per
standards/TREND_ANALYSIS_STANDARD.md
approved geography and time horizon
project brief specifying audience and framing expectations
Preconditions
the decade trend analysis workflow has been completed and its outputs have passed
qa-review/TREND_OUTPUT_REVIEW.md
the indicator package has been classified as current-snapshot, 10-year trend-ready, or selective extended-history
the
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
has been read by the analyst or agent
the project has confirmed the audience and sensitivity level of the deliverable
Preferred Tools
GeoPandas or pandas for tabular analysis and derived metrics
firm charting scripts or libraries for visualization
text templates or agent prompts for narrative generation
Execution Order
Phase 1: Change Metric Preparation
Start from the validated trend endpoint datasets.
For each approved shift indicator, compute or confirm:
absolute count change (endpoint 2 count minus endpoint 1 count)
share at each endpoint (e.g., Hispanic share in 2012 vs. 2022)
share-point change (endpoint 2 share minus endpoint 1 share)
Classify each metric per
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
:
count change: additive
share change: derived from rate components
median change: non-additive, handle per standard
Flag indicators where the change is within the margin of error or where the absolute count is very small.
Phase 2: Composition vs. Change Separation
Produce two distinct output layers for each indicator:
current composition
: what the geography looks like at the most recent endpoint
change over time
: how it has shifted between endpoints
Do not combine these into a single table or narrative without clearly labeling which is which.
If the project requires both, produce side-by-side summaries or separate sections.
Phase 3: Framing and Narrative
Apply the framing rules from
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
:
state the geography explicitly
state the time horizon explicitly
distinguish count change from share change
avoid causal claims unless the project has specific evidence
do not frame ordinary directional change as a social conclusion
Draft the narrative summary:
lead with the most significant and defensible changes
note magnitude and direction
caveat small changes or changes in small populations
if race or ethnicity categories changed between endpoints, note that explicitly
If an agent generates the narrative, mark it for human review.
Phase 4: Visualization
Produce charts and maps for key shift indicators:
bar charts comparing composition at each endpoint
change maps using a diverging color scale
tables showing count change and share-point change side by side
Validate visualizations per
qa-review/MAP_QA_CHECKLIST.md
for maps and the visualization section of
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
for charts.
Phase 5: Review
Run the output through
qa-review/TREND_OUTPUT_REVIEW.md
for trend-specific checks.
Run the narrative through
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
for framing checks.
Confirm that the output meets the audience and sensitivity expectations from the project brief.
Package outputs for delivery or handoff.
Validation Checks
every shift claim traces to a specific indicator and endpoint pair
count change and share change are clearly distinguished
composition and change outputs are separated
category definitions are stable across the compared endpoints, or instability is caveated
small-population indicators are flagged rather than presented as confident findings
inflation adjustment is applied for income-related shift indicators
the narrative does not overclaim causation
Common Failure Modes
presenting share-point change without the count context (e.g., "Hispanic share dropped 3 points" without noting total population grew)
conflating current composition with change over time in the same paragraph
describing ordinary demographic movement as "displacement" or "gentrification" without evidence
over-reading changes within the margin of error
using unstable race or ethnicity categories across endpoints without noting the break
producing a shift narrative from snapshot-only variables that were not approved for trend use
letting agent-generated framing go to the client without human review
Escalate When
the shift narrative could be politically or commercially sensitive
race or ethnicity category comparability is weak for the chosen endpoints
the project brief implies a causal or advocacy framing that the data alone cannot support
a key indicator's change is within the margin of error but the client expects a definitive statement
the audience is public, media, or regulatory rather than an internal client team
Outputs
shift summary table (count change, share at each endpoint, share-point change)
current composition table
narrative summary following the firm's demographic shift standard
charts and maps for key indicators
methodology note documenting endpoints, indicators, framing choices, and caveats
Related Standards
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
standards/TREND_ANALYSIS_STANDARD.md
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
standards/OPEN_EXECUTION_STACK_STANDARD.md
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md
— general analysis conventions this workflow specializes for demographic shift framing
qa-review/TREND_OUTPUT_REVIEW.md
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
qa-review/MAP_QA_CHECKLIST.md
Sources
Census ACS documentation
firm demographic methodology notes
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
(primary methodological reference)
Trust Level
Draft Workflow Needs Testing Human Review Required
