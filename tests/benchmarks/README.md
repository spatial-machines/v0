# Benchmark Suite

Systematic quality testing for the GIS Agent pipeline.

## Purpose

The benchmark suite provides a standardized set of test cases for evaluating pipeline quality, reproducibility, and agent coordination. It answers:

- Does the pipeline produce correct, complete outputs for known problem types?
- Do map, report, and data quality meet the 22/30 client-ready threshold?
- Which agents are contributing correctly and which are bottlenecks?
- Are regressions introduced when scripts are updated?

Each benchmark case is based on a real analysis type with known expected outputs and quality criteria. Scoring uses the `scorecard-template.md`.

---

## Test Cases

See `suite.json` for full definitions. Summary:

| ID | Name | Type | Geography |
|---|---|---|---|
| `ks-poverty-health` | Kansas Poverty & Health | Choropleth + summary stats | Kansas tracts |
| `ks-healthcare-access` | Kansas Healthcare Access | Point overlay + bivariate + hotspots | Kansas tracts |
| `sd-tracts-demo` | South Dakota Demographic Baseline | Simple demographic | SD tracts |
| `chicago-food-access` | Chicago Food Access | Federal data + service areas | Cook County tracts |
| `la-environmental-justice` | LA Environmental Justice | Multi-indicator | LA County tracts |

---

## How to Run a Benchmark

### 1. Run the analysis

For each test case, create the project brief from the benchmark definition and run the full pipeline:

```bash
# Create a project workspace from the benchmark spec
python scripts/core/create_run_plan.py \
  --benchmark benchmarks/suite.json \
  --id ks-poverty-health \
  --output analyses/benchmark-ks-poverty-health/

# Run the pipeline (send to lead-analyst agent via your AI coding agent)
# Or run manually stage by stage
```

### 2. Score the output

Open `benchmarks/scorecard-template.md`, copy it to the analysis output folder, and fill it in:

```
cp benchmarks/scorecard-template.md analyses/benchmark-ks-poverty-health/scorecard.md
# Edit scorecard.md with actual scores
```

### 3. Compare to quality_criteria

Each benchmark entry in `suite.json` defines `quality_criteria` — use these as the rubric while scoring.

### 4. Record results

Update this table with benchmark run results:

| Date | Benchmark | Score | Grade | Notes |
|---|---|---|---|---|
| 2026-04-03 | ks-poverty-health | 23/30 | B | Client-ready |
| 2026-04-03 | ks-healthcare-access | 22/30 | B | Client-ready |
| 2026-04-03 | sd-tracts-demo | — | — | Not yet run as benchmark |
| 2026-04-03 | chicago-food-access | 20/30 | C | USDA URL dead |
| 2026-04-03 | la-environmental-justice | 21/30 | C+ | Just under threshold |

---

## Scoring Threshold

- **≥ 22/30** → Client-ready ✅
- **18–21/30** → Needs revision before delivery ⚠️
- **< 18/30** → Do not deliver ❌

---

## Files

- `suite.json` — benchmark test case definitions
- `scorecard-template.md` — blank grading template for a single run
