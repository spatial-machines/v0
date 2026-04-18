# Patches

This file tracks customizations you (or your AI agent) have made to your fork of spatial-machines. It exists so that when the upstream project releases an update, your agent can read this file and intelligently re-apply your changes to the new version.

**This file is yours.** The upstream repo ships it empty. You fill it as you customize.

## How it works

1. You fork spatial-machines and start customizing it with your AI agent.
2. Every time you make a meaningful change, your agent documents it here.
3. When a new version of spatial-machines is released, you pull the update.
4. You tell your agent: "Re-apply my patches from PATCH.md to the new version."
5. Your agent reads the *intent* of each patch (not just the diff) and re-applies them intelligently, handling any conflicts with the new code.

## Format

For each customization, document:

```markdown
## [Short title]
- **Intent:** What this change accomplishes (one sentence)
- **Files modified:** List of files added or changed
- **Why:** Why you need this (your use case)
- **Depends on:** Any new dependencies added
- **Notes:** Anything an agent should know when re-applying this
```

## Example

```markdown
## Australian Bureau of Statistics data source
- **Intent:** Fetch ABS demographic data for Australian Statistical Areas
- **Files modified:** scripts/core/fetch_abs_data.py (new), config/data_sources.json (added entry)
- **Why:** I work with Australian geography and need ABS TableBuilder integration
- **Depends on:** requests, pandas (already in requirements)
- **Notes:** Uses the ABS Data API v2. Requires a free API key in .env as ABS_API_KEY.

## Dark basemap default
- **Intent:** All maps use CartoDB Dark Matter instead of the light basemap
- **Files modified:** config/map_styles.json (changed basemap_url in all profiles)
- **Why:** My presentations use dark backgrounds
- **Depends on:** None
- **Notes:** Only changes the default. The --basemap CLI flag still works for overrides.
```

---

## Your patches

<!-- Add your customizations below this line -->

## HTML reporter rebuild: modern parity + auto-caveats
- **Intent:** Replace the receipts-style `write_html_report.py` with a self-contained, client-ready HTML report that matches (and extends) the sedgwick demo's visual quality: executive summary, KPI hero cards, inline base64-embedded maps and charts, interactive-map iframe, and standard peer-reviewer-flagged caveats (MOE / proxy / causation / institutional) injected by default.
- **Files modified:** `scripts/core/write_html_report.py` (full rewrite; 278 lines → ~540; splits build into per-section helpers: header, executive_summary, kpis, maps_section, charts_section, interactive_map, methods, qa, caveats, alternatives, sources). Added `--analysis-dir` and `--project-brief` CLI flags; auto-infers analysis_dir when the manifest lives under `<analysis>/runs/`.
- **Why:** The old reporter produced an 8KB receipts-style page with a Methods section that was empty, a hardcoded boilerplate caveat about "demo dataset with 1.8% coverage," and no embedded imagery. Peer-review kept flagging missing MOE / proxy / causation / institutional caveats every run. This rebuild is the fix plus the visual quality bump — phila report went from 8KB skeleton to 4.9MB self-contained document with all 5 maps, 5 charts, interactive iframe, KPIs auto-derived from food_desert_demographics.csv (88 tracts / 410k residents / 25.9% / +5.4pp gap) and the pyramid lead from project_brief.json.
- **Depends on:** No new deps. Uses stdlib base64 + csv + html. Resolves asset paths against analysis_dir, analysis_dir.parent, PROJECT_ROOT, and PROJECT_ROOT/analyses so any of the three path conventions in existing manifests work.
- **Notes:** KPI auto-derivation has three tiers — (1) food-access domain KPIs from food_desert_demographics.csv, (2) generic descriptive KPIs from summary_stats.csv, (3) manifest-count fallback. Extend `_derive_kpis` with a new domain branch as new analysis domains are added. The 4 STANDARD_CAVEATS and 2 ALTERNATIVE_EXPLANATIONS are module-level constants; curate them as the peer-reviewer feedback evolves. `collect_report_assets.py` wasn't touched — this rebuild consumes its existing manifest format.

