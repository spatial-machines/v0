# Count, Rate, and Median Aggregation Standard

Purpose:
define how the firm classifies and handles different metric types during aggregation
prevent invalid arithmetic on rates, shares, medians, and other non-additive statistics
provide a single reference for the metric-classification logic used across all rollup, enrichment, and summary workflows
Use When
Use this standard whenever a workflow:
aggregates values from a finer geography to a coarser geography
summarizes values across multiple features into a single row
combines tract, block-group, or point data into ZIP, buffer, service-area, or other composite outputs
computes weighted or derived metrics from source components
Do Not Use When
Do not use this standard for:
single-feature attribute lookups with no aggregation
metadata or categorical fields that are not being summarized
Approved Rule
Every metric being aggregated must be classified before aggregation begins.
Metric Classes
Additive Counts
Definition:
values that can be summed directly across features
Examples:
total population
number of households
count of owner-occupied units
count of workers in an industry
Approved aggregation:
sum, optionally weighted by an allocation factor when features are split across target zones
control totals should be checked after summation
Rates and Shares
Definition:
values expressed as a proportion, percentage, or per-unit metric that depend on both a numerator and a denominator
Examples:
bachelor's degree share (holders / population 25+)
renter share (renter-occupied / total occupied)
poverty rate (below poverty / total for whom status is determined)
persons per household
Approved aggregation:
recompute from aggregated numerator and aggregated denominator
do not average rates or shares across features without weighting
if weighted averaging is the only practical approach, document the weighting method and label the result as an approximation
Forbidden:
simple (unweighted) averaging of rates across features
Medians and Non-Additive Statistics
Definition:
values that cannot be reconstructed from component sums
Examples:
median household income
median age
median gross rent
median home value
Approved aggregation:
use a source-native estimate at the target geography when available (e.g., ACS publishes ZCTA-level medians for some tables)
use a documented approximation method (e.g., population-weighted interpolation of tract medians) and label the result explicitly as an approximation
if no defensible method exists, either keep the metric at the source geography or exclude it from the aggregated output
Forbidden:
averaging medians
summing medians
treating an averaged median as if it were a true median
Indices and Composite Scores
Definition:
derived scores that combine multiple inputs through a formula or model
Examples:
diversity index
walkability score
market-opportunity index
Approved aggregation:
recompute from component inputs at the target geography where possible
if recomputation is not possible, document the approximation method
do not average index values across features unless the index is designed for that use
Inputs
list of metrics to be aggregated
classification of each metric (count, rate, median, index)
source geography and target geography
allocation or weighting method if features are being split
Method Notes
Classify metrics at the beginning of the aggregation workflow, not after the aggregation is done.
Document the classification in the methodology note or data dictionary.
When a metric's class is ambiguous, default to the more conservative handling (treat it as non-additive until proven otherwise).
Rates and shares should carry their numerator and denominator through the pipeline so they can be recomputed at any target geography.
When using area-weighted or population-weighted allocation, apply the weight to the numerator and denominator independently before recomputing the rate at the target geography.
Validation Rules
An aggregation output should fail validation if:
any metric lacks a documented class
rates or shares were averaged without documented weighting
medians were summed, averaged, or otherwise aggregated without a documented method
control totals for additive counts do not reconcile within an acceptable tolerance
a recomputed rate's denominator is zero or missing and the result was not flagged
Human Review Gates
Escalate when:
a client expects a median at a coarse geography and no source-native estimate exists
the weighting method for rate aggregation could materially change the result
an aggregation produces values outside the plausible range for the metric
the metric classification is disputed within the team
Common Failure Modes
averaging tract-level median incomes and calling the result a ZIP-level median
averaging percentage shares without weighting by the underlying population
treating a ratio (e.g., persons per household) as an additive count
losing numerators and denominators during pipeline steps, making rate recomputation impossible
applying an area weight to a rate instead of to the numerator and denominator separately
presenting an approximated median without labeling it as such
Related Workflows
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/GEOCODE_BUFFER_ENRICHMENT.md
workflows/SERVICE_AREA_ANALYSIS.md
Sources
U.S. Census Bureau ACS methodology documentation
firm ZIP aggregation methodology notes
standard statistical practice for weighted aggregation
Trust Level
Production Standard Human Review Required
