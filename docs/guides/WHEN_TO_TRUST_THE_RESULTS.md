# When to Trust the Results

Guidance on interpreting spatial-machines outputs with appropriate confidence. Same spirit as a cartographer's internal "should I ship this?" checklist.

## The short version

- **Trust the geometry.** If source data came from Census TIGER, EPA EJScreen, FEMA NFHL, or USGS, the boundaries are authoritative and the pipeline validates them (CRS, geometry validity, feature count).
- **Trust the arithmetic.** Derived fields (rates, ratios, area calculations) use simple, auditable math.
- **Trust the validation verdict.** `PASS`, `PASS WITH WARNINGS`, and `REWORK NEEDED` mean what they say. Read the warnings before citing anything.
- **Be cautious about inference when coverage is low.** ACS at tract level has real margins of error; 1-year ACS estimates are noisier than 5-year; CV > 0.15 (high-CV) tracts are flagged by the pipeline — don't treat those as precise.
- **Be cautious with small-N analyses.** A choropleth of 30 tracts is illustrative; a choropleth of 3,000 tracts is statistical.

## How to assess confidence for a run

### 1. What is the join coverage?

Every pipeline run's validation handoff records join coverage — how many rows from the attribute data found a matching geometry (or vice versa).

| Coverage | Confidence |
|---|---|
| > 90% | High — results represent the geography well |
| 50–90% | Medium — note which areas are missing and whether that matters for the question |
| < 50% | Low — results describe only the covered subset, not the full geography |
| < 10% | Demo-level — useful for pipeline testing, not for analysis |

### 2. What does the validation status say?

| Status | What it means |
|---|---|
| `PASS` | All checks within thresholds. Results are as reliable as the input data allows. |
| `PASS WITH WARNINGS` | Pipeline is correct, but data quality flags were raised. **Read every warning** before citing the results. |
| `REWORK NEEDED` | Something is broken. Do not use the outputs for analysis. Investigate and re-run. |

### 3. What are the null rates?

High null rates for a field mean statistics and maps for that field reflect a subset, not the whole geography. Check `null_pct` in the summary-stats CSV.

| Null rate | Guidance |
|---|---|
| 0–5% | Field is well-populated; results are reliable |
| 5–25% | Usable but note the gaps in captions |
| 25–50% | Describes less than 3/4 of features — use with caution |
| > 50% | More than half the data is missing — don't treat results as representative |

### 4. What's the MOE profile (for ACS data)?

American Community Survey estimates come with margins of error. The pipeline attaches `*_moe` fields to every ACS-derived column and the Spatial Stats agent flags high-CV tracts (CV = MOE/1.645/estimate > 0.15).

| Profile | Guidance |
|---|---|
| CV mostly < 0.10 | Estimates are precise; rankings are meaningful |
| CV mostly 0.10–0.30 | Estimates are usable; avoid over-interpreting tiny differences |
| CV often > 0.30 | Noise dominates; consider aggregating to county or block group level, or using a 5-year ACS release instead of a 1-year |

### 5. Was the spatial-stats gate honored?

Global Moran's I must run before any local spatial analysis (Getis-Ord Gi*, LISA). If the global result is insignificant, the local "hotspots" are probably spurious. The pipeline enforces this; look for the Moran's I result in the analysis handoff.

Also check for FDR correction on Gi* / LISA: Benjamini-Hochberg adjusts for multiple testing across thousands of tracts. Raw p-values without FDR overstate significance; corrected p-values are the honest version.

### 6. Were institutional tracts flagged?

Military bases, prisons, universities, and nursing homes have populations that don't reflect the surrounding community's demographics. The pipeline flags these via `institutional_flag`. If you're mapping "median income" or "poverty rate" and a tract sits at the extreme tail, check whether it's institutional before drawing a conclusion.

### 7. Is the CRS correct?

The pipeline validates CRS presence and value. EPSG:4269 (NAD83) is the default for TIGER; EPSG:5070 for area/distance calculations in the contiguous US. If validation reports "CRS missing" or an unexpected value, investigate before trusting area calculations or spatial joins.

### 8. Were there geometry errors?

The vector validator checks geometry validity. If all geometries are valid, spatial operations (area, joins, choropleth rendering) are reliable. If invalid geometries are reported, downstream results for those features may be wrong.

## Red flags to watch for

- Validation status is `REWORK NEEDED` but someone used the outputs anyway
- Join coverage below 50% but results are presented as if they cover the full geography
- Choropleth maps for fields with > 25% null values (missing data distorts the visual)
- Summary statistics where `count` is much smaller than the expected feature count
- Reports that don't mention caveats or validation warnings
- Claims of causation from correlational analyses
- "Hotspots" without a significant global Moran's I
- Tiny rate differences compared across tracts with wide MOEs
- Cross-tract income / poverty comparisons without checking `institutional_flag`

## When to ship vs. when to hold

Ship when:
- Validation is `PASS` or `PASS WITH WARNINGS` and every warning has been read
- Coverage is > 80% (or clearly bounded if lower)
- The peer-reviewer agent issued `PASS` or `REVISE` (not `REJECT`)
- Caveats are in the report

Hold when:
- Validation is `REWORK NEEDED`
- Peer-reviewer verdict is `REJECT`
- You can't explain a finding when someone asks "why?"
- The map tells a different story than the statistics

## The demo is a demo

The bundled Sedgwick County demo uses Census data with full coverage, so its outputs are statistically sound for that county. But it's still a pedagogical example, not a real engagement. Don't ship a Sedgwick-poverty finding to a Sedgwick client just because the pipeline produced a clean report — go back through the above checklist first, decide whether the scope, coverage, and MOE profile actually meet what the client needs, and update the project brief before claiming the result.

## See also

- [`docs/wiki/standards/SPATIAL_STATS_STANDARD.md`](../wiki/standards/SPATIAL_STATS_STANDARD.md) — the mandatory statistical rules (Moran's I gate, FDR correction, MOE handling)
- [`docs/wiki/qa-review/`](../wiki/qa-review/) — validation checklists by domain
- [`docs/reference/PIPELINE_STANDARDS.md`](../reference/PIPELINE_STANDARDS.md) — the enforceable output standards