## Categorical support in analyze_choropleth + overlay polish
- **Intent:** Fold two one-off cartography helpers back into core: add `--categorical` mode to `analyze_choropleth.py` (for USDA LILA flags, risk tiers, hotspot classes) and teach `overlay_points.py` to use the style registry's palette + write a sidecar that the QGIS + ArcGIS packagers recognize.
- **Files modified:** `scripts/core/analyze_choropleth.py` (added `--categorical`, `--category-colors`, `--category-order` CLI flags; added `_render_categorical` helper + `_parse_category_colors` JSON/file loader; dispatches early when field is non-numeric OR flag is set). `scripts/core/overlay_points.py` (added `--attribution`, `--point-label`, `--no-sidecar` flags; routed palette through `resolve_palette()`; computes explicit breaks via mapclassify; writes a `map_family=point_overlay` sidecar with `source_gpkg`, `field`, `palette`, `breaks`, `colors_rgb`, and point-layer metadata). Deleted `analyses/philadelphia-food-access/_scripts/` (both one-off helpers).
- **Why:** Philadelphia's food_desert categorical map and supermarket overlay were made by hand-written helpers because the core scripts couldn't handle a categorical LILA flag or emit a sidecar the packagers could match. That created two problems: the maps didn't get into the ArcGIS/QGIS packages styled, and future analyses with similar needs would have to repeat the one-off work.
- **Depends on:** Existing `style_utils.resolve_palette`, `write_style_sidecar` (already accepts `categorical_map`).
- **Notes:** `--category-colors` accepts either inline JSON or a path to a JSON file (auto-detected by leading `{`/`[`). The categorical branch in `analyze_choropleth.py` preserves all the cartographic contract features (dissolved outline, title, attribution, basemap, labels) — it's a sibling of the numeric branch, not a downgrade. Re-applying after an upstream update: if upstream added a different categorical path, merge the best of both; the sidecar schema (`classification: "categorical"`, `categorical_map`) must match what the ArcGIS matcher (`_plan_lyrx_from_sidecars`) and the QGIS `_build_categorized_renderer` expect.

## ArcGIS Pro packager: sidecar-driven .lyrx matching
- **Intent:** Make the ArcGIS Pro packager actually produce `.lyrx` files by iterating sidecars (not feature classes) and matching via `source_gpkg`/`source_layer` or `field` column presence.
- **Files modified:** `scripts/core/package_arcgis_pro.py` (replaced `_find_sidecar_for_layer` with `_sidecar_source_stem` + `_plan_lyrx_from_sidecars`; rewrote the `.lyrx` production block to drive off the plan; also added `encoding="utf-8"` to all `write_text` calls to fix cp1252 crashes on Windows).
- **Why:** Sidecars are named after MAPS (`poverty_rate_choropleth.style.json`), feature classes are named after SOURCE DATA (`phila_tracts_enriched`). The old matcher tried 3 heuristics on the layer name and failed on all of them — Philadelphia's full pipeline produced 0 `.lyrx`. New matcher uses the explicit `source_gpkg` / `source_layer` keys cartography already writes to sidecars, falling back to `field` column presence on the FC column set.
- **Depends on:** None new. Requires sidecars to declare `source_gpkg` (choropleth scripts already do) or `field` (most do).
- **Notes:** Match result is recorded as `match_via` in `review-spec.json#lyrx_layers`, so reviewers can audit which sidecars landed and which didn't. Warnings name the specific sidecar that failed and why (field-not-on-any-FC vs no-source-or-field) — each warning is actionable. The pass-3 categorical fallback is narrow: only triggers when a sidecar has no field AND a categorical_map, preventing false positives (early version wrongly matched food_desert_tracts → hotspots_poverty because both had category-flavored columns).

