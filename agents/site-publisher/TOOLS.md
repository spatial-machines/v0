# TOOLS.md — Delivery Packaging

Approved operational tools for the Delivery Packaging role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`

## Primary Tool Classes

- `packaging`

## Approved Production Tools

### Packaging & Catalogs
- `write_publishing_handoff.py`
- `write_data_catalog.py`
- `generate_all_catalogs.py`

### QGIS Project Assembly
- `package_qgis_review.py` — full review package (styled .qgs, review-spec.json, review-notes.md, manifest.json, README.md). Pass `--style-dir` to inherit cartography agent's styling decisions.
- `write_qgis_project.py` — lower-level styled .qgs generation (graduated renderers, basemap, auto-zoom). Called by package_qgis_review.py.
- Print layout template: `templates/qgis/print_layout.qpt` — import in QGIS for pub-quality export

### ArcGIS Pro Project Assembly
- `package_arcgis_pro.py` — full review package (file geodatabase, `.lyrx` per map, charts folder, `make_aprx.py` helper, review-spec.json, review-notes.md, manifest.json, README.md). Pass `--style-dir outputs/maps/` and `--charts-dir outputs/charts/` to inherit cartography styling and chart outputs.
- `lyrx_writer.py` — pure-Python `.lyrx` JSON writer from a `.style.json` sidecar. No arcpy dependency on the OSS path.
- `aprx_scaffold.py` — detects arcpy and optionally builds a full `.aprx`; writes `make_aprx.py` helper otherwise.
- `validate_arcgis_package.py` — QA gate for the ArcGIS Pro package (.gdb readable, layers present, .lyrx valid).
- `renderers.py` — sidecar → renderer translation, shared across QGIS / ArcGIS Pro / ArcGIS Online.

### External Publishing (opt-in)
- `publish_arcgis_online.py` — publishing adapter CLI for ArcGIS Online. Default sharing=PRIVATE, supports `--dry-run`. Credentials via `.env` (`AGOL_URL`, `AGOL_USER`, `AGOL_PASSWORD`, or `AGOL_API_KEY`). Never auto-publishes — triggered only when `publish_targets` in the project brief includes `"arcgis_online"` or when the human runs the CLI directly.
- `publishing/arcgis_online.py` — the adapter implementation (import-only).
- `publishing/base.py` — abstract adapter interface `PublishAdapter` + `PublishRequest` + `PublishResult` (import-only).
- `publishing/{enterprise,geoserver,s3}.py` — stubs that raise with pointers to `docs/extending/PUBLISHING_ADAPTERS.md`. Planned for v1.1.

### Output Collection
- `collect_report_assets.py`

## Conditional / Secondary Tools

Use when the workflow explicitly supports them:
- interactive map packaging (Folium HTML assembly)
- batch catalog generation for all analyses

## Experimental Tools

Escalate before relying on:
- ArcGIS Enterprise, GeoServer, and static-site (S3 / GitHub Pages / Netlify) publishing — stubs exist, planned for v1.1
- vector tile generation
- custom dashboard / StoryMap / Experience Builder assembly

## Inputs You Depend On

- reports
- maps
- tables
- validation state
- templates
- project metadata

## Outputs You Are Expected To Produce

- organized output directory
- data catalogs
- QGIS review bundles where applicable
- ArcGIS Pro review bundles when `arcgis_delivery: true` in the project brief (default)
- publishing handoff
- delivery summary with paths to key outputs

## Operational Rules

- packaging and assembly are your job
- content meaning belongs to upstream roles
- the packaged deliverable must expose validation status, not obscure it
- invoke packaging tools as direct single-script exec calls, not wrapped shell batches
- QGIS and ArcGIS Pro projects must use relative paths so they work on any machine
- ArcGIS Pro package always produces the OSS baseline (.gdb + .lyrx + docs); pre-built `.aprx` only when arcpy is importable at package time
- run `validate_arcgis_package.py` after generating the ArcGIS Pro bundle
- external publishing is **opt-in, never auto-triggered**. Check `outputs.publish_targets` in the project brief; if `"arcgis_online"` is present, run `publish_arcgis_online.py --dry-run` first, review `publish-status.json`, then run without `--dry-run`
- default AGOL sharing is `PRIVATE`. Promote to `ORG` or `PUBLIC` only when the brief's `publish_sharing` explicitly requests it
