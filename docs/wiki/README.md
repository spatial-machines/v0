# Wiki

The wiki is the **source of truth for reusable GIS methodology**. Every agent reads the relevant wiki pages before it acts. If you're extending spatial-machines for your firm, this is also where your standards live — add your own pages here and your fork's agents will use them.

Think of the wiki as:

- a **methods library** — how to do the work
- a **standards manual** — what "good" looks like
- a **workflow directory** — which step comes next, with which script
- a **QA handbook** — what to check before you ship
- a **data-source catalog** — authoritative guides per source
- a **training system** for humans and agents

See [`docs/architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) for the wiki's role in the three-layer knowledge / agents / scripts stack.

## Layout

| Subdir | Count | Purpose |
|---|---|---|
| [`standards/`](standards/) | 16 | Firm-wide rules — mandatory, enforced by agents |
| [`workflows/`](workflows/) | 33 | Step-by-step playbooks for specific operations |
| [`domains/`](domains/) | 40 | Domain-specific methodology (healthcare access, food access, hazards, equity, …) |
| [`data-sources/`](data-sources/) | 25 | Authoritative guides per data source |
| [`qa-review/`](qa-review/) | 13 | Validation checklists and review gates |
| [`toolkits/`](toolkits/) | 6 | Tool references (GDAL, GeoPandas, PostGIS, Rasterio, WhiteboxTools, ArcGIS Python API) |

## Start here: the must-reads

These pages are referenced by name from [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md), and the agent role definitions. They're the most-read wiki pages and the ones most likely to apply to any analysis.

### Standards (enforceable)
- [**CARTOGRAPHY_STANDARD**](standards/CARTOGRAPHY_STANDARD.md) — read before any map. Map family taxonomy, typography, palette rules, accessibility.
- [**CHART_DESIGN_STANDARD**](standards/CHART_DESIGN_STANDARD.md) — read before any chart. Chart family taxonomy, pairing rule (every choropleth gets a paired distribution + top-N chart), typography.
- [**SPATIAL_STATS_STANDARD**](standards/SPATIAL_STATS_STANDARD.md) — read before any local spatial analysis. Moran's I gate, FDR correction, MOE handling.
- [**CRS_SELECTION_STANDARD**](standards/CRS_SELECTION_STANDARD.md) — geographic (EPSG:4269) vs projected (EPSG:5070) and when each applies.
- [**STRUCTURAL_QA_STANDARD**](standards/STRUCTURAL_QA_STANDARD.md) — the mandatory validation gates.
- [**PROVENANCE_AND_HANDOFF_STANDARD**](standards/PROVENANCE_AND_HANDOFF_STANDARD.md) — what every pipeline handoff must record.
- [**ARCGIS_PRO_PACKAGE_STANDARD**](standards/ARCGIS_PRO_PACKAGE_STANDARD.md) — what the ArcGIS Pro package guarantees.
- [**PUBLISHING_READINESS_STANDARD**](standards/PUBLISHING_READINESS_STANDARD.md) — ship / don't-ship criteria.
- [**INTERPRETIVE_REVIEW_STANDARD**](standards/INTERPRETIVE_REVIEW_STANDARD.md) — what the peer-reviewer agent checks.

### Workflows (operational playbooks)
- [**LEAD_ANALYST_ORCHESTRATION**](workflows/LEAD_ANALYST_ORCHESTRATION.md) — how the pipeline is assembled per request.
- [**GENERAL_RETRIEVAL_AND_PROVENANCE**](workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md) — data retrieval from scratch.
- [**GENERAL_PROCESSING_AND_STANDARDIZATION**](workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md) — raw → analysis-ready.
- [**GENERAL_ANALYSIS_AND_OUTPUT_GENERATION**](workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md) — running the actual analysis.
- [**VALIDATION_AND_QA_STAGE**](workflows/VALIDATION_AND_QA_STAGE.md) — structural QA gates.
- [**REPORTING_AND_DELIVERY**](workflows/REPORTING_AND_DELIVERY.md) — report assembly.
- [**QGIS_HANDOFF_PACKAGING**](workflows/QGIS_HANDOFF_PACKAGING.md) — how the QGIS package is built.
- [**ARCGIS_ONLINE_PUBLISHING**](workflows/ARCGIS_ONLINE_PUBLISHING.md) — opt-in AGOL adapter, subscription-tier notes.
- [**CHOROPLETH_DESIGN**](workflows/CHOROPLETH_DESIGN.md) · [**BIVARIATE_CHOROPLETH_DESIGN**](workflows/BIVARIATE_CHOROPLETH_DESIGN.md) · [**HOTSPOT_MAP_DESIGN**](workflows/HOTSPOT_MAP_DESIGN.md) · [**POINT_OVERLAY_DESIGN**](workflows/POINT_OVERLAY_DESIGN.md) — family-specific map playbooks.

### Domains (worth a read when the request touches them)
- [**DEMOGRAPHICS_AND_MARKET_ANALYSIS**](domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md)
- [**CLIMATE_RISK_AND_RESILIENCE**](domains/CLIMATE_RISK_AND_RESILIENCE.md)
- [**CRIME_PUBLIC_SAFETY_AND_INCIDENT_MAPPING**](domains/CRIME_PUBLIC_SAFETY_AND_INCIDENT_MAPPING.md)
- [**DISASTER_RESPONSE_AND_RECOVERY_SUPPORT**](domains/DISASTER_RESPONSE_AND_RECOVERY_SUPPORT.md)
- [**ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS**](domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md)
- Browse the rest at [`domains/`](domains/).

### Data sources (guides per source)
- [**CENSUS_ACS**](data-sources/CENSUS_ACS.md) · [**CDC_PLACES**](data-sources/CDC_PLACES.md) · [**EPA_EJSCREEN**](data-sources/EPA_EJSCREEN.md) · [**FEMA_NFHL**](data-sources/FEMA_NFHL.md) · [**NOAA_CLIMATE**](data-sources/NOAA_CLIMATE.md) · [**HUD_HOUSING**](data-sources/HUD_HOUSING.md) · [**LEHD_LODES**](data-sources/LEHD_LODES.md) · [**GTFS_TRANSIT**](data-sources/GTFS_TRANSIT.md) — full list at [`data-sources/`](data-sources/).

### QA checklists
- [**MAP_QA_CHECKLIST**](qa-review/MAP_QA_CHECKLIST.md) — final visual check before delivery.
- [**STRUCTURAL_QA_CHECKLIST**](qa-review/STRUCTURAL_QA_CHECKLIST.md) — validation-gate checklist.
- [**INTERPRETIVE_REVIEW_CHECKLIST**](qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md) — peer-review criteria.
- Full list at [`qa-review/`](qa-review/).

### Toolkits (per tool reference)
- [**GEOPANDAS_TOOLKIT**](toolkits/GEOPANDAS_TOOLKIT.md) · [**GDAL_OGR_TOOLKIT**](toolkits/GDAL_OGR_TOOLKIT.md) · [**POSTGIS_TOOLKIT**](toolkits/POSTGIS_TOOLKIT.md) · [**RASTERIO_TOOLKIT**](toolkits/RASTERIO_TOOLKIT.md) · [**WHITEBOXTOOLS_TOOLKIT**](toolkits/WHITEBOXTOOLS_TOOLKIT.md) · [**ARCGIS_PYTHON_API**](toolkits/ARCGIS_PYTHON_API.md).

## Contributing to the wiki

Your fork's wiki is how your firm's knowledge becomes agent-usable. To add a page:

1. **Pick the right subdir.** New data source → `data-sources/`. New method family → `workflows/`. New hard rule → `standards/`. New domain playbook → `domains/`. New tool guide → `toolkits/`. New QA list → `qa-review/`.
2. **Use the naming convention.** UPPER_SNAKE_CASE.md (e.g., `HEAT_VULNERABILITY_INDEX.md`).
3. **Follow the existing page template.** Each subdir's pages follow a consistent structure — read a neighbor before you write.
4. **Reference the page from the relevant agent's SOUL.md or TOOLS.md** if it should be read before certain work.
5. **Document the addition in `PATCH.md`** — this is how your customizations survive upstream updates. See [PATCH.md](../../PATCH.md).

Contributions welcome upstream too — especially new domain playbooks and new data source guides. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Design principles (short version)

1. **Workflow first, tool second.** Describe what to do, in what order, with what prerequisites. Don't just dump the tool's man page.
2. **Separate universal standards from project decisions.** Reusable logic belongs here; one-off client decisions belong in the project brief.
3. **Capture trust explicitly.** Mark each page as production standard, validated playbook, draft workflow, or research note.
4. **Repeatable procedures over prose essays.** The agent reads this. Give it clear steps.
5. **Tables and lists over paragraphs** for lookup content. Keep narrative for the "why" sections only.
