# Choropleth Design Workflow

## Purpose

- design and produce a single-variable choropleth map for a rate, percentage, share, or other normalized quantitative metric across polygons
- inherit the firm's universal cartographic rules from `standards/CARTOGRAPHY_STANDARD.md` and apply them to the thematic choropleth family

## Map Family

This workflow produces a **thematic choropleth**. Per the family taxonomy in `standards/CARTOGRAPHY_STANDARD.md`:

- basemap: forbidden
- scale bar: forbidden
- north arrow: forbidden
- title, legend, attribution, dissolved outline: required

The thematic choropleth family forbids chrome elements because the polygon fills are the visual story; chrome competes with the data layer.

## Typical Use Cases

- demographic rate by census tract or ZCTA (poverty rate, uninsured rate, median income)
- prevalence rate by health district or county
- share of a category by polygon (percent renters, percent in a tenure category)
- normalized metric where each polygon has a comparable per-area or per-population value

## Inputs

- analysis-ready GeoDataFrame with the polygons and the target field
- a single quantitative variable that is a rate, percentage, share, or other normalized metric (NOT a raw count)
- project brief specifying audience, geography, time period, and delivery format
- optional: a documented threshold or class break rationale if the project brief requires manual classification

## Preconditions

- CRS confirmed per `standards/CRS_SELECTION_STANDARD.md`
- structural QA passed per `standards/STRUCTURAL_QA_STANDARD.md`
- the variable is a rate, share, or normalized metric (raw counts must use proportional symbol or a different family)
- the dataset has been validated upstream and is not a snapshot of in-flight processing

## Preferred Tools

- `scripts/core/analyze_choropleth.py` — primary production script
- `scripts/core/render_web_map.py` — interactive Folium output
- `config/map_styles.json` — style registry (read before every map)
- `scripts/core/style_utils.py` — palette lookup and classification (imported by analyze_choropleth)
- `scripts/core/write_style_sidecar.py` — records styling decisions for QGIS inheritance
- `scripts/core/validate_cartography.py` — QA gate
- `scripts/core/check_colorblind.py` — accessibility validation

## Script Usage

```bash
# Basic (auto-palette from field name)
python scripts/core/analyze_choropleth.py data/processed/tracts.gpkg poverty_rate \
    -o outputs/maps/poverty_choropleth.png

# Full featured (inset, labels, attribution)
python scripts/core/analyze_choropleth.py data/processed/tracts.gpkg poverty_rate \
    --title "Poverty Rate by Census Tract, Douglas County, NE (2022)" \
    --attribution "U.S. Census Bureau ACS 5-Year Estimates, 2022" \
    --inset --labels \
    -o outputs/maps/poverty_choropleth.png

# Override auto-palette
python scripts/core/analyze_choropleth.py data/processed/tracts.gpkg median_income \
    --cmap YlGnBu --scheme quantiles \
    -o outputs/maps/income_choropleth.png

# With hatching for print accessibility
python scripts/core/analyze_choropleth.py data/processed/tracts.gpkg vacancy_rate \
    --pattern "///" --inset \
    -o outputs/maps/vacancy_choropleth.png
```

The script auto-resolves palettes via `config/map_styles.json` and writes a `.style.json` sidecar alongside every map PNG.

## Execution Order

1. **Confirm the data is normalized.** A choropleth on raw counts produces a population-density proxy and is misleading. If the input is a count, either compute a rate first (and use this workflow on the rate) or switch to a proportional symbol map.
2. **Confirm the family.** The map is a thematic choropleth. Apply the `CARTOGRAPHY_STANDARD.md` family rules (no basemap, no scale bar, no north arrow). Do not import chrome from other families.
3. **Let auto-palette resolve the colormap, or choose manually.** The script reads `config/map_styles.json` and matches field names to palettes (poverty → YlOrRd, income → YlGnBu, distance → YlOrBr). Override with `--cmap` only when the auto-selection doesn't fit. Match palette semantics to the variable: warm (YlOrRd, RdPu, magma) for risk and intensity; cool (YlGnBu, PuBu, viridis) for access and coverage.
4. **Choose a classification scheme.** Match the method to the distribution and the project brief:
   - natural breaks for skewed distributions
   - quantile when the project asks for rank framing
   - equal interval for uniform distributions
   - manual when the project defends a known threshold (and the threshold is documented)
