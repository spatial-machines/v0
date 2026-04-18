# Handbook Status Ledger

Status: active
Last pass: 2026-04-16 (handbook consolidation — research + active-project files relocated to `archive/`)

Purpose:
- provide a quick reference view of handbook migration state
- prevent handbook pages from competing silently with wiki canon
- track which handbook files remain active vs archived

Notes:
- The wiki (`docs/wiki/`) is the source of truth for reusable GIS methods. Handbooks remain authoritative only for role-boundary content.
- The root of `docs/handbooks/` contains only role-boundary docs, this ledger, and one `active-temp` handbook pending wiki migration.
- Everything else (migrated, research, active-project, archived) lives under `archive/` — retained for traceability but not primary reading material.

## Status definitions

| Status | Meaning |
|---|---|
| `active-role` | Authoritative role-boundary doc (wiki does not cover role boundaries) |
| `active-temp` | Still needed operationally, but intended to migrate to wiki canon |
| `active-project` | Project-specific or internal-process content, not wiki canon |
| `migrated` | Fully superseded by wiki canon, retained only for traceability |
| `research` | Aspirational or untested content, not for production use |
| `archived` | Obsolete or retired content |

## Current ledger

### Top-level (authoritative or pending migration)

| File | Status | Notes |
|---|---|---|
| `roles/data-retrieval-agent.md` | `active-role` | — |
| `roles/data-processing-agent.md` | `active-role` | — |
| `roles/spatial-analysis-agent.md` | `active-role` | — |
| `roles/validation-agent.md` | `active-role` | — |
| `roles/reporting-agent.md` | `active-role` | — |
| `roles/lead-analyst-agent.md` | `active-role` | — |
| `field-data-guide.md` | `active-temp` | Pending migration to `wiki/domains/FIELD_DATA` or similar — no live wiki target yet |

### Archived (all under `archive/`, retained for traceability)

| File | Status | Wiki target (if migrated) |
|---|---|---|
| `archive/roles/memory-agent.md` | `archived` | — |
| `archive/roles/qgis-bridge-agent.md` | `archived` | — |
| `archive/workflows/retrieval-and-provenance.md` | `migrated` | `workflows/GENERAL_RETRIEVAL_AND_PROVENANCE` |
| `archive/workflows/processing-and-standardization.md` | `migrated` | `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION` |
| `archive/workflows/analysis-and-output-generation.md` | `migrated` | `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION` |
| `archive/workflows/validation-and-qa.md` | `migrated` | `workflows/VALIDATION_AND_QA_STAGE` + wiki QA pages |
| `archive/workflows/reporting-and-delivery.md` | `migrated` | `workflows/REPORTING_AND_DELIVERY` |
| `archive/workflows/lead-analyst-orchestration.md` | `migrated` | `workflows/LEAD_ANALYST_ORCHESTRATION` |
| `archive/workflows/qgis-bridge-and-review.md` | `migrated` | `workflows/QGIS_HANDOFF_PACKAGING` |
| `archive/workflows/memory-and-learning-loop.md` | `active-project` | — |
| `archive/sources/census-tiger.md` | `migrated` | `data-sources/CENSUS_ACS`, `data-sources/TIGER_GEOMETRY` |
| `archive/sources/local-files.md` | `migrated` | `data-sources/LOCAL_FILES` |
| `archive/sources/remote-files.md` | `migrated` | `data-sources/REMOTE_FILES` |
| `archive/cartography/qgis-review-conventions.md` | `migrated` | `workflows/QGIS_HANDOFF_PACKAGING` |
| `archive/cartography-style-guide.md` | `migrated` | `standards/CARTOGRAPHY_STANDARD` |
| `archive/cartography-advanced.md` | `research` | — |
| `archive/spatial-stats-guide.md` | `migrated` | `standards/SPATIAL_STATS_STANDARD` |
| `archive/postgis-usage.md` | `migrated` | `toolkits/POSTGIS_TOOLKIT` |
| `archive/tool-registry-summary.md` | `migrated` | `toolkits/*` (GEOPANDAS, GDAL_OGR, POSTGIS, WHITEBOXTOOLS, RASTERIO) |
| `archive/benchmark-scorecard.md` | `active-project` | — |
| `archive/3d-visualization-guide.md` | `research` | — |
| `archive/vector-tiles-guide.md` | `research` | — |
| `archive/qgis-tools-research.md` | `research` | — |
| `archive/pre-tier-cleanup.md` | `active-project` | — |
| `archive/agent-self-assessments.md` | `active-project` | — |
| `archive/agent-upgrade-plan.md` | `active-project` | — |
| `archive/autonomous-gis-principles.md` | `active-project` | — |
