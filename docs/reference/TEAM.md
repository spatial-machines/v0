# Team

## Team Concept

This project treats the GIS system as a small analyst team rather than a single generalist agent. Each agent is a specialist with a defined role, bounded scope, and specific toolset. The Lead Analyst orchestrates — all others execute.

**Active specialists: 9** (plus main assistant)  
**Agent list:** lead-analyst, data-retrieval, data-processing, cartography, spatial-stats, validation-qa, report-writer, site-publisher, peer-reviewer

---

## Specialist Agents

### 🧠 Lead Analyst
**Mission:** Orchestrate the full pipeline, manage scope, integrate outputs, and communicate with the human.

**Key responsibilities:**
- Interpret requests and decide delegation level
- Write the project brief and run plan
- Assign work to specialist agents in the right sequence
- Review handoff JSON chain for completeness
- Integrate outputs into a final synthesis
- Resolve conflicts between agents
- Deliver the final human-facing summary

---

### 📦🔍 Data Retrieval & Discovery
**Mission:** Acquire the right data from authoritative sources and know what datasets exist for any geospatial question.

**Key responsibilities:**
- Identify candidate data sources (Census, HRSA, CDC, EPA, USDA, FEMA, etc.)
- Use the wiki first for reusable source guidance and workflow method. Fall back to the firm's source handbooks only when the relevant wiki source or workflow page is incomplete.
- Fetch local/remote/API data and document provenance
- Know the global data portal catalog (40+ portals across satellite, demographics, environment, infrastructure)
- Report source limitations, vintage, and resolution constraints

*(Merged from former data-discovery agent — 2026-04-04)*

---

### ⚙️ Data Processing
**Mission:** Convert raw data into analysis-ready, standardized GeoPackages.

**Key responsibilities:**
- Inspect schema and geometry validity
- Normalize field names, types, and keys
- Manage CRS and reprojection (target: EPSG:4269)
- Clip, filter, and spatially join datasets
- Create derived fields and join tabular data to spatial layers
- Write transformation logs and `.processing.json` sidecars
- Prefer wiki standards and workflows for reusable processing method. Keep role docs and handoff contracts as the authority for scope boundaries and stage responsibilities.

---

### 🗺️📊 Cartography (Visualization)
**Mission:** Produce gallery-quality, accessible maps **and statistical charts** using open-source tools only.

**Key responsibilities:**
- Generate choropleth, bivariate, proportional symbol, and hotspot maps
- Generate statistical charts: distribution (histogram/KDE/box/violin), comparison (bar/lollipop/dot), relationship (scatter/scatter+OLS/hexbin/correlation heatmap), time series (line/area/small_multiples)
- Apply the pairing rule: every choropleth ships with a paired distribution + top-N chart; every bivariate map with a scatter_ols; every change-over-time with a line chart
- Enforce firm cartographic standards per map family (see `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` Map Family Taxonomy)
- Enforce chart design rules (see `docs/wiki/standards/CHART_DESIGN_STANDARD.md`)
- DPI: 200 preferred for client-grade output; 150 minimum. Figure size: 14×10 for state-level, 12×10 for local-area
- Use the semantic palette registry (`config/palettes.json` and `config/chart_styles.json`) for variable-to-color consistency
- Produce interactive web maps (Folium) and static exports
- Check colorblind accessibility before any deliverable
- Write `.style.json` sidecars for every map and every chart — inherited by QGIS, ArcGIS Pro, and ArcGIS Online packagers
- Validate all maps and charts with `scripts/core/validate_cartography.py` before delivery

---

### 📈📊 Spatial Statistics & Demographics
**Mission:** Bring statistical rigor and Census expertise to geospatial analysis.

**Key responsibilities:**
- Compute hotspots (Gi*, FDR-corrected), LISA clusters, spatial autocorrelation
- Always run Global Moran's I before any local spatial analysis
- Know the Census product catalog deeply (Decennial, ACS 1-year/5-year, PL 94-171)
- Select correct ACS table and denominator for rate calculations
- Propagate margins of error; flag high-CV (unreliable) tracts
- Report uncertainty alongside every finding
- Flag institutional tracts (military, prisons, universities)
- Prefer wiki standards, workflows, and QA pages for reusable analytic method. Use handbook material only when a relevant wiki page does not yet cover the needed method.

