# Hotspot Analysis Workflow (Getis-Ord Gi*)

## Purpose

- run a Getis-Ord Gi* hotspot analysis on a quantitative variable to identify statistically significant clusters of high values (hot spots) and low values (cold spots)
- produce per-feature significance classifications that downstream workflows render and review
- inherit the firm's spatial statistics policy from `standards/SPATIAL_STATS_STANDARD.md`

This workflow owns the **analytic** side of Gi*. The **cartographic** side — color taxonomy, legend ordering, map family rules — is owned by `workflows/HOTSPOT_MAP_DESIGN.md`.

## Typical Use Cases

- finding intensity clusters in normalized demographic data (poverty rate, uninsured rate, vacancy rate)
- finding spatial concentrations of a market or risk indicator
- producing a hotspot output that the cartography workflow renders for a client deliverable
- baseline cluster discovery when the analytic question is "where are the highs and lows?"

If the question is "are there outliers as well as clusters?" use `workflows/LISA_CLUSTER_ANALYSIS.md` instead.

## Inputs

- analysis-ready GeoDataFrame with the polygons and the target variable
- the variable must be a normalized metric (rate, share, percentage), not a raw count
- the spatial stats handoff entry from `workflows/SPATIAL_AUTOCORRELATION_TEST.md` showing a clustered gate result for this variable
- a documented decision about which spatial weights type to use (consistent with the gate)

## Preconditions