## AGOL adapter: GDB-only REST publishing + subscription/scope diagnostics
- **Intent:** Narrow the ArcGIS Online publishing scope to "one File Geodatabase → one hosted Feature Service → one Web Map," dropping the prior PNG / chart / HTML mirror logic; rewrite the adapter to call AGOL's REST endpoints directly (no `arcgis` Python dependency); detect AGOL's silent `/publish` no-op (Location Platform subscription tier or insufficient API key scope) and emit an actionable error rather than the cryptic "no services" message; auto-clean orphan GDB items when publish fails so re-runs don't pile up dead source items.
- **Files modified:** `scripts/core/publishing/arcgis_online.py` (replaced gpkg-loop + image/report uploads with `_resolve_gdb_path` → `_zip_gdb` → `_upload_file_geodatabase` → `_publish_gdb_to_service` → `_fetch_service_layers` → `_match_layers_to_sidecars` → per-layer `updateDefinition` → multi-layer Web Map; ported sidecar-matching from `package_arcgis_pro._plan_lyrx_from_sidecars`; added `_introspect_gdb_fcs` GDAL-or-gpkg-fallback; added `_check_subscription_supports_hosting` probe; reordered credential precedence to prefer USER+PASSWORD over API key; kept the old `_upload_image`, `_upload_report`, `_upload_geopackage`, `_build_web_map`, `_plan_items`, `_match_sidecar` helpers DORMANT in case a future sharing mode wants them; added `delete_item` for orphan cleanup). `scripts/core/publish_arcgis_online.py` (CLI now requires GDB to exist before any AGOL call, prints a clear "run package_arcgis_pro.py first" error if missing; dropped `--style-dir` defaulting to maps/, dropped collection of map_pngs/chart_pngs/report_html, added `--gdb` override). `docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md` (rewrote to match the GDB-only flow; replaced the misdiagnosed API-key-scope-only troubleshooting with the subscription-tier-first diagnosis discovered live; documented the iteration loop: package → dry-run → publish → spot-check → teardown). `scripts/core/teardown_agol.py` (new — already existed prior to this patch but is part of the iteration loop).
- **Why:** The prior adapter used the `arcgis` Python package which has chronic distutils / ssl_context bugs; rewriting to REST gives us a stable, dependency-light adapter we control end-to-end. The scope decision (drop PNG/chart/HTML mirror) was made because AGOL's strength is hosted feature layers + Web Maps — duplicating image and report uploads to AGOL didn't add stakeholder value over the local HTML report and was burning credits unnecessarily. The subscription / scope diagnostics came from a real debugging session where `/publish` silently returned `{item, sharing}` instead of `{services}` for a Location Platform developer subscription — AGOL accepts the upload, accepts `/analyze`, and then no-ops `/publish` with no error. Without the diagnostic, the only signal was "publish returned no services," which sent us down API-key-scope and zip-structure rabbit holes for an hour.
- **Depends on:** `requests` (already in core), `osgeo.ogr` optionally (falls back to gpkg-copy enumeration via stdlib `sqlite3` when GDAL isn't importable in the venv).
- **Notes:** The adapter is fully verified architecturally but live publish is gated on having an ArcGIS Online subscription (not Location Platform). The 21-day AGOL trial covers the full publishing flow for verification; current account is on the free Developer / Location Platform tier which doesn't include hosted feature service publishing. When re-applying after an upstream update: keep the dormant helpers in place if upstream still calls them; reconcile sidecar-matching logic with `package_arcgis_pro._plan_lyrx_from_sidecars` if upstream changed the matching heuristic (the two should stay in sync — they're the same matching, applied to two different consumers). The `_check_subscription_supports_hosting` probe uses the public `subscriptionInfo.type` field; if Esri renames the tier in the future, update the substring match.

## QGIS packager hybrid: in-process PyQGIS or subprocess fallback
- **Intent:** Let `package_qgis_review.py` produce a styled `.qgs` even when run under a regular pip venv that can't `import qgis.core`; auto-discover an installed QGIS and spawn `write_qgis_project.py` as a subprocess under its python.
- **Files modified:** `scripts/core/qgis_env.py` (new), `scripts/core/package_qgis_review.py` (replaced in-process build call with `build_qgs_hybrid`; also fixed cp1252 encoding crashes on README/notes/spec writes by adding `encoding="utf-8"`).
- **Why:** Pipeline runs happen under the project venv. PyQGIS isn't pip-installable — it ships with QGIS itself — so the packager was silently shipping .qgs-less packages. `demo.py` had already solved this with `_find_qgis_python()` but only for the demo path; the pipeline packager needed the same capability.
- **Depends on:** None new. Requires QGIS (any of OSGeo4W, QGIS standalone installer, macOS QGIS.app, Linux `python3-qgis`) installed somewhere on the system. If no QGIS is found, `build_qgs_hybrid` returns `{"path": "failed", ...}` with a clear message and the rest of the package still ships (gpkgs + review-spec + notes + manifest).
- **Notes:** `qgis_env.find_qgis_python()` probes `$QGIS_PYTHON` → current interpreter → Windows/macOS/Linux default install locations, preferring LTR. `build_qgs_hybrid` returns `path: "in-process" | "subprocess" | "failed"` and `interpreter:` for observability. Surfaces through the packager result as `qgs_generation_path` and `qgs_interpreter`. When re-applying after an upstream update, ensure `demo.py`'s private `_find_qgis_python()` and `qgis_env.find_qgis_python()` don't both exist — ideally `demo.py` imports from `qgis_env` (not yet done here; deferred).
