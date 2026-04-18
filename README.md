# spatial-machines

A multi-agent GIS pipeline that runs on your laptop. Apache-2.0.

**Site:** [sm.touchgrass.design](https://sm.touchgrass.design)

This is the technical reference for the repo. For the pitch and output preview, see the site.

---

## What it is

Nine specialist agents running sequentially as a pipeline: lead analyst, retrieval, processing, spatial stats, cartography, QA, reporting, publishing, peer review. You type a spatial question into your coding agent. The pipeline reads from 134 pages of encoded methodology and runs 155 production scripts. You get styled maps, an interactive web map, a narrative HTML report, a QGIS project, and an ArcGIS Pro package.

Each stage writes a structured handoff the next stage reads. Retrieval finishes before processing starts. Processing finishes before the statistician sees it. The agents work sequentially.

You pick the story. The agents do the drudgery.

---

## Install

You need Python 3.11+, a terminal, and an AI coding agent.

### 1. Install Python 3.11 or newer

| Platform | Easiest path |
|---|---|
| Windows | Microsoft Store → search "Python 3.12" → Install. Or [python.org](https://www.python.org/downloads/) (check "Add python.exe to PATH"). |
| macOS | `brew install python@3.12`. Or [python.org](https://www.python.org/downloads/). |
| Linux / WSL | `sudo apt install python3.12 python3.12-venv`. |

Verify: `python --version` (Windows) or `python3 --version` (macOS/Linux). 3.11.x or higher.

### 2. Clone, create a venv, install deps

```bash
git clone https://github.com/spatial-machines/v0.git spatial-machines
cd spatial-machines
```

A venv is a private Python sandbox for this project. Don't skip it.

```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Windows (cmd)
python -m venv venv
venv\Scripts\activate.bat

# macOS / Linux / WSL
python3 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` at the start of your prompt. Re-run the activate line in any new terminal.

```bash
pip install -r requirements.txt
```

First install takes a couple minutes (geopandas, matplotlib, fiona). Cached after.

> PowerShell blocking the activate script? Run this once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 3. Copy the env template

```bash
cp .env.example .env        # macOS / Linux / WSL
copy .env.example .env      # Windows
```

Census-only analyses work with zero keys. The `.env` is for optional sources (NOAA, CDC, FBI, USDA, etc.). Signup links are inside the file. All free.

### 4. Install a coding agent

| Agent | Install |
|---|---|
| Claude Code (Anthropic) | `npm i -g @anthropic-ai/claude-code` or [claude.ai/claude-code](https://claude.ai/claude-code) |
| Codex CLI (OpenAI) | `npm i -g @openai/codex` |
| OpenCode | [opencode.ai](https://opencode.ai) |
| Cursor / Windsurf / Aider | Open the repo in your tool |

Each agent reads its matching entry file (`CLAUDE.md` or `AGENTS.md`) on its own. From inside the repo with your venv active, launch the agent and start talking.

### Verify install without an agent

```bash
make demo            # or: python demo.py
```

Runs a 10-second poverty analysis on bundled Census data for Sedgwick County, KS. Opens an HTML report. No keys, no internet, no agent. Confirms Python and dependencies are happy.

---

## Your first prompt

Inside the repo, with your venv active, launch your coding agent and type:

```
What does poverty look like in Cook County, Illinois?
```

Or:

```
Map median household income for every census tract in Harris County, TX,
and tell me which neighborhoods are statistical hot spots.
```

Or:

```
I'm writing a grant for a rural health clinic in eastern Kentucky.
Build me a needs assessment: uninsured rate, poverty rate, distance
to nearest hospital, chronic disease burden at the tract level.
Include uncertainty maps for ACS estimates with high MOEs.
```

The agent scopes, plans, fetches, processes, analyzes, renders, validates, peer-reviews, and synthesizes. Usually 5 to 20 minutes depending on data volume. You see every decision narrated as it happens.

---

## How it works

Three layers:

```
   ┌──────────────────────────────────────────────┐
   │  KNOWLEDGE — docs/wiki/  (134 pages)         │  ← what to do, when
   │  standards, domains, workflows, data guides  │
   └──────────────────────────────────────────────┘
                          │
   ┌──────────────────────────────────────────────┐
   │  AGENTS — agents/  (9 specialists)           │  ← who decides
   │  lead, retrieval, processing, stats,         │
   │  cartography, validation, report, publish,   │
   │  peer-review                                 │
   └──────────────────────────────────────────────┘
                          │
   ┌──────────────────────────────────────────────┐
   │  TOOLS — scripts/core/  (155 Python scripts) │  ← how to do it
   │  fetch_acs_data, analyze_choropleth,         │
   │  compute_hotspots, package_arcgis_pro, …     │
   └──────────────────────────────────────────────┘
```

The **wiki** is knowledge. 134 pages of standards (cartography, spatial stats, CRS, QA), domain playbooks (food access, healthcare, hazards, equity), and authoritative data-source guides. It's how the system knows a poverty-rate field gets a YlOrRd palette, that LISA results need FDR correction, that a food-access analysis should overlay supermarkets and skip water features.

The **agents** are 9 role-specialists. Each has a `SOUL.md` (mission, non-negotiables) and a `TOOLS.md` (approved scripts). The Lead Analyst orchestrates. The others execute their stage. Every handoff is a JSON artifact you can inspect.

The **scripts** are 155 production tools with standardized interfaces. Every visual writes a `.style.json` sidecar so QGIS, ArcGIS Pro, and ArcGIS Online deliverables all render from one source of truth.

---

## Make it yours

Fork it. The repo is designed to be extended by the same agents that run it.

Need a fetch script for an API your team uses? Ask your agent. It writes the code, registers it in `config/data_sources.json`, documents it, and wires it into the retrieval role. You review the diff.

Customizations land in `PATCH.md`: intent, files touched, why. When upstream ships an update, pull, and your agent re-applies your patches by reading the recorded intent. Your work survives updates.

| Want to... | Change |
|---|---|
| Add a data source | Write `fetch_<source>.py` (see [pattern](docs/extending/ADDING_DATA_SOURCES.md)), register in `config/data_sources.json` |
| Encode your firm's domain methodology | Add a page to `docs/wiki/domains/` |
| Change default map styles | Edit `config/map_styles.json` |
| Connect PostGIS / SDE / AGOL / GeoServer | See `docs/extending/CONNECTING_INFRASTRUCTURE.md` |
| Build a publishing adapter | Implement `publishing.base.PublishAdapter`. See [`scripts/core/publishing/arcgis_online.py`](scripts/core/publishing/arcgis_online.py) as reference |
| Add a new agent role | Drop a directory in `agents/<role>/` with `SOUL.md` and `TOOLS.md` |
| Change cartography rules | Edit `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` |

---

## What it produces

Every run writes to `analyses/<project>/outputs/`:

- **Maps**: choropleth, bivariate (3×3 Stevens), hotspot, LISA, point overlay, dot density, proportional symbol, small multiples, uncertainty. 200 DPI, colorblind-checked, with `.style.json` sidecars.
- **Charts**: distribution, comparison, relationship, time series. PNG and SVG.
- **Interactive web maps**: Folium with toggleable layers, popups, multiple basemaps.
- **QGIS package**: `.qgs` project with graduated/categorized renderers, basemap, auto-zoom, print layout template.
- **ArcGIS Pro package**: file geodatabase, styled `.lyrx` files, `make_aprx.py` helper. No Esri license required to produce. If `arcpy` is available locally, a full `.aprx` is pre-built.
- **ArcGIS Online (opt-in)**: uploads the GDB, publishes a hosted Feature Service, applies sidecar renderers, builds a Web Map. Default sharing is PRIVATE. See the [workflow doc](docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md) for subscription-tier notes.
- **Narrative report**: self-contained HTML with exec summary, KPIs, embedded visuals, methodology, caveats, sources.
- **Solution graph**: DAG of every input, operation, and output. PNG, SVG, JSON, Mermaid.
- **QA scorecards, data dictionaries, provenance records, handoff JSON**.

---

## The nine agents

| Agent | Role |
|---|---|
| Lead Analyst | Orchestrates the pipeline, scopes work, integrates and synthesizes |
| Data Retrieval | Acquires data from 20+ built-in sources |
| Data Processing | Cleans, normalizes, joins into analysis-ready GeoPackages with provenance |
| Spatial Stats | Hotspot (Gi*), LISA, Moran's I, change detection. FDR correction by default |
| Cartography | Maps and statistical charts |
| Validation QA | Geometry, join rates, null values, structural integrity gates |
| Report Writer | Pyramid Principle reports (answer first). HTML + Markdown |
| Site Publisher | QGIS package, ArcGIS Pro package, optional AGOL publishing |
| Peer Reviewer | Independent gate for unsupported claims, overconfidence, missing caveats |

Each agent has `agents/<role>/SOUL.md` (mission, non-negotiables) and `agents/<role>/TOOLS.md` (approved scripts).

---

## Built-in data sources

| Category | Sources | Auth |
|---|---|---|
| Demographics | Census ACS, Decennial Population, TIGER, LEHD/LODES | Free key optional |
| Health | CDC PLACES, EPA EJScreen | None |
| Food & housing | USDA Food Access Atlas, HUD Fair Market Rents | Free key optional |
| Hazards & climate | FEMA Flood Zones, NOAA Climate, OpenWeatherMap | Free keys |
| Economic & safety | BLS employment, FBI crime | Free keys |
| Places & POI | OpenStreetMap (Overpass), Overture Maps | None |
| Terrain | USGS National Map (DEM) | None |
| Transit | GTFS feeds | None |
| Open data | Socrata (thousands of city/county/state portals) | Optional token |
| Generic | Any URL, any local file (GPKG, SHP, CSV, GeoJSON) | None |

Full registry: [`config/data_sources.json`](config/data_sources.json). Add your own: [`docs/extending/ADDING_DATA_SOURCES.md`](docs/extending/ADDING_DATA_SOURCES.md).

---

## What's in the repo

```
spatial-machines/
├── CLAUDE.md            ← Claude Code entry point
├── AGENTS.md            ← Agent-agnostic orchestration guide
├── PATCH.md             ← Your customization log (starts empty)
├── demo.py              ← Standalone demo
├── Makefile             ← `make demo`, `make verify`
├── .env.example         ← API key template (all free sources)
├── requirements.txt
├── agents/              ← 9 specialist role definitions
├── docs/
│   ├── wiki/            ← 134 pages of canonical GIS methodology
│   │   ├── standards/   ← cartography, charts, spatial-stats, CRS, QA
│   │   ├── workflows/   ← step-by-step playbooks
│   │   ├── domains/     ← healthcare, food access, equity, hazards
│   │   ├── data-sources/← authoritative source guides
│   │   └── toolkits/    ← GDAL, GeoPandas, PostGIS, Rasterio
│   ├── architecture/    ← pipeline canon, tool governance
│   ├── reference/       ← TEAM.md, PIPELINE_STANDARDS.md
│   ├── guides/          ← INSTALL, ANALYST_GUIDE, TROUBLESHOOTING
│   └── extending/       ← add data sources, infrastructure, adapters
├── scripts/core/        ← 155 production scripts
├── config/              ← style registries, palettes, data sources
├── templates/           ← project brief, report, QGIS, ArcGIS templates
├── tests/               ← pytest suite
├── demos/               ← pre-rendered no-install previews
└── analyses/            ← your work goes here
```

---

## Documentation

- **[Wiki](docs/wiki/):** 134 pages the agents consult before every analysis
- **[Architecture](docs/architecture/ARCHITECTURE.md):** how the 9-agent system is organized
- **[Pipeline Standards](docs/reference/PIPELINE_STANDARDS.md):** mandatory output quality standards
- **[Cartography Standard](docs/wiki/standards/CARTOGRAPHY_STANDARD.md):** full map family taxonomy and design rules
- **[Chart Design Standard](docs/wiki/standards/CHART_DESIGN_STANDARD.md):** mandatory rules for statistical charts
- **[ArcGIS Pro Package Standard](docs/wiki/standards/ARCGIS_PRO_PACKAGE_STANDARD.md):** what the `.gdb` + `.lyrx` bundle guarantees
- **[ArcGIS Online Publishing](docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md):** opt-in AGOL workflow + subscription notes
- **[Install Guide](docs/guides/INSTALL.md):** deeper setup (GDAL on Windows, PostGIS, etc.)
- **[Troubleshooting](docs/guides/TROUBLESHOOTING.md)**
- **[Extending](docs/extending/):** data sources, infrastructure, adapters
- **[Contributing](CONTRIBUTING.md)**

---

## License + acknowledgments

Apache-2.0. See [LICENSE](LICENSE).

"spatial-machines" is a trademark. Forks must use a different name. See [TRADEMARK.md](TRADEMARK.md). The PATCH.md model means you can run a customized fork of your own without renaming; published forks ship under your own name.

The GIS tool registry (`scripts/tool-registry/`) is built on research from the [SpatialAnalysisAgent](https://github.com/Teakinboyewa/SpatialAnalysisAgent) project by Akinboyewa et al. at Penn State. The solution-graph concept comes from the autonomous-GIS prototype by Ning et al. (*International Journal of Digital Earth*, 2023):

> Ning, H., Li, Z., Akinboyewa, T., & Lessani, M. N. (2023). *An autonomous GIS agent framework for geospatial data retrieval.* doi:10.1080/17538947.2023.2278895
>
> Akinboyewa, T., Xu, Z., Huan, X., & Li, Z. (2024). *GIS Copilot: Towards an Autonomous GIS Agent for Spatial Analysis.* doi:10.1080/17538947.2025.2497489

Under GPL-3.0 where applicable.
