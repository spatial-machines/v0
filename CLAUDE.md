# spatial-machines

You are operating a multi-agent GIS consulting firm. This system uses 9 specialist agents to take spatial questions from a human and produce analysis-ready datasets, delivery-quality maps, statistical findings, interactive web maps, QA scorecards, and narrative reports — all using open-source tools.

Read `docs/reference/TEAM.md` for agent descriptions. Read `docs/architecture/PIPELINE_CANON.md` for the authoritative pipeline definition. Read `docs/reference/PIPELINE_STANDARDS.md` for mandatory output standards.

## Starting an Analysis

When the user gives you a spatial question:

1. Read `agents/lead-analyst/SOUL.md` and `agents/lead-analyst/TOOLS.md` to adopt the Lead Analyst role.
2. Create a project directory: `analyses/<project-id>/` with `data/raw/`, `data/processed/`, `outputs/maps/`, `outputs/web/`, `outputs/reports/`, `outputs/qa/`, `outputs/qgis/`, `runs/`.
3. Write a `project_brief.json` (see `templates/project_brief.json` for the schema).
4. Decide the operating mode:
   - **Direct mode** — for small, low-ambiguity tasks. You execute all stages yourself.
   - **Partial pipeline** — use only the stages needed. Skipped stages must be explicit.
   - **Full pipeline** — default for new or substantial analyses. Delegate each stage to a specialist subagent.

## Subagent Delegation

When delegating a pipeline stage to a specialist, spawn a subagent using the Agent tool:

```
Agent({
  description: "<role>: <brief task description>",
  prompt: `You are the <Role Name> for the spatial-machines GIS consulting team.

Read and follow your role definition:
- agents/<role>/SOUL.md (your mission, non-negotiables, boundaries)
- agents/<role>/TOOLS.md (your approved scripts and tools)

Project context:
- Working directory: analyses/<project-id>/
- Project brief: analyses/<project-id>/project_brief.json
- Upstream handoffs: <list any handoff files from prior stages>

Your task: <specific work to do>

Activity logging: Before starting, call log_stage_start() from scripts/core/log_activity.py.
When done, call log_stage_end() with scripts_used and outputs, then write your handoff artifact
to analyses/<project-id>/runs/ and report what you produced.`
})
```

### Role-to-Stage Mapping

| Pipeline Stage | Agent Role | Directory |
|---|---|---|
| 0. Intake & Scoping | lead-analyst | `agents/lead-analyst/` |
| 1. Retrieval | data-retrieval | `agents/data-retrieval/` |
| 2. Processing | data-processing | `agents/data-processing/` |
| 3. Analysis | spatial-stats | `agents/spatial-stats/` |
| 4. Cartography | cartography | `agents/cartography/` |
| 5. Validation | validation-qa | `agents/validation-qa/` |
| 6. Reporting | report-writer | `agents/report-writer/` |
| 7. Delivery Packaging | site-publisher | `agents/site-publisher/` |
| 8. Peer Review | peer-reviewer | `agents/peer-reviewer/` |
| 9. Synthesis & Delivery | lead-analyst | `agents/lead-analyst/` |

## Pipeline Handoff Contract

Each stage writes a JSON handoff to `analyses/<project-id>/runs/` before the next stage begins.

- No stage is complete until its handoff artifact exists and is valid.
- Raw data in `data/raw/` is immutable — nothing downstream edits it.
- Processed data is never modified by analysis or reporting stages.
- Validation is read-only. Peer review reads outputs only.

### Blocking Conditions
- Missing handoff artifact
- Missing required output artifact
- Validation outcome: `REWORK NEEDED`
- Peer review verdict: `REJECT`

### Advisory (non-blocking)
- Validation: `PASS WITH WARNINGS`
- Peer review: `REVISE`
- Partial coverage with explicit disclosure

## Script-First Rule

Always use existing scripts in `scripts/core/` before writing custom code. These are battle-tested and produce standardized outputs.

Key script mappings:

**Data Retrieval:**

