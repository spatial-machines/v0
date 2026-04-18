# LISA Cluster Analysis Workflow (Local Moran's I)

## Purpose

- run a Local Moran's I (LISA) analysis on a quantitative variable to identify both statistically significant clusters AND spatial outliers
- produce per-feature classifications across four cluster categories (HH, LL, HL, LH) plus a Not Significant category
- inherit the firm's spatial statistics policy from `standards/SPATIAL_STATS_STANDARD.md`

This workflow owns the **analytic** side of LISA. The **cartographic** side is owned by `workflows/HOTSPOT_MAP_DESIGN.md`.

## When to Use LISA Instead of Gi*

LISA distinguishes **clusters** (high values surrounded by high values, low values surrounded by low values) from **spatial outliers** (high values surrounded by low values, or vice versa). Use LISA when the analytical question is:

- "where are the outliers?" (a wealthy tract surrounded by poor ones, a high-vacancy block in a stable neighborhood)
- "are there features that diverge from their neighborhood context?"
- "is a feature an exception to its surroundings?"

If the question is only "where are the high and low concentrations?" — `workflows/HOTSPOT_ANALYSIS.md` (Gi*) is the simpler choice.

## Typical Use Cases

- finding spatial outliers in demographic data (high-income tracts adjacent to low-income clusters)
- identifying neighborhood discontinuities for market or equity analysis
- producing a cluster + outlier output for a report that emphasizes spatial heterogeneity
- complementing a Gi* analysis when the project brief specifically asks about outliers

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
- the variable is normalized (a rate, share, or percentage; raw counts are inappropriate for LISA)

## Preferred Tools

- Python and PySAL / esda for the analysis (`esda.moran.Moran_Local`)
- libpysal for spatial weights construction
- canonical core script: `compute_spatial_autocorrelation.py` (per `PIPELINE_STANDARDS.md` §2)

The wiki workflow describes the method. The script implementation lives in the canonical core scripts under `scripts/core/`.

## Execution Order

1. **Verify the Moran's I gate passed** for this variable. Read the spatial stats handoff entry produced by `workflows/SPATIAL_AUTOCORRELATION_TEST.md`. If the gate result is dispersed or random, halt and either choose a value choropleth via `workflows/CHOROPLETH_DESIGN.md` or escalate per the standard.
2. **Construct the spatial weights matrix** with the same type used for the gate. **Use row-standardized weights** for LISA (the gate also uses row-standardized; LISA matches that — unlike Gi*, which uses binary).
3. **Compute Local Moran's I per feature.** Each feature receives a local statistic plus a permutation-based significance value.
4. **Apply multiple comparisons correction** per the standard's required rule. Use False Discovery Rate (FDR) for exploratory work, Bonferroni for confirmatory work, and report **both** the uncorrected and the corrected significant feature counts. LISA's per-feature significance test is more sensitive to multiple comparisons than the global Moran's I; the correction matters more here than in many other contexts.
5. **Classify each feature into one of five categories** per the standard's reporting templates:
   - **HH (High-High)** — high value surrounded by high values → true hot cluster
   - **LL (Low-Low)** — low value surrounded by low values → true cold cluster
   - **HL (High-Low)** — high value surrounded by low values → spatial outlier (high)
   - **LH (Low-High)** — low value surrounded by high values → spatial outlier (low)
   - **Not Significant** — fails the significance test (after correction)
6. **Write the per-feature classification** to the output GeoDataFrame as a new field. The field is what `workflows/HOTSPOT_MAP_DESIGN.md` reads to render the LISA cluster map. The classification field should also include the local statistic value and the significance value per feature for reproducibility.
7. **Write the spatial stats handoff entry** for the LISA run. Record the weights type (row-standardized), the correction method, the uncorrected and corrected significant feature counts, the per-category counts (HH / LL / HL / LH / Not Significant), and the answers to the 5-question interpretation template.
8. **Hand off** to `workflows/HOTSPOT_MAP_DESIGN.md` for cartographic rendering, or to a report-writing workflow if no map is needed.

## Validation Checks

- the Moran's I gate result is documented and shows clustered (significant positive Moran's I) for this variable
- the same weights type is used for the gate and the LISA run on the same variable
- weights are row-standardized for LISA (not binary)
- multiple comparisons correction is applied and the method is named (FDR or Bonferroni)
- both uncorrected and corrected significant feature counts are reported
- per-feature classifications cover all features (no nulls in the classification field except where the source variable is null)
- the per-category counts (HH / LL / HL / LH / Not Significant) are recorded
- the 5-question interpretation template can be answered from the handoff
- spatial outliers (HL and LH) are not silently merged with clusters (HH and LL) in the output
- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` will pass against the output

## Common Failure Modes

- running LISA without first running and documenting the Moran's I gate
- running LISA on data that failed the gate
- using binary weights for LISA (should be row-standardized; binary is for Gi*)
- skipping multiple comparisons correction (LISA's per-feature significance is especially sensitive)
- reporting only HH and LL ("clusters") and silently dropping HL and LH ("outliers"), losing the unique value LISA provides
- conflating LISA categories with Gi* significance tiers in the output
- running LISA on raw counts instead of normalized metrics
- running LISA on n < 30 features and citing unstable results
- producing the analytic output without writing the handoff entry
- choosing LISA when Gi* would have been the simpler choice for the project's actual question

## Escalate When

- the Moran's I gate failed but the project brief still expects a LISA deliverable
- the corrected significant feature count is very small (single-digit) across all four cluster types
- HL or LH outliers are individually consequential and warrant feature-level investigation
- the result depends sensitively on the choice of weights type
- the topic is politically or commercially sensitive (LISA outputs name specific outlier features, which can be especially sensitive)
- the corrected count differs dramatically from the uncorrected count
- the LISA outliers intersect with known data quality issues (high-CV features, institutional tracts)

## Outputs

- a GeoDataFrame with a per-feature LISA classification field plus the local statistic value and significance value per feature
- a spatial stats handoff entry conveying:
  - weights type (row-standardized)
  - correction method (FDR or Bonferroni)
  - uncorrected significant count
  - corrected significant count
  - per-category counts (HH, LL, HL, LH, Not Significant)
  - 5-question template answers
  - timestamp
- handoff to `workflows/HOTSPOT_MAP_DESIGN.md` for cartographic rendering when a map is part of the deliverable

## Related Standards

- `standards/SPATIAL_STATS_STANDARD.md` — the firm's spatial statistics policy, the weights rule, the FDR/Bonferroni rule, the required reporting template
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition

## Related Workflows

- `workflows/SPATIAL_AUTOCORRELATION_TEST.md` — the Moran's I gate procedure that must run first
- `workflows/HOTSPOT_ANALYSIS.md` — alternative for cluster-only questions (no outlier emphasis)
- `workflows/HOTSPOT_MAP_DESIGN.md` — cartographic rendering workflow that consumes this workflow's output
- `workflows/CHOROPLETH_DESIGN.md` — the appropriate fallback when the gate fails

## Related QA

- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — operational checklist for any spatial stats output, including the LISA category integrity rules
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity gate run upstream
- `qa-review/MAP_QA_CHECKLIST.md` — for the cartographic side of any rendered LISA output
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — for narrative claims that name specific outlier features

## Sources

- firm spatial statistics methodology
- Anselin, L. (1995). Local Indicators of Spatial Association — LISA. *Geographical Analysis*, 27(2), 93-115.
- GeoDa Center workbook on local spatial autocorrelation
- PySAL / esda documentation

## Trust Level

Validated Workflow — Needs Testing
