# Configuration Reference

What actually configures behavior in spatial-machines, where it lives, and what reads it.

There is no single unified settings file. Configuration is split by concern:

| Concern | Where it lives | Who reads it |
|---|---|---|
| API credentials | `.env` at repo root (gitignored; copy from `.env.example`) | Data-retrieval scripts, AGOL adapter |
| Map styling | `config/map_styles.json` | Every map script, QGIS + ArcGIS Pro + AGOL packagers |
| Chart styling | `config/chart_styles.json` | Every chart script |
| Palettes (legacy auxiliary) | `config/palettes.json` | `scripts/core/charts/_base.py` |
| Data source registry | `config/data_sources.json` | Data-retrieval agent, `fetch_*.py` scripts |
| Data freshness schedule | `config/data-freshness-schedule.json` | `check_data_freshness.py`, `check_reanalysis_needed.py`, `audit_delegation.py` |
| Re-analysis trigger thresholds | `config/reanalysis-triggers.json` | `check_reanalysis_needed.py` |
| POI scoring weights | `config/scoring/poi_default_weights.md` | POI scoring scripts |
| Per-analysis scope, audience, QA thresholds | `analyses/<project>/project_brief.json` | All 9 agents — read before every stage |

## .env — credentials

Copy `.env.example` to `.env` and fill in the keys you need. **Every analysis that uses only Census data works with zero keys.** The file is gitignored. Signup links for all free sources are inside `.env.example`.

Key variables (full list in `.env.example`):