*(Merged with former demographics agent — 2026-04-04)*

---

### ✅ Validation QA
**Mission:** Independently verify that outputs are correct, complete, and honest before reporting.

**Key responsibilities:**
- Verify geometry validity, CRS consistency, and feature counts
- Check join rates (flag if < 95%)
- Run programmatic QA gates (Moran's I gate, institution flags, null rates)
- Produce per-check validation JSONs and aggregated handoff
- Issue PASS / PASS WITH WARNINGS / REWORK NEEDED determination
- Never share the pipeline context — review outputs only
- Use wiki QA pages and standards as the primary reusable review layer. Keep the role boundary here, but do not let handbook QA prose compete with the canonical wiki QA layer.

---

### 📝 Report Writer
**Mission:** Package analysis outputs into clear, client-quality deliverables using the Pyramid Principle.

**Key responsibilities:**
- Write executive briefs (1-page, lead with the answer)
- Write technical reports (full methodology, findings, caveats, sources)
- Generate self-contained HTML reports (no external dependencies)
- Write data dictionaries for every GeoPackage
- Run sensitivity checks before publishing
- Reference all upstream handoffs and QA results
- Prefer the wiki for reusable reporting and delivery method once a relevant workflow exists. Keep client-specific packaging decisions in project docs.

---

### 🌐 Site Publisher (Delivery Packaging)
**Mission:** Organize and package analysis outputs into portable, styled deliverables across every supported output channel.

**Key responsibilities:**
- Organize outputs into standard directory structure (`maps/`, `web/`, `reports/`, `qa/`, `qgis/`, `arcgis/`)
- Generate data catalogs using `generate_all_catalogs.py`
- Package a styled QGIS project using `package_qgis_review.py` — `.qgs` file + graduated/categorized renderers + basemap + print-layout template
- Package a styled ArcGIS Pro deliverable using `package_arcgis_pro.py` — file geodatabase + `.lyrx` layer files + `make_aprx.py` helper (and a pre-built `.aprx` when `arcpy` is available)
- Publish to ArcGIS Online via `publish_arcgis_online.py` when `outputs.publish_targets` in the project brief opts in — uploads the GDB, publishes a hosted Feature Service + Web Map, applies sidecar-driven renderers
- All three packagers inherit styling from the same `.style.json` sidecars — one source of truth for QGIS, ArcGIS Pro, and AGOL
- Verify that all expected output artifacts exist before handoff
- Assemble delivery summary pointing the user to key outputs
- Report missing assets or packaging inconsistencies

---

### 🔍 Peer Reviewer
**Mission:** Provide independent QC by critiquing completed analysis outputs without seeing the pipeline.

**Key responsibilities:**
- Read only from `outputs/` — never from scripts, data, or handoffs
- Evaluate maps, reports, and QA results independently
- Issue PASS / REVISE / REJECT with 3-5 specific findings
- Flag unsupported conclusions, misleading maps, or missing caveats
- Provide specific, actionable critique (not vague "improve the map")

---

## Operating Modes

### Direct Mode
The Lead Analyst handles a small task directly without spawning specialists. Best for:
- Simple data lookups
- Quick map regeneration with existing data
- Status checks and project summaries

### Partial Pipeline
Lead Analyst activates only the necessary specialists. Best for:
- Incremental updates to a completed analysis
- Re-running a single stage (e.g., map style change only)
- Quick choropleth + report (no hotspot analysis needed)

### Full Pipeline
The standard mode for new analyses. Sequence:
1. **Lead Analyst** — writes project brief and run plan
2. **Data Retrieval** — fetches boundaries and tabular data
3. **Data Processing** — cleans, joins, and standardizes
4. **Spatial Stats** — computes analysis, generates maps
5. **Cartography** — refines maps to firm standards (optional stage for complex cartography)
6. **Validation QA** — QA gates before reporting
7. **Report Writer** — produces markdown + HTML reports
8. **Site Publisher** — QGIS package + ArcGIS Pro package + optional ArcGIS Online publishing
9. **Peer Reviewer** — independent QC at end (Gate 2)
10. **Lead Analyst** — final synthesis and human delivery
