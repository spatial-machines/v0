# Architecture

## Overview

The GIS Analyst Agent Team is a role-based multi-agent system operating in a reproducible GIS workspace. The architecture separates concerns across specialist agents while keeping user communication and final synthesis in the hands of the Lead Analyst Agent.

**Current team size:** 9 active specialist agents (consolidated from 12 on 2026-04-04)

---

## Core Layers

### 1. Environment Layer
A reproducible runtime for GIS work. Everything runs in a local Python venv — no Docker, no cloud requirement.

**Active stack:**
- Python 3.11+
- geopandas, pandas, numpy, shapely, pyproj, pyogrio / fiona
- rasterio, rasterstats, richdem
- matplotlib, seaborn
- folium (interactive web maps)
- libpysal, esda (spatial statistics)
- mapclassify, contextily
- scikit-learn, pykrige (optional)
- jinja2, pydantic, requests

**Optional (unlocks additional capability):**
- QGIS 3.28+ LTR — enables in-process `.qgs` generation via PyQGIS
- ArcGIS Pro 3.1+ — enables auto-building `.aprx` projects via arcpy
- PostGIS — only needed for local OpenStreetMap mirror workflows
- osmnx — service-area analysis

---

### 2. Memory Layer
Structured knowledge artifacts that let the team improve over time.

| Type | Location | Purpose |
|---|---|---|
| Project memory | `docs/memory/PROJECT_MEMORY.md` | Institutional memory — read first on every engagement |
| Lessons log | `docs/memory/lessons-learned.jsonl` | Append-only JSONL with category, tags, timestamps |
| Run retrospectives | `docs/memory/retrospectives/` | Per-run markdown retrospectives |
| Role handbooks | `docs/handbooks/roles/` | Agent-specific role-boundary guidance |
| Wiki canon | `docs/wiki/` | Reusable methods — standards, workflows, QA, sources, toolkits, domains |

Memory conventions:
- `PROJECT_MEMORY.md` is human-maintained — update it after significant changes
- Lessons log is append-only — run `log_lesson.py` (core/) to add entries
- Retrospectives are per-run — not yet automated

---

### 3. Knowledge Layer
All documentation lives under `docs/`:

**Wiki (canonical methods)** — `docs/wiki/` (136 pages)
- `standards/` — firm-wide methodological rules
- `workflows/` — step-by-step operational playbooks
- `qa-review/` — validation checklists and review gates
- `data-sources/` — source family documentation
- `toolkits/` — tool references grouped by workflow use
- `domains/` — domain-specific analytic logic (40 domains)

**Must-read before work:**
- `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` — **read before any map** (Map Family Taxonomy)
- `docs/wiki/standards/SPATIAL_STATS_STANDARD.md` — **read before any clustering/autocorrelation**

**Handbooks** — `docs/handbooks/`
- `roles/` — per-agent role-boundary guidance (6 active role docs)
- `archive/` — migrated method handbooks (retained for traceability)
- `STATUS_LEDGER.md` — migration tracking

**Memory** — `docs/memory/`
- `PROJECT_MEMORY.md` — institutional memory, read first on every engagement
- `lessons-learned.jsonl` — append-only structured lessons
- `retrospectives/` — per-run markdown retrospectives

> **Canon rule (active as of 2026-04-09):** The wiki is the primary authority for reusable methods. Handbooks remain authoritative only for role-boundary content (agent responsibilities, scope). See `docs/handbooks/STATUS_LEDGER.md` for migration status.

---

### 4. Agent Layer

**9 active specialists:**

| Agent | Emoji | Primary Role |
|---|---|---|
| lead-analyst | 🧠 | Orchestrate, plan, synthesize, visual QA |
| data-retrieval | 📦🔍 | Data acquisition and source discovery |
| data-processing | ⚙️ | Clean, join, standardize |
| cartography | 🗺️ | Map production and design |
| spatial-stats | 📈📊 | Statistical analysis and Census expertise |
| validation-qa | ✅ | QA gates and verification |
| report-writer | 📝 | Reports, briefs, data dictionaries |
| site-publisher | 🌐 | Review site build and publishing |
| peer-reviewer | 🔍 | Independent output QC |

See [TEAM.md](../reference/TEAM.md) for full agent descriptions.