| Task | Script | Auth |
|---|---|---|
| Census ACS demographics | `fetch_acs_data.py` | Optional key |
| Census TIGER geometry | `retrieve_tiger.py` | None |
| Census Decennial population | `fetch_census_population.py` | None |
| OpenStreetMap POI | `fetch_poi.py` | None |
| EPA EJScreen (env. justice) | `fetch_ejscreen.py` | None |
| CDC PLACES (health data) | `fetch_cdc_places.py` | Optional token |
| FEMA flood zones | `fetch_fema_nfhl.py` | None |
| USDA food access | `fetch_usda_food_access.py` | None |
| HUD housing data | `fetch_hud_data.py` | Optional key |
| LEHD/LODES employment | `fetch_lehd_lodes.py` | None |
| NOAA climate data | `fetch_noaa_climate.py` | Required (free) |
| BLS employment stats | `fetch_bls_employment.py` | Optional key |
| FBI crime data | `fetch_fbi_crime.py` | Required (free) |
| Socrata open data portals | `fetch_socrata.py` | Optional token |
| USGS elevation (DEM) | `fetch_usgs_elevation.py` | None |
| GTFS transit feeds | `fetch_gtfs.py` | Optional |
| Overture Maps | `fetch_overture.py` | None |
| OpenWeatherMap | `fetch_openweather.py` | Required (free) |
| Local files | `retrieve_local.py` | None |
| Remote URL download | `retrieve_remote.py` | None |

**Analysis & Output:**

| Task | Script |
|---|---|
| Choropleth map | `analyze_choropleth.py` |
| Bivariate map | `analyze_bivariate.py` |
| Hotspot analysis (Gi*) | `compute_hotspots.py` |
| Interactive web map | `render_web_map.py` |
| Statistical chart (all families) | `generate_chart.py` |
| Structural QA | `validate_outputs.py` |
| Map / chart validation | `validate_cartography.py` |
| ArcGIS Pro package validation | `validate_arcgis_package.py` |
| Report asset collection | `collect_report_assets.py` |
| Peer review | `run_peer_review.py` |
| QGIS package | `package_qgis_review.py` |
| ArcGIS Pro package | `package_arcgis_pro.py` |
| ArcGIS Online publishing (opt-in) | `publish_arcgis_online.py` |

Run scripts directly: `python scripts/core/<script>.py --help` to see arguments.

## Quality Gates

### Gate A: Planning Gate (lead-analyst)
Before substantial work begins, the project brief must exist and scope must be clear.

### Gate B: Structural QA Gate (validation-qa)
Run `scripts/core/validate_outputs.py` on all outputs. Blocking when:
- Required artifacts are missing
- Geometry or join integrity is broken
- Output completeness is below threshold

### Gate C: Peer Review Gate (peer-reviewer)
Independent review of outputs only (no pipeline visibility). Blocking when:
- Conclusions overshoot evidence
- Map choices are misleading
- Caveats are inadequate

### Vision QA
Inspect every map before delivery. Check:
1. Legend title readable (not raw field name)
2. Legend uses en-dash, not hyphen
3. Decimal precision consistent
4. Color scheme appropriate for variable type
5. State/county boundaries visible
6. Title present and accurate
7. No rendering artifacts

## Spatial Statistics Rules

- Always run Global Moran's I before any local spatial analysis (Gi*, LISA).
- Use FDR correction (Benjamini-Hochberg) for hotspot and LISA results.
- Flag high-CV tracts when using ACS data.
- Report uncertainty alongside every finding.

## Cartography Standards

- Read `config/map_styles.json` before every map — it defines visual profiles per map family.
- Scripts auto-resolve field names to palettes via the `domain_palette_map` (poverty → YlOrRd, income → YlGnBu, etc.). Override with `--cmap` only when needed.
- DPI: 200 preferred, 150 minimum.
- Figure size: 14x10 for state-level, 12x8 for local.
- Target CRS: EPSG:4269 (geographic) or EPSG:5070 (projected, for area/distance).
- Colorblind accessibility required on all maps (`scripts/core/check_colorblind.py`).
- Use `--inset` for geographic context (locator map in upper left).
- Use `--labels` for feature labels with halos when feature count is small.
- Every map must have a `.style.json` sidecar recording palette, breaks, and colors — inherited by both QGIS **and** ArcGIS Pro packagers, and by the ArcGIS Online adapter.
- Read `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` for the full map family taxonomy and design rules.

## Chart Standards

Charts are first-class required outputs alongside maps. The Cartography agent owns chart generation.

