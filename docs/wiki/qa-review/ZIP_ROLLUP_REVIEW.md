# ZIP Rollup Review Checklist

Purpose:
provide a focused review checklist for outputs that have been aggregated from tracts (or block groups) to ZIP or ZCTA geography
catch the specific errors that arise from geographic rollup, which are distinct from general structural or interpretive QA
enforce the firm's ZIP / ZCTA Aggregation Standard in review
Use When
Use this checklist when reviewing any output where:
tract-level or block-group-level data has been rolled up to ZIP or ZCTA
the client delivery is ZIP-oriented but the analysis was performed at a finer geography
a crosswalk or allocation method was used to translate between geographies
Do Not Use When
Do not use this checklist if:
the output is natively at tract level and no rollup occurred
the source data was originally produced at ZIP or ZCTA level (e.g., ACS ZCTA-level tables used directly)
Core Review Checks
Geography Identity
the output explicitly states whether the delivery geography is ZCTA, USPS ZIP, or another ZIP-like representation
the choice of ZIP representation is documented in the methodology note
the output does not silently mix ZCTA and USPS ZIP codes
the geometry vintage is stated (e.g., 2020 ZCTAs)
Crosswalk and Allocation Method
the tract-to-ZIP or block-group-to-ZIP crosswalk is named and documented
the allocation method is stated: area-weighted, population-weighted, housing-unit-weighted, or other
if a spatial join was used instead of a published crosswalk, the method and its limitations are documented
the crosswalk vintage matches the data vintage
Additive Count Rollup
population, household, and other additive counts were summed through the crosswalk
the total population (or other control total) at ZIP level reconciles reasonably with the county or state total
no double-counting occurred from tracts allocated to multiple ZIPs without proportional splitting
Rate and Share Rollup
shares and rates were recomputed from rolled-up numerators and denominators
shares were not averaged across tracts without weighting
the denominator for each rate is explicitly stated at the ZIP level
if weighted averaging was used instead of numerator/denominator recomputation, the weighting method is documented and justified
Non-Additive Metric Handling
medians (income, age, rent, etc.) were not summed or averaged naively
if a median appears in the ZIP output, the approximation method is documented
if no defensible method exists for a median at ZIP level, the metric is either excluded or caveated prominently
any proxy methods (e.g., tract-population-weighted median approximation) are labeled as approximations
Plausibility Checks
ZIP-level population totals are plausible relative to known benchmarks
extreme values (very high or very low) are investigated, not silently passed through
ZIPs with very few contributing tracts are flagged (results may be dominated by a single tract)
ZIPs that span county or state boundaries are handled explicitly
Documentation
the methodology note describes the rollup in plain English
the rollup method is reproducible from the documentation
limitations of the rollup are stated (e.g., "medians are approximations" or "this crosswalk does not account for split tracts")
Escalate When
the rollup method materially changes a key metric compared to the tract-level result
median income or other non-additive metrics appear at ZIP level without a method note
the ZIP representation choice (ZCTA vs. USPS) is unresolved
the client has strong expectations about ZIP accuracy that the method cannot fully support
shares or rates at ZIP level do not reconcile with expectations
Common Failure Modes
averaging tract-level medians to produce a ZIP median
averaging tract-level shares without population weighting
using a casual spatial join as if it were a published crosswalk
hiding whether the geography is ZCTA or USPS ZIP
not checking control totals after rollup
treating the rolled-up output as equally precise to the tract-level input
delivering ZIP-level metrics with more decimal places than the method supports
Relationship to Other QA Pages
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
— the governing standard for this review
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first for general structural integrity
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
— run after this checklist to validate narrative claims about ZIP-level findings
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
— the workflow this review validates
Trust Level
Validated QA Page Needs Testing Human Review Required
