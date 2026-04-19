# Install Guide

Deeper install details beyond the four-step README quick-start. Use this guide if the quick-start didn't work, or if you want to understand each step.

## Prerequisites

- **Python 3.12**. Pin to 3.12, not 3.13+. Geospatial wheels (fiona/GDAL via rasterstats) lag behind new Python releases and will fail to build from source on Windows.
- **Git**
- **An AI coding agent** — Claude Code, Codex CLI, OpenCode, Cursor, etc.

The spatial C libraries (GDAL, PROJ, GEOS) come bundled with the Python packages on Windows and macOS via platform wheels. Linux may need them installed separately — see the per-platform notes below.

### Optional system dependencies

These are only needed on Linux, or if you want faster installs / local-build flexibility.

**Ubuntu / Debian / WSL:**
```bash
sudo apt install gdal-bin libgdal-dev libgeos-dev libproj-dev python3-dev
```

**macOS (Homebrew):**
```bash
brew install gdal geos proj
```

**Windows:**
Not needed. The pip wheels include everything. If you want a full system-level geospatial toolkit, OSGeo4W is the standard installer: https://trac.osgeo.org/osgeo4w/

## Step 1: Clone the repo

```bash
git clone https://github.com/spatial-machines/spatial-machines.git
cd spatial-machines
```

## Step 2: Create a virtual environment

A venv is a private Python sandbox for this project so its dependencies don't collide with other Python projects on your machine. Skip this and you'll eventually regret it.

**Windows (Command Prompt, recommended):**
```
py -3.12 -m venv venv
venv\Scripts\activate
```

Use `py -3.12` explicitly. If your default `python` is 3.13 or 3.14, plain `python -m venv venv` silently builds the venv on the wrong version and the `pip install` step will fail on fiona.

**Windows (PowerShell, if you prefer it):**
```powershell
py -3.12 -m venv venv
venv\Scripts\Activate.ps1
```
If PowerShell rejects the activation script with an execution-policy error, run this once, then re-run the activate line:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**macOS / Linux / WSL:**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` at the start of your prompt when it's active. Re-run the activate line in every new terminal. The agent needs the venv active when you launch it so it calls the right Python.

## Step 3: Install Python dependencies

With your venv active:

```
pip install -r requirements.txt
```

First-time install takes a couple of minutes (geopandas, matplotlib, libpysal, rasterstats, etc.). Cached after.

`requirements.txt` includes all core dependencies. Optional packages (spatial regression, network analysis, etc.) are listed as comments — uncomment what you need.

If `pip install` fails on a C-extension package (fiona, rasterio, pyogrio), you're almost certainly on Python 3.13+. Prebuilt wheels for the geospatial stack lag one or two Python versions behind. Install Python 3.12, recreate the venv, re-run `pip install`.

## Step 4: Configure environment

```bash
cp .env.example .env        # macOS / Linux / WSL
copy .env.example .env      # Windows
```

Edit `.env` and add keys you'll use:
- `CENSUS_API_KEY` — recommended for Census ACS (free, avoids rate limiting)
- All other keys are optional — see `.env.example` for signup links

## Step 5: Verify the installation

```bash
make verify
```

This checks that core scripts compile, wiki pages are present, and agent roles are defined.

For a deeper check:
```bash
make test
```

This runs the full pytest suite.

Or skip `make` entirely and run the bundled demo:
```bash
python demo.py
```

A 10-second poverty analysis on Sedgwick County, KS. No API keys, no internet, no agent. If the demo finishes and opens an HTML report in your browser, your install is good.

## Step 6: Run your first agent-driven analysis

Open your AI coding agent (Claude Code, Codex, etc.) in the `spatial-machines` directory and ask a spatial question. See the [README](../../README.md) for example prompts.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Reference

- [MACHINE_REQUIREMENTS.md](../reference/MACHINE_REQUIREMENTS.md) — hardware and software specs
- [CONFIG_REFERENCE.md](../reference/CONFIG_REFERENCE.md) — environment variables and config
