# Spatial Stats Standard

Purpose:
define the firm's policy for spatial autocorrelation, clustering, and outlier analysis
prevent the most common spatial-stats failures: false-positive hotspot maps on randomly distributed data, ignored multiple-comparisons corrections, and unreported uncertainty
make spatial-stats decisions consistent across projects
Use When
Use this standard whenever a workflow includes:
spatial autocorrelation testing (Global Moran's I)
local clustering analysis (Getis-Ord Gi*, Local Moran's I / LISA)
spatial weights construction
any output that classifies features by spatial cluster type
spatial analysis of variables that have already been validated for trend or shift framing per
standards/TREND_ANALYSIS_STANDARD.md
and
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
Do Not Use When
Do not use this standard for analyses that do not involve spatial autocorrelation or clustering. The following situations are explicit preclusions for spatial-stats methods:
the data is not area data (use point pattern analysis instead)
n < 30 features (permutation tests are unstable; report a raw choropleth instead)
all values are identical (autocorrelation cannot be computed)
the question is about individual features (use filtering or ranking, not clustering)
the question is about change over time (cross-sectional autocorrelation is the wrong tool; use space-time analysis if available)
Approved Rule — The Moran's I Gate
Local spatial statistics may not be run without first running and documenting the result of a Global Moran's I test on the same variable, with the same spatial weights, on the same geography.
A workflow must:
compute Global Moran's I before any local statistic
record the statistic value, the z-score, the p-value, the spatial weights type, and the feature count
classify the result as significantly clustered, significantly dispersed, or random
proceed to local analysis only if the result is significantly clustered (positive Moran's I, p < 0.05)
The gate exists to prevent false-positive hotspot and LISA maps on data that has no spatial structure. A local statistic run on randomly distributed data will produce noise that looks like a real cluster pattern.
Approved Rules
Spatial weights selection
Choose the weights type that matches the geometry and the question:
queen contiguity for census tracts and other polygons sharing edges or corners (the firm's default)
rook contiguity for polygons sharing edges only (more conservative)
KNN (K=8) for irregular polygons or when contiguity creates many islands
distance band for point data or when a specific distance threshold matters
Row-standardize weights for Moran's I and LISA. Use binary weights for Getis-Ord Gi*.
Multiple comparisons correction
Local statistics across many features produce false positives by chance alone. With 800+ tracts at p < 0.05, dozens of significant results would be expected from random data. Apply correction:
Bonferroni bound for confirmatory work (most conservative)
False Discovery Rate (FDR) for exploratory work (less conservative, more practical)
Report both the uncorrected and the corrected significant feature counts.
Required reporting (the 5-question interpretation template)
Every spatial stats output must answer all five questions:
1. Is there statistically significant spatial structure? (Global Moran's I result)
2. If yes, where does it cluster? (local statistic results by feature)
3. What type of clustering is present? (HH / LL / HL / LH for LISA; hot/cold/not significant for Gi*)
4. How many significant clusters remain after multiple-comparisons correction?
5. What does this mean for the analytical question?
Outputs that do not answer all five questions are incomplete and should not be released.
Uncertainty handling
Every spatial stats output must report the uncertainty of the underlying source data and flag features that fail the firm's uncertainty thresholds. The propagation method, the threshold values, and the flagging procedure are owned by the orchestration role's non-negotiables (see
TEAM.md
Spatial Statistics & Demographics section) and by a future firm-wide standard for margin-of-error and coefficient-of-variation handling. This standard names the requirement; it does not redefine the method.
Inputs
Required inputs for any workflow that invokes this standard:
analysis-ready GeoDataFrame with the target variable
geography polygons confirmed for the project scope
working CRS confirmed per
standards/CRS_SELECTION_STANDARD.md
the source readiness tier of the underlying data per
standards/SOURCE_READINESS_STANDARD.md
Method Notes
Decision framework
Run Global Moran's I first. Then:
significant positive Moran's I (clustered) → proceed to local analysis with Gi* (intensity clusters) or LISA (clusters and outliers)
significant negative Moran's I (dispersed) → checkerboard pattern; rare in socioeconomic data; report the finding without local analysis
not significant (random) → do not run local statistics; map individual values as a choropleth or filter to high-value features directly; tell the story of uniformity if appropriate
Tool mapping (open execution stack)
The firm uses Python and PySAL / esda for spatial statistics. ArcGIS users coming to the firm's stack can map tools as follows:
| ArcGIS tool | PySAL / esda equivalent | When to use |
|---|---|---|
| Spatial Autocorrelation (Moran's I) | esda.moran.Moran | Test if data clusters globally |
| Hot Spot Analysis (Getis-Ord Gi*) | esda.getisord.G_Local | Find high/low intensity clusters |
| Cluster and Outlier (LISA) | esda.moran.Moran_Local | Find clusters and outliers |
| OLS Regression | spreg.OLS | Model spatial relationships (preconditions and full guidance live in the role doc) |
| Spatial Lag Model | spreg.ML_Lag | When OLS residuals are autocorrelated |
| Spatial Error Model | spreg.ML_Error | Alternative spatial regression |
Reporting templates
Phrase Global Moran's I results as a clustered/random/dispersed claim with the statistic, z-score, and p-value:
"Moran's I = 0.47 (z = 12.3, p < 0.001) → significant positive spatial autocorrelation; values cluster geographically"
"Moran's I = 0.06 (z = 1.4, p = 0.16) → no significant spatial clustering; a choropleth is appropriate; hot-spot analysis would not be meaningful"
Phrase Gi* results as significance-tier categories: Hot Spot (99% / 95% / 90%), Cold Spot (90% / 95% / 99%), Not Significant.
Phrase LISA results as four-category labels: HH (true hot spot), LL (true cold spot), HL (high outlier), LH (low outlier), plus a Not Significant class.
Validation Rules
A spatial stats output should fail validation if:
the Global Moran's I result is not documented before a local statistic is reported
the spatial weights type is not stated
multiple-comparisons correction is missing or its method is unstated
uncorrected and corrected significant feature counts are not both reported
the 5-question interpretation template is incomplete
features failing uncertainty thresholds are not flagged
the Moran's I gate failed (random data) but a hotspot or LISA map was produced anyway
Human Review Gates
Escalate when:
the Moran's I gate fails (random data) and the project brief still expects a clustering deliverable
n < 30 features and the project brief still expects a local statistic
spatial regression is being considered (operational guidance is owned by the role doc, not by this standard yet)
the analysis crosses multiple geographies with different weights structures and the results disagree
the source data has a high proportion of features failing uncertainty thresholds
the finding could be politically or commercially sensitive and the reviewer wants a confirmatory pass
Common Failure Modes
running local statistics without first running Global Moran's I
publishing a hotspot map produced from data with no significant global clustering
ignoring multiple-comparisons correction and citing raw p-value counts
reporting "significant" cluster counts without naming the correction method
weights type mismatch between Moran's I and the local statistic (e.g., binary for one and row-standardized for the other on the same variable)
treating "not significant" tracts in a Gi* output as if they were significant
using row-standardized weights for Gi* (should be binary) or binary weights for Moran's I (should be row-standardized)
small-N analyses with n < 30 producing unstable permutation tests
mixing categories from LISA (HH/LL/HL/LH) and Gi* (hot/cold/not significant) in the same output
Related Workflows
workflows/SPATIAL_AUTOCORRELATION_TEST.md
workflows/HOTSPOT_ANALYSIS.md
workflows/LISA_CLUSTER_ANALYSIS.md
workflows/DECADE_TREND_ANALYSIS.md
standards/TREND_ANALYSIS_STANDARD.md
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/STRUCTURAL_QA_STANDARD.md
qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
Sources
Anselin, L. (1995). Local Indicators of Spatial Association — LISA. Geographical Analysis, 27(2), 93-115.
GeoDa Center workbook on local spatial autocorrelation
Esri Spatial Statistics resources
Trust Level
Production Standard Human Review Required
