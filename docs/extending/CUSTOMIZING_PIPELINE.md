# Customizing the Pipeline

spatial-machines ships with sensible defaults — color palettes, QA thresholds, report templates, and agent roles tuned for general-purpose GIS consulting. This guide covers how to customize them for your organization.

## Color Palettes

### What it controls
Every map the system produces uses colors from `config/palettes.json`. The palette registry maps variable types to ColorBrewer/matplotlib color ramps, classification methods, and class counts.

### How to customize

Edit `config/palettes.json`. Each entry has:

```json
{
  "poverty": {
    "cmap": "YlOrRd",
    "scheme": "natural_breaks",
    "k": 5,
    "reverse": false,
    "notes": "Warm palette for deprivation metrics"
  }
}
```

**Fields:**
- `cmap` — any matplotlib/ColorBrewer colormap name (YlOrRd, Blues, RdYlGn, viridis, etc.)
- `scheme` — classification method: `natural_breaks`, `quantile`, `equal_interval`
- `k` — number of classes (typically 5)
- `reverse` — flip the color ramp direction

### Adding a new palette

Add a new key to the JSON. The cartography agent matches variable names to palette keys — if your analysis uses a field like `transit_score`, add a `transit_score` palette:

```json
{
  "transit_score": {
    "cmap": "PuBuGn",
    "scheme": "quantile",
    "k": 5,
    "reverse": false,
    "notes": "Cool palette for transit accessibility scores"
  }
}
```

### Organization branding

Replace the default palettes with your organization's color scheme. The agents will pick them up automatically. Ensure your custom colors pass colorblind accessibility checks (`scripts/core/check_colorblind.py`).

---

## QA Thresholds

### What it controls
The validation-qa agent uses thresholds to determine PASS / PASS WITH WARNINGS / REWORK NEEDED outcomes.

### Key thresholds

These are currently defined in the agent SOUL files and wiki standards:

| Check | Default Threshold | Where Defined |
|---|---|---|
| Join coverage rate | Flag if < 95% | `docs/wiki/qa-review/STRUCTURAL_QA_CHECKLIST.md` |
| Null geometry rate | Flag if any nulls | `agents/validation-qa/SOUL.md` |
| High-CV tract rate | Flag if > 20% of tracts | `docs/wiki/standards/SPATIAL_STATS_STANDARD.md` |
| Moran's I gate | Must be significant before local analysis | `agents/spatial-stats/SOUL.md` |
| Map DPI minimum | 150 DPI (200 preferred) | `docs/reference/PIPELINE_STANDARDS.md` |

### How to customize

1. **Edit the relevant SOUL.md** to change an agent's non-negotiable thresholds.
2. **Edit the wiki standard** if the threshold is methodology-driven (e.g., Moran's I significance level).
3. **Edit PIPELINE_STANDARDS.md** if it affects output format requirements.

For example, to lower the join coverage warning threshold from 95% to 90%:
- Edit `docs/wiki/qa-review/STRUCTURAL_QA_CHECKLIST.md` — change the threshold text
- The validation-qa agent reads this before every QA run

---

## Report Templates

### What it controls
The report-writer agent generates markdown and HTML reports. The format follows the Pyramid Principle (answer first, then supporting evidence).

### How to customize

1. **Edit `templates/reports/run-report-template.md`** to change the report structure.
2. **Edit `templates/project_brief.json`** to change what information is captured at project scoping.
3. **Add methodology templates** in `templates/methodologies/` — these define standard analysis approaches for common question types.

### Adding a custom report template

Create a new template in `templates/reports/`:

```markdown
# {{project_name}} — {{report_type}}

## Executive Summary
{{executive_summary}}

## Key Findings
{{findings}}

## Methodology
{{methodology}}

## Data Sources
{{data_sources}}

## Limitations
{{limitations}}
```

Then reference it in the report-writer agent's TOOLS.md or project brief.

---

## Agent Roles

### Modifying an existing role

Each agent is defined by 3 files in `agents/<role>/`:
- **SOUL.md** — mission, non-negotiables, decision heuristics
- **TOOLS.md** — approved scripts and execution rules
- **AGENTS.md** — upstream/downstream relationships, handoff expectations

To modify an agent's behavior, edit its SOUL.md. The non-negotiables section is the most impactful — it defines what the agent refuses to do and what it always does.

### Adding a new agent role

1. Create `agents/<your-role>/` with the 3 standard files.
2. Define the role's mission, scope, and boundaries in SOUL.md.
3. List approved scripts in TOOLS.md.
4. Add the role to `docs/reference/TEAM.md`.
5. Update `docs/architecture/ACTIVE_TEAM.md`.
6. If the role is a pipeline stage, update `docs/architecture/PIPELINE_CANON.md`.
7. Reference the role in `CLAUDE.md` and `AGENTS.md` (top-level).

**Example: Adding a "Data Visualization" specialist**

```markdown
# SOUL.md — Data Visualization

You are the **Data Visualization** specialist for the GIS consulting team.

Your job is to:
- Create interactive dashboards from analysis outputs
- Build D3.js or Plotly visualizations for web delivery
- Design infographics from spatial analysis findings

## Non-Negotiables
1. Never alter the underlying data — visualization is read-only.
2. Every visualization must have a title, source attribution, and date.
3. Interactive visualizations must work without a backend server.
```

### Removing an agent role

Delete the `agents/<role>/` directory and remove references from TEAM.md, ACTIVE_TEAM.md, PIPELINE_CANON.md, CLAUDE.md, and AGENTS.md.

---

## Project Brief Schema

### What it controls
The project brief is the first artifact created for every analysis. It defines scope, data needs, deliverables, and constraints.

### How to customize

Edit `templates/project_brief.json` to add or modify fields. The lead-analyst agent reads this template when creating new project briefs.

Common customizations:
- Add organization-specific metadata fields (client name, project code, budget code)
- Add required deliverable types for your workflow
- Add standard caveats or disclaimers

---

## Methodology Templates

### What they are
Methodology templates in `templates/methodologies/` define standard analysis patterns for common question types. They specify which data to fetch, which scripts to run, and what outputs to produce.

### How to add one

Create a JSON file in `templates/methodologies/`:

```json
{
  "name": "Transit Equity Analysis",
  "description": "Analyze transit access disparities across demographic groups",
  "data_requirements": [
    {"source": "census-acs", "variables": "B17001_001E,B17001_002E", "note": "Poverty"},
    {"source": "gtfs-transit", "note": "Transit routes and stops"},
    {"source": "census-tiger", "note": "Tract boundaries"}
  ],
  "pipeline": [
    "fetch_acs_data.py",
    "fetch_gtfs.py",
    "retrieve_tiger.py",
    "process_vector.py",
    "compute_isochrones.py",
    "analyze_choropleth.py",
    "validate_outputs.py",
    "collect_report_assets.py"
  ],
  "outputs": ["choropleth map", "isochrone map", "demographic summary", "report"]
}
```

The lead-analyst agent uses these templates to build run plans for analyses that match known patterns.

---

## Pipeline Standards

### What it controls
`docs/reference/PIPELINE_STANDARDS.md` defines mandatory output requirements — DPI, figure sizes, file formats, map element requirements, and QA scorecard format.

### How to customize
Edit the file directly. Common changes:
- **DPI:** Change from 200 to your organization's standard
- **Figure size:** Adjust from 14x10 to match your deliverable format
- **Required map elements:** Add or remove elements (e.g., add a mandatory disclaimer footer)
- **CRS:** Change target CRS from EPSG:4269 to your region's standard
