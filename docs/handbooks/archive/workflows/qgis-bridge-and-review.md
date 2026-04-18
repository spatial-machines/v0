# Workflow Handbook — QGIS Bridge and Review

## Purpose
Package GIS team outputs into a portable review folder that a human reviewer can open in QGIS on a separate local PC.

## Prerequisites
- a completed pipeline run with lead analyst handoff (or at minimum a validation handoff)
- processed spatial data in `data/processed/` (GeoPackage format preferred)
- output artifacts in `outputs/` (maps, tables, reports)

## Workflow Steps

### 1. Check QGIS environment (optional)
Run `check_qgis_environment.py` to report whether QGIS is available locally. This is informational only — the bridge does not require QGIS.

### 2. Package the review folder
Run `package_qgis_review.py` to:
- create `outputs/qgis/<run-id>/`
- copy spatial data into `data/` subfolder
- copy report artifacts into `reports/` subfolder

### 3. Generate the .qgs project file
Run `write_qgis_project.py` to produce a plain XML `.qgs` file with:
- relative paths to data files in the package
- human-readable layer names
- sensible layer grouping (data layers, reference layers)
- default styling (simple fill for polygons)

### 4. Write review notes
Run `write_qgis_review_notes.py` to generate:
- `README.md` — how to open and use the package
- `review-notes.md` — QA status, validation results, caveats, demo limitations

### 5. Write the handoff artifact
Run `write_qgis_handoff.py` to produce a structured JSON handoff in `runs/`.

### 6. Hand off to reviewer
Copy the entire `outputs/qgis/<run-id>/` folder to the reviewer's machine. The reviewer opens `project.qgs` in QGIS.

## Review Guidance for the Reviewer
1. Copy the package folder to a PC with QGIS 3.x installed.
2. Open `project.qgs` in QGIS.
3. Read `review-notes.md` first for QA status and known caveats.
4. Start with the full processed tract layer — check geometry, coverage, and field values.
5. Inspect the demographic subset layer — note that coverage is partial (demo data).
6. Cross-reference with the reports in the `reports/` subfolder.
7. Report findings back to the lead analyst.

## Conventions
- package is self-contained: no external file references
- `.qgs` uses relative paths only
- validation warnings are surfaced honestly, not hidden
- demo data limitations are stated explicitly in all review docs
- QGIS is never required on the build host
