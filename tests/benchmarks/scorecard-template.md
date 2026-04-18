# Analysis Run Scorecard

**Project ID:** `_______________`  
**Benchmark Case:** `_______________`  
**Run Date:** `_______________`  
**Scored By:** `_______________`  
**Pipeline Stages Completed:** retrieval / processing / analysis / validation / reporting _(circle)_

---

## Scoring Guide

Each section is scored 0–5. Total is out of 30.
**Client-ready threshold: 22/30**

| Score | Meaning |
|---|---|
| 5 | Excellent — exceeds expectations, no issues |
| 4 | Good — meets expectations, minor notes only |
| 3 | Acceptable — meets minimum bar, has notable gaps |
| 2 | Below bar — has significant issues but partially usable |
| 1 | Poor — major problems, requires rework |
| 0 | Missing or completely broken |

---

## Section 1: Data Quality (0–5)

**What to check:**
- All expected geographic units are present (join rate ≥ 95%)
- No NULL values from failed joins (as opposed to Census suppression)
- Institutional tracts flagged (prisons, military, universities)
- Data vintage noted and appropriate for the question
- MOE/reliability flags present where applicable

**Score: ___ / 5**

**Notes:**
```
(What's missing, what issues were found, what was good)
```

---

## Section 2: Analysis Rigor (0–5)

**What to check:**
- Correct denominators used for rate calculations
- Global Moran's I run before any hotspot/LISA analysis
- FDR correction applied to multiple comparison tests
- Classification scheme appropriate and documented (quantile vs natural breaks vs equal interval)
- Spatial weights matrix choice documented
- Uncertainty/reliability flagged for small-N tracts

**Score: ___ / 5**

**Notes:**
```
(Which methods were used, which were skipped, any methodological issues)
```

---

## Section 3: Map Quality (0–5)

**What to check:**
- Maps are 200dpi or higher, 14×10 minimum
- Colorblind-accessible palette
- Legend is clear and correctly labeled
- State/county outline present for context
- Title includes variable name and vintage year
- No clipping or misaligned layers
- Attribution present (data source, projection)

**Score: ___ / 5**

**Notes:**
```
(Map-by-map notes, specific issues with palette/legend/extent)
```

---

## Section 4: Report Quality (0–5)

**What to check:**
- Report leads with the key finding (Pyramid Principle — answer first)
- Methods section is present and accurate
- Caveats section acknowledges data limitations
- Sources cited with URLs and vintage
- Figures are referenced in the text
- No fabricated or hallucinated statistics
- Executive summary is standalone (readable without maps)

**Score: ___ / 5**

**Notes:**
```
(Report structure, missing sections, any factual issues)
```

---

## Section 5: Pipeline Completeness (0–5)

**What to check:**
- All expected output files exist and are non-empty
- Handoff chain JSON present for each stage
- Validation QA report produced and signed off
- No orphaned temp files or incomplete stages
- Run is reproducible (script call logged in handoff)

**Score: ___ / 5**

**Notes:**
```
(Missing stages, broken handoffs, any pipeline gaps)
```

---

## Section 6: Interpretation & Narrative (0–5)

**What to check:**
- Analysis answers the actual question posed (not just produces outputs)
- Geographic patterns correctly described (not just "there is variation")
- Results contextualized (compared to state/national benchmarks where available)
- No overreach — conclusions are supported by the data
- Appropriate hedging for model-based estimates (CDC PLACES, EJScreen)

**Score: ___ / 5**

**Notes:**
```
(Is the story told correctly? Is anything misleading or unsupported?)
```

---

## Overall Grade

**Total: ___ / 30**

| Score | Grade | Interpretation |
|---|---|---|
| 27–30 | A | Exceptional — publishable quality |
| 22–26 | B | Client-ready ✅ |
| 18–21 | C | Needs revision before delivery ⚠️ |
| 12–17 | D | Major rework required ❌ |
| 0–11 | F | Do not deliver — fundamental issues |

**Grade: ___**

**Client-ready? YES / NO**

---

## Recommended Actions

```
(List specific fixes needed before delivery, or note what made this run exceptional)
```

---

## Comparison to Benchmark Quality Criteria

For this benchmark case, the quality criteria defined in `suite.json` are:

> *(Copy the quality_criteria for this benchmark case here for reference while scoring)*

**Data Quality criteria met? YES / PARTIAL / NO**  
**Analysis Rigor criteria met? YES / PARTIAL / NO**  
**Map Quality criteria met? YES / PARTIAL / NO**  
**Report Quality criteria met? YES / PARTIAL / NO**