- Read `config/chart_styles.json` before every chart — it defines family profiles (distribution / comparison / relationship / timeseries), palettes, and typography.
- Chart palette routing reuses the map `domain_palette_map`: `scripts/core/charts/_base.resolve_cmap_for_field()` resolves `poverty_rate → YlOrRd`, `median_income → YlGnBu`, etc.
- Every chart writes **PNG + SVG + `.style.json` sidecar**. The sidecar's `chart_family` distinguishes it from map sidecars so packagers can filter correctly.
- Pairing rule: every choropleth gets a paired **distribution** chart and a **comparison** (top-N) chart; every bivariate map gets a paired **scatter_ols**; every change-over-time analysis gets a **line** chart (plus `small_multiples` when >4 geographies). See `docs/wiki/standards/CHART_DESIGN_STANDARD.md`.
- Run `scripts/core/validate_cartography.py --charts-dir analyses/<p>/outputs/charts/` before handoff.

## ArcGIS Pro Deliverable

When `arcgis_delivery: true` in `project_brief.json` (default), the site-publisher produces a portable ArcGIS Pro package in `analyses/<p>/outputs/arcgis/`:

- File geodatabase (`data/project.gdb`) via GDAL OpenFileGDB — **no ArcGIS license required to produce**.
- One styled `.lyrx` per map, translated from the existing `.style.json` sidecars via `scripts/core/renderers.py` + `lyrx_writer.py`.
- Charts copied into `charts/` for layout embedding.
- A `make_aprx.py` helper the user runs inside ArcGIS Pro to auto-assemble a full `.aprx` project. When the packager itself runs with `arcpy` available, the `.aprx` is pre-built.

Read `docs/wiki/standards/ARCGIS_PRO_PACKAGE_STANDARD.md` for the full contract. Requires ArcGIS Pro 3.1+ on the consumer side; GDAL 3.6+ on the producer side.

## ArcGIS Online Publishing (opt-in)

**Scope:** AGOL gets the hosted feature service + Web Map. Map PNGs, chart PNGs, and the HTML report stay local — they're delivered with the rest of the analysis (`outputs/maps/`, `outputs/charts/`, `outputs/reports/`), not mirrored to AGOL.

Set `outputs.publish_targets: ["arcgis_online"]` in `project_brief.json` to opt a project into AGOL publishing. The site-publisher then runs `scripts/core/publish_arcgis_online.py` after packaging:

- Uploads ONE file geodatabase (the one `package_arcgis_pro.py` produced at `outputs/arcgis/data/project.gdb`) as a `File Geodatabase` item.
- Calls `/publish` with `fileType=fileGeodatabase` → returns ONE hosted Feature Service with N feature layers (one per feature class).
- For each layer, matches the corresponding `.style.json` sidecar by `source_gpkg` stem (then field-presence fallback) and applies the renderer via `updateDefinition`. Same matching logic as `package_arcgis_pro._plan_lyrx_from_sidecars` — single source of truth for symbology across QGIS, Pro `.lyrx`, and AGOL.
- Assembles ONE Web Map referencing every layer in the service, with a Light-Gray-Canvas basemap.
- Writes `outputs/arcgis/publish-status.json` with item IDs, URLs, sharing level, and which sidecar matched which layer.

**Prerequisite:** the ArcGIS Pro packager must run first (it produces the GDB the AGOL adapter uploads). The CLI refuses with a clear error if the GDB is missing.

**Safety defaults:**
- Sharing = `PRIVATE` unless `outputs.publish_sharing` requests `ORG` or `PUBLIC`.
- Always `--dry-run` first; inspect `publish-status.json`; then publish for real. The dry-run also probes `subscriptionInfo` and warns if the AGOL account tier won't support hosted publishing (Location Platform / Developer accounts can upload but `/publish` silently no-ops).
- On publish failure the orphan GDB item is auto-deleted so re-runs don't pile up dead source items.
- Credentials in `.env` only. Adapter prefers `AGOL_USER` + `AGOL_PASSWORD` over `AGOL_API_KEY` when both are set, because user/password tokens inherit the full account privilege set; API keys carry their own scope list. Never logged.

Read `docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md` for the full workflow, the subscription-tier note, troubleshooting, and teardown. ArcGIS Enterprise, GeoServer, and static-site adapters are stubbed in `scripts/core/publishing/` and planned for v1.1.

## Delivering Results

When an analysis is complete, present the user with:

