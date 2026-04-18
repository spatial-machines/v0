# spatial-machines

A decade in GIS. The part of the job I trained for — looking at a map and *thinking*, talking to a client about what they're really asking, iterating on a design until it tells the story — kept getting squeezed by the part nobody asks about: finding the right Census table, fixing CRS mismatches, re-projecting someone's badly-exported shapefile, joining tract IDs that wouldn't join, restyling a legend for the fourth time, formatting exports for a colleague's Pro template.

I built this to get that time back.

**spatial-machines** is an AI-coding-agent playbook for GIS. You write a question in plain English. The agent (Claude Code, Codex CLI, whatever you use) reads the project's wiki, fetches the data, processes it, runs the stats, draws the maps, makes the charts, packages the deliverable for QGIS *and* ArcGIS Pro *and* (optionally) ArcGIS Online, writes the report, and hands you back a folder you can use. Then you and the agent iterate until the map tells the truth.

It's not magic. It's 9 specialist agent roles, 134 pages of methodology I wish someone had handed me on day one, and 155 production scripts broken and fixed on real analyses. The drudgery is automated. The cartographic decisions, the story, the conversation stay with you.

> Better than Esri's docs is the bar.

---

## Who this is actually for

I built this because the people who *should* be doing GIS — public servants, local planners, journalists, students, lonely-GIS-team-of-one consultants — are getting pushed out of the field by tooling that costs too much, takes too long to learn, and rewards button-clicking over thinking.

| You are... | What changes for you |
|---|---|
| **A GIS team of 1–2** | Ship deliverables that look like you have a senior cartographer on staff. Styled `.lyrx` for the Pro user on the team, an HTML report for the client, a Web Map URL for the dashboard. Iterate on a draft in 30 minutes instead of three days. |
| **A local government employee** (planner, public health, public works) | Run the equity / hazard / access analyses your council keeps asking for, without waiting six weeks on the regional GIS contractor. Standard methodology, defensible outputs, audit trail you can hand to anyone who asks "why did you choose those breaks?" |
| **A journalist or researcher** | Get to the map and the statistic without becoming a GIS expert first. Every figure has a sidecar tracing it back to the data and the choices made. If your editor asks where a number came from, you have the receipt. |
| **A student or early-career analyst** | Read the wiki to learn how a senior cartographer thinks about palette choice, classification, and uncertainty. Read the scripts to see how the tools actually work. Modify a palette, ask the agent to redo it, watch what happens. The system *is* the textbook. |
| **An educator** | Set up the repo once, give your class a prompt, every student gets a complete project to dissect. The PATCH.md model means students can fork and customize without breaking anything. |
| **A GIS contractor / freelancer** | Cut your time-to-first-draft from days to hours. Spend the hours you saved on the part that earns the invoice — the conversation with your client. |

**This is NOT for you if** you only ever need one map, you already have ArcGIS Pro open with a project that works, and you're billing by the hour. Just open Pro.

It's also not the right tool yet for **pure raster work at scale** — elevation, NDVI, lidar workflows are supported, but vector and choropleth are where the system shines. v2 will fix that.

And if you want a button-you-click product, **wait**. There's a QGIS plugin coming in v1.1 that wraps the prompt UX. Today, this is a coding-agent-driven system. You'll see Python tracebacks occasionally. If that's a dealbreaker, give it a season.

---

## What this actually does, in 60 seconds

You install [Claude Code](https://claude.ai/claude-code) (or Codex CLI, or any agent that reads markdown). You clone this repo. You activate a Python venv. You type:

> *"Map median household income for every census tract in Harris County, TX, and tell me which neighborhoods are statistical hot spots."*

15 minutes later, in `analyses/<your-project>/outputs/`:

- a **styled choropleth map** — palette auto-selected from the field name (the system knows `median_income` wants YlGnBu), breaks chosen statistically, colorblind-checked, with the legend and inset locator placed where they don't fight the data
- a paired **distribution chart** that shows the spread the map can't, with mean/median lines
- a **hotspot map** computed via Getis-Ord Gi*, with FDR correction and Moran's I gating (so you don't publish noise)
- a **QGIS project** (`.qgs`) that opens with the same styling
- an **ArcGIS Pro package** — file geodatabase + styled `.lyrx` files + a helper script that auto-builds an `.aprx` inside Pro
- an **interactive web map** in your browser, with toggleable layers and popups
- a **narrative HTML report** — exec summary, KPIs, embedded visuals, methodology, caveats, sources, all self-contained
- a **QA scorecard** + an **independent peer review** of the work
- a **solution graph** — the DAG of every input, operation, and output for the run

