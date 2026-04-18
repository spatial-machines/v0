# ZIP / ZCTA Aggregation Standard

Purpose:
define how tract- or block-group-based analysis is rolled up to ZIP-oriented outputs
prevent invalid aggregation of non-additive metrics
make ZIP delivery reproducible and explainable
Use When
Use this standard whenever:
final client outputs are ZIP-oriented
upstream analysis is tract- or block-group-based
results need to be summarized to ZIP or ZCTA geography
Do Not Use When
Do not use this standard if:
the source data is already natively produced at the approved ZIP or ZCTA geography
the project is only delivering tract-level outputs
Approved Rule
Default upstream geography:
tract
Default delivery geography:
ZCTA or another explicitly validated ZIP-like layer
Do not assume USPS ZIPs and Census ZCTAs are identical. The chosen ZIP representation must be documented in the project.
Inputs
Required inputs:
approved tract or block-group working layer
approved ZIP or ZCTA delivery layer
explicit crosswalk or allocation method
metric classification
Metric classes (see
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
for the full general rules):
additive counts
rates and shares
medians and other non-additive statistics
Method Notes
Additive counts
Examples:
population
households
counts of degree holders
Approved approach:
roll up using a defended tract-to-ZIP or block-group-to-ZIP allocation method
document whether allocation is area-weighted, address-weighted, housing-weighted, population-weighted, or based on another defended crosswalk
Rates and shares
Examples:
bachelor's degree share
renter share
Hispanic share
Approved approach:
do not average rates unless the weighting method is explicitly justified
recompute from rolled-up numerators and denominators where possible
Medians and non-additive metrics
Examples:
median household income
median age
Approved approach:
do not sum or average naively
use a documented approximation, proxy, or source-native ZIP estimate
if no defensible method exists, keep the metric at tract level or mark it as not safely rollup-ready
Validation Rules
The output should fail validation if:
ZIP geography is undefined
a median is simply averaged from tract values with no method note
shares are averaged with no weighting rationale
the rollup method is not documented
Human Review Gates
Escalate when:
choosing between USPS ZIP and ZCTA representation
rolling up non-additive metrics
using block groups as the default base geography
using a crosswalk that could materially affect client interpretation
Common Failure Modes
treating ZIP and ZCTA as interchangeable
averaging medians
averaging shares without weighting logic
hiding the crosswalk choice
using a casual spatial join as if it were a defensible aggregation method
Related Workflows
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/DECADE_TREND_ANALYSIS.md
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
— general metric-class rules for aggregation
data-sources/ZCTA_AND_ZIP_NOTE.md
— canonical reference on ZIP vs. ZCTA distinction
qa-review/ZIP_ROLLUP_REVIEW.md
Sources
U.S. Census ZCTA documentation and ACS geography support
TIGER / Census geometry guidance
firm methodology notes from LA phase 1
Trust Level
Production Standard Needs Source Validation Human Review Required
