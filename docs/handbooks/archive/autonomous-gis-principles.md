# Autonomous GIS Principles
## For the Lead Analyst
### Sources: Penn State GIS Science Lab, LLM-Geo (Zhenlong Li), arXiv:2305.06453

---

## What This Firm Is

This GIS consulting firm is an implementation of **Autonomous GIS** — the paradigm introduced by the Penn State GIScience Lab in 2023. In that model:

> "An AI-powered GIS that leverages LLM's general abilities in natural language understanding, reasoning, and coding for addressing spatial problems with automatic spatial data collection, analysis, and visualization."

The five autonomous goals we aim for:
1. **Self-generating** — Generate new tools and code when needed
2. **Self-organizing** — Decompose a problem and sequence the work
3. **Self-verifying** — Check our own outputs before delivery
4. **Self-executing** — Run the analysis without human intervention at each step
5. **Self-growing** — Learn from each project and improve

The lead analyst is the **LLM brain** of this autonomous system. The specialist agents are the **digital hands**.

---

## The GIS Problem-Solving Framework
### (Penn State GEOG 483: Problem-Solving with GIS)

Every GIS problem has a six-step structure. Follow this every time:

```
Step 1: STATE THE PROBLEM
   → What exactly is the client asking?
   → Is it a descriptive question (what/where), explanatory (why), or prescriptive (what should we do)?
   → What decision will this analysis support?

Step 2: BREAK IT DOWN
   → What spatial data is needed?
   → What analytical operations are required?
   → What's the logical sequence? (Can't analyze without processing; can't process without data)
   → Which agents handle which parts?

Step 3: EXPLORE INPUT DATASETS
   → What's the spatial resolution? (tract, county, zip code)
   → What's the temporal vintage? (2022 ACS, 2024 TIGER)
   → Are there known quality issues? (group quarters, water-only tracts)
   → What's the join key? (GEOID format — always verify)

Step 4: PERFORM ANALYSIS
   → Run the appropriate analytical methods
   → Check intermediate results before proceeding
   → Run Global Moran's I BEFORE any spatial clustering tools
   → Verify outputs make geographic sense

Step 5: VERIFY THE MODEL RESULT
   → Does the output match expectations?
   → Are there outliers that need explanation?
   → Do the maps tell a coherent story?
   → Are university/military tracts distorting poverty stats?

Step 6: IMPLEMENT THE RESULT
   → Format for the audience (consulting firm partner, not just GIS analyst)
   → Write narrative that leads with findings
   → Deliver to the review site
```

---

## Decision Support vs. Pure Analysis

From GEOG 483: GIS is most powerful when it supports a **decision**, not when it produces maps for their own sake.

**Always ask:** "What decision does this analysis support?"

| Question type | Right approach | Wrong approach |
|---|---|---|
| "Where are the highest-poverty areas?" | Choropleth + Top-N ranking | Hotspot analysis of spatially random data |
| "Where should we place a clinic?" | Drive-time + point overlay + underserved tracts | Just mapping poverty |
| "Are poverty and uninsurance correlated spatially?" | Global Moran's I + Bivariate choropleth | Two separate choropleths |
| "Has poverty changed since 2017?" | Temporal comparison + change detection | Single-year choropleth |

---

## The LLM-Geo Lesson: Use Existing Tools, Don't Reinvent

From the LLM-Geo paper: "LLM-Geo tends to develop complex functions from scratch based on GeoPandas for spatial operations that are already available in traditional GIS packages or toolboxes."

**This firm has scripts for everything.** Check the scripts directory before writing new code:
- `overlay_points.py` — nearest distance, point-in-polygon, buffer counts
- `compute_hotspots.py` — Gi* analysis
- `compute_spatial_autocorrelation.py` — Moran's I + LISA
- `analyze_bivariate.py` — bivariate choropleth
- `fetch_acs_data.py` — Census data retrieval
- `analyze_choropleth.py` — single-variable choropleth

Only write new scripts when the task genuinely isn't covered. When writing new scripts, save them to `scripts/` for reuse.

---

## Analytical Quality Gates

Before delivering results, verify:

### Data quality
- [ ] Join match rate > 95%? (If not, diagnose GEOID format before proceeding)
- [ ] Null/zero population tracts identified and flagged?
- [ ] Data vintage matches the question? (ACS 2022 ≠ 2024 conditions)

### Analysis validity
- [ ] For spatial clustering: Global Moran's I run first?
- [ ] For any rate: divided by correct denominator? (not total population for insurance)
- [ ] For comparison: same geography, same year, same table?

### Output quality
- [ ] Maps tell a coherent story?
- [ ] Key findings are specific numbers, not vague statements?
- [ ] University/institutional effects called out where relevant?
- [ ] QGIS review package generated for in-depth human review?

---

## Tool Selection Matrix

| Task | Primary Tool | Notes |
|---|---|---|
| Describe distribution | Summary stats + choropleth | Always first |
| Find high/low areas | Top-N ranking + choropleth | More useful than hotspots for diffuse data |
| Test for clustering | Global Moran's I | Gate for all local methods |
| Map clusters | Gi* or LISA | Only if global I is significant |
| Two variables together | Bivariate choropleth | Better than two separate maps |
| Points + polygon | overlay_points.py | Count, nearest, buffer |
| Causal explanation | Spatial regression | After OLS residual check |
| Change over time | Temporal join + difference map | Need two vintage datasets |
| Service area | Drive-time (osmnx) | Use 10/20/30 min thresholds |
| Site selection | Multi-criteria overlay | Filter → intersect → rank |

---

## Communicating Analytical Limitations

Be specific. Not "there are some data quality issues" but:

- "12 of 829 Kansas tracts (1.4%) have zero population for poverty determination — likely water-only or group-quarters tracts. These are excluded from statistical analysis and mapped as missing."
- "ACS 5-year estimates for very small rural tracts have margins of error that can exceed the estimate itself. Rates for tracts with fewer than 500 people should be interpreted cautiously."
- "The University of Kansas and K-State tracts show extreme poverty rates (47-56%) due to student populations who report low income but often have institutional health coverage. These should be excluded from policy-focused analyses targeting persistent economic disadvantage."

---

## QGIS Output — Always Required

Every analysis must produce a QGIS review package (`outputs/qgis/`). This allows the human reviewer to:
- Open the actual GeoPackage in QGIS for detailed inspection
- Modify symbology, classification, or projection
- Add additional layers
- Create print-quality layout exports via QGIS Print Composer

The QGIS package is the deliverable that lets the client do their own further analysis. A PNG map is a snapshot; a QGIS project is a working dataset.

**Use:** `scripts/write_qgis_project_pyqgis.py` or `scripts/package_qgis_review.py`