**Retired agents (consolidated 2026-04-04):**
- `db-manager` — PostGIS backend manager, dormant until PostGIS is an active production role
- `data-discovery` — merged into `data-retrieval`
- `demographics` — merged into `spatial-stats`

See [ACTIVE_TEAM.md](ACTIVE_TEAM.md) for the canonical active/archived roster.

---

### 5. Script Layer
All analysis scripts are organized under `scripts/`:

| Folder | Contents |
|---|---|
| `scripts/core/` | Battle-tested scripts used in real analyses |
| `scripts/future/` | Aspirational scripts — written but not yet battle-tested |
| `scripts/demos/` | Shell scripts for pipeline demonstrations |
| `scripts/deprecated/` | Old scripts kept for reference (do not use) |

**Script Enforcement Rules:**  
Agents are required to use canonical core scripts for standard analysis types. The Lead Analyst, Cartography, and Spatial Stats agents each have an explicit `⛔ Script-First Rule` in their SOUL.md files mapping analysis types to specific scripts. Custom code is a last resort, not a first instinct.

Key core scripts:
- `scripts/core/fetch_acs_data.py` — Census ACS retrieval
- `scripts/core/analyze_choropleth.py` — Choropleth maps
- `scripts/core/compute_hotspots.py` — Gi* hotspot analysis
- `scripts/core/analyze_bivariate.py` — Bivariate choropleth
- `scripts/core/render_web_map.py` — Folium interactive maps
- `scripts/core/validate_outputs.py` — QA gate
- `scripts/core/collect_report_assets.py` — Asset collection (supports `--scan-outputs`)

See `scripts/README.md` for a full listing.

---

### 6. Deliverables Layer
Each analysis lives entirely under `analyses/<project-id>/` — full isolation, no shared data or output directories.

```
analyses/<project-id>/
├── project_brief.json     # Scope, audience, QA thresholds (read before every stage)
├── data/raw/              # Immutable source data with manifest JSON sidecars
├── data/processed/        # Analysis-ready GeoPackages
├── outputs/maps/          # Static PNGs (200dpi) + .style.json sidecars
├── outputs/charts/        # Statistical charts + .style.json sidecars
├── outputs/web/           # Folium interactive HTML maps (self-contained)
├── outputs/reports/       # Markdown + HTML reports
├── outputs/qa/            # Validation and peer review JSON
├── outputs/qgis/          # QGIS project package (styled .qgs + data)
├── outputs/arcgis/        # ArcGIS Pro package (.gdb + .lyrx) + AGOL publish-status if opted in
├── runs/                  # Handoff JSON chain + activity.log
└── data_catalog.json      # Machine-readable data dictionary
```

See [WORKSPACE_MODEL.md](../reference/WORKSPACE_MODEL.md) for the full on-disk convention and immutability rules.

---

### 7. Vision QA Layer
The Lead Analyst is required to inspect every map using the `image()` tool before delivering to the human. The checklist covers:

1. Legend title uses readable label (not raw field name)
2. Legend ranges use en-dash (–), not hyphen
3. Decimal precision is consistent and appropriate
4. Color scheme is appropriate for variable type
5. State/county boundaries are visible
6. Title is present and accurate
7. No rendering artifacts or blank tiles

**Hard rule:** No map ships without visual inspection.

---

### 8. Delivery Packaging Layer
The site-publisher agent packages analysis outputs into portable, styled deliverables across every supported channel.

- Each analysis directory contains organized outputs in `outputs/maps/`, `outputs/charts/`, `outputs/web/`, `outputs/reports/`, `outputs/qa/`, `outputs/qgis/`, `outputs/arcgis/`
- Data catalogs generated by `scripts/core/generate_all_catalogs.py`
- **QGIS package** (`outputs/qgis/`) — styled `.qgs` + graduated/categorized renderers + basemap + print layout template. Built by `scripts/core/package_qgis_review.py`.
- **ArcGIS Pro package** (`outputs/arcgis/`) — file geodatabase + styled `.lyrx` per map + `make_aprx.py` helper (and a pre-built `.aprx` when `arcpy` is available). Built by `scripts/core/package_arcgis_pro.py`. No Esri license required to produce.
- **ArcGIS Online publishing** (opt-in, via `outputs.publish_targets: ["arcgis_online"]` in the project brief) — uploads the GDB, publishes a hosted Feature Service + Web Map, applies sidecar-driven renderers. Dry-run first; PRIVATE by default. Built by `scripts/core/publish_arcgis_online.py`.
- All three packagers inherit from the same `.style.json` sidecars — single source of truth for symbology across QGIS, ArcGIS Pro, and AGOL.