You didn't pick the palette. You didn't decide the breaks. You didn't write the report outline. The system applied 134 pages of wiki-encoded standards because it knew what kind of question you asked.

This is the kind of deliverable I used to spend three days on. Now I get a draft in 15 minutes, and I spend the saved time on the part that actually matters — *iterating on the design with the client in the room.*

---

## See it before you install

Open **`demos/sedgwick-poverty/preview.html`** in any browser. No Python, no agent, no setup — just a styled map, a chart, and the report scaffold from a real run on Sedgwick County poverty data. The PNGs in `demos/sedgwick-poverty/samples/` are the same outputs unpacked.

That's the bar for what one prompt produces. If it looks worth 10 minutes of setup, the install is below.

---

## Get it running in 10 minutes

You need three things: **Python 3.11+**, a **terminal**, and an **AI coding agent**. Four steps.

### 1 — Install Python 3.11 or newer

| Platform | Easiest path |
|---|---|
| **Windows** | Microsoft Store → search "Python 3.12" → Install. Or [python.org](https://www.python.org/downloads/) (check "Add python.exe to PATH"). |
| **macOS** | `brew install python@3.12` (install Homebrew first from [brew.sh](https://brew.sh/)). Or [python.org](https://www.python.org/downloads/). |
| **Linux / WSL** | `sudo apt install python3.12 python3.12-venv` or your distro's equivalent. |

Verify: `python --version` (Windows) or `python3 --version` (macOS/Linux). You want `3.11.x` or higher.

### 2 — Clone, create a venv, install deps

```bash
git clone https://github.com/spatial-machines/spatial-machines.git
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

You'll see `(venv)` at the start of your prompt — that's how you know it's active. Re-run the activate line in any new terminal.

```bash
pip install -r requirements.txt
```

First time takes a couple minutes (geopandas, matplotlib, fiona, etc.). Cached after.

> **PowerShell yelling about execution policy?** Run this once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 3 — Create your env file

```bash
cp .env.example .env        # macOS / Linux / WSL
copy .env.example .env      # Windows
```

**Every analysis using only Census data works with zero keys.** The `.env` is for optional sources (NOAA, CDC, FBI, USDA, etc.). Signup links are inside the file. All free.

### 4 — Install your AI coding agent

| Agent | Install | Entry file |
|---|---|---|
| **Claude Code** (Anthropic) | `npm i -g @anthropic-ai/claude-code` or [claude.ai/claude-code](https://claude.ai/claude-code) | `CLAUDE.md` |
| **Codex CLI** (OpenAI) | `npm i -g @openai/codex` | `AGENTS.md` |
| **OpenCode** | [opencode.ai](https://opencode.ai) | `AGENTS.md` |
| **Cursor / Windsurf / Aider** | Open the repo in your tool | `AGENTS.md` |

Each agent reads its matching entry file and adopts the Lead Analyst role on its own. From inside the repo with your venv active, type the agent's launch command (e.g. `claude`) and start talking.

### Skip the agent entirely (just to verify install)

```bash
make demo            # or: python demo.py
```

Runs a 10-second poverty analysis on bundled Census data for Sedgwick County, KS. Opens an HTML report. **No keys, no internet, no agent.** This is purely to confirm Python and the dependencies are happy. The interesting part is the agent flow below.

---

## Your first real prompt

Inside the repo, with your venv active, in your agent of choice:

### 🟢 Starter prompts (Census-only, no extra keys)

```
What does poverty look like in Cook County, Illinois?
```

```
Map median household income for every census tract in Harris County, TX,
and tell me which neighborhoods are statistical hot spots.
```

```
Rank the top 20 counties in Georgia by uninsured rate. Map and chart them.
```

```
Show me where children under 5 live relative to lead-paint risk in Baltimore.
```

### 🟡 Multi-source prompts (need a free NOAA / CDC key)

```
Where in Florida do high flood-risk areas overlap with elderly populations
and low household income? Show me the high-priority intersection.
```

```
For Philadelphia, map diabetes prevalence against walkability (POI density)
at the tract level. Is there a spatial correlation worth investigating?
```

### 🔴 Deep analysis prompts (full pipeline)

```
I'm writing a grant for a rural health clinic in eastern Kentucky.
Build me a needs assessment: uninsured rate, poverty rate, distance
to nearest hospital, chronic disease burden at the tract level. Include
uncertainty maps for ACS estimates with high MOEs, and write the narrative
in pyramid principle (answer first, evidence second).
```

```
For Miami-Dade, model heat vulnerability as a composite of: elderly
population density, lack of A/C access (proxy: pre-1970 housing stock),
poverty, and surface temperature from the latest NOAA layer. Identify
the top 10 priority block groups and explain what makes each vulnerable.
```

The agent will scope, plan, fetch, process, analyze, render, validate, peer-review, and synthesize — usually 5 to 20 minutes depending on data volume. You'll see every decision narrated as it happens.

---

## You don't get a handoff — you get a collaborator

Traditional GIS consulting is a transaction: you hand a brief to an analyst, they disappear for two weeks, they come back with a PDF. If the map is wrong, or the story isn't quite right, or you want it from a different angle — that's another round trip, another invoice, another week.

This flips that. You're in the room with the analyst the whole time.

The agent shows you a draft map. You say *"the legend is covering downtown, move it."* Or *"add supermarkets so people can see why the south side is a food desert."* Or *"this is too busy — strip the water layer."* The agent re-renders, the map gets better, you keep going until it's right.

What this changes:

- **You see the work as it happens.** The agent narrates its decisions — palette, classification method, what caveats apply. You can interrogate every step before delivery.
- **You steer with plain English.** *"Make the annotations smaller. Use a dark basemap. Same map but for Detroit."* The agent translates.
- **You learn while you work.** Every back-and-forth is a small cartography or stats lesson. The agent cites the wiki standards it's applying.
- **You keep the artifacts.** Every run writes style sidecars, a solution graph, and JSON handoffs. Reproducing the same map in QGIS or Pro six months later is "open the package."

This is what "AI-native GIS" actually means to me. Not "there's a chatbot somewhere." Not "the software generated a map." It means the analyst-tool boundary dissolves — *you* are the analyst, the agent is the mechanic, and the two of you iterate until the answer is good. The part of the job I missed is back.

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

The **wiki** is knowledge. 134 pages of standards (cartography, spatial-stats, CRS, QA), domain playbooks (food access, healthcare, hazards, equity), and authoritative data-source guides (Census, EPA, FEMA, NOAA…). It's how the system knows that a poverty-rate field deserves a YlOrRd palette. That LISA results need FDR correction. That a food-access analysis should overlay supermarkets and skip water features. The wiki is the methodology I wish someone had written down when I started.

The **agents** are 9 role-specialists. Each has a `SOUL.md` (mission + boundaries) and a `TOOLS.md` (approved scripts). The Lead Analyst orchestrates; the others execute their stage; every handoff is a JSON artifact you can inspect.

The **scripts** are 155 production tools. Battle-tested means we ran them on real analyses, broke them, fixed them, standardized their outputs. Every visual writes a `.style.json` sidecar so the QGIS, ArcGIS Pro, and ArcGIS Online deliverables all render from one source of truth. That fidelity is the whole point.

The agent reads the relevant wiki page, picks the right scripts, runs them in the right order, validates the result, and reports back. Composable knowledge over a curated tool inventory.

---

## Why it's agentic, patchable, and yours

This project is designed to be forked. Every script, prompt, agent definition, and config file is plain text written for an AI agent to read and modify. You're not "users" of a black-box product. You're operating the system.

### The PATCH.md model

Customization happens through `PATCH.md` at the repo root. Every time your AI agent changes the system — adds a data source, changes a default palette, alters pipeline behavior — it writes a `PATCH.md` entry recording **intent**, files modified, why, and notes for re-applying.

When upstream ships an update:

1. Pull the update.
2. Tell your agent: *"Re-apply my patches from PATCH.md to the new version."*
3. The agent reads the *intent* of each change (not just the literal diff) and re-applies it intelligently against the new code.

This means your fork stays yours, *and* you can pull upstream improvements without losing your work. Your customizations are written down in plain English you (and any future agent) can understand.

### Make it your firm's

| You want to... | What to change |
|---|---|
| Add a data source (custom API, paywalled feed, internal table) | Write a `fetch_<source>.py` following the [pattern](docs/extending/ADDING_DATA_SOURCES.md). Add an entry to `config/data_sources.json`. |
| Encode your firm's methodology for a domain | Add a page to `docs/wiki/domains/`. The agent will read it before any analysis in that domain. |
| Change default map styles | Edit `config/map_styles.json`. Five families, 31 palettes. |
| Connect your PostGIS / SDE / ArcGIS Online / GeoServer | See `docs/extending/CONNECTING_INFRASTRUCTURE.md`. |
| Build a publishing adapter (S3, GeoServer, internal portal) | Implement `publishing.base.PublishAdapter`. See [`scripts/core/publishing/arcgis_online.py`](scripts/core/publishing/arcgis_online.py) as the reference implementation. |
| Add a new agent role | Drop a directory in `agents/<role>/` with `SOUL.md` + `TOOLS.md`. The lead-analyst can delegate to it. |
| Change cartography rules | Edit `docs/wiki/standards/CARTOGRAPHY_STANDARD.md`. The cartography agent reads it before every map. |

The wiki is your firm's knowledge base, encoded once, applied automatically. The scripts are your tool library, with clear contracts. The agents are your team's decision-making, made explicit. Your fork becomes your firm.

---

## Learning geospatial analysis with it

This is the part I'm most quietly proud of. Two ways to use it:

**As a textbook.** Read the wiki. 134 pages of how a senior cartographer actually thinks about palette choice, classification methods, projection selection, MOE handling, hotspot interpretation, accessibility checks. The kind of accumulated tradecraft normally locked inside senior practitioners' heads. (Mine, plus the standards from the literature, plus the dumb mistakes I made early.)

**As a lab.** Pick a real question — your hometown's poverty rate, your campus walkshed, a hazard you've worried about — run the agent on it, and read everything it produces: the project brief, the activity log, the code that ran, the validation report, the peer review. Modify a palette, ask the agent to redo the map, watch the change propagate. Modify a wiki page, watch the next analysis honor your rule.

For an instructor running an undergraduate or graduate spatial-analysis class:

- **Setup once.** Clone, install, hand out access.
- **One prompt = one project deliverable.** Students get a complete, fork-able package — data, processing scripts, maps, charts, report, audit trail.
- **Customization is the assignment.** "Add a new data source" or "add a new domain page for X" or "modify the cartography standard for Y" are real, learnable, finishable assignments that map to professional skills.
- **PATCH.md becomes a portfolio.** The student's fork *is* their submission. Their PATCH.md entries serve as documented design decisions.

If you teach with this and want to share materials, **open an issue.** I'd love to host community-contributed teaching modules.

---

## What you can analyze

| Domain | Example questions |
|---|---|
| **Equity & demographics** | Poverty hot spots, racial dot maps, income disparity at scale, ACS uncertainty visualization |
| **Healthcare access** | Distance to nearest hospital / FQHC / pharmacy, uninsured-rate maps, chronic-disease burden, healthcare desert detection |
| **Food access** | LILA tracts, supermarket density, food-desert composition, USDA Food Access Atlas integration |
| **Hazards & climate** | FEMA flood-zone overlays, heat-vulnerability composites, NOAA temperature trends, fire-risk surface combinations |
| **Environmental justice** | EPA EJScreen indicators, pollution-exposure overlays, vulnerability indexes |
| **Transit & mobility** | GTFS service area, walkshed analysis, transit equity, POI accessibility |
| **Housing** | HUD Fair Market Rents vs. local incomes, housing-cost burden, displacement risk |
| **Public safety** | Crime density vs. demographics, disparity analyses, FBI UCR integration |
| **Education access** | School-district demographic profiles, distance-to-school, opportunity maps |
| **Economic development** | LEHD/LODES commute flows, job density, employment hubs, retail gap analysis |

Bring your own data via `retrieve_local.py` or `retrieve_remote.py` — anything you can put in a GeoPackage, Shapefile, GeoJSON, or CSV with lat/long is fair game.

---

## What gets produced

Every run writes to `analyses/<project>/outputs/`:

- **Maps** — choropleth, bivariate (3×3 Stevens), hotspot, LISA, point overlay, dot density, proportional symbol, small multiples, uncertainty. 200 DPI, colorblind-checked, with `.style.json` sidecars.
- **Charts** — distribution (histogram / KDE / box / violin), comparison (bar / lollipop / dot), relationship (scatter / scatter+OLS / hexbin / correlation heatmap), time series (line / area / small multiples). PNG + SVG.
- **Interactive web maps** — Folium, toggleable layers, popups, multiple basemaps.
- **QGIS package** — `.qgs` project, graduated/categorized renderers, basemap, auto-zoom, print layout template.
- **ArcGIS Pro package** — file geodatabase (`.gdb`), styled `.lyrx` layer files, `make_aprx.py` helper, charts folder. **No Esri license required to produce.** If `arcpy` is available, a full `.aprx` is pre-built.
- **ArcGIS Online (opt-in)** — uploads the GDB, publishes a hosted Feature Service with N layers, applies sidecar renderers, builds a Web Map. Default sharing is PRIVATE. Requires an ArcGIS Online subscription (Location Platform / Developer tier doesn't include hosted publishing — see the [workflow doc](docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md)).
- **Narrative report** — self-contained HTML with exec summary, KPIs, embedded maps + charts, methodology, caveats, sources.
- **Solution graph** — DAG showing every input → operation → output. PNG, SVG, JSON, Mermaid.
- **QA scorecards**, **data dictionaries**, **provenance records**, **handoff JSON** — full auditability.

---

## The 9 specialists

| Agent | Role |
|---|---|
| 🧠 **Lead Analyst** | Orchestrates the pipeline, scopes work, integrates and synthesizes |
| 📦 **Data Retrieval** | Acquires data from 20+ built-in sources (Census, EPA, CDC, FEMA, NOAA, OSM, …) |
| ⚙️ **Data Processing** | Cleans, normalizes, joins → analysis-ready GeoPackages with provenance |
| 📊 **Spatial Stats** | Hotspot (Gi*), LISA, Moran's I, change detection — with FDR correction by default |
| 🗺️ **Cartography** | Maps **and** statistical charts — distribution, comparison, relationship, time series |
| ✅ **Validation QA** | Geometry, join rates, null values, structural integrity gates |
| 📝 **Report Writer** | Pyramid Principle (answer first), HTML + Markdown |
| 📦 **Site Publisher** | QGIS package, ArcGIS Pro package, optional AGOL publishing |
| 🔍 **Peer Reviewer** | Independent gate — catches unsupported claims, overconfidence, missing caveats |

Each agent has `agents/<role>/SOUL.md` (mission + boundaries) and `agents/<role>/TOOLS.md` (approved scripts). Read either to understand exactly what each will and won't do.

---

## Built-in data sources

| Category | Sources | Auth |
|---|---|---|
| **Demographics** | Census ACS, Decennial Population, TIGER, LEHD/LODES | Free key optional |
| **Health** | CDC PLACES, EPA EJScreen | None |
| **Food & housing** | USDA Food Access Atlas, HUD Fair Market Rents | Free key optional |
| **Hazards & climate** | FEMA Flood Zones, NOAA Climate, OpenWeatherMap | Free keys |
| **Economic & safety** | BLS employment, FBI crime | Free keys |
| **Places & POI** | OpenStreetMap (Overpass), Overture Maps | None |
| **Terrain** | USGS National Map (DEM) | None |
| **Transit** | GTFS feeds | None |
| **Open data** | Socrata (1000s of city/county/state portals) | Optional token |
| **Generic** | Any URL, any local file (GPKG, SHP, CSV, GeoJSON) | None |

Full registry: [`config/data_sources.json`](config/data_sources.json). Add your own: [`docs/extending/ADDING_DATA_SOURCES.md`](docs/extending/ADDING_DATA_SOURCES.md).

---

## What's in the repo

```
spatial-machines/
├── CLAUDE.md            ← Claude Code entry point
├── AGENTS.md            ← Agent-agnostic orchestration guide
├── PATCH.md             ← Your customization log (yours; starts empty)
├── demo.py              ← Standalone demo
├── Makefile             ← `make demo`, `make verify`
├── .env.example         ← API key template (all free sources)
├── requirements.txt
├── agents/              ← 9 specialist role definitions
├── docs/
│   ├── wiki/            ← 134 pages of canonical GIS methodology
│   │   ├── standards/   ← cartography, charts, spatial-stats, CRS, QA
│   │   ├── workflows/   ← step-by-step playbooks
│   │   ├── domains/     ← healthcare, food access, equity, hazards, …
│   │   ├── data-sources/← authoritative source guides
│   │   └── toolkits/    ← GDAL, GeoPandas, PostGIS, Rasterio, …
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

## Joining in

This project is openly developed. Things I'd most love help with:

- **New data sources.** Write a `fetch_*.py` following the pattern, add to the registry. Domain-specific sources (state-level health, regional planning datasets, niche industry feeds) especially welcome.
- **Domain wiki pages.** Encode your specialty — utility-line vegetation management, retail site selection, brownfield prioritization, anything. One good page = many future analyses get smarter.
- **Real prompts that produced bad output.** File an issue. The system improves the most when we surface friction. The goal isn't a benchmark; it's "did this produce a thing a real client would accept?"
- **Teaching modules.** If you use this in a class or workshop, share the materials. I want this in classrooms.
- **New publishing adapters.** GeoServer, S3 / static-site, internal portals, internal SDE. Implement `PublishAdapter`, ship it, write the workflow doc.

Start at [CONTRIBUTING.md](CONTRIBUTING.md). For non-trivial changes please open an issue first to discuss.

---

## What we enforce

- **Script-first** — use existing core scripts before writing custom code
- **Style registry** — `config/map_styles.json` and `config/chart_styles.json` are read before every visual
- **FDR correction** — Benjamini-Hochberg on all hotspot/LISA results
- **Moran's I gate** — global autocorrelation tested before any local spatial analysis
- **Colorblind accessibility** — every map and multi-series chart is checked
- **Pyramid Principle** — reports lead with the answer, not the methodology
- **Vision QA** — the agent inspects every map before delivery
- **Peer review** — independent gate catches unsupported claims

These are wiki-encoded; agents enforce them automatically and cite the standard when asked why.

---

## Documentation

- **[Wiki](docs/wiki/)** — 134 pages the agents consult before every analysis
- **[Architecture](docs/architecture/ARCHITECTURE.md)** — how the 9-agent system is organized
- **[Pipeline Standards](docs/reference/PIPELINE_STANDARDS.md)** — mandatory output quality standards
- **[Cartography Standard](docs/wiki/standards/CARTOGRAPHY_STANDARD.md)** — full map family taxonomy + design rules
- **[Chart Design Standard](docs/wiki/standards/CHART_DESIGN_STANDARD.md)** — mandatory rules for statistical charts
- **[ArcGIS Pro Package Standard](docs/wiki/standards/ARCGIS_PRO_PACKAGE_STANDARD.md)** — what the `.gdb` + `.lyrx` bundle guarantees
- **[ArcGIS Online Publishing](docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md)** — opt-in AGOL workflow + subscription / scope notes
- **[Install Guide](docs/guides/INSTALL.md)** — deeper setup (GDAL on Windows, PostGIS, etc.)
- **[Troubleshooting](docs/guides/TROUBLESHOOTING.md)** — common issues and fixes
- **[Extending](docs/extending/)** — add data sources, connect infrastructure, customize palettes, build adapters

---

## License + acknowledgments

**License:** Apache-2.0. See [LICENSE](LICENSE).

**Trademark:** "spatial-machines" is a project name. Forks must use a different name. See [TRADEMARK.md](TRADEMARK.md). The PATCH.md model means you can run a customized fork-of-yours-only without renaming; published forks ship under your own name.

**Acknowledgments:** the GIS tool registry (`scripts/tool-registry/`) is built on research from the [SpatialAnalysisAgent](https://github.com/Teakinboyewa/SpatialAnalysisAgent) project by Akinboyewa et al. at Penn State. The solution-graph concept comes from the autonomous-GIS prototype by Ning et al. (*International Journal of Digital Earth*, 2023):

> Ning, H., Li, Z., Akinboyewa, T., & Lessani, M. N. (2023). *An autonomous GIS agent framework for geospatial data retrieval.* doi:10.1080/17538947.2023.2278895
>
> Akinboyewa, T., Xu, Z., Huan, X., & Li, Z. (2024). *GIS Copilot: Towards an Autonomous GIS Agent for Spatial Analysis.* doi:10.1080/17538947.2025.2497489

Under GPL-3.0 where applicable.

---

If you build something with this you're proud of — a community map, a report that moved a council vote, a class project that taught a student to think spatially — open an issue and tell me. I'm collecting these. The point of getting the drudgery out of GIS was always so we could go back to doing the work that mattered.
