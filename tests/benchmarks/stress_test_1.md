# Stress Test 1: Travis County Poverty & Health Outcomes

**Prompt:** "Analyze poverty and health outcomes in Travis County, Texas (FIPS 48453) census tracts"  
**Run Date:** 2026-04-05  
**Type:** Predicted score (not live run)

---

## What the Lead Analyst Should Do

1. **Parse task** → `parse_task.py` → project_brief.json
2. **Delegate to data-retrieval:**
   - `fetch_acs_data.py` for B17001 (poverty), B27010 (insurance), B19013 (income)
   - `retrieve_tiger.py --state 48` for Texas tract boundaries
   - CDC PLACES for health outcomes (model-based tract estimates)
3. **Delegate to data-processing:**
   - `join_data.py` to merge ACS + TIGER
   - `derive_fields.py` for poverty rate, uninsured rate
   - `compute_rate.py` with MOE propagation
4. **Delegate to spatial-stats:**
   - `compute_spatial_autocorrelation.py` (Global Moran's I)
   - `compute_hotspots.py` (Gi* with FDR correction)
   - `analyze_summary_stats.py`, `analyze_top_n.py`
5. **Delegate to cartography:**
   - `analyze_choropleth.py` for poverty, uninsured, income maps
   - `analyze_bivariate.py` for poverty × health outcome
   - `render_web_map.py` for interactive multi-layer map
6. **Delegate to validation-qa:** full QA gate
7. **Delegate to report-writer:** executive brief + technical report
8. **Delegate to delivery packaging:** `package_qgis_review.py`
9. **Delegate to peer-reviewer:** `run_peer_review.py`

## Predicted Score

| Dimension | Score | Rationale |
|---|---|---|
| Data Quality | 4/5 | ACS + TIGER is battle-tested. CDC PLACES may require manual URL fetch (not fully automated). |
| Analysis Rigor | 4/5 | Moran's I → Gi* pipeline is well-documented in SOUL.md. MOE propagation is in core scripts. May miss CDC PLACES correlation analysis. |
| Map Quality | 5/5 | Choropleth + bivariate + interactive maps all have core scripts. Vision QA enforced. |
| Report Quality | 3/5 | Report skeleton works but `key_findings` and `interpretation` still depend on analyst populating manifest. Weak spot. |
| Pipeline Completeness | 4/5 | Handoff chain should be complete. QGIS package now available. Data catalog via `write_data_catalog.py`. |
| Interpretation & Narrative | 3/5 | Lead analyst SOUL.md has good guidance but interpretation quality varies. Travis County is well-known enough for good context. |

**Predicted Total: 23/30 (B — Client-ready)**

## Strengths
- This is a standard equity analysis — the system's sweet spot
- ACS data retrieval is fully automated
- All map types have core scripts
- Vision QA and script enforcement are in place

## Risks
- CDC PLACES integration isn't fully automated (may require manual data fetch)
- Report narrative quality depends on lead analyst populating key_findings
- Travis County has 218 tracts — moderate complexity, should handle fine

## What Would Push This to 27+
- Automated CDC PLACES fetch via `fetch_federal_data.py` (currently in future/)
- Better auto-population of `key_findings` in `collect_report_assets.py`
- Lead analyst providing rich interpretation in the manifest
