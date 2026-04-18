# Stress Test 3: Douglas County Poverty + Transit Access

**Prompt:** "Which census tracts in Douglas County, Nebraska have both high poverty AND poor transit access?"  
**Run Date:** 2026-04-05  
**Type:** Predicted score (not live run)

---

## What the Lead Analyst Should Do

1. **Recognize reuse opportunity:** We already have `analyses/omaha-equity-analysis/` with Nebraska tract data (scored 27/30). The lead analyst SHOULD check existing analyses before starting from scratch.
2. **Parse task** → `parse_task.py` → project_brief.json referencing existing Omaha data
3. **Delegate to data-retrieval:**
   - Reuse existing TIGER tracts from Omaha analysis
   - Fetch transit stop data: `fetch_poi.py` (Overpass: public_transport=stop_position in Douglas County)
   - OR use GTFS data if available
4. **Delegate to data-processing:**
   - Filter to Douglas County (FIPS 31055) tracts
   - `spatial_join.py` to count transit stops per tract or compute distance to nearest stop
   - `derive_fields.py` to create "poor transit" flag (low stop density or high distance)
   - Cross-reference with existing poverty rate data
5. **Delegate to spatial-stats:**
   - `analyze_bivariate.py` for poverty × transit access
   - `compute_hotspots.py` on combined disadvantage index
   - `analyze_top_n.py` for tracts that are worst on both dimensions
6. **Delegate to cartography:**
   - `analyze_bivariate.py` — poverty × transit
   - `analyze_choropleth.py` — transit access standalone
   - `overlay_points.py` — transit stops on poverty choropleth
   - `render_web_map.py` — interactive multi-layer
7. **Validation, reporting, publishing, peer review**

## Predicted Score

| Dimension | Score | Rationale |
|---|---|---|
| Data Quality | 4/5 | Existing Omaha ACS data is high quality (scored 27). Transit data via OSM is the unknown. |
| Analysis Rigor | 3/5 | Bivariate + hotspot is well-supported. "Poor transit access" definition is subjective — needs clear operationalization. |
| Map Quality | 4/5 | Bivariate choropleth + point overlay + interactive map all have core scripts. |
| Report Quality | 3/5 | Same key_findings population issue. The "both X AND Y" framing needs clear threshold definitions. |
| Pipeline Completeness | 3/5 | Data reuse from existing analysis is smart but may not be automated. Transit data pipeline is newer. |
| Interpretation & Narrative | 4/5 | Omaha context is well-known. Poverty + transit is a well-studied equity question. Lead analyst should have good framing. |

**Predicted Total: 21/30 (C — Needs revision before delivery)**

## Strengths
- **Data reuse from existing Omaha analysis** — if the lead analyst recognizes this, it saves significant time and ensures data quality
- Bivariate choropleth for poverty × transit is exactly what this question needs
- The system has all the analysis scripts needed
- Douglas County has ~180 tracts — manageable size

## Risks
- **Transit data** is the biggest unknown — OSM transit stop coverage in Omaha may be incomplete
- **"Poor transit access" operationalization** — the system doesn't have a standard definition. Need to decide: stop density per tract? Distance to nearest stop? Service frequency?
- **Data reuse is not automated** — lead analyst must manually discover and reference existing Omaha data
- GTFS feed integration is not in core scripts

## What Would Push This to 25+
- Standard transit access metric built into the pipeline (e.g., stops within 400m of tract centroids)
- Automated discovery of existing analyses for the same geography
- GTFS integration in `fetch_poi.py` or a dedicated transit fetch script
- Lead analyst SOUL.md guidance on cross-referencing existing analyses
