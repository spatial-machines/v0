# QGIS Review Guide

How to open and review the QGIS package that every pipeline run produces.

## What you get

After a pipeline run, the site-publisher writes a QGIS package to:

```
analyses/<project>/outputs/qgis/
├── project.qgs          ← open this in QGIS
├── README.md            ← read first: what's in the package and how to use it
├── review-notes.md      ← validation status, warnings, coverage, review checklist
├── review-spec.json     ← machine-readable layer introspection
├── manifest.json        ← file inventory with sizes
└── <data files>.gpkg    ← the GeoPackages the project references (relative paths)
```

The `.qgs` is plain XML with relative paths, so it's portable — you can open it on the same machine where you ran the pipeline, or copy the whole folder to another machine.

## Prerequisites

- **QGIS 3.28 LTR or newer**. Download from [qgis.org](https://qgis.org). On Windows, OSGeo4W is the recommended installer.
- No other prerequisites. The package is self-contained.

## Opening the package

### On the same machine that produced it

1. Open QGIS.
2. `File → Open Project` (or `Ctrl+O` / `Cmd+O`).
3. Navigate to `analyses/<your-project>/outputs/qgis/project.qgs`.
4. The project loads with pre-styled layers — graduated renderers, basemap, and auto-zoomed extent.

### On a different machine (reviewer)

1. Copy the **entire** `outputs/qgis/` folder to the reviewer's machine. Keep the folder structure intact — the `.qgs` uses relative paths.
2. Open `project.qgs` in QGIS on that machine.

Any method of copy works — USB drive, network share, `scp` / `rsync`, cloud storage, email with the folder zipped. The only hard requirement is that the folder's internal structure is preserved.

## Review workflow

### 1. Read `README.md` and `review-notes.md` before opening QGIS

- **`README.md`** — what the package contains, how to load it in QGIS (drag-and-drop or open-project), what questions the analysis was answering.
- **`review-notes.md`** — validation status (`PASS` / `PASS WITH WARNINGS` / `REWORK NEEDED`), the fields covered, the warnings the validation stage flagged, and the recommended review order.

Opening QGIS first means you start forming impressions without the QA context. Start with the notes.

### 2. Open the project and check layer rendering

Each layer should load already styled:

- **Choropleth layers** — graduated renderers with palette and breaks matching the static PNG in `../maps/`.
- **Categorical layers** — unique-value renderers (e.g., LISA cluster classes, hotspot classes).
- **Point overlays** — proportional or categorical symbols per the sidecar.

If a layer loads flat-colored, the sidecar probably wasn't matched. Check `review-spec.json` to see which sidecars were applied and which were skipped.

### 3. Compare to the static maps

Every styled layer should visually match the corresponding PNG in `analyses/<project>/outputs/maps/`. If they don't match:

- Palette difference — check the `.style.json` sidecar vs the QGIS renderer.
- Break difference — classification method (natural breaks vs quantile) may have produced different bins.
- Extent difference — the static map may be clipped; QGIS shows the full dataset.

### 4. Sanity-check the attribute table

Open the attribute table (right-click layer → Open Attribute Table) and verify:

- Feature count matches what the validation stage reported.
- Join key fields (usually `GEOID`) are 11-digit tract IDs, 5-digit county IDs, etc.
- Numeric fields are plausible — no negative populations, no 99999 sentinel values slipping through.
- MOE fields (if ACS data) have reasonable values. Very high MOE indicates unreliable estimates; the validation stage should have flagged these.

### 5. Spot-check against the HTML report

`analyses/<project>/outputs/reports/*.html` is a self-contained report. Open it in a browser alongside QGIS. The KPIs in the report exec summary should match what you see in QGIS by querying the data.

## Customizing styling inside QGIS

The package ships with the pipeline's styling choices. If a reviewer wants to try a different classification or palette:

1. Right-click a layer → `Properties → Symbology`.
2. Adjust classification method, number of classes, palette.
3. `Apply`. QGIS updates in place without touching the `.qgs` file on disk until you save.
4. If you save the project, consider saving as a copy (`project-reviewed.qgs`) rather than overwriting the pipeline output.

A print layout template is available at `templates/qgis/print_layout.qpt` for publication-quality PDF exports with title, legend, scale bar, and north arrow. Import it via `Project → Layouts → New from Template`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `"Layer not found"` on open | Files moved within the package folder | Restore the original folder structure; relative paths require it. |
| CRS prompt on open | Data is in EPSG:4269 (NAD83). | Accept the source CRS. Don't reproject without a reason. |
| Flat single-color rendering | Sidecar didn't match the layer | Check `review-spec.json` to see which sidecars were matched. |
| Older QGIS version warning | `.qgs` file stamped with a newer QGIS version | Usually safe to ignore; QGIS is backward-compatible within 3.x. |
| Basemap tile 401 / 403 | Your org's proxy blocks the tile provider | Configure QGIS's proxy settings, or swap the basemap layer to a locally-cached source. |

## See also

- [QGIS_PROJECT_CONTRACT.md](QGIS_PROJECT_CONTRACT.md) — formal contract for what the QGIS package guarantees
- [`docs/wiki/workflows/QGIS_HANDOFF_PACKAGING.md`](../wiki/workflows/QGIS_HANDOFF_PACKAGING.md) — how the packager assembles the project
