# Project Start Guide

How to start a new analysis project in spatial-machines.

## The easy way

Open your AI coding agent in the spatial-machines directory and describe what you want to analyze:

> "Analyze poverty rates across census tracts in Douglas County, Nebraska. Include a choropleth map, hotspot analysis, and a summary report."

The lead analyst agent will:
1. Create a project directory under `analyses/`
2. Write a `project_brief.json` scoping the work
3. Plan the pipeline stages
4. Delegate to specialist agents
5. Deliver results to `outputs/`

## The manual way

If you want to set up a project structure yourself:

### Step 1: Create the project directory

```bash
mkdir -p analyses/my-analysis/{data/{raw,processed},outputs/{maps,charts,web,reports,qa,qgis,arcgis},runs}
```

### Step 2: Write a project brief

Copy the template and fill in the fields that apply:

```bash
cp templates/project_brief.json analyses/my-analysis/project_brief.json
```

The template schema has sections for `client`, `audience`, `engagement` (hero question, deadline, budget tier), `geography` (study area, unit, CRS), `data` (primary sources, vintage), `analysis` (variables, methods, classification), `outputs` (required deliverables + publish targets), `report` (tone, pyramid lead, SCQA), and `qa` (thresholds). Each agent reads this before its stage, so fill in what you know — leave the rest for the agent to propose.

See [`docs/reference/WORKSPACE_MODEL.md`](../reference/WORKSPACE_MODEL.md) for how the brief is used.

### Step 3: Retrieve data

```bash
# Census ACS poverty data
python scripts/core/fetch_acs_data.py 31 \
    --variables B17001_001E,B17001_002E --year 2022 \
    -o analyses/my-analysis/data/raw/poverty.csv

# TIGER tract boundaries
python scripts/core/retrieve_tiger.py 31 \
    -o analyses/my-analysis/data/raw/
```

### Step 4: Process and analyze

Point the processing and analysis scripts at your raw data. Each script accepts `--help` for full usage.

### Step 5: Review outputs

Your analysis outputs will be in:
- `analyses/my-analysis/outputs/maps/` — styled PNG maps + `.style.json` sidecars
- `analyses/my-analysis/outputs/charts/` — statistical charts paired with the maps
- `analyses/my-analysis/outputs/reports/` — markdown and HTML reports
- `analyses/my-analysis/outputs/qgis/` — styled QGIS project package
- `analyses/my-analysis/outputs/arcgis/` — ArcGIS Pro package (`.gdb` + `.lyrx`)

## Before you begin — decisions

1. **What geography?** State FIPS, county FIPS, boundary level (tract, county, block group)
2. **What data?** Which data sources will you use? See `config/data_sources.json` for 20+ options.
3. **What questions?** What do you want to map, analyze, or compare?

## Project isolation

Each analysis lives entirely under `analyses/<project-id>/`. No cross-project file references. Raw data is immutable. See `analyses/README.md` for the directory structure.