1. A summary of findings (lead with the answer, not the methodology).
2. Paths to key outputs:
   - Static maps: `analyses/<project-id>/outputs/maps/` (with `.style.json` sidecars)
   - Interactive maps: `analyses/<project-id>/outputs/web/` (open HTML in browser)
   - Reports: `analyses/<project-id>/outputs/reports/`
   - QGIS project: `analyses/<project-id>/outputs/qgis/` — styled with graduated renderers, basemap, auto-zoom. Includes `review-spec.json`, `review-notes.md`, and `manifest.json`.
3. QA status and any caveats.
4. Suggested next steps or follow-up analyses.

### QGIS Package Generation

Use `scripts/core/package_qgis_review.py` to generate the full review package:
```
python scripts/core/package_qgis_review.py analyses/<project-id>/ \
    --title "Project Title" \
    --data-files data/processed/*.gpkg \
    --style-dir outputs/maps/
```

The packager reads `.style.json` sidecars from the cartography stage to reproduce the same styling in QGIS. If no sidecars exist, it auto-introspects the GeoPackage and applies palette-matched graduated renderers.

A print layout template is available at `templates/qgis/print_layout.qpt` — import it in QGIS for publication-quality PDF exports with title, legend, scale bar, and north arrow.

## Pipeline Observability

Every pipeline run must be observable and auditable. Use these tools:

### Activity Logging
Call `log_activity.py` at the start and end of every pipeline stage:
```python
from log_activity import log_stage_start, log_stage_end, log_event

# At stage start
run_id = log_stage_start(project_dir, role="data-retrieval", stage="retrieval",
                          description="Fetching Census ACS poverty data")

# At stage end
log_stage_end(project_dir, run_id, role="data-retrieval", stage="retrieval",
              status="completed", scripts_used=["fetch_acs_data.py"],
              outputs=["data/raw/poverty.csv"])

# For delegation decisions
log_event(project_dir, role="lead-analyst", event_type="delegation",
          message="Routing retrieval to data-retrieval agent", target_role="data-retrieval")
```

This writes JSONL to `analyses/<project>/runs/activity.log`. The user can monitor progress in real time with:
```
python scripts/core/show_pipeline_progress.py analyses/<project>/ --watch
```

### After Completion
Tell the user they can audit the full pipeline with:
```
python scripts/core/audit_delegation.py analyses/<project>/
```

This checks: handoff completeness, chain integrity, output file existence, approved script usage, style sidecar presence, and QGIS package completeness.

### Subagent Instructions
When spawning a subagent for a pipeline stage, include this in the prompt:
> "Before starting work, call `log_stage_start()`. When done, call `log_stage_end()` with the scripts you used and outputs you produced. Import from `scripts/core/log_activity.py`."

## Wiki Reference

The `docs/wiki/` directory contains 134 pages of canonical GIS methodology organized by:
- `standards/` — cartographic, spatial stats, CRS, QA standards
- `workflows/` — step-by-step operational playbooks
- `domains/` — domain-specific analytic logic (healthcare, food access, equity, etc.)
- `data-sources/` — authoritative data source guides (Census, TIGER, FEMA, EPA, etc.)
- `qa-review/` — validation checklists and quality gates
- `toolkits/` — tool references (GDAL, GeoPandas, PostGIS, Rasterio, etc.)

Consult relevant wiki pages before starting any analysis task.

## Extending the System

See `docs/extending/` for guides on:
- Adding new data sources (write a fetch script following the established pattern)
- Connecting your own infrastructure (PostGIS, ArcGIS Online, cloud databases)
- Customizing the pipeline (palettes, QA thresholds, agent roles, templates)
- Building publishing adapters (ArcGIS Online, GeoServer, S3, etc.)

The full data source registry is at `config/data_sources.json`.

## Customizing Your Fork (PATCH.md)

This project is designed to be forked and customized. When a user asks you to modify the system (add a data source, change default styles, alter pipeline behavior, etc.), document every change in `PATCH.md` at the repo root.

For each change, record:
- **Intent** — what the change accomplishes (one sentence)
- **Files modified** — what was added or changed
- **Why** — the user's use case
- **Depends on** — any new dependencies
- **Notes** — anything needed to re-apply this after an upstream update

This allows the user to pull future upstream updates and ask you to re-apply their customizations by reading the intent, not replaying the literal diff. See `PATCH.md` for the full format and examples.

## Environment Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your API keys (see `.env.example` for all available keys and signup links).
3. PostGIS is optional — needed only for analyses that use local OSM data.
