# spatial-machines — Agent Guide (OpenCode)

You are operating a multi-agent GIS consulting firm powered by 9 specialist agents. Read `CLAUDE.md` first if you are using Claude Code — it has harness-specific subagent syntax. This file covers OpenCode and harness-agnostic operation.

## Quick Start Commands

```bash
make verify    # Check core scripts compile + wiki/agent count
make test      # Run full test suite (pytest)
make demo      # Run the built-in demo (Sedgwick County poverty, ~15 sec)
```

To run a single script: `python scripts/core/<script>.py --help`

## System Overview

- **Python 3.11+** with GDAL, PROJ, GEOS (system libraries, not pip)
- **Setup:** `pip install -r requirements.txt` then `cp .env.example .env`
- **Working directory:** Always the repo root. All paths are relative.
- **Script-first:** Use `scripts/core/` before writing any custom code
- **Workspace isolation:** Each project lives in `analyses/<project-id>/`

## Project Structure

```
analyses/<project-id>/       # Project workspace (fully isolated)
├── project_brief.json      # Created by lead-analyst at intake
├── data/raw/               # Immutable source data
├── data/processed/         # Analysis-ready datasets
├── outputs/maps/           # Static PNG maps (200 DPI)
├── outputs/web/            # Interactive Folium HTML maps
├── outputs/reports/        # Markdown + HTML reports
├── outputs/qa/             # Validation results
├── outputs/qgis/           # QGIS project packages
└── runs/                   # Pipeline handoff JSONs (handoff chain)

scripts/core/               # 155 battle-tested production scripts
scripts/future/             # 15 experimental scripts (not battle-tested)
config/map_styles.json      # 31 palettes, 5 map families — read before every map
docs/wiki/                  # 136 pages of canonical GIS methodology
```

## Pipeline Stages (artifact-driven)

Each stage reads upstream artifacts, writes downstream artifacts. No stage is complete until its handoff JSON exists in `runs/`.

| Stage | Owner | Ready Flag |
|---|---|---|
| 0. Intake | lead-analyst | `ready_for: retrieval` |
| 1. Retrieval | data-retrieval | `ready_for: processing` |
| 2. Processing | data-processing | `ready_for: analysis` |
| 3. Analysis | spatial-stats | `ready_for: cartography` or `ready_for: validation` |
| 4. Cartography | cartography | `ready_for: validation` |
| 5. Validation | validation-qa | `ready_for: reporting` |
| 6. Reporting | report-writer | `ready_for: publishing` |
| 7. Publishing | site-publisher | `ready_for: peer-review` |
| 8. Peer Review | peer-reviewer | `ready_for: delivery` |
| 9. Delivery | lead-analyst | `ready_for: human-review` |

Pipeline variants: **Direct** (small tasks), **Partial** (skip stages explicitly), **Full** (default for new analyses).

## Activation Protocol

To adopt a role, read two files:
1. `agents/<role>/SOUL.md` — mission, non-negotiables, boundaries
2. `agents/<role>/TOOLS.md` — approved scripts and tools

Role directories: `lead-analyst/`, `data-retrieval/`, `data-processing/`, `spatial-stats/`, `cartography/`, `validation-qa/`, `report-writer/`, `site-publisher/`, `peer-reviewer/`

In single-threaded mode (OpenCode), switch roles by re-reading the appropriate SOUL.md + TOOLS.md before each stage.

## Cartography Standards (non-negotiable)

Read `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` and `config/map_styles.json` before any map. Key rules:

- **Choropleth family:** No basemap, no scale bar, no north arrow. Data IS the map.
- **Point overlay / reference families:** Basemap required, scale bar and north arrow optional.
- **DPI:** 200 preferred, 150 minimum.
- **Figure size:** 14×10 for state-level, 12×10 for local.
- **CRS:** EPSG:4269 (geographic) or EPSG:5070 (projected, for area/distance).
- **NoData:** Mask to `np.nan`, set `ax.set_facecolor("white")`. Never render as black.
- **Style sidecar:** Every map writes a `.style.json` alongside the PNG. Do not skip this.
- **Vision QA:** Inspect every map before delivery using the image tool. Checklist:
  1. Legend title readable (not raw field name)
  2. Legend uses en-dash (–), not hyphen
  3. Decimal precision consistent
  4. Color scheme appropriate for variable type
  5. State/county boundaries visible
  6. Title present and accurate
  7. No rendering artifacts

