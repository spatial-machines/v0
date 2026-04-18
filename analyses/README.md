# Analyses

Each analysis lives in its own isolated directory under `analyses/<project-id>/`.

## Starting a New Analysis

Ask your AI agent to run a spatial analysis. The lead-analyst role will create a project directory here with a `project_brief.json` and the standard folder structure.

## Expected Directory Structure

```
analyses/<project-id>/
├── project_brief.json          # Scope, questions, data plan, deliverables
├── inventory.json              # Asset inventory (auto-maintained)
├── data/
│   ├── raw/                    # Immutable source data (never edited downstream)
│   └── processed/              # Analysis-ready datasets (GeoPackage preferred)
├── outputs/
│   ├── maps/                   # Delivery-quality static maps (PNG, 200 DPI)
│   ├── web/                    # Interactive Folium maps (self-contained HTML)
│   ├── reports/                # Markdown and HTML reports
│   ├── qa/                     # Validation results, QA scorecards
│   └── qgis/                   # QGIS project packages for follow-up work
├── runs/                       # Pipeline handoff artifacts (JSON chain-of-custody)
└── data_catalog.json           # Machine-readable data dictionary
```

## Key Rules

- **Raw data is immutable.** Nothing downstream edits files in `data/raw/`.
- **Processed data is never modified by analysis or reporting stages.**
- **Each project is fully self-contained.** No cross-project file references.
- **Handoff artifacts in `runs/` record provenance** for every pipeline stage.

## After an Analysis Completes

Your agent will point you to the key outputs:
- Static maps in `outputs/maps/`
- Interactive maps in `outputs/web/` (open the HTML files in a browser)
- Reports in `outputs/reports/`
- QGIS project files in `outputs/qgis/` for further exploration in QGIS Desktop
