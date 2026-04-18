# Scripts

All executable analysis code for the spatial-machines pipeline. Agents call these scripts to do the actual work.

## Layout

| Folder | Contents |
|---|---|
| [`core/`](core/) | **Battle-tested production scripts.** Used by every real analysis run. These are the scripts agents are required to prefer over writing custom code. |
| [`future/`](future/) | **Aspirational scripts** — written but not yet proven on real analyses. Use with caution; may need debugging. May promote to `core/` once battle-tested. |
| [`tool-registry/`](tool-registry/) | The 679-tool GIS method registry from the SpatialAnalysisAgent research — a reference index agents can consult for method discovery. Not executed directly. |
| `demo.py` | Runs the Sedgwick County poverty demo end-to-end. Invoked by `make demo` and by the root `demo.py` launcher. |

## Running any script

Every script documents itself:

```bash
python scripts/core/<script_name>.py --help
```

That's the authoritative source for arguments, flags, and usage. Catalogs in markdown drift; `--help` doesn't.

## Categories in `core/`

To orient — core scripts fall into these families. Browse [`core/`](core/) for the full list.

- **Retrieval (`fetch_*.py`, `retrieve_*.py`)** — 20+ data sources: Census ACS/Decennial/TIGER/LODES, EPA EJScreen, CDC PLACES, FEMA NFHL, NOAA, BLS, FBI, USDA, HUD, OpenStreetMap, Overture, USGS, GTFS, Socrata, and generic URL/local-file retrievers.
- **Processing (`process_*.py`, `join_*.py`, `derive_*.py`, `batch_join.py`, `spatial_join.py`, `compute_rate.py`)** — raw → analysis-ready GeoPackages with provenance.
- **Analysis (`analyze_*.py`, `compute_*.py`, `overlay_points.py`)** — choropleth, bivariate, hotspots (Gi*), LISA clusters, Moran's I, summary stats, top-N, change detection.
- **Charting (`generate_chart.py`, `charts/_base.py`)** — distribution / comparison / relationship / timeseries chart families, paired with maps.
- **Validation (`validate_*.py`)** — geometry, CRS, join coverage, null rates, cartography QA, ArcGIS package QA, handoff chain completeness.
- **Reporting (`write_*_handoff.py`, `write_html_report.py`, `write_markdown_report.py`, `collect_report_assets.py`)** — narrative reports, handoff chain, report asset collection.
- **Packaging (`package_qgis_review.py`, `package_arcgis_pro.py`, `publish_arcgis_online.py`, `teardown_agol.py`)** — QGIS project, ArcGIS Pro (GDB + .lyrx + .aprx helper), optional AGOL publishing, AGOL teardown.
- **Pipeline observability (`log_activity.py`, `show_pipeline_progress.py`, `audit_delegation.py`, `check_*.py`)** — progress monitoring, delegation auditing, data freshness, memory status.
- **Project brief / intake (`parse_task.py`, `create_run_plan.py`)** — natural-language task → project brief, run plans.
- **Styling utilities (`style_utils.py`, `write_style_sidecar.py`, `renderers.py`, `lyrx_writer.py`, `aprx_scaffold.py`, `qgis_env.py`)** — palette routing, sidecar I/O, renderer translation across QGIS / `.lyrx` / AGOL.

## Adding a new script

See [docs/extending/ADDING_DATA_SOURCES.md](../docs/extending/ADDING_DATA_SOURCES.md) for the specific case of a new data fetcher. In general:

1. Use the standard argparse pattern (see any `fetch_*.py` for a reference).
2. Write to paths under `analyses/<project>/...` — never to global state.
3. Write a `.style.json` / `.provenance.json` / `.manifest.json` sidecar where applicable.
4. Place in `scripts/core/` and document in [PATCH.md](../PATCH.md) for fork tracking.

## Principles

- **Scripts are the agent's tools, not its brain.** The wiki tells the agent *when* to use a script; the script just does the thing.
- **Prefer composing existing core scripts over writing new ones.** Agents are required to check core before writing custom code — see the `⛔ Script-First Rule` in the lead-analyst, cartography, and spatial-stats SOUL.md files.
- **Every script should support `--help`, be idempotent, and write provenance.** No silent side effects.
