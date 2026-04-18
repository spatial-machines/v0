# QGIS Project Contract

## Purpose

This document defines the contract for QGIS review packages produced by the GIS Agent Team. A review package is a self-contained folder that a human analyst can open in QGIS without building the first map from scratch.

## Review Spec

Every review package is driven by a **review spec** (`review-spec.json`) — a machine-readable document that describes what's in the package and how it should be presented. The spec is produced by `build_review_spec.py` by introspecting the source GeoPackage.

### Layer Roles

| Role | Meaning | Default Group |
|------|---------|---------------|
| `primary_analysis` | The main layer the reviewer should inspect first | Review Layers |
| `secondary_review` | Supporting analysis layers for cross-checking | Review Layers |
| `reference` | Context layers (boundaries, basemaps) | Reference Layers |

### Field Roles

Field roles are auto-classified from column names and types:

| Role | Examples | Styling Use |
|------|----------|-------------|
| `id` | GEOID, FIPS, tract_id | Not styled; used for identification |
| `id_system` | fid, objectid | Hidden from review |
| `label` | NAME, tract_name | Used for map labels if feature count < 100 |
| `count` | total_pop, pop_total | Graduated: natural breaks, YlGnBu ramp |
| `percent` | water_pct, vacancy_rate | Graduated: quantile, YlOrRd ramp |
| `area` | land_area_sqm, total_area | Graduated: equal interval, Greens ramp |
| `measure` | (numeric, unmatched) | Graduated: equal interval, Greens ramp |
| `attribute` | (text, unmatched) | Not styled |
| `geometry` | geom, shape | Internal; not exposed |

### Thematic Field Selection

The primary thematic field (used for initial map styling) is chosen automatically:
1. **percent** fields are preferred (distribution patterns are most reviewable)
2. **count** fields are next (population, totals)
3. **measure** fields as fallback

Within each role, the field with the highest non-null coverage wins.

### Symbology Defaults

| Field Role | Renderer | Method | Classes | Color Ramp |
|------------|----------|--------|---------|------------|
| percent | graduated | quantile | 5 | YlOrRd |
| count | graduated | natural_breaks | 5 | YlGnBu |
| measure | graduated | equal_interval | 5 | Greens |
| (none) | single | — | — | neutral gray |

## Package Structure

```
<run-id>/
├── project.qgs          # QGIS project — open this
├── review-spec.json      # Machine-readable spec (drives project generation)
├── README.md             # Human instructions
├── review-notes.md       # QA status, caveats, what to look for
├── manifest.json         # File inventory with sizes
├── data/                 # GeoPackage(s), CSVs
└── reports/              # Markdown, HTML, PNGs
```

## Generation Pipeline

```
GeoPackage
    │
    ▼
build_review_spec.py     →  review-spec.json
    │
    ▼
build_qgis_project.py   →  project.qgs  (PyQGIS headless)
    │
    ▼
write_qgis_review_notes.py  →  README.md, review-notes.md
```

### Commands

```bash
# 1. Build review spec from GeoPackage
python scripts/build_review_spec.py data/processed/joined.gpkg \
    --layer-name joined_layer \
    --title "My Analysis" \
    -o review-spec.json

# 2. Generate styled QGIS project
python scripts/build_qgis_project.py review-spec.json outputs/qgis/my-review/

# 3. Write review notes
python scripts/write_qgis_review_notes.py outputs/qgis/my-review/ \
    --run-id my-review --title "My Analysis" \
    --review-spec review-spec.json
```

## Portability

- All paths in `project.qgs` are **relative** — the package can be copied anywhere
- The `.qgs` file is post-processed to replace absolute paths with `./` references
- CRS is preserved from the source data (not reprojected)
- QGIS 3.22+ required to open

## Review Experience

When a reviewer opens `project.qgs`:

1. **Layers are grouped** — "Review Layers" and "Reference Layers" in the layer panel
2. **The primary layer has thematic styling** — graduated colors on the most reviewable field
3. **The map zooms to the data extent** — no manual zoom needed
4. **Legend shows class breaks** — the reviewer can see the data distribution at a glance
5. **Attribute table works** — click any feature to inspect field values
6. **Review notes are in the package** — `review-notes.md` documents QA status and caveats

## Extension Points

- Add more layers to the review spec (secondary, reference) for multi-layer reviews
- Override thematic field in the spec to force a different initial map
- Add label configuration for small-feature-count layers
- Add print layout templates for standardized map exports
