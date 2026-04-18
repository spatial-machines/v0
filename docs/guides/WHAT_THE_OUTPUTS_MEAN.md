# What the Outputs Mean

A format-by-format guide to the files spatial-machines produces. Once you know what shape each artifact takes, you can open any analysis and know what to look for.

## Directory layout recap

Every analysis writes to `analyses/<project>/`:

```
data/
  raw/            ← immutable source files (CSV, shapefile, GeoJSON, etc.)
  processed/      ← analysis-ready GeoPackages
outputs/
  maps/           ← PNG + .style.json sidecars
  charts/         ← PNG + SVG + .style.json sidecars
  web/            ← Folium interactive HTML (self-contained)
  reports/        ← HTML + Markdown narrative reports
  qa/             ← JSON validation + scorecards
  qgis/           ← QGIS project package (.qgs + data + notes)
  arcgis/         ← ArcGIS Pro package (GDB + .lyrx + helper)
runs/             ← pipeline handoff JSONs + activity.log
data_catalog.json ← machine-readable dictionary of every layer and field
```

## GeoPackages (`data/processed/*.gpkg`)

Each file is one dataset (tracts + joined attributes, places, points of interest, etc.). Fields you'll commonly see:

| Field family | What it is |
|---|---|
| `GEOID` | Census identifier — 2-digit state, 5-digit county, 11-digit tract, 12-digit block group. This is usually the join key. |
| `NAME` / `NAMELSAD` | Human-readable name ("Census Tract 22.01", "Sedgwick County"). |
| `ALAND` / `AWATER` (or renamed `land_area_sqm` / `water_area_sqm`) | Land and water area in square meters, from TIGER. |
| Domain fields | Variable-specific — e.g. `poverty_rate`, `median_income`, `pct_uninsured`, `diabetes_prevalence`. Named to match the wiki's domain palette map so auto-styling works. |
| `*_moe` | Census margin of error for the matching estimate field. Used by uncertainty maps. |
| `institutional_flag` | 1 if the tract is institutional (military, prison, university), 0 otherwise. The Spatial Stats agent uses this to exclude noisy tracts. |
| `geometry` | Polygon, line, or point in the dataset's source CRS (usually EPSG:4269 NAD83). |

You can open a GeoPackage in QGIS, ArcGIS Pro, or interrogate it from Python:

```python
import geopandas as gpd
gdf = gpd.read_file("analyses/my-project/data/processed/tracts.gpkg")
gdf.columns          # all fields
gdf.dtypes           # field types
gdf.geometry.crs     # CRS
gdf.describe()       # numeric summary
```

## Static maps (`outputs/maps/<name>.png`)

200 DPI PNGs. Each map has a matching `<name>.style.json` sidecar that records:

- `map_family` — `thematic_choropleth`, `thematic_categorical`, `thematic_bivariate`, `reference`, `point_overlay`
- `field` — the variable mapped
- `palette` — name (e.g. `YlOrRd`) and RGB ramp
- `classification` — `natural_breaks`, `quantiles`, `equal_interval`, or `categorical`
- `breaks` — numeric cut points
- `colors_rgb` — per-class color values
- `source_gpkg` / `source_layer` — the data source, so QGIS + ArcGIS Pro + AGOL packagers can match
- `title`, `attribution`

This sidecar is the **single source of truth** for symbology. The same JSON drives the static PNG, the QGIS renderer, the ArcGIS `.lyrx`, and (if opted in) the AGOL layer renderer.

## Statistical charts (`outputs/charts/<name>.png` + `.svg` + `.style.json`)

Four families, distinguished by `chart_family` in the sidecar:

| Family | Kinds |
|---|---|
| `distribution` | histogram, KDE, box, violin |
| `comparison` | bar, lollipop, dot, ordered_bar |
| `relationship` | scatter, scatter_ols, hexbin, correlation_heatmap |
| `timeseries` | line, area, small_multiples |

The **pairing rule**: every choropleth ships with a paired distribution + top-N chart, every bivariate with a scatter + OLS, every change-over-time with a line chart. So if you see `poverty_choropleth.png` you'll also find `poverty_distribution.png` and `poverty_top_n.png`.

## Interactive web maps (`outputs/web/*.html`)

Self-contained Folium HTML. Opens in any browser, no server, no internet required (tile basemaps need internet on first pan). Toggleable layers, clickable popups, multiple basemap options.

## Summary-statistics CSVs (`outputs/tables/*.csv`)

One row per numeric field. Columns:

| Column | Meaning |
|---|---|
| `field` | Field name |
| `count` | Non-null value count |
| `null_count`, `null_pct` | Missing-data counts |
| `mean`, `std` | Mean and standard deviation |
| `min`, `25%`, `50%`, `75%`, `max` | Five-number summary |

## Top-N rankings (`outputs/tables/*_top_*.csv`)

Top-k and bottom-k features by some metric. Columns: `rank`, identifier (`GEOID`/`NAME`), the ranked metric, and any context fields the analyst requested.

