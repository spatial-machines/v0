# GIS Firm Benchmark Scorecard

Used to evaluate each completed analysis project. Score each dimension 1–5.
A score of 3 = acceptable. 4 = good. 5 = client-ready.

---

## Dimension 1: Data Quality (max 5)
Can we trust the numbers?

| Score | Criteria |
|---|---|
| 1 | No QA run, unknown null/join rates |
| 2 | QA run but >20% nulls or <80% join rate, no flags addressed |
| 3 | QA passed, null rate <15%, join rate >85%, warnings noted in report |
| 4 | QA passed, institutional tracts flagged, MOE handled, caveats in report |
| 5 | All of 4 + Moran's I gate enforced, data dictionary delivered, vintage documented |

**Check:** Does `validate_analysis.py` show 0 blocking failures? Are institution flags reviewed?

---

## Dimension 2: Spatial Analysis Rigor (max 5)
Is the analysis actually spatial, not just a table with a map?

| Score | Criteria |
|---|---|
| 1 | Only descriptive stats, no spatial component |
| 2 | Single choropleth, no clustering or pattern analysis |
| 3 | Choropleth + Moran's I confirmed + one spatial method (hotspots OR regression) |
| 4 | Multiple spatial methods, model selection justified, residuals checked |
| 5 | All of 4 + FDR correction applied, interpretation addresses Moran's I result |

**Check:** Was Global Moran's I run before local stats? Was spatial regression model chosen correctly (OLS → LM → Lag/Error)?

---

## Dimension 3: Cartographic Quality (max 5)
Do the maps communicate something, or just display data?

| Score | Criteria |
|---|---|
| 1 | Default matplotlib colors, no title/legend, illegible at delivery size |
| 2 | Has title + legend, but wrong map type for data (choropleth of counts) |
| 3 | Correct map type, semantic palette, readable title + legend, state outline |
| 4 | All of 3 + caption explains the finding (not just what the map shows), attribution |
| 5 | All of 4 + appropriate classification scheme justified, interactive web map, consistent palette across project |

**Check:** Are counts mapped with proportional symbols (not choropleth)? Is the palette from `config/palettes.json`? Does each map caption assert a finding?

---

## Dimension 4: Report Quality (max 5)
Does the report lead with the answer or bury it?

| Score | Criteria |
|---|---|
| 1 | No report or raw data dump |
| 2 | Report structured around pipeline steps ("First we retrieved... then we processed...") |
| 3 | Pyramid structure: answer first, then evidence. Plain language executive summary. |
| 4 | All of 3 + SCQA arc, audience-calibrated, separate exec brief vs technical appendix |
| 5 | All of 4 + slide deck outline, data dictionary, map caption sheet, no unsupported claims |

**Check:** Does the first sentence of the report state the key finding? Is there a 1-page exec brief?

---

## Dimension 5: Deliverable Completeness (max 5)
Did we actually deliver everything a client would expect?

| Score | Criteria |
|---|---|
| 1 | Only raw outputs (CSV/GeoPackage), no report |
| 2 | Report + maps, but no QGIS package, no data download |
| 3 | Report + maps + QGIS package + data downloads on review site |
| 4 | All of 3 + interactive web map + validation report |
| 5 | All of 4 + PDF print layout, data dictionary, exec brief as standalone file |

**Check:** Are deliverables organized in `outputs/`? Does the QGIS package open styled? Are maps, reports, and QA results present?

---

## Dimension 6: Pipeline Efficiency (max 5)
Did the agents work cleanly without errors or manual intervention?

| Score | Criteria |
|---|---|
| 1 | Multiple errors requiring human intervention |
| 2 | Completed but with significant workarounds |
| 3 | Completed with 1–2 minor errors caught and corrected by agents |
| 4 | Clean run, all handoffs successful, log trail complete |
| 5 | All of 4 + parallel steps used, project brief maintained throughout |

**Check:** Are all `runs/` handoff JSONs present? Did any step have to be re-run?

---

## Scoring Template

```
Project: _______________
Date: _______________
Geography: _______________

Dimension                   | Score | Notes
----------------------------|-------|------
1. Data Quality             |  /5   |
2. Spatial Analysis Rigor   |  /5   |
3. Cartographic Quality     |  /5   |
4. Report Quality           |  /5   |
5. Deliverable Completeness |  /5   |
6. Pipeline Efficiency      |  /5   |
TOTAL                       |  /30  |

Threshold for "client-ready": 22/30 (avg 3.7)
Threshold for "firm standard": 26/30 (avg 4.3)

Key findings from this run:
-
-
-

What to fix before next run:
-
-
```

---

## Benchmark Targets by Project

| Project | Expected Difficulty | Target Score |
|---|---|---|
| `chicago-food-access` | Medium — new federal data sources, service areas | 18/30 |
| `tx-healthcare-access` | Medium-Hard — spatial regression, proportional symbols | 17/30 |
| `mn-poverty-change` | Medium — change detection, small multiples | 19/30 |
| `la-environmental-justice` | Hard — EPA EJScreen + bivariate + hotspots | 16/30 |

These are first-run targets. We expect gaps — the point is to identify them.
