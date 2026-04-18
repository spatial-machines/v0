# Roadmap

Post-v1 direction. Nothing here is promised — this is what we think will matter most. Feedback from the `enterprise-ask` and `domain-request` GitHub issue tags can move items around.

## v1 (shipped) — recap

Nine-agent pipeline, 20+ data sources, four chart families, QGIS + ArcGIS Pro packages, ArcGIS Online publishing, solution graph, self-contained HTML report. See [OSS_RELEASE_PLAN.md](OSS_RELEASE_PLAN.md) for the full capability list.

---

## v1.1 — Embedded QGIS copilot (~3 months post v1)

**Why first:** pure Python, no proprietary deps, reach the entire ~300k QGIS user base through the official Plugin Repository.

**Scope:**

- `plugins/qgis/spatial_machines/` — QGIS 3.22+ plugin (`metadata.txt` + `__init__.py` + `plugin.py`)
- Dockable panel with a chat box; agent runs as a subprocess with the user's analysis folder as working directory
- Stages stream live to the panel via `runs/activity.log` (reuses the observability story — no new infra)
- On completion, every produced `.gpkg` loads into the active QGIS project with its `.style.json` sidecar applied via existing `write_qgis_project.build_qgs_from_gpkg()` logic
- Packaged as a `.zip` for the QGIS Plugin Repository and as a git checkout for advanced users

**Non-goals for v1.1:**
- Web-based UI (desktop only)
- Embedding arbitrary external LLMs (plugin drives the same CLI shim; LLM backend is the user's choice)

**Changes to core:** none. The plugin wraps existing CLI scripts.

---

## v1.2 — Embedded ArcGIS Pro copilot (~6 months post v1)

**Why second:** bigger engineering lift than QGIS, requires an Esri license to test, reaches the professional GIS market where Esri currently has a near-monopoly.

**Scope:**

- `plugins/arcgis_pro/spatial_machines.pyt` — Python toolbox (Pro's native extension format). One tool per common analysis pattern plus a generic "ask a question" tool.
- Optional .NET add-in for a better UI experience (parked until v1.3+ unless community contributes)
- Tool launches the agent (same CLI shim the QGIS plugin uses) and injects produced `.lyrx` layers into the active map via `arcpy.mp.MapView`
- Respects Pro's Python environment quirks (older bundled Python, environment cloning)

**Non-goals for v1.2:**
- ModelBuilder integration (Pro Tasks cover the common case)
- Custom ribbon tab (would require .NET)

**Changes to core:** minor — surface `renderers.py` sidecar helpers via a stable import path that toolboxes can rely on.

---

## v1.3 — MapLibre web-app generator (~9 months post v1)

**Why third:** replaces Esri's Experience Builder / StoryMaps for the community, complementary to v1.1/v1.2 (analyst loads data → Pro/QGIS copilot → generates web app for stakeholders).

**Scope:**

- `scripts/core/generate_web_app.py` — orchestrator; reads `analyses/<project>/outputs/` + brief + handoffs
- `templates/web_app/` — Tailwind + Alpine.js static template (no build step required); MapLibre GL JS for the map canvas
- `renderers.maplibre_renderer()` — extend the existing sidecar→renderer module with a MapLibre style-spec target, joining the QGIS/LYRX/AGOL parity matrix
- Static-site output; deploys to S3, GitHub Pages, Netlify, or any other static host via existing publishing-adapter stubs
- Optional ArcGIS JS SDK adapter for orgs already on Esri; same template, different map library
- Features: chart carousel, filter/search, deep-link state, inline data-downloads

**Non-goals for v1.3:**
- Server-side rendering / SSR
- Real-time collaborative editing
- Auth-gated data (free tier is for public datasets; private data pushes you to the Enterprise Pro tier)

**Changes to core:** `renderers.py` extension, new template tree, renderer parity tests expand to include MapLibre.

---

## Beyond v1.3 — candidates, not commitments

Ordered rough preference:

- **Streaming / incremental analyses** — retry-safe, resumable pipelines so a 30-minute county analysis doesn't restart from scratch when one fetch fails
- **Better spatial-stats** — GWR, spatial panel regression, Bayesian hierarchical models — via `mgwr` / `pymc-bayes`
- **3D / scene support** — CityGML, 3D Tiles, deck.gl layers for elevation-heavy analyses
- **GeoParquet-first pipelines** — replace GeoPackage intermediates with GeoParquet where that's faster (with fallback)
- **LLM-agnostic agent runtime** — current design already supports any agent that reads `CLAUDE.md` / `AGENTS.md`; formalise with an `agent-protocol.json` schema
- **Multi-analysis comparison** — side-by-side runs of the same question across different geographies or time periods

---

## How to influence this

- **GitHub issue tags** — `enterprise-ask` and `domain-request` are the primary demand signal channels. Label your issue honestly.
- **"Sponsor a data source" / "Sponsor a template"** — orgs can fund specific public work. Becomes part of the community edition when shipped.
- **Community Slack / Discord** `#analyst-requests` — moderated, read by product.
- **Pull requests welcome** — start a discussion issue first for anything larger than a fix.

See [COMMERCIAL_STRATEGY.md](../internal/COMMERCIAL_STRATEGY.md) (private) for the open-core strategy that funds the engineering behind this roadmap.
