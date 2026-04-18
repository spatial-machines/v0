# Workspace Model

How spatial-machines organizes projects, data, and outputs on disk.

## Mental model

Think of the system like a consulting firm's file room. Each engagement gets its own case folder. Inside that folder: raw source material, work products, QA results, deliverables. Nothing from one case leaks into another.

```
analyses/
  README.md                     ← overview of the analyses folder
  <project-id>/                 ← one case folder per engagement
    project_brief.json          ← scope, audience, data plan, deliverables
    data/
      raw/                      ← immutable source data
      processed/                ← analysis-ready GeoPackages
    outputs/
      maps/                     ← static maps + .style.json sidecars
      charts/                   ← statistical charts + .style.json sidecars
      web/                      ← interactive Folium maps
      reports/                  ← narrative HTML + Markdown
      qa/                       ← validation results, QA scorecards
      qgis/                     ← QGIS project package
      arcgis/                   ← ArcGIS Pro package (+ AGOL publish-status if opted in)
    runs/                       ← pipeline handoff JSON chain + activity.log
    data_catalog.json           ← machine-readable data dictionary
```

## The project brief is the contract

`project_brief.json` is the single source of truth for per-project scope. It's written by the lead-analyst at engagement start and read by every downstream agent before they do any work. Schema at `templates/project_brief.json`. Key sections:

- **client** — who the work is for
- **audience** — primary reader, technical level, what they're deciding
- **engagement** — hero question, deliverable type, deadline, budget tier
- **geography** — study area, geographic unit (tract/county/blockgroup), CRS, bounding box
- **data** — primary sources, vintage, known quality issues, institutional areas to flag, join key
- **analysis** — dependent/independent variables, analysis types, spatial weights, classification
- **outputs** — required maps, charts, statistics, formats, publish targets
- **report** — tone, pyramid lead, SCQA framing, key findings draft
- **qa** — max null %, min join rate, Moran's gate, institution flag

When a downstream agent reads the brief and hits a contradiction (e.g., `dependent_variable: poverty_rate` but `primary_sources` doesn't include ACS), it escalates back to the lead-analyst rather than guessing.

## Immutability rules

These are enforced by convention and by the validation stage:

- **`data/raw/` is immutable.** Nothing downstream writes here. If you need a cleaned version of a raw file, write it to `data/processed/` with a new name.
- **`data/processed/` is written once by the data-processing stage.** Analysis and reporting stages read it; they do not modify it.
- **`outputs/` is per-stage write-only.** Cartography writes to `maps/` and `charts/`; report-writer writes to `reports/`; site-publisher writes to `qgis/` and `arcgis/`. No stage writes to another stage's output directory.
- **`runs/` is append-only.** Each stage writes a handoff JSON artifact and appends to `activity.log`. Nothing is deleted.

These rules let you re-run a single stage without corrupting upstream state, and make the handoff chain fully auditable.

## Isolation between projects

Each project is fully self-contained. No cross-project file references, no shared state, no shared scratch space. This means:

- You can delete an entire analysis by deleting its folder. No orphaned references elsewhere.
- You can zip an analysis folder and hand it to a reviewer or client. It opens as-is on any machine with Python + the venv (or QGIS, for the QGIS package alone).
- Running two analyses in parallel (two agents, two folders) does not cause conflicts.

The one exception: global config (`config/map_styles.json`, `config/data_sources.json`, the wiki) is shared across projects by design — that's where your firm's standards live. Global config changes are managed via `PATCH.md` so customizations persist across upstream updates.

## Handoff artifacts (`runs/`)

Every pipeline stage writes a JSON handoff artifact to `runs/` before the next stage begins. Naming convention: `<stage-name>-handoff.json` (e.g., `retrieval-handoff.json`, `processing-handoff.json`).

The lead-analyst reads these in order to verify the chain is complete before delivering to the human. Any missing or invalid handoff blocks the pipeline.

The `activity.log` JSONL file in `runs/` is the per-run timeline: one line per agent action (stage start, script call, stage end). Useful for debugging a run that went sideways. Tail it live with:

```bash
python scripts/core/show_pipeline_progress.py analyses/<project>/ --watch
```

## What's NOT in the workspace model (today)

The project does not currently implement a cross-project registry, a lifecycle state machine, or per-project manifests. **Projects are just folders. Their existence is their state.**

If a registry becomes useful later — for example, "show me every analysis that used ACS 2022 data" or "auto-archive analyses older than 1 year" — it will appear in [`docs/architecture/ROADMAP.md`](../architecture/ROADMAP.md) first. For now: `ls analyses/` is the project list.
