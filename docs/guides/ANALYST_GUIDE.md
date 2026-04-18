# Analyst Guide

This guide is for analysts, researchers, and consultants who will use spatial-machines to run analyses. You don't need to read the source code — just ask your AI coding agent a spatial question.

## What this system does

spatial-machines is a multi-agent pipeline that:

1. **Scopes** your question into a project brief (lead analyst)
2. **Retrieves** data from 20+ built-in sources — Census, EPA, CDC, FEMA, NOAA, OSM, and more (data retrieval)
3. **Processes** and joins datasets into analysis-ready GeoPackages (data processing)
4. **Analyzes** the data — spatial statistics, hotspots, clustering, demographic patterns (spatial stats)
5. **Maps** the results with auto-styled choropleths, bivariate maps, and more (cartography)
6. **Validates** all outputs independently (validation QA)
7. **Reports** findings in markdown and HTML with the Pyramid Principle (report writer)
8. **Packages** everything — styled QGIS project, ArcGIS Pro package (`.gdb` + `.lyrx`), and optionally publishes to ArcGIS Online as a hosted Feature Service + Web Map (site publisher)
9. **Reviews** the outputs independently for quality and honesty (peer reviewer)

Each stage produces a JSON handoff artifact that creates a full audit trail from raw data to final deliverables.

## How to request an analysis

Open your AI coding agent (Claude Code, Codex, etc.) in the spatial-machines directory and ask a question in natural language:

> "What does poverty look like across census tracts in Douglas County, Nebraska?"

> "Are there statistically significant hotspots of diabetes in Kansas counties?"

> "How does food access correlate with poverty in Atlanta?"

The agent will scope the question, plan the pipeline, delegate to specialists, and deliver results.

## What you'll get back

After an analysis completes, look in `analyses/<project-id>/`:

| Directory | Contents |
|---|---|
| `outputs/maps/` | Styled PNG maps (200 DPI) with `.style.json` sidecars |
| `outputs/charts/` | Statistical charts (distribution, comparison, relationship, timeseries) — PNG + SVG + `.style.json` |
| `outputs/web/` | Self-contained interactive Folium maps (open HTML in browser) |
| `outputs/reports/` | Markdown and HTML reports |
| `outputs/qa/` | Validation results and QA scorecards |
| `outputs/qgis/` | Styled QGIS project with basemap, graduated renderers, and print layout template |
| `outputs/arcgis/` | ArcGIS Pro package (`.gdb` + `.lyrx`) + optional AGOL publish-status if opted in |
| `data/raw/` | Source data (immutable) |
| `data/processed/` | Analysis-ready GeoPackages |
| `runs/` | Pipeline handoff artifacts (JSON audit trail) + activity.log |

## Opening the QGIS package

1. Navigate to `analyses/<project-id>/outputs/qgis/`
2. Open the `.qgs` file in QGIS Desktop (>= 3.22)
3. Layers load styled with graduated colors matching the static maps
4. A CartoDB basemap provides geographic context
5. The map auto-zooms to the data extent
6. For print export: import `templates/qgis/print_layout.qpt` via Layout Manager

## Understanding the maps

Maps follow the firm's cartography standard:
- **Warm colors** (yellow → red) indicate risk, disadvantage, intensity
- **Cool colors** (light → dark blue) indicate positive metrics, access, coverage
- **Gray** means "no data" — never white (white reads as zero)
- **Diverging colors** (red ↔ blue) show change above/below a baseline
- Legends use en-dash separators and rounded break values

See `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` for the full visual language.

## Understanding the reports

Reports follow the Pyramid Principle:
1. **Answer first** — the key finding is in the first paragraph
2. **Supporting evidence** — maps, statistics, and tables that back the finding
3. **Methodology** — how the analysis was done (for reproducibility)
4. **Caveats** — limitations, data gaps, and uncertainty

## Available data sources

The system ships with 20+ data source fetch scripts. See `config/data_sources.json` for the full registry, or ask the agent what data is available for your topic.

## What the system can and can't do

**Strong at:**
- Demographic and socioeconomic analysis (Census ACS/TIGER)
- Health outcome mapping (CDC PLACES)
- Environmental justice screening (EPA EJScreen)
- Hotspot analysis (Gi* with FDR correction)
- Spatial autocorrelation (Moran's I, LISA)
- Multi-variable analysis (bivariate choropleth)
- Food access, housing, employment, crime analysis

**Experimental:**
- Service area / isochrone analysis
- Raster terrain analysis
- Spatial regression

**Not yet available:**
- Real-time data streams
- 3D visualization
- Full raster pipelines at scale
