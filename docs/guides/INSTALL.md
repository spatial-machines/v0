# Install Guide

Deeper install details beyond the four-step README quick-start. Use this guide if the quick-start didn't work, or if you want to understand each step.

## Prerequisites

- **Python 3.11+** — required
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

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```
If PowerShell rejects the activation script with an execution-policy error:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Then re-run the activate line.

**Windows (cmd.exe):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux / WSL:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` at the start of your prompt when it's active. Re-run the activate line in every new terminal.

## Step 3: Install Python dependencies

With your venv active:

```bash
pip install -r requirements.txt
```

First-time install takes a couple of minutes (geopandas, matplotlib, fiona, libpysal, etc.). Cached after.

`requirements.txt` includes all core dependencies. Optional packages (spatial regression, network analysis, etc.) are listed as comments — uncomment what you need.

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
