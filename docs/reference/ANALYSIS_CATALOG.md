# Analysis Type Catalog

The lead analyst uses this to match incoming questions to proven methodologies. Each type lists: when to use it, required data, the pipeline, scripts involved, and what "good" looks like.

**Rule: Only accept work we can execute well. If a request needs tools we don't have, say so and propose what we'd need.**

Last updated: 2026-04-06

---

## Tier 1 — Battle-Tested (Proven on real projects)

These have been executed end-to-end with quality results. Agents know the pattern.

### 1. Equity & Environmental Justice Analysis
**Pattern:** Identify communities facing compounding disadvantage across multiple dimensions.

**When to use:** Questions about disparities, environmental burden, health access, food access, housing burden, transit access — especially when race, income, or vulnerability is a dimension.

**Examples delivered:**
- Omaha Transit, Food Access & Health Equity
- Atlanta Housing Affordability & Transit Access
- Atlanta Heat Vulnerability & EJ Index
- LA County Environmental Justice & PM2.5
- Kansas Healthcare Access
- Chicago Food Access & Health Outcomes

**Required data:**
- Census ACS demographics (race, poverty, insurance, housing cost burden) via `fetch_acs_data.py`
- Infrastructure/facility points (transit stops, hospitals, grocery stores) via `fetch_poi.py` or manual
- Optional: federal data (EPA EJScreen, HRSA HPSA, USDA food desert)