## Narrative reports (`outputs/reports/*.html` and `.md`)

Markdown for source-of-truth editing, HTML for delivery. Both follow the Pyramid Principle — answer first, then evidence, methodology, caveats, sources. The HTML is self-contained (inline CSS, base64-embedded maps and charts) so it works offline and can be emailed as a single attachment.

Standard sections:

1. **Title + scope** — what was analyzed, for whom, which data
2. **Executive summary** — one paragraph with the headline finding
3. **Auto-derived KPIs** — key numbers (tract counts, populations, rate differences) lifted from the data
4. **Maps** — inline-embedded with captions
5. **Charts** — inline-embedded with captions
6. **Interactive map** — embedded via iframe
7. **Methodology** — how the analysis ran (classification, spatial weights, stats)
8. **Caveats** — standard peer-reviewer-flagged items: ACS MOE, proxy variables, causation vs correlation, institutional tracts
9. **Sources** — provenance for every dataset used

## Validation results (`outputs/qa/` + `runs/validation/`)

Per-check JSONs:

| Field | Meaning |
|---|---|
| `check_name` | What was validated (geometry, CRS, join rate, etc.) |
| `status` | `PASS` / `WARN` / `FAIL` |
| `details` | Concrete findings (counts, values, specific feature IDs) |
| `thresholds` | What thresholds were applied for pass/warn/fail |

The aggregated `qa_scorecard.json` rolls these up to one of three outcomes: `PASS`, `PASS WITH WARNINGS`, or `REWORK NEEDED`.

## Handoff artifacts (`runs/*.json`)

Machine-readable chain-of-custody. Each pipeline stage writes one before the next begins. Common fields:

| Field | Meaning |
|---|---|
| `run_id` | Identifies the pipeline run |
| `stage` | Which agent wrote it (`retrieval`, `processing`, `analysis`, etc.) |
| `timestamp` | When it was written |
| `description` | Human-readable summary |
| `output_files` | Paths to artifacts produced |
| `warnings` | Any issues encountered |
| `ready_for` | What comes next (`validation`, `reporting`, `human-review`, etc.) |
| `upstream_refs` | Previous handoff filenames — makes the chain walkable |

You don't usually read these by hand — the lead-analyst's final summary synthesizes them. But they're available for audit, debugging, and re-running a failed stage without redoing upstream work.

## Activity log (`runs/activity.log`)

JSONL file, one line per agent action. Every stage writes at start and end, plus per-script call. Tail it live during a run:

```bash
python scripts/core/show_pipeline_progress.py analyses/<project>/ --watch
```

## QGIS review package (`outputs/qgis/`)

See [QGIS_REVIEW_GUIDE.md](../reference/QGIS_REVIEW_GUIDE.md). Key files:

- `project.qgs` — open in QGIS
- `README.md`, `review-notes.md` — read first
- `review-spec.json`, `manifest.json` — machine-readable introspection and inventory
- `data/` — the GeoPackages the project references

## ArcGIS Pro package (`outputs/arcgis/`)

| File | Purpose |
|---|---|
| `data/project.gdb/` | File geodatabase with every feature class |
| `layers/*.lyrx` | One styled layer file per map sidecar |
| `charts/` | Copies of chart PNGs + SVGs for layout embedding |
| `make_aprx.py` | Helper script to auto-build a full `.aprx` inside Pro |
| `review-spec.json`, `review-notes.md`, `manifest.json`, `README.md` | Introspection + how-to |

Drag any `.lyrx` into Pro for an already-styled layer, or run `make_aprx.py` from Pro's Python window to get a ready-to-share `.aprx` project.

## AGOL publish status (`outputs/arcgis/publish-status.json`)

Only present when `outputs.publish_targets` in the project brief included `"arcgis_online"`. Records every item created: Feature Service ID, Web Map ID, sharing level, which sidecar was matched to which published layer, URLs, and any warnings.

## Solution graph (`outputs/solution_graph.*`)

DAG showing every input → operation → output for the run. PNG and SVG for humans; JSON for machines; Mermaid for rendering inline in reports and GitHub. Built from the activity log + handoff chain + sidecars.

## Data catalog (`data_catalog.json`)

Layer-by-layer field dictionary: geometry type, feature count, CRS, bounding box, every column with its dtype, description, non-null count. Useful for:

- Answering "what fields does this layer have?" without opening QGIS
- Picking a field to map when you're building a new analysis
- Diffing two analyses to see how schemas evolved

## Style sidecars vs renderer consistency

Every static map produces a `.style.json` sidecar. Both the ArcGIS Pro packager and the AGOL adapter match sidecars to feature classes using the same logic (by `source_gpkg` stem first, then field presence, then categorical fallback). This means: **change a palette in one place (the cartography script's `.style.json` output) and QGIS + ArcGIS Pro + AGOL all render the new style consistently.** That's the whole point of the sidecar model.
