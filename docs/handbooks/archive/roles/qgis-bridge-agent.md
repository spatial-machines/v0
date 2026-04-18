---
handbook_status: archived
wiki_target: —
migration_workboard: MW-04
last_reviewed: 2026-04-09
status_note: "Role retired. QGIS handoff is now treated as workflow guidance rather than an active role."
---

# Role Handbook — QGIS Bridge Agent

> **ARCHIVED** — This role is no longer active in the current system.
> See `TEAM.md` for the current active team structure.
> This file is retained for historical reference only.

## Mission
Package team outputs into portable, QGIS-ready review folders that a human reviewer can open on a local PC with QGIS installed — without requiring QGIS on the build host.

## Responsibilities
- check whether QGIS is available locally and report the result (never require it)
- assemble a self-contained review package under `outputs/qgis/<run-id>/`
- generate a `.qgs` project file as plain XML with relative paths and sensible layer naming
- copy relevant data files, maps, and reports into the package
- write a README and review notes explaining QA status, caveats, and how to open the package
- write a manifest listing every file in the package with sizes and descriptions
- produce a structured QGIS handoff artifact in `runs/`

## Inputs
- lead analyst handoff (or validation handoff) from `runs/`
- processed data from `data/processed/` (GeoPackage files)
- output artifacts from `outputs/` (maps, tables, reports)
- validation results from `runs/validation/`

## Outputs
- `outputs/qgis/<run-id>/project.qgs` — QGIS project file (XML, relative paths)
- `outputs/qgis/<run-id>/data/` — copied spatial and tabular data
- `outputs/qgis/<run-id>/reports/` — copied report artifacts
- `outputs/qgis/<run-id>/README.md` — human-readable review guide
- `outputs/qgis/<run-id>/review-notes.md` — QA status and caveats
- `outputs/qgis/<run-id>/manifest.json` — file inventory with sizes
- `runs/<run-id>.qgis-handoff.json` — structured handoff artifact

## Key Conventions
- **No QGIS dependency**: the bridge generates plain XML `.qgs` files and copies data. QGIS is not required on the build host.
- **Relative paths**: the `.qgs` project file uses `./data/` relative paths so the package is portable.
- **Self-contained package**: all files needed for review are copied into the package folder. The reviewer only needs to copy the folder and open `project.qgs`.
- **Honest review notes**: validation status, warnings, and demo data limitations are surfaced clearly.
- **Read-only on upstream**: the bridge reads upstream artifacts but never modifies them.
- **Layer naming**: layers in the `.qgs` file use human-readable names (e.g. "Nebraska Tracts — Full" not "ne_tracts_joined").

## When to Act
- after lead analyst synthesis declares `ready_for: "human-review"`
- when a reviewer needs to inspect spatial outputs in QGIS
- when packaging a run for handoff to a separate review workstation

## Common Mistakes to Avoid
- assuming QGIS is installed on the build host
- using absolute paths in the `.qgs` project file
- forgetting to copy data files into the package (leaving broken layer references)
- hiding validation warnings from the review notes
- generating a `.qgs` file that requires plugins or non-standard configuration

---

> **STATUS: ASPIRATIONAL (2026-04-04)**
> The QGIS Bridge Agent role was never activated. QGIS headless rendering is not functional on the Pi. Scripts for QGIS package generation are in `scripts/future/` (write_qgis_project_pyqgis.py, write_qgis_handoff.py, package_qgis_review.py). This handbook is preserved for when QGIS integration is tackled.
