# TOOLS.md — Cartography

Approved operational tools for the Cartography role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`
- `config/map_styles.json` — unified map style registry (read before every map)
- `config/chart_styles.json` — chart style registry (read before every chart)
- `config/palettes.json` — semantic palette definitions

## Primary Tool Classes

- `cartography`
- `charts`
- `style`

## Approved Production Tools

### Static Delivery Maps (base thematic renderers)
- `analyze_choropleth.py` — single-variable thematic choropleth with auto-palette, feature labels, pattern fills, optional basemap, dynamic legend placement, style sidecar output
- `analyze_bivariate.py` — two-variable bivariate choropleth (3×3 Stevens' scheme) with style sidecar
- `overlay_points.py` — point features on polygon context with optional choropleth base
- `compute_hotspots.py` — Gi* hotspot analysis + categorical map with style sidecar
- `compute_spatial_autocorrelation.py` — LISA cluster map

### Composable Map Layers (scripts/core/layers/)
These layer scripts each expose a `render(ax, gdf, **kwargs)` function
AND a CLI. Chain them in a single figure for delivery-quality composition.
A map with inset + water + place labels + annotations is produced by
calling each in sequence on the same matplotlib Axes.

- `layers/add_water_layer.py` — renders Census TIGER AREAWATER features
  (lakes, rivers, bays). Auto-detects county from STATEFP/COUNTYFP in data.
  Theme-aware color (blue on light, dark teal on dark).
- `layers/add_place_labels.py` — labels top-N cities/towns by area from
  Census TIGER PLACE. Accepts custom GeoPackage for neighborhoods or
  community areas (e.g., Chicago's 77 community areas).
- `layers/add_inset_locator.py` — inset map showing study area within
  its state (or custom context geometry). Uses figure-relative coordinates
  so the inset sits in the margin, never overlapping data.
- `layers/add_top_n_annotations.py` — spatially-aware callout annotations.
  Labels pushed outward from map center with enforced angular separation;
  adjustText resolves any residual overlap. Accepts a `label_field`
  for human-readable names (neighborhood, place) instead of FIPS codes.
- `layers/_base.py` — shared helpers: font chain parsing, FIPS detection
  from data columns, theme inference from basemap.

**Composition pattern** (example: `analyses/demo-chicago-food-access/render_food_access_map.py`):
```python
import add_water_layer, add_place_labels, add_inset_locator, add_top_n_annotations

fig, ax = plt.subplots(...)
gdf.plot(ax=ax, ...)                              # base choropleth
cx.add_basemap(ax, ...)                           # contextual basemap
add_water_layer.render(ax, gdf)                   # water features
add_place_labels.render(ax, gdf, top_n=8)         # city labels
add_top_n_annotations.render(ax, gdf,             # callouts with
    field="score", label_field="community_area")  #   neighborhood names
add_inset_locator.render(fig, ax, gdf,            # inset in margin
    placement="upper-left", size=0.15)
```

### Secondary Map Types
- `analyze_dot_density.py` — dot density for count data
- `analyze_proportional_symbols.py` — proportional circles for count data
- `analyze_small_multiples.py` — small multiples grid for comparing variables
- `analyze_uncertainty.py` — two-panel estimate + reliability maps (ACS MOE)

### Interactive Web Maps
- `render_web_map.py` — Folium multi-layer interactive maps with toggles and popups

### Statistical Charts
- `generate_chart.py` — family-aware CLI entry point (distribution / comparison / relationship / timeseries)
- `charts/distribution.py` — histogram, KDE, box, violin
- `charts/comparison.py` — bar, grouped_bar, lollipop, dot
- `charts/relationship.py` — scatter, scatter_ols, hexbin, correlation_heatmap
- `charts/timeseries.py` — line, area, small_multiples
- `charts/_base.py` — shared theming, palette routing, save-chart helper (import only)

### Style & Validation
- `style_utils.py` — palette lookup, color ramp interpolation, classification, field role detection (utility, import only)
- `write_style_sidecar.py` — write .style.json sidecar for QGIS / ArcGIS inheritance (maps)
- `validate_cartography.py` — QA gate for map PNGs AND chart PNGs (size, blank check, sidecar validity, chart_family)
- `check_colorblind.py` — colorblind accessibility simulation and validation
- `renderers.py` — shared sidecar → ArcGIS Pro CIM / ArcGIS Online renderer translation (import only)

## Key Parameters (analyze_choropleth.py)

| Flag | Purpose |
|---|---|
| `--cmap` | Override auto-selected colormap |
| `--scheme` | Classification: natural_breaks, quantiles, equal_interval |
| `--k` | Number of classes (default 5) |
| `--inset` | Add inset locator map for geographic context |
| `--labels` | Add feature labels with halos |
| `--pattern` | Add hatching for print accessibility |
| `--attribution` | Source citation text |
| `--no-sidecar` | Skip .style.json sidecar output |

## Style Registry Workflow

1. Read `config/map_styles.json` to get the family profile for the map type
2. The script auto-resolves the field name to a palette via `domain_palette_map`
3. Apply the family's typography, stroke, legend, and figure settings
4. After rendering, write a `.style.json` sidecar with the exact decisions made
5. The QGIS packager reads this sidecar to reproduce the same styling

## Inputs You Depend On

- analysis-ready outputs (GeoPackage, GeoJSON)
- analysis handoff
- project brief
- style registry (`config/map_styles.json`)

## Outputs You Are Expected To Produce

- delivery-quality static maps (PNG, 200 DPI)
- statistical charts (PNG + SVG, 200 DPI) — see the pairing rule in `CHART_DESIGN_STANDARD.md`
- `.style.json` sidecars for each map and each chart
- map metadata / log JSONs (`.choropleth.json`, etc.)
- optional interactive map HTML (Folium)

## Operational Rules

- always read the relevant style registry before rendering (`map_styles.json` for maps, `chart_styles.json` for charts)
- let auto-palette resolve the colormap unless you have a documented reason to override
- every map PNG must have a companion .style.json sidecar
- every chart must produce PNG + SVG + .style.json (with `chart_family`)
- apply the pairing rule: choropleth → distribution + top-N; bivariate → scatter_ols; time series → line
- visual quality review is your responsibility
- structural QA is not your responsibility
- do not treat aesthetic preference as a substitute for methodological fit
- run `validate_cartography.py --input-dir outputs/maps/ --charts-dir outputs/charts/` before handoff