Validate after generation: `python scripts/core/validate_cartography.py --input-dir outputs/maps/`

## Spatial Statistics Rules

- Always run Global Moran's I before Gi* or LISA analysis.
- Use FDR correction (Benjamini-Hochberg) for all hotspot and LISA results.
- Flag high-CV ACS tracts.
- Report uncertainty alongside every finding.

## Quality Gates

**Gate A (Planning):** Project brief must exist before substantial work.
**Gate B (Structural QA):** Blocking on missing artifacts, broken geometry, join rates below threshold.
**Gate C (Peer Review):** Blocking on conclusions overshooting evidence, misleading maps, inadequate caveats.

Blocking conditions: missing handoff, missing required artifact, `REWORK NEEDED` status, `REJECT` verdict.
Advisory (non-blocking): `PASS WITH WARNINGS`, `REVISE`, partial coverage with disclosure.

## Known Active Issues

- GAP-03: No `--project-dir` flag on scripts — isolated project execution requires explicit `--output-dir` on every call
- GAP-08: SD handoff logs reference NE paths in `processing_logs`/`analysis_logs` arrays (output_files are correct)
- GAP-09: SD provenance mixes absolute and relative paths
- KI-06: QGIS project files target different versions (3.34.0 vs 3.22.16) — cosmetic, both work

See `docs/internal/KNOWN_ISSUES.md` and `docs/internal/ARCHITECTURE_GAPS.md` for full inventory.

## Key References

- `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` — read before any map
- `docs/wiki/standards/SPATIAL_STATS_STANDARD.md` — read before any autocorrelation/clustering
- `docs/reference/PIPELINE_STANDARDS.md` — mandatory output standards, style constants, report structure
- `docs/architecture/PIPELINE_CANON.md` — authoritative pipeline definition (source of truth over prose)
- `docs/architecture/ARCHITECTURE.md` — system architecture, what works vs aspirational
- `config/map_styles.json` — 31 palettes, domain-to-palette mapping (poverty→YlOrRd, income→YlGnBu, etc.)
- `templates/project_brief.json` — project brief schema

## QA Scorecard (30-point rubric)

Minimum for client-ready: **≥22/30**

Weights: Spatial stats 8pts, Map quantity 6pts, Map quality 4pts, Interactive web map 3pts, Report 4pts, Data catalog 2pts, QGIS package 2pts, Handoff files 1pt.

An agent must never self-score ≥22 if any map fails `validate_cartography.py`.

## Report Structure (Pyramid Principle)

Every `analysis_report.md` must follow this order:
1. Key Findings (specific numbers, up top)
2. Morphometrics / Summary Stats table
3. Methodology
4. Detailed Findings
5. Validation
6. Caveats & Limitations
7. Output File Inventory

## Delivering Results

Present the user with:
1. Summary of findings (lead with the answer)
2. Paths to key outputs (maps, web maps, reports, QGIS package)
3. QA status and caveats
4. Suggested next steps

## Wiki Canon Rule

The `docs/wiki/` directory (136 pages) is the primary authority for reusable GIS methods. Handbooks remain authoritative only for role-boundary content. See `docs/handbooks/STATUS_LEDGER.md` for migration status.

## Customizing Your Fork (PATCH.md)

This project is designed to be forked and customized. When the user asks you to modify the system (add a data source, change defaults, alter pipeline behavior), document every change in `PATCH.md` at the repo root. Record the intent, files modified, reasoning, and dependencies for each change. This allows re-applying customizations after pulling upstream updates. See `PATCH.md` for the format.
