# Machine Requirements

What you need on your machine to run spatial-machines.

## Short version

| Component | What you need |
|---|---|
| OS | Windows 10/11, macOS 12+, Linux, or WSL2 |
| Python | 3.12 (pin here; 3.13+ breaks geospatial wheels) |
| RAM | 4 GB minimum, 8 GB+ recommended |
| Storage | 5 GB free for repo + deps; more if you keep many analyses |
| Network | Needed for data-fetching and AI-agent calls; not for rendering |
| AI coding agent | Claude Code, Codex CLI, OpenCode, Cursor, etc. |

No Docker required. No ArcGIS license required. No QGIS required (though installing QGIS unlocks a nicer `.qgs` output — see below).

## Python

Python 3.12 specifically. Tested against 3.11 and 3.12 on Windows, macOS, and Linux. Python 3.13+ will fail to install the geospatial stack: prebuilt wheels for fiona, rasterio, and pyogrio lag behind new Python releases, and source builds need GDAL headers that aren't on a default Windows or macOS box.

If you already have 3.13+ installed for other projects, install 3.12 alongside it. On Windows, the py launcher (`py -3.12 -m venv venv`) lets you pick which one.

Install paths:

| Platform | Path |
|---|---|
| **Windows** | Microsoft Store → search "Python 3.12" → Install. Or [python.org](https://www.python.org/downloads/release/python-3129/) (check "Add python.exe to PATH"). |
| **macOS** | `brew install python@3.12` (install [Homebrew](https://brew.sh/) first) or [python.org](https://www.python.org/downloads/release/python-3129/). |
| **Linux / WSL** | `sudo apt install python3.12 python3.12-venv` (Ubuntu/Debian) or your distro's equivalent. |

Verify: `python --version` (Windows) or `python3.12 --version` (macOS/Linux). Must print 3.12.x.

## Recommended resources

| Resource | Minimum | Comfortable |
|---|---|---|
| RAM | 4 GB | 8 GB+ |
| CPU | Any 64-bit x86 or ARM | Multi-core helps the stats stage |
| Disk | 5 GB for repo + venv | 20 GB+ if you keep dozens of analyses |
| Network | Any working connection | — |

**What uses memory:** typical analyses stay under 500 MB of peak RAM. Large states (California ~8,000 tracts, multi-source join) can push toward 1–2 GB. The cartography and AGOL-publishing stages are the heaviest.

**What uses disk:** the bulk comes from the venv (~1.5 GB after `pip install`) and per-analysis artifacts (raw data, GeoPackages, map PNGs, reports — a typical analysis is 20–200 MB).

## Software dependencies (pip-installed into your venv)

All handled by `pip install -r requirements.txt`. Key packages:

| Package | Purpose |
|---|---|
| geopandas, pandas, numpy, shapely, pyproj, pyogrio | Core geospatial stack |
| rasterio, rasterstats | Raster analysis (pulls fiona transitively) |
| matplotlib, seaborn | Static map and chart rendering |
| mapclassify, contextily | Classification + basemap tiles |
| folium, branca | Interactive web maps |
| libpysal, esda | Spatial statistics (Moran's I, Getis-Ord Gi*, LISA) |
| requests | Data retrieval + AGOL REST adapter |

GDAL/PROJ/GEOS are pulled in by the above via platform wheels — no separate system install needed on Windows or macOS. Some Linux distros may want the system GDAL for faster installs; see [docs/guides/INSTALL.md](../guides/INSTALL.md).

## Optional software

Installing these unlocks additional capabilities but is not required:

| Software | Unlocks |
|---|---|
| **QGIS 3.28+** (LTR) | In-process `.qgs` project generation (the packager otherwise produces styled `.qgs` via a subprocess or ships without one). Install via [qgis.org](https://qgis.org). On Windows, OSGeo4W is the recommended installer. |
| **ArcGIS Pro 3.1+** | Automatic `.aprx` generation from the ArcGIS Pro package. Without Pro, the package ships with `.gdb` + `.lyrx` files + a `make_aprx.py` helper that builds the `.aprx` when opened inside Pro. |
| **ArcGIS Online subscription** | Optional publishing to hosted Feature Service + Web Map. Free Developer / Location Platform accounts can **not** publish hosted feature layers; a paid ArcGIS Online subscription (or the 21-day trial) is required. See [AGOL workflow doc](../wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md). |
| **PostGIS** | Only needed if you work with a local OpenStreetMap mirror. Most analyses don't need it. |

## What you don't need

- **Docker.** The project used to ship as a Docker image; the modern path is a local venv.
- **ArcGIS Desktop or Pro license on the producer machine.** The Pro package is produced via GDAL's OpenFileGDB driver. You only need Pro on the consumer side (to open the package).
- **A GPU.** Rendering is CPU matplotlib, not GPU.
- **A beefy machine.** A 4 GB laptop can run most analyses. The Sedgwick demo runs in 10 seconds on anything modern.

## AI coding agent

The system is driven by an AI coding agent that reads `CLAUDE.md` or `AGENTS.md` and adopts the Lead Analyst role. Tested with Claude Code, Codex CLI, OpenCode, and Cursor. See the [README](../../README.md#4--install-your-ai-coding-agent) for install links.

Network access to the agent's API is required during a run (the agent calls the model). Once a run is complete, you can browse outputs offline.

## Concurrent runs

Single-analysis at a time is the design default. Running two agents simultaneously on the same repo is supported but untested — each agent writes to its own `analyses/<project>/` folder so there's no artifact collision, but file-level locks on the config JSONs during rapid edits could surface edge cases.
