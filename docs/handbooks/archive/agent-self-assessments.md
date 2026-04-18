# Agent Self-Assessments
## April 3, 2026

---

## Spatial Stats Agent — Self-Assessment

### What they CAN do well now:
- Descriptive statistics, Top-N rankings, rate computation with MOE propagation
- Choropleth maps, point overlays
- Ad-hoc Python (geopandas/scipy/numpy) in Docker

### Critical gaps (their own words):
> "The entire core of my SOUL.md's 'Non-Negotiable Protocol' has NO dedicated scripts."

Specifically missing:
1. No `compute_morans_i.py` — have to write raw Python each time
2. No standardized Gi*/LISA script with FDR correction
3. No spatial regression script
4. No spatial weights wrapper
5. No kernel density estimation
6. No gating logic in code (Global Moran's I check is aspirational only)

### Top 3 scripts they want:
1. **`compute_spatial_autocorrelation.py`** — Global Moran's I with pass/fail gate
2. **`analyze_hotspots.py`** — Combined Gi* + LISA with FDR correction, refuses to run without global gate
3. **`analyze_spatial_regression.py`** — OLS → residual check → auto Spatial Lag/Error

### Guide feedback:
- Wants explicit effect size threshold (I < 0.15 = significant but weak)
- Wants island tract handling guidance
- Wants CRS projection warning (Kansas = EPSG:26914 or EPSG:3085)
- Wants space-time analysis guidance

### Kansas-specific needs:
- BRFSS data, Kansas Medicaid expansion context (didn't expand until 2022!)
- HPSA/MUA overlays for policy context
- CDC PLACES small-area estimates
- Fort Riley / university tract GEOID lookup table
- Historical redlining maps for Kansas cities
- Robert Wood Johnson Foundation county health rankings

---

## Cartography Agent — Self-Assessment

### What they CAN do well now:
- Single-variable choropleth (multiple classification schemes)
- Bivariate choropleth (Stevens' 3x3)
- Hotspot maps, LISA cluster maps
- Point overlay on choropleth (functional but mediocre)
- QGIS review packages (.qgs project files)

### Critical gaps:
1. **Point overlay is their biggest failure** — 12px markers (invisible), no basemap, no labels, no facility differentiation, no state outline on top
2. **No proportional symbol maps** — the style guide says "don't choropleth counts" but there's no script for the alternative
3. **No dot density maps** for raw count data
4. **No small multiples** for temporal comparison
5. **No diverging choropleth** for change maps
6. **QGIS Print Layout → PDF/PNG export** — project files exist but no headless render script
7. **analyze_choropleth.py has wrong defaults** — 10x8 figsize (should be 14x10), centered title (should be left-aligned), no state outline, `std_mean` scheme is silently broken

### Top asks:
1. Fix `analyze_choropleth.py`: figsize 14x10, state outline on top, left-aligned title, fix std_mean
2. Fix `overlay_points.py`: 60-80px markers, contextily basemap, adjustText labels, facility differentiation
3. **`render_print_layout.py`** — headless QGIS Print Layout → PDF/PNG (the "client-ready deliverable" gap)
4. **`palettes.json`** — firm-standard semantic palette aliases ("poverty" → YlOrRd, "hotspot" → RdBu diverging)
5. **Proportional symbol script** for count data
6. `.qpt` layout templates for standard map types

### Design reference asks:
- ColorBrewer as local JSON, Carto Colors, Crameri scientific colormaps (`cmcrameri`)
- Curated John Nelson / NYT / WaPo map screenshots for style matching
- Named palette registry file for consistency across all outputs

---

## Report Writer Agent — Self-Assessment

### What they CAN do well now:
- Structured markdown + HTML reports with consistent sections
- Executive summaries (3-4 bullets)
- Map captions that explain what to notice
- Honest methodology and limitations sections
- Traceable — every claim links to an upstream handoff

### Critical gaps (their own words):
> "My reports follow a pipeline logic — organized around what the *pipeline did*, not what the *client needs to decide*. McKinsey reports lead with the answer. Mine lead with the process. That's the wrong direction."

**Structure gap:** Bottom-up (data → conclusion) instead of top-down (conclusion → evidence)
**Narrative gap:** Sections, not a story with tension (SCQA arc missing)
**Audience gap:** Writes for "generic non-technical client" — that's not a person
**Format gap:** Only produces monolithic reports. Missing: 1-page executive brief, separate technical appendix, slide deck outline, data dictionary
**Visual gap:** HTML is functional, not compelling

### What they want from the lead analyst:
1. One-paragraph audience brief per engagement (who, what decision, what they already think)
2. The "hero question" — the single question this analysis answers
3. Politically sensitive findings to handle carefully
4. Internal vs external deliverable flag
5. Preferred technical detail level

### Frameworks they want to adopt:
- **Pyramid Principle** (Minto) — lead with the answer, group 3 arguments, evidence per argument
- **SCQA** (Situation-Complication-Question-Answer) — for exec summaries
- **Assertion-Evidence** — each section opens with a declarative finding, then evidence

### Output formats they want to add:
1. **1-page executive brief** (separate file, not a section)
2. **Technical appendix** (methodology + caveats split out)
3. **Slide deck outline** (title + assertion + data point per slide)
4. **Data dictionary** (column definitions, units, vintage, limitations)
5. **Map caption sheet** (standalone page listing all maps with captions + sources)

---

## Lead Analyst Agent — Self-Assessment

### Honest scope assessment:
> "We do tract-level Census thematic analysis well. That's maybe 10-15% of what a real geospatial consulting firm does."

### 5 biggest gaps vs a real firm (Esri PS / WSP / Deloitte):
1. **Census-only** — entire pipeline built around ACS + TIGER. No automated retrieval for CDC, HRSA, USDA, EPA, BLS, commercial data
2. **No network analysis** — can't answer "how far by road?" Can't do site selection, service areas, routing, isochrones
3. **No interactive/web deliverables** — static PNGs and HTML pages, no Leaflet/Mapbox/dashboards
4. **No raster/imagery** — 100% vector. No land cover, NDVI, flood modeling, terrain, satellite change detection
5. **Scripts are fragile and partially broken** — wrong defaults, silent bugs, no enforced quality gates in code

### Top 10 scripts they want (priority order):
1. `compute_service_areas.py` — OSMnx drive-time isochrones (biggest single capability gap)
2. `fetch_federal_data.py` — generic wrapper for CDC PLACES, HRSA, USDA, EPA, BLS, FEMA
3. `render_web_map.py` — Leaflet/Folium interactive HTML map from any GeoPackage
4. `analyze_spatial_regression.py` — OLS → spatial diagnostics → auto Lag/Error
5. `render_print_layout.py` — headless QGIS → PDF
6. `compute_change_detection.py` — compare two ACS vintages, diverging choropleth
7. Spatial data catalog/registry (machine-readable, not prose)
8. `geocode_addresses.py` — batch geocoding via Nominatim/Census Geocoder
9. Proportional symbol + dot density map scripts
10. `validate_analysis.py` — programmatic quality gates (Moran's I check, join rate, institution flags)

### Inter-agent communication issues:
- **Context loss on handoff** — agents don't share a "project brief"; each gets only the task description
- **No error recovery loop** — if processing fails due to bad retrieval output, no automatic retry
- **No parallel coordination** — sequential spawning even when steps could parallel
- **No shared memory between runs** — re-learns lessons (university tracts, etc.) every project
- **Docker cold starts** — 5-15s overhead per script execution, 5+ containers per pipeline
- **Analytical decisions not persisted** — "why natural_breaks over quantiles?" lives in context window, not on disk

### What it would take to support:
- **Any US state:** Mostly there. Need state CRS lookup, more data retrieval scripts. ~2-3 weeks.
- **Any country:** Major architecture change. Need configurable data registry, OSM as universal geometry, WorldPop/GADM, multi-language. ~3-6 months.
- **Any spatial question:** Network analysis, raster pipeline, geocoding, time-series, ML integration. ~6-12 months.

### Redesign ideas (if starting from scratch):
- Shared project brief document all agents reference
- Error recovery/retry loops in delegation
- Project-level persistent memory (lessons learned, data catalog)
- Parallel agent coordination
- Programmatic quality gates that block delivery

## Data Discovery Agent — Self-Assessment

### What they CAN do well now:
- ~20-25 US federal datasets: Census ACS/TIGER, HRSA, CDC PLACES, USDA, EPA, FEMA, HIFLD, BLS, HUD
- Census API with key configured
- retrieve_remote.py + inspect_dataset.py + fetch_acs_data.py

### Critical gaps (their own words):
> "My SOUL.md and TOOLS.md are almost entirely US-domestic and US-federal."

**Missing entire categories:**
- **Satellite/Remote Sensing:** Zero coverage. No NASA Earthdata, no Copernicus, no GEE, no Landsat/Sentinel workflows
- **International:** No World Bank, UN, Eurostat, FAO, WHO, OECD, country-specific NSOs
- **Climate:** No NOAA CDO, no ERA5, no CHIRPS, no WorldClim, no CMIP6
- **Land Cover:** Missing NLCD (basic US gap!), no ESA WorldCover, no Global Forest Watch
- **Elevation/Terrain:** No SRTM, ASTER, 3DEP, CoastalDEM — "fundamental to flood risk, routing, visibility"
- **Humanitarian:** No HDX, GDACS, ReliefWeb, EM-DAT
- **Real-time:** No USGS streamflow, no PurpleAir, no disaster feeds
- **Agriculture:** No USDA NASS CropScape, no FAO, no SPAM
- **Demographics (non-US):** No WorldPop, GHSL, GPW, LandScan

### Could they handle non-US questions?
- "Analyze deforestation in Amazon" → "I'd be reinventing the wheel every time. Not confident. Not fast."
- "Map transit access in London" → "I'd find it, but slowly, and I'd make rookie mistakes on UK geography."
- "Assess flood risk in Bangladesh" → "I'd need significant research before I could even recommend a stack."

### What would make them world-class:
1. Global-first mindset — know authoritative sources per country/region
2. Satellite data fluency — Sentinel, Landsat, MODIS, VIIRS as first-class
3. Real-time data layer — USGS, EPA AirNow, GDACS, weather APIs
4. Humanitarian data fluency — HDX is backbone of conflict/disaster work
5. Elevation as first-class data type — SRTM, 3DEP, CoastalDEM
6. A living bookmarks system — structured, versioned catalog with vintage/resolution/format
7. Knowing what costs money vs what's free

### Portal list they want bookmarked:
- Satellite: NASA Earthdata, Copernicus Hub, USGS Earth Explorer, Google Earth Engine, OpenTopography
- Global demos: WorldPop, GHSL, GPW, World Bank API, UN Data, Eurostat, FAO
- Disaster/humanitarian: GDACS, ReliefWeb, HDX, EM-DAT, Copernicus EMS
- Climate: NOAA CDO, CHIRPS, WorldClim, Copernicus CDS
- Transport: Transitland, Overpass API, OpenRailwayMap
- US gaps: NLCD (mrlc.gov), USGS StreamStats, EIA energy, USDA NASS CropScape