5. **Set 4–5 classes** per the standard's classification rules. Three classes is too coarse; six or more overwhelms.
6. **Round legend break values** to readable numbers per the standard's legend rules.
7. **Apply the standard's border rules.** Thin (0.2 mm), white or light gray tract borders. Add a dissolved outer outline (0.35 mm, medium gray) on top as a separate layer.
8. **Set title and attribution** per the standard. Title names the metric, the geography, and the time period in plain language. Attribution names the data source and vintage.
9. **Add a "no data" category** if any features have null values for the target variable. Missing data is medium gray (#d0d0d0) per the standard, never white.
10. **Save at the family's numeric defaults.** DPI 200 preferred (150 minimum), figure size 14×10 for state-level or 12×10 for local-area framings.
11. **Run `qa-review/MAP_QA_CHECKLIST.md`** before declaring the map complete.

## Validation Checks

- the variable is a normalized metric, not a raw count
- the family is thematic choropleth and the family rules are respected (no basemap, no scale bar, no north arrow)
- the palette matches the variable type (sequential for magnitude, not categorical or diverging unless the project explicitly calls for them)
- classification has 4–5 classes
- the classification method is documented and appropriate for the distribution
- legend title uses a human label with units, not a raw field name
- legend break values are rounded
- a "no data" category is shown when null features exist
- tract borders are thin and light per the standard
- a dissolved outer outline is present per the standard
- title names metric, geography, and time period in plain language
- attribution cites source and vintage
- DPI and figure size meet the family defaults
- `MAP_QA_CHECKLIST.md` has been run

## Common Failure Modes

- mapping a raw count and producing a population-density proxy
- using equal-interval classification on a heavily skewed distribution, putting most features in one class
- using a diverging palette for a metric that has no meaningful midpoint
- showing missing data as white (it reads as zero) or omitting null features entirely
- legend title is the raw field name (`poverty_rate` instead of "Poverty Rate (%)")
- legend break values are unrounded (`0.00–4.53` instead of `0–5%`)
- only three classes (too coarse) or seven-plus (overwhelming)
- thick black tract borders that compete with the fill
- title editorializes or fails to name the metric, geography, or time period
- adding a basemap, scale bar, or north arrow despite the family taxonomy forbidding them on thematic choropleth

## Escalate When

- the project brief requires a non-standard projection or non-standard chrome configuration
- the data is too sparse or too noisy to support a meaningful classification
- the variable's distribution is bimodal or otherwise resistant to standard classification methods
- the audience is unfamiliar with choropleth maps and an alternative visualization (table, ranked bar) would communicate better
- the topic is politically or commercially sensitive and the visual framing could mislead

## Outputs

- a static PNG choropleth at 200 DPI, 14×10 inches (state-level) or 12×8 (local)
- a `.style.json` sidecar recording palette, classification, breaks, colors (for QGIS inheritance)
- a `.choropleth.json` metadata log with assumptions, warnings, and parameters
- optionally an interactive Folium web map via `render_web_map.py`
- optionally an inset locator map (`--inset`) and feature labels (`--labels`)

## Related Standards

- `standards/CARTOGRAPHY_STANDARD.md` — universal design rules and the family taxonomy this workflow inherits from
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition
- `standards/PUBLISHING_READINESS_STANDARD.md` — downstream gate before client delivery

## Related Workflows

- `workflows/POINT_OVERLAY_DESIGN.md` — when points are overlaid on a thematic base
- `workflows/HOTSPOT_MAP_DESIGN.md` — when the data is a clustering output
- `workflows/BIVARIATE_CHOROPLETH_DESIGN.md` — when two related variables are visualized together
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — common upstream stage producing the input dataset
- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — earlier upstream stage

## Related QA

- `qa-review/MAP_QA_CHECKLIST.md` — operational checks applied to the finished map
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative-side review when the map is paired with prose claims

## Sources

- firm cartographic methodology
- the cartography standard's source list (Buckley, Nelson, Tufte, Brewer)

## Trust Level

Validated Workflow — Needs Testing
