# Spatial Stats Output Review Checklist

This checklist is the QA gate for any output that includes spatial autocorrelation, hotspot, or cluster analysis. Use it together with `standards/SPATIAL_STATS_STANDARD.md` (the governing standard) and `qa-review/STRUCTURAL_QA_CHECKLIST.md` (the upstream structural integrity gate).

Purpose:
provide a dedicated review checklist for spatial statistics outputs (Global Moran's I, Getis-Ord Gi*, Local Moran's I / LISA)
catch the specific failures that arise from clustering and autocorrelation analysis, which are distinct from structural or interpretive QA
enforce the firm's Spatial Stats Standard in review
Use When
Use this checklist when reviewing any output that includes:
Global Moran's I results
Getis-Ord Gi* hot/cold spot classification
Local Moran's I (LISA) cluster classification
maps that visualize any of the above
narrative claims about spatial clustering, hotspots, or outliers
Do Not Use When
Do not use this checklist for:
pure choropleth maps of values (no clustering analysis applied) — those use
qa-review/MAP_QA_CHECKLIST.md
trend or change-over-time outputs without a clustering component — those use
qa-review/TREND_OUTPUT_REVIEW.md
outputs from statistical methods other than spatial autocorrelation or local clustering
Core Review Checks
Moran's I gate documentation
the output documents a Global Moran's I result for the variable being analyzed
the statistic value, the z-score, and the p-value are recorded
the gate decision (clustered / dispersed / random) is stated explicitly
any local statistic shown is accompanied by the gate result that justified running it
the gate result is computed on the same variable, the same weights, and the same geography as the local statistic
Spatial weights documentation
the weights type is named (queen contiguity, rook contiguity, KNN, distance band)
weights are row-standardized for Moran's I and LISA, or binary for Getis-Ord Gi*
weights consistency: the same weights type is used for the global gate and the local statistic on the same variable
if the weights produced many islands or empty rows, the choice is justified
Multiple comparisons correction documentation
the correction method is named (Bonferroni or False Discovery Rate)
both the uncorrected and the corrected counts of significant features are reported
the corrected count is plausible relative to the uncorrected count and the dataset size
no "significant feature" claim cites only the uncorrected count
The 5-question interpretation template completeness
the output answers all five required questions from the standard:
1. Is there statistically significant spatial structure?
2. If yes, where does it cluster?
3. What type of clustering is present?
4. How many significant clusters remain after correction?
5. What does this mean for the analytical question?
any unanswered question is a failure; outputs that skip the template should not be released
Cluster category integrity
for Gi* outputs: hot spot tiers (99% / 95% / 90%), "not significant", and cold spot tiers (90% / 95% / 99%) are all distinguishable in the output
for LISA outputs: HH, LL, HL, LH, and "not significant" are all distinguishable
"not significant" features are visible in the output and visually subordinate to the significant clusters (not invisible or styled as significant)
no Gi* and LISA categories are mixed in the same output legend
the significance threshold is named and defended
Uncertainty / MOE flagging
features that fail the firm's uncertainty thresholds are flagged in the output (per the orchestration role's non-negotiables and any future MOE standard)
the source data's vintage and uncertainty characteristics are recorded
small-population or high-CV features that influence the cluster pattern are noted
For maps showing spatial stats results
map family is thematic categorical per
standards/CARTOGRAPHY_STANDARD.md
no basemap, no scale bar, no north arrow on the map (per the family rules)
title names both the underlying metric and the analysis type (Gi* or LISA)
attribution cites both the source data and the analytic method with weights and correction
legend ordering is correct (Gi*: hot → not significant → cold; LISA: HH → HL → not significant → LH → LL)
Escalate When
the global Moran's I gate failed (random data) but a local statistic is being shown anyway
n < 30 features and the analysis was run anyway (permutation tests are unstable)
the corrected count of significant features is very small (single-digit) and the narrative overstates the finding
spatial weights are inconsistent between the gate and the local statistic
the cluster pattern would change materially if a different weights type were used (sensitivity concern)
the topic is politically or commercially sensitive and the cluster pattern could mislead
the source data has a high proportion of features failing uncertainty thresholds
the analyst is presenting raw uncorrected results as significant clusters
Common Failure Modes
running and reporting a local statistic without a Global Moran's I gate result
publishing a hotspot map for data that failed the gate
ignoring multiple-comparisons correction or citing uncorrected counts as significant
weights mismatch between the gate (e.g., row-standardized) and the local statistic (e.g., binary on the same variable)
treating "not significant" features as if they were significant in the narrative or in the map's color choices
mixing Gi* significance tiers with LISA cluster types in the same output
small-N analyses (n < 30) with unstable permutation results presented as confident findings
narrative claims that overstate the strength of the clustering finding
missing or incomplete answers to the 5-question interpretation template
not flagging small-population features whose clustering contribution is statistically unstable
title that names only the underlying metric (so the viewer thinks they are looking at a value choropleth rather than a clustering result)
Relationship to Other QA Pages
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first for general structural integrity of the underlying dataset
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
— run after for narrative-level claims that derive from the spatial stats output
qa-review/MAP_QA_CHECKLIST.md
— run for the cartographic side of any spatial stats map
standards/SPATIAL_STATS_STANDARD.md
— the governing standard for the analytic side of every check on this page
workflows/SPATIAL_AUTOCORRELATION_TEST.md
— the workflow this checklist verifies for the gate step
workflows/HOTSPOT_ANALYSIS.md
— the workflow this checklist verifies for Gi* outputs
workflows/LISA_CLUSTER_ANALYSIS.md
— the workflow this checklist verifies for LISA outputs
Governing Standard
standards/SPATIAL_STATS_STANDARD.md
— defines the firm's policy on spatial autocorrelation and clustering, the Moran's I gate, the weights rule, the FDR / Bonferroni rule, the required reporting template, and the escalation rules
Trust Level
Validated QA Page Needs Testing
