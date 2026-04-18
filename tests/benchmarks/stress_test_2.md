# Stress Test 2: Kansas Starbucks Demographic Profile

**Prompt:** "Map all Starbucks locations in Kansas and show the demographic profile within 3 miles of each location"  
**Run Date:** 2026-04-05  
**Type:** Predicted score (not live run)

---

## What the Lead Analyst Should Do

1. **Parse task** → `parse_task.py` → project_brief.json
2. **Delegate to data-retrieval:**
   - `fetch_poi.py` for Starbucks locations in Kansas (Overpass/OSM query: amenity=cafe, name~Starbucks)
   - `fetch_acs_data.py` for demographics (B01003 population, B19013 income, B17001 poverty, B03002 race/ethnicity)
   - `retrieve_tiger.py --state 20` for Kansas tract boundaries
3. **Delegate to data-processing:**
   - `compute_trade_areas.py` to generate 3-mile buffers around each Starbucks
   - `enrich_points.py` to pull demographic data within each buffer
   - `spatial_join.py` to intersect trade areas with census tracts
4. **Delegate to spatial-stats:**
   - `analyze_summary_stats.py` for demographic profile of trade areas vs state
   - `analyze_top_n.py` for most/least affluent trade areas
5. **Delegate to cartography:**
   - `overlay_points.py` for Starbucks locations on Kansas base map
   - `analyze_choropleth.py` for income/poverty choropleth with point overlay
   - `render_web_map.py` for interactive map with Starbucks points + demographics
6. **Delegate to validation-qa, report-writer, site-publisher, peer-reviewer**

## Predicted Score

| Dimension | Score | Rationale |
|---|---|---|
| Data Quality | 3/5 | `fetch_poi.py` exists but Overpass queries can be unreliable. Starbucks name matching may miss variants. OSM completeness varies. |
| Analysis Rigor | 3/5 | Trade area + enrichment pipeline exists but hasn't been battle-tested end-to-end. 3-mile buffer is simple but adequate. |
| Map Quality | 4/5 | Point overlay + choropleth is well-supported. Interactive map with trade areas would be impressive. |
| Report Quality | 3/5 | Same weakness as Test 1 — key_findings population. POI analysis narrative requires different framing than equity analysis. |
| Pipeline Completeness | 3/5 | POI → trade area → enrichment is a newer pipeline path. Handoff chain may have gaps. |
| Interpretation & Narrative | 3/5 | "Starbucks as demographic indicator" is well-documented in GIS literature. Lead analyst should know this frame. |

**Predicted Total: 19/30 (C — Needs revision before delivery)**

## Strengths
- All required scripts exist in core/ (`fetch_poi.py`, `compute_trade_areas.py`, `enrich_points.py`)
- Interactive map with point overlay is well-supported
- Demographic enrichment pipeline is documented

## Risks
- **`fetch_poi.py` via Overpass has not been heavily tested** — this is the biggest risk
- `compute_trade_areas.py` and `enrich_points.py` may not have been run end-to-end in production
- OSM may not have complete Starbucks coverage for Kansas (rural areas)
- The POI → trade area → enrichment pipeline is less battle-tested than the ACS equity pipeline

## What Would Push This to 25+
- Verified Overpass query for Starbucks in Kansas (test `fetch_poi.py` with this query)
- Battle-tested `compute_trade_areas.py` → `enrich_points.py` pipeline
- Optiplex OSM DB connection for reliable POI data (production roadmap item)
- Template for "demographic profile of [brand] locations" analysis type