- **the Moran's I gate has passed** for this variable, with the same weights and the same geography that will be used here. The gate result must be recorded in the spatial stats handoff per `workflows/SPATIAL_AUTOCORRELATION_TEST.md`. Without a documented gate pass, this workflow must not run.
- CRS confirmed per `standards/CRS_SELECTION_STANDARD.md`
- structural QA passed per `standards/STRUCTURAL_QA_STANDARD.md`
- n ≥ 30 features (the standard's "Do Not Use When" preclusion applies)
- the variable is not constant
- the variable is normalized (a rate, share, or percentage; raw counts are inappropriate for Gi*)

## Preferred Tools

- Python and PySAL / esda for the analysis
- libpysal for spatial weights construction
- canonical core script: `compute_hotspots.py` (per `PIPELINE_STANDARDS.md` §2)

The wiki workflow describes the method. The script implementation lives in the canonical core scripts under `scripts/core/`.

## Execution Order

1. **Verify the Moran's I gate passed** for this variable. Read the spatial stats handoff entry produced by `workflows/SPATIAL_AUTOCORRELATION_TEST.md`. If the gate result is dispersed or random, halt and either choose a value choropleth via `workflows/CHOROPLETH_DESIGN.md` or escalate per the standard.
2. **Construct the spatial weights matrix** with the same type used for the gate. **Use binary weights** for Getis-Ord Gi* (the gate uses row-standardized; Gi* uses binary — this is the firm's convention per the standard).
3. **Compute the Gi* statistic per feature.** Each feature receives a z-score reflecting whether its value, plus its neighbors' values, deviates significantly from the global mean.
4. **Apply multiple comparisons correction** per the standard's required rule. Use False Discovery Rate (FDR) for exploratory work, Bonferroni for confirmatory work, and report **both** the uncorrected and the corrected significant feature counts.
5. **Classify each feature into significance tiers** per the standard's reporting templates:
   - **Hot Spot (99% confidence)** — Gi* z-score > 2.58
   - **Hot Spot (95%)** — Gi* z-score > 1.96
   - **Hot Spot (90%)** — Gi* z-score > 1.65
   - **Not Significant** — Gi* z-score in the range that fails the chosen significance level (after correction)
   - **Cold Spot (90%)** — Gi* z-score < -1.65
   - **Cold Spot (95%)** — Gi* z-score < -1.96
   - **Cold Spot (99%)** — Gi* z-score < -2.58
6. **Write the per-feature classification** to the output GeoDataFrame as a new field. The field is what `workflows/HOTSPOT_MAP_DESIGN.md` reads to render the cluster map.
7. **Write the spatial stats handoff entry** for the Gi* run. Record the weights type, the correction method, the uncorrected and corrected significant feature counts, the significance threshold, and the per-tier feature counts. The 5-question interpretation template (per the standard's Required Reporting rule) must be answerable from this entry.
8. **Hand off** to `workflows/HOTSPOT_MAP_DESIGN.md` for cartographic rendering, or to a report-writing workflow if no map is needed.

## Validation Checks

- the Moran's I gate result is documented and shows clustered (significant positive Moran's I) for this variable
- the same weights type is used for the gate and the Gi* run on the same variable
- weights are binary for Gi* (not row-standardized)
- multiple comparisons correction is applied and the method is named (FDR or Bonferroni)
- both uncorrected and corrected significant feature counts are reported
- the significance threshold is named and defended
- per-feature classifications cover all features (no nulls in the classification field except where the source variable is null)
- the per-tier feature counts are recorded
- the 5-question interpretation template can be answered from the handoff
- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` will pass against the output

## Common Failure Modes

- running Gi* without first running and documenting the Moran's I gate
- running Gi* on data that failed the gate (the most consequential failure: the output looks meaningful but is noise)
- using row-standardized weights for Gi* (should be binary)
- skipping multiple comparisons correction and reporting raw significant counts as final
- citing only the uncorrected count of significant features
- choosing a different significance threshold than the standard's tiers without justification
- running Gi* on a raw count instead of a normalized metric, producing a population-density artifact in cluster space
- running Gi* on n < 30 features and citing the unstable result as a finding
- running Gi* on a variable that's not in the spatial stats handoff's gate-passed set
- producing the analytic output without writing the handoff entry (the cartography workflow then has nothing to verify against)

## Escalate When

- the Moran's I gate failed but the project brief still expects a hotspot deliverable
- the corrected significant feature count is very small (single-digit) and the narrative would overstate the finding
- the result depends sensitively on the choice of weights type (e.g., switching from queen to KNN materially changes the cluster pattern)
- the topic is politically or commercially sensitive
- the corrected count is dramatically smaller than the uncorrected count and the project brief expected the uncorrected scale
- the cluster pattern intersects with known data quality issues (high-CV features, institutional tracts, demographic floors)

## Outputs

- a GeoDataFrame with a per-feature Gi* classification field
- a spatial stats handoff entry conveying:
  - weights type (binary)
  - correction method (FDR or Bonferroni)
  - uncorrected significant count
  - corrected significant count
  - significance threshold
  - per-tier feature counts (Hot 99/95/90, Not Significant, Cold 90/95/99)
  - 5-question template answers
  - timestamp
- handoff to `workflows/HOTSPOT_MAP_DESIGN.md` for cartographic rendering when a map is part of the deliverable

## Related Standards

- `standards/SPATIAL_STATS_STANDARD.md` — the firm's spatial statistics policy, the weights rule, the FDR/Bonferroni rule, the required reporting template
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition

## Related Workflows

- `workflows/SPATIAL_AUTOCORRELATION_TEST.md` — the Moran's I gate procedure that must run first
- `workflows/LISA_CLUSTER_ANALYSIS.md` — alternative when outliers are part of the question
- `workflows/HOTSPOT_MAP_DESIGN.md` — cartographic rendering workflow that consumes this workflow's output
- `workflows/CHOROPLETH_DESIGN.md` — the appropriate fallback when the gate fails

## Related QA

- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — operational checklist for any spatial stats output, including the Gi* requirements
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity gate run upstream
- `qa-review/MAP_QA_CHECKLIST.md` — for the cartographic side of any rendered Gi* output
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — for narrative claims that derive from Gi* findings

## Sources

- firm spatial statistics methodology
- Getis, A. & Ord, J.K. (1992). The Analysis of Spatial Association by Use of Distance Statistics. *Geographical Analysis*, 24(3), 189-206.
- Anselin, L. (1995). Local Indicators of Spatial Association — LISA. *Geographical Analysis*, 27(2), 93-115.
- PySAL / esda documentation
- GeoDa Center workbook

## Trust Level

Validated Workflow — Needs Testing