---

## Orchestration Modes

### Direct Mode
Lead Analyst handles small tasks without spawning specialists. Best for quick lookups, status checks, or simple updates.

### Partial Delegation
Lead Analyst activates only the needed specialists. Best for incremental updates or single-stage reruns.

### Full Pipeline
Standard for new analyses:
1. Lead Analyst → project brief + run plan
2. Data Retrieval → raw data + provenance
3. Data Processing → cleaned GeoPackages
4. Spatial Stats → analysis + maps
5. Cartography (optional) → refined maps
6. Validation QA → QA gate
7. Report Writer → deliverables
8. Site Publisher → QGIS package + ArcGIS Pro package + optional AGOL publishing
9. Peer Reviewer → Gate 2 QC
10. Lead Analyst → visual QA + human delivery

---

## Handoff Contracts

Each pipeline stage writes a structured JSON handoff to `runs/` before passing control.

### Retrieval Handoff
- Dataset manifest with file paths
- Provenance (source URL, download date, format)
- Source limitations and known issues
- Warnings (missing data, partial coverage)

### Processing Handoff
- Cleaned dataset paths in `data/processed/`
- Transformation log (operations applied)
- Schema notes (field names, types, GEOID format)
- Join match rates
- Warnings (low match rate, nulls, CRS changes)

### Analysis Handoff
- Output file paths (maps in `outputs/maps/`, web maps in `outputs/web/`, tables)
- Analysis steps taken (classification scheme, null handling, coverage)
- Assumptions and caveats
- `ready_for: "validation"` flag

### Validation Handoff
- Per-check result JSONs in `runs/validation/`
- Aggregated handoff JSON in `runs/`
- Overall status: PASS / PASS WITH WARNINGS / REWORK NEEDED
- `ready_for: "reporting"` (PASS) or `ready_for: "review"` (issues)

### Reporting Handoff
- Asset manifest in `outputs/reports/`
- Markdown + self-contained HTML reports
- `ready_for: "synthesis"` flag

### Lead Analyst Handoff
- Run plan JSON in `runs/`
- Lead summary markdown in `outputs/reports/`
- Pipeline status, upstream references, validation status, key outputs, aggregated warnings
- `ready_for: "human-review"` (complete) or `ready_for: "rework"` (failed)

---

## Current Limitations

| Limitation | Status | Notes |
|---|---|---|
| PostGIS backend | ❌ Not live | `db-manager` agent dormant; PostGIS only used for optional local OSM mirror |
| Vector tile publishing | ❌ Not functional | Requires Martin tile server; `publish_tiles.py` in `scripts/future/` |
| Service area analysis | ⚠️ Aspirational | `osmnx` isochrones work on fast hardware; not in core-tested paths |
| Time-series animation | ⚠️ Aspirational | `animate_time_series.py` in `scripts/core/` — written but not battle-tested |
| 3D terrain | ⚠️ Aspirational | `render_3d_terrain.py` in `scripts/future/` |
| Memory automation | ⚠️ Manual | Lessons log and retrospectives are manually maintained |
| Raster pipeline | ⚠️ Aspirational | Raster scripts in `scripts/future/` — not on core-tested paths |
| Global data portals | ⚠️ Manual | `data-retrieval` knows the portals but automated fetching is aspirational |

**What DOES work reliably (battle-tested):**
- Census ACS + TIGER retrieval → processing → choropleth → validation → report (full pipeline)
- Hotspot analysis (Gi*, FDR-corrected) and spatial autocorrelation
- Point overlay analysis
- Bivariate choropleth
- Interactive Folium web maps
- Vision QA (agent inspects maps before delivery)
- Peer review gate
- HTML/markdown report generation with auto-derived KPIs
- QGIS + ArcGIS Pro + (opt-in) ArcGIS Online delivery packaging, all driven by one set of `.style.json` sidecars