| Variable | Required for | Free? |
|---|---|---|
| `CENSUS_API_KEY` | Optional rate-limit relief on ACS / Decennial fetches | Yes — [api.census.gov/data/key_signup](https://api.census.gov/data/key_signup.html) |
| `NOAA_API_TOKEN` | NOAA climate data | Yes |
| `FBI_API_KEY` | FBI crime data | Yes |
| `CDC_API_TOKEN` | CDC PLACES (optional; works anon) | Yes |
| `BLS_API_KEY` | BLS employment (optional) | Yes |
| `HUD_API_KEY` | HUD housing data (optional) | Yes |
| `OPENWEATHER_API_KEY` | OpenWeatherMap | Yes |
| `AGOL_URL` | Default `https://www.arcgis.com` | — |
| `AGOL_USER` + `AGOL_PASSWORD` | ArcGIS Online publishing (preferred) | — |
| `AGOL_API_KEY` | ArcGIS Online publishing (alternative; has scope caveats — see [AGOL workflow doc](../wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md)) | — |
| `SOCRATA_APP_TOKEN` | Optional for Socrata portals (higher rate limit) | Yes |
| `OSM_DB_*` | Optional PostGIS connection for local OSM mirror | — |

## config/map_styles.json

Primary style registry. Read before every map and inherited by QGIS, ArcGIS Pro, and AGOL packagers via `.style.json` sidecars.

Top-level keys:

- `families` — 5 map families (`thematic_choropleth`, `thematic_categorical`, `thematic_bivariate`, `reference`, `point_overlay`). Each declares typography, layout, legend behavior, inset locator rules.
- `palettes` — per-family palette options (31 total). Agents pick via `domain_palette_map` unless a script passes `--cmap` explicitly.
- `domain_palette_map` — field-name regex → palette (`poverty_rate` → `YlOrRd`, `median_income` → `YlGnBu`, etc.). This is how auto-palette routing works.
- `color_ramps_rgb` — RGB arrays for every palette. Single source of truth for matplotlib, matplotlib→lyrx translation, and AGOL renderer construction.
- `typography` — title / subtitle / legend / attribution / inset font sizes by family.
- `patterns` — hatch patterns for print-friendly black-and-white reproduction.
- `inset_locator` — sizing and position rules for the locator map.

Overriding: edit this file in your fork. Document the change in `PATCH.md` so upstream updates can be re-applied without losing customizations.

## config/chart_styles.json

Sibling of `map_styles.json` for statistical charts. Top-level keys:

- `families` — 4 chart families (`distribution`, `comparison`, `relationship`, `timeseries`). Each declares figure size, DPI, default palette family.
- `palettes_categorical` — local copy of categorical palettes; falls back to `palettes.json` when a field isn't matched here.
- `typography` — title / subtitle / axis / tick font sizes.
- `attribution_position`, `number_format` — output-level defaults.

The chart palette routing reuses the map `domain_palette_map` via `scripts/core/charts/_base.resolve_cmap_for_field()` — so `poverty_rate` gets the same palette family in a histogram as in a choropleth.

## config/palettes.json

Legacy palette file, still read by `scripts/core/charts/_base.load_palettes()`. Contains `categorical`, `access`, `bivariate_3x3`, `change_negative`, `change_positive`, `distance`. Prefer adding new palettes to `map_styles.json` or `chart_styles.json`; keep this file in sync when you do.

## config/data_sources.json

Registry of 20 built-in data sources. Structure:

```json
{
  "version": "...",
  "description": "...",
  "sources": {
    "<source_id>": {
      "name": "...",
      "category": "demographics | health | hazards | …",
      "auth_required": true | false,
      "auth_env_var": "…",
      "fetch_script": "fetch_*.py",
      "signup_url": "…",
      "documentation_url": "…"
    }
  }
}
```

Add your own source: write a `fetch_<source>.py` in `scripts/core/` following the pattern, then add an entry here. See [docs/extending/ADDING_DATA_SOURCES.md](../extending/ADDING_DATA_SOURCES.md).

## config/data-freshness-schedule.json

Declares how often each source should be considered fresh. `check_data_freshness.py` reads this to flag stale inputs in audit reports. Entries look like:

```json
"census_acs": {
  "cadence_days": 365,
  "release_month": 12,
  "note": "ACS 5-year release lands in December"
}
```

## config/reanalysis-triggers.json

Used by `check_reanalysis_needed.py` to decide whether a prior analysis should be re-run given upstream data or method changes. Declares:

- `monitored_analyses` — which analyses are on the watch list
- `source_criticality` — how much each source's freshness matters
- `impact_scoring` — weighting of field changes / row changes / schema changes
- `notification_thresholds` — when to warn vs. block

## config/scoring/

- `poi_default_weights.md` — default weights for POI scoring when a domain playbook doesn't specify its own.

## analyses/\<project\>/project_brief.json

Per-analysis configuration. Written by the lead-analyst at engagement start. All 9 agents read it before every stage. Full schema at `templates/project_brief.json`. Key sections:

- `client` — who, what type, contact
- `audience` — primary reader, technical level, what they're deciding, what they already believe
- `engagement` — hero question, deliverable type, deadline, budget tier, sensitive findings
- `geography` — study area, geographic unit, CRS, bounding box
- `data` — primary sources, vintage, known quality issues, institutional areas to flag, join key
- `analysis` — dependent/independent variables, analysis types, spatial weights, classification scheme, k classes
- `outputs` — required maps, charts, statistics, formats, publish targets
- `report` — tone, pyramid lead, SCQA framing, key findings draft
- `qa` — max null %, min join rate, Moran's gate, institution flag

## Where to override what

| You want to... | Edit |
|---|---|
| Change default map palette for a variable | `config/map_styles.json` → `domain_palette_map` |
| Add a new palette | `config/map_styles.json` → `palettes` + `color_ramps_rgb` |
| Change default chart typography | `config/chart_styles.json` → `typography` |
| Add a data source | Write `fetch_<source>.py` + add to `config/data_sources.json` |
| Set a credential | Add to `.env` (never commit) |
| Change QA thresholds for one analysis | `analyses/<project>/project_brief.json` → `qa` |
| Change QA thresholds globally | Edit `templates/project_brief.json` |
| Mark an analysis for re-run monitoring | `config/reanalysis-triggers.json` → `monitored_analyses` |

Every edit you make to a shipped config file should get a `PATCH.md` entry so upstream updates can be re-applied intelligently.
