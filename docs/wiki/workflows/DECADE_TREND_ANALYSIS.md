# Decade Trend Analysis Workflow

Purpose:
produce a defendable 10-year trend workflow for demographic and socioeconomic indicators
keep the firm's default trend lane disciplined and repeatable
Typical Use Cases
market-analysis trend summaries
ZIP-oriented app preparation using tract-first analysis
client-facing demographic change reporting
internal screening of trend-ready versus snapshot-only variables
Inputs
approved project brief
approved variable package
approved geography level
approved endpoint vintages
approved inflation policy where relevant
Preconditions
the project has read
standards/TREND_ANALYSIS_STANDARD.md
the project has classified indicators as:
current snapshot only
10-year trend-ready
selective extended-history
the project has confirmed whether outputs remain tract-level or will later roll to ZIP / ZCTA
Preferred Tools
firm ACS retrieval scripts
tract geometry retrieval
GeoPandas or PostGIS for joins and shaping
approved derived-metric helpers such as CAGR computation
Execution Order
Confirm the approved 10-year endpoint pair.
Confirm the approved geography.
Retrieve only the variables approved as 10-year trend-ready.
Retrieve or confirm the geometry needed for the approved geography.
Join each endpoint dataset to the working geometry using stable IDs.
Validate the endpoint tables before deriving change.
Compute:
absolute change
percent change where appropriate
CAGR where appropriate
For income or currency-sensitive variables, apply the approved inflation treatment before presenting change.
Produce trend tables and draft maps.
Mark any unstable metrics as snapshot-only or caveated.
Validation Checks
endpoint years are explicit everywhere
the geography is consistent across endpoints
derived change metrics reconcile with source values
inflation handling is documented for income
the output clearly distinguishes current value from change over time
Common Failure Modes
mixing multiple ACS vintages without a clear endpoint strategy
showing nominal income change as if it were real growth
treating all variables as equally trend-ready
mixing tract and ZIP logic too early in the process
creating charts that imply stronger comparability than the sources support
Escalate When
endpoint selection changes the story materially
geography drift makes the trend weakly defensible
race / ethnicity category comparability becomes ambiguous
the client asks for a 20-year story on variables that are only safe for 10-year use
Outputs
validated endpoint datasets
trend summary table
derived growth metrics
draft charts or maps
methodology note describing endpoint and comparability choices
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/TREND_ANALYSIS_STANDARD.md
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md
— general analysis conventions this workflow specializes for 10-year trend analysis
Related Data Sources
data-sources/CENSUS_ACS.md
data-sources/TIGER_GEOMETRY.md
Related QA Pages
qa-review/TREND_OUTPUT_REVIEW.md
Sources
Census ACS documentation
firm trend methodology notes
Trust Level
Validated Workflow Needs Testing