**Pipeline:**
1. `fetch_acs_data.py` → tract/block group demographics
2. `fetch_poi.py` or manual → facility point data
3. `overlay_points.py` → distance to nearest, count within threshold per tract
4. `derive_fields.py` → rates, burden indices, composite scores
5. `compute_spatial_autocorrelation.py` → Global Moran's I (gate check)
6. `compute_hotspots.py` → Gi* clusters (only if Moran's I significant)
7. `analyze_bivariate.py` → key relationship (e.g., poverty × distance)
8. `analyze_choropleth.py` → primary and secondary variable maps
9. `overlay_points.py` → point overlay on choropleth
10. `render_web_map.py` → multi-layer interactive map

**What "good" looks like:**
- Identifies specific dual/triple-burdened tracts by name or GEOID
- Bivariate map showing the key intersection (vulnerability × access)
- Hotspot map (if significant) showing where burden clusters spatially
- Point overlay showing facility locations against the choropleth
- Report names specific places and quantifies the gap

---

### 2. Site Selection / Market Analysis
**Pattern:** Rank geographic units by unmet demand to identify expansion opportunities.

**When to use:** "Where should we open a new [store/clinic/facility]?" or "Where is the market gap?"

**Examples delivered:**
- Starbucks Denver Metro (v2 — tract-based)

**Required data:**
- Census ACS demographics (population, income, education, commute) via `fetch_acs_data.py`
- Existing brand locations via `fetch_poi.py` (OSM)
- Competitor locations via `fetch_poi.py` (OSM — flag incompleteness!)

**Pipeline:**
1. `fetch_acs_data.py` → tract demographics for study area counties
2. `fetch_poi.py` → brand + competitor POI
3. `overlay_points.py` → point-in-polygon counts per tract
4. `derive_fields.py` → demand factors (pop density, income, education, transit)
5. `score_sites.py` or custom → composite demand-supply score
6. `analyze_top_n.py` → top 10 candidate tracts
7. `analyze_choropleth.py` → site score map, saturation map
8. `overlay_points.py` → existing locations on score choropleth
9. `render_web_map.py` → multi-layer with score, demand factors, existing points

**⛔ CRITICAL RULE: ALWAYS use census tracts. NEVER use buffer-based circles.**

**What "good" looks like:**
- Top 10 ranked candidate tracts with specific demographics
- Clear demand-supply gap visualization
- Honest caveat about OSM data completeness
- Scoring methodology explained and reproducible

---

### 3. Temporal Change Detection
**Pattern:** Compare two time periods to identify where conditions improved or worsened.

**When to use:** "How has [poverty/income/population] changed?" or "Which areas are gentrifying?"

**Examples delivered:**
- Minnesota Poverty Change 2017–2022

**Required data:**
- Two ACS vintages (e.g., 2017 5-year and 2022 5-year)
- Same tract geometries for both (use 2020 TIGER)

**Pipeline:**
1. `fetch_acs_data.py` × 2 → both vintages
2. `compute_change_detection.py` → join vintages, compute change fields
3. `analyze_choropleth.py` with diverging colormap (RdBu_r) → change map
4. `analyze_small_multiples.py` → side-by-side vintage comparison
5. `analyze_choropleth.py` → baseline maps for each vintage
6. `render_web_map.py` → layers for each vintage + change

**What "good" looks like:**
- Diverging map with clear zero midpoint (red = worsened, blue = improved)
- Small multiples showing both vintages side-by-side
- Report quantifies: how many tracts improved vs worsened, and by how much
- Notes that ACS 5-year is a pooled estimate, not point-in-time

---

### 4. Healthcare / Service Access Analysis
**Pattern:** Measure geographic access to facilities and identify underserved areas.

**When to use:** "Where are healthcare deserts?" or "Which communities lack access to [service]?"

**Examples delivered:**
- Kansas Healthcare Access (hospitals + HPSA)
- Texas Healthcare Access & HPSA Coverage

**Required data:**
- Census ACS demographics via `fetch_acs_data.py`
- Facility locations (hospitals, clinics, FQHCs) via `fetch_poi.py` or federal data
- Optional: HRSA HPSA designations, drive-time isochrones

**Pipeline:**
1. `fetch_acs_data.py` → demographics
2. `fetch_poi.py` or manual → facility points
3. `overlay_points.py` → distance to nearest facility per tract, count within threshold
4. `derive_fields.py` → access indices
5. `analyze_bivariate.py` → poverty × distance (the key equity question)
6. `compute_hotspots.py` → cluster detection (if Moran's I significant)
7. `analyze_choropleth.py` → distance map, demographic maps
8. `overlay_points.py` → facility points on choropleth

**What "good" looks like:**
- Bivariate map: high poverty × far from hospital = intervention target
- Distance statistics: mean/median/max by urban vs rural
- Named intervention targets (specific tracts or communities)

---

## Tier 2 — Proven Scripts, Not Yet Full End-to-End Projects

These use scripts we have and libraries that are installed, but we haven't run a complete project with the full pipeline yet.

### 5. Suitability Analysis (Multi-Criteria)
**Pattern:** Weighted overlay of multiple factors to identify suitable locations for a specific land use.

**When to use:** "Where is the best location for [solar farm/warehouse/park/housing development]?"

**Scripts available:**
- `derive_fields.py` → normalize and weight factors
- `score_sites.py` → composite scoring
- `analyze_choropleth.py` → suitability map
- Custom: raster overlay via `rasterstats` + `rasterio` (both installed)

**Data needed:**
- Census demographics, land use/land cover, zoning (varies by project)
- Environmental constraints (flood zones, wetlands, protected areas)
- Infrastructure (roads, utilities, transit)

**What we'd need to build:**
- Constraint masking script (exclude areas that are absolute no-gos)
- Possibly raster-based suitability if resolution matters

---

### 6. Spatial Regression / Explanatory Modeling
**Pattern:** Identify which factors explain a geographic pattern statistically.

**When to use:** "What drives poverty rates?" or "What predicts health outcomes in this region?"

**Scripts available:**
- `analyze_spatial_regression.py` (OLS + spatial diagnostics)
- `spreg` library installed (spatial lag, spatial error models)
- `compute_spatial_autocorrelation.py` → check residuals

**What we'd need to build:**
- GWR support (need `mgwr` — currently not installed)
- Model comparison output (AIC, R², Moran's I of residuals)

---

### 7. Network / Accessibility Analysis
**Pattern:** Measure travel time or distance along a real road network, not straight-line.

**When to use:** "How far is the nearest hospital by road?" or "What areas are within 15 minutes of a fire station?"

**Scripts available (future):**
- `compute_service_areas.py` (in future/)
- `networkx` installed, `osmnx` NOT installed

**What we'd need:**
- Install `osmnx` for road network download
- Or connect to PostGIS OSM database on the Optiplex for pre-built networks
- Isochrone generation script

---

### 8. Demographic Profile / Community Assessment
**Pattern:** Comprehensive snapshot of a community's demographics, economy, and housing.

**When to use:** "Tell me about this community" or "What does [city/county] look like demographically?"

**Scripts available:**
- `fetch_acs_data.py` → any ACS variable
- `analyze_summary_stats.py` → descriptive statistics
- `analyze_top_n.py` → rankings
- `analyze_choropleth.py` → thematic maps

**This is basically the simplest case — no spatial statistics needed, just good cartography and clear narrative.**

---

## Tier 3 — Feasible but Need New Scripts

### 9. Land Use / Land Cover Change
**Pattern:** Compare satellite imagery or NLCD over time to detect development, deforestation, etc.

**What we'd need:**
- `rasterio` + `rasterstats` (installed) for raster processing
- NLCD download script (USGS)
- Change matrix computation
- Raster-to-vector conversion for reporting

### 10. Flood Risk / Hazard Analysis
**Pattern:** Overlay FEMA flood zones with demographics and infrastructure.

**What we'd need:**
- FEMA NFHL download integration
- Flood zone classification parser
- Exposure calculation (population/properties in flood zones)

### 11. Transportation / Commute Analysis
**Pattern:** Analyze commute patterns, transit coverage, transportation equity.

**What we'd need:**
- LEHD LODES data fetcher (origin-destination flows)
- GTFS transit feed parser
- Network routing for actual travel times

### 12. Real Estate / Property Analysis
**Pattern:** Property value modeling, zoning analysis, development impact assessment.

**What we'd need:**
- Property parcel data integration (county assessor feeds vary wildly)
- Hedonic pricing model script
- Zoning overlay tools

---

## Tier 4 — Would Need Significant New Infrastructure

### 13. Remote Sensing / Satellite Imagery
Heat island detection, NDVI vegetation analysis, impervious surface mapping.
**Need:** `xarray`, satellite data download pipeline (Sentinel, Landsat), raster classification.

### 14. 3D Visualization / Viewshed
Line-of-sight analysis, 3D building models, solar exposure.
**Need:** DEM processing pipeline, 3D rendering, viewshed algorithm.

### 15. Real-Time / Streaming Analysis
Live traffic, sensor data, IoT integration.
**Need:** Completely different architecture. Not a near-term goal.

---

## Decision Tree for the Lead Analyst

When a new question comes in:

```
Is it about disparities, equity, or burden?
  → Equity & Environmental Justice (#1)

Is it about "where should we put/open something?"
  → Site Selection (#2) — USE TRACTS NOT BUFFERS

Is it about change over time?
  → Temporal Change Detection (#3)

Is it about access to services/facilities?
  → Healthcare/Service Access (#4)

Is it about "what's the best location for [land use]?"
  → Suitability Analysis (#5) — Tier 2, may need custom work

Is it about "what causes this pattern?"
  → Spatial Regression (#6) — Tier 2

Is it about travel time or road network distance?
  → Network Analysis (#7) — Tier 2, needs osmnx or PostGIS

Is it about "describe this community"?
  → Demographic Profile (#8) — simplest case

Does it involve satellite imagery or land cover?
  → Tier 3/4 — flag limitations, scope carefully

None of the above?
  → Decompose the question into sub-questions that map to types above.
  → If it truly doesn't fit, it's probably outside our current capability — say so.
```

---

## What We Should Build Next (Priority Order)

1. **Install `osmnx`** — unlocks real network-based accessibility (Tier 2 → Tier 1)
2. **Connect PostGIS on Optiplex** — unlocks large-scale spatial joins, planet-wide POI queries
3. **FEMA flood zone fetcher** — high-demand analysis type, data is freely available
4. **LEHD LODES fetcher** — commute flow analysis, origin-destination mapping
5. **`mgwr` install** — geographically weighted regression for Tier 2 explanatory modeling
6. **NLCD raster pipeline** — land cover change detection
