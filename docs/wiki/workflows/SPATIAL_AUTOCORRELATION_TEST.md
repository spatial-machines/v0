# Spatial Autocorrelation Test Workflow (Moran's I Gate)

## Purpose

- run the firm's mandatory Global Moran's I test as a precondition for any local spatial statistic
- produce the gate decision (clustered / dispersed / random) that determines whether hotspot or LISA analysis is appropriate
- inherit the firm's spatial statistics policy from `standards/SPATIAL_STATS_STANDARD.md`

This workflow exists as a dedicated page because the Moran's I gate is the firm's hardest spatial-stats rule. Both `workflows/HOTSPOT_ANALYSIS.md` and `workflows/LISA_CLUSTER_ANALYSIS.md` reference this workflow as a precondition.

## Typical Use Cases

- precondition test before any Getis-Ord Gi* hotspot analysis
- precondition test before any Local Moran's I (LISA) cluster analysis
- diagnostic test when deciding between a value choropleth and a clustering visualization
- baseline check on whether a variable has spatial structure worth analyzing locally

## Inputs

- analysis-ready GeoDataFrame with the polygons and the target variable
- a single quantitative variable to test for spatial structure
- a documented decision about which spatial weights type to use (per the spatial stats standard's weights rule)

## Preconditions

- CRS confirmed per `standards/CRS_SELECTION_STANDARD.md`
- structural QA passed per `standards/STRUCTURAL_QA_STANDARD.md`
- the dataset has at least 30 features (n < 30 makes permutation tests unstable; the standard's "Do Not Use When" preclusion applies)
- the variable is not constant (all-identical values cannot have spatial autocorrelation)
- the variable has been validated upstream (this workflow does not run on in-flight data)

## Preferred Tools

- Python and PySAL / esda for the test
- libpysal for spatial weights construction
- canonical core script: `compute_spatial_autocorrelation.py` (per `PIPELINE_STANDARDS.md` §2)

The wiki workflow describes the method. The script implementation lives in the canonical core scripts under `scripts/core/`.

## Execution Order

1. **Construct the spatial weights matrix.** Choose the type per `standards/SPATIAL_STATS_STANDARD.md` Approved Rules — queen contiguity is the firm's default for census tracts and polygons sharing edges or corners. Use rook for edge-only contiguity, KNN for irregular polygons or many islands, distance band for point data or specific-distance questions.
2. **Row-standardize the weights matrix.** Global Moran's I requires row-standardized weights. (The same variable's later local statistic — Gi* — uses binary weights instead; the local-statistic workflow handles its own weights setup.)
3. **Compute the Global Moran's I statistic** with the weights matrix and the target variable. Record the statistic value, the z-score, and the p-value.
4. **Classify the gate decision** per the standard's decision framework:
   - significant positive Moran's I (p < 0.05) → **clustered** → proceed to local analysis is permitted
   - significant negative Moran's I → **dispersed** → checkerboard pattern; rare in socioeconomic data; report the finding without local analysis
   - not significant → **random** → do not run local statistics; map individual values as a choropleth or filter to high-value features directly
5. **Document the result in the spatial stats handoff.** Record the statistic value, the z-score, the p-value, the spatial weights type used, the feature count, the gate decision, and the timestamp. The downstream local-statistic workflow reads this entry as its precondition; without it, the local statistic must not run.
6. **Decide the next step** per the gate result. If clustered, hand off to `workflows/HOTSPOT_ANALYSIS.md` or `workflows/LISA_CLUSTER_ANALYSIS.md` per the project brief. If dispersed or random, halt the clustering branch and either choose a value-based visualization or escalate per the standard.

## Validation Checks

- the spatial weights type is documented and matches the standard's weights selection rule
- weights are row-standardized for the global test
- the statistic value, z-score, and p-value are all recorded
- the gate decision (clustered / dispersed / random) is stated explicitly
- the gate result is recorded in the spatial stats handoff before any local statistic is run on the same variable
- n ≥ 30 features
- the variable is not constant
- the same variable, weights, and geography will be used by any downstream local statistic
- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` will be runnable against the downstream output

## Common Failure Modes

- skipping the Moran's I gate entirely and running a hotspot or LISA workflow on data with no spatial structure (the most consequential failure)
- using binary weights for the global test (the global test requires row-standardized weights; binary is for Gi*)
- using a different weights type for the gate than for the downstream local statistic on the same variable
- running the test on n < 30 features and treating the unstable result as authoritative
- running the test on a constant variable
- documenting only the statistic value without the z-score or p-value
- treating a p-value just above 0.05 as "almost significant" and proceeding to local analysis
- forgetting to record the gate result in the spatial stats handoff so downstream workflows have nothing to verify against

## Escalate When

- n < 30 features and the project brief still expects a clustering deliverable (the standard's Do Not Use When preclusion applies)
- the variable is constant or near-constant (no spatial structure can be measured)
- the weights matrix has many islands or empty rows and the result depends on how isolated features are handled
- the gate is borderline (p between 0.04 and 0.06) and the project brief expects a confident clustering finding
- the gate fails (random data) but the project brief still expects a hotspot or LISA deliverable
- the gate result contradicts a prior known characterization of the variable (sanity check failure)

## Outputs

- a Moran's I result entry in the spatial stats handoff JSON, conveying:
  - statistic value
  - z-score
  - p-value
  - spatial weights type
  - feature count
  - gate decision (clustered / dispersed / random)
  - timestamp
- a yes/no gate decision that the downstream local-statistic workflow consumes as its precondition

For the exact JSON schema of the spatial stats handoff, see the canonical core script and `ARCHITECTURE.md`. This workflow describes what the handoff conveys, not its on-disk shape.

## Related Standards

- `standards/SPATIAL_STATS_STANDARD.md` — the firm's spatial statistics policy; the Moran's I gate is the standard's headline rule
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition

## Related Workflows

- `workflows/HOTSPOT_ANALYSIS.md` — Gi* analytic workflow that consumes this gate's result as its precondition
- `workflows/LISA_CLUSTER_ANALYSIS.md` — LISA analytic workflow that consumes this gate's result as its precondition
- `workflows/CHOROPLETH_DESIGN.md` — the appropriate fallback when the gate result is random and a value visualization is the right tool
- `workflows/HOTSPOT_MAP_DESIGN.md` — cartographic rendering workflow downstream of a successful gate plus a Gi* or LISA run

## Related QA

- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — operational checklist for any spatial stats output, including the Moran's I gate documentation
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity gate run before this workflow

## Sources

- firm spatial statistics methodology
- Anselin, L. (1995). Local Indicators of Spatial Association — LISA. *Geographical Analysis*, 27(2), 93-115.
- GeoDa Center workbook on spatial autocorrelation
- PySAL / esda documentation

## Trust Level

Validated Workflow — Needs Testing
