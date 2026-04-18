# Workflow — Chart Generation

How the Cartography (Visualization) agent produces statistical charts as required outputs alongside maps.

## When

Every analysis. Charts are a required output, not optional. The specific families depend on what spatial-stats produced upstream — see the pairing rule in `CHART_DESIGN_STANDARD.md`.

## Inputs the agent reads

1. `analyses/<project>/project_brief.json` — audience, required_statistics
2. `analyses/<project>/runs/*_analysis_handoff.json` — what stats/fields are in play, with any recommended chart families from spatial-stats
3. `analyses/<project>/data/processed/*.gpkg` or CSV tables — the numeric inputs
4. `config/chart_styles.json` — family profiles, palettes, typography
5. `config/map_styles.json` — `domain_palette_map` for field-aware palette routing

## Decision tree

```
Is the analysis about ONE variable across space?
├─ Yes → produce distribution + top/bottom comparison
│         (paired with the choropleth)
└─ No
   ├─ Two variables? → scatter_ols (pair with bivariate map)
   ├─ Three+ variables? → correlation_heatmap
   ├─ Change over time? → line (+ small_multiples if >4 geographies)
   └─ Ranking/decision? → bar or lollipop
```

## Script entry point

```bash
# distribution
python scripts/core/generate_chart.py distribution \
  --data analyses/p1/data/processed/tracts.gpkg \
  --layer tracts \
  --field poverty_rate \
  --kind histogram \
  --output analyses/p1/outputs/charts/poverty_histogram \
  --title "Poverty rate distribution — Douglas County tracts" \
  --attribution "U.S. Census Bureau ACS 5-Year, 2022"

# ranked comparison
python scripts/core/generate_chart.py comparison \
  --data analyses/p1/data/processed/tracts.gpkg --layer tracts \
  --category-field name --value-field poverty_rate \
  --kind lollipop --top-n 15 \
  --output analyses/p1/outputs/charts/top_tracts

# relationship
python scripts/core/generate_chart.py relationship \
  --data analyses/p1/data/processed/tracts.gpkg --layer tracts \
  --x-field median_income --y-field poverty_rate \
  --kind scatter_ols \
  --output analyses/p1/outputs/charts/income_vs_poverty

# correlation heatmap
python scripts/core/generate_chart.py relationship \
  --data analyses/p1/data/processed/tracts.gpkg --layer tracts \
  --fields median_income poverty_rate unemployment_rate pct_bachelors \
  --kind correlation_heatmap \
  --output analyses/p1/outputs/charts/correlations

# time series
python scripts/core/generate_chart.py timeseries \
  --data analyses/p1/data/processed/trend.csv \
  --time-field year --value-field poverty_rate \
  --kind line \
  --output analyses/p1/outputs/charts/poverty_trend
```

`--output` is a stem; `.png`, `.svg`, and `.style.json` are written as siblings.

## Programmatic (from an agent)

```python
import sys
sys.path.insert(0, "scripts/core")
from charts import distribution, comparison, relationship, timeseries

result = distribution.render(
    data="analyses/p1/data/processed/tracts.gpkg",
    layer="tracts",
    field="poverty_rate",
    kind="histogram",
    output="analyses/p1/outputs/charts/poverty_histogram",
    title="Poverty rate distribution",
    attribution="U.S. Census Bureau ACS 5-Year, 2022",
)
# -> {"png": "...", "svg": "...", "sidecar": "..."}
```

Each module exposes a `KINDS` tuple and a `render(...)` function. Activity logging wraps the outer script call via `log_stage_start` / `log_stage_end`.

## Handoff

Add produced charts to the cartography handoff's `charts[]` array (parallel to `maps[]`):

```json
{
  "charts": [
    {
      "path": "outputs/charts/poverty_histogram.png",
      "svg": "outputs/charts/poverty_histogram.svg",
      "sidecar": "outputs/charts/poverty_histogram.style.json",
      "family": "distribution",
      "kind": "histogram",
      "field": "poverty_rate",
      "pairs_with": "outputs/maps/poverty_choropleth.png"
    }
  ]
}
```

`pairs_with` (optional) lets report-writer place the chart adjacent to its companion map in narrative reports.

## Validation

```bash
python scripts/core/validate_cartography.py \
  --charts-dir analyses/p1/outputs/charts/
```

Failure blocks Gate B the same way a failing map does.

## Anti-patterns

See `CHART_DESIGN_STANDARD.md`. Common failures we've caught:

- Calling `generate_chart.py` with no `--attribution` on a report-destined chart
- Using `kind=histogram` on categorical data (use `bar` instead)
- Skipping the paired `distribution` chart next to a choropleth — reader can't see skew
- Producing a 200-row `bar` chart with no `--top-n` — label overlap is unreadable
