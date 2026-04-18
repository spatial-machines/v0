# GIS Agent Pipeline Standards
**Version:** 1.0 — 2026-04-05
**Status:** Mandatory. All pipeline scripts and agents must comply.

---

## 1. Cartographic Standards (Non-Negotiable)

Every map PNG produced by this framework must meet the requirements for its **map family**. Required elements are family-dependent — see the table below and `docs/wiki/standards/CARTOGRAPHY_STANDARD.md` for the full canonical standard.

### 1.1 Required Elements by Map Family

| Element | Thematic choropleth | Thematic categorical | Point overlay | Reference / orientation | Raster surface |
|---|---|---|---|---|---|
| **Basemap** (CartoDB.Positron) | Forbidden | Forbidden | Required | Required | (raster IS base) |
| **Scale bar** | Forbidden | Forbidden | Optional | Required | Required |
| **North arrow** | Forbidden | Forbidden | Optional | Required | Required |
| **Title** | Required | Required | Required | Required | Required |
| **Legend** | Required | Required | Required | Optional | Required |
| **Attribution** | Required | Required | Required | Required | Required |
| **Dissolved outline** (state/county boundary) | Required | Required | Required | Optional | Required |

### 1.1a Map Family Definitions

- **Thematic choropleth:** Single-variable polygon fills where the data IS the visual (e.g., poverty rate by tract, median income by ZCTA). Basemap, scale bar, and north arrow are forbidden — they compete with the data.
- **Thematic categorical:** Hotspot, LISA cluster, or other categorical polygon maps. Same chrome rules as thematic choropleth.
- **Point overlay:** Points overlaid on a polygon base where context matters. Basemap required; scale bar and north arrow optional.
- **Reference / orientation:** Maps where geographic context IS the message. All chrome elements required.
- **Raster surface:** DEM, hillshade, slope, suitability. The raster IS the base — no additional basemap needed.

### 1.2 Prohibited
- ❌ Black NoData — always mask to `np.nan` before plotting. Set `ax.set_facecolor("white")`
- ❌ Full raster/tile extent — always clip to analysis area + 5–10% padding
- ❌ Overlapping opaque circles as demographic choropleth — use tract polygons
- ❌ Scientific notation on axes — format as `{x:,.0f}` or use human units
- ❌ Inline matplotlib map generation — use the established scripts (see §3)
- ❌ Self-assigned QA scores without cartographic validation — run `validate_cartography.py`

### 1.3 Style Constants
```python
# Dissolved outline (state/county/study-area boundary) — draw on top
OUTLINE_EDGE_COLOR = "#555555"
OUTLINE_EDGE_WIDTH = 0.35

# Tract/interior borders — thin, subordinate
INTERIOR_EDGE_COLOR = "white"  # or light gray
INTERIOR_EDGE_WIDTH = 0.2

# Output quality
DPI = 200           # 200 preferred for client-grade; 150 minimum
FIGSIZE = (14, 10)  # 14x10 for state-level; 12x10 for local-area
FACECOLOR = "white"

# Basemap (point overlay and reference families only)
BASEMAP_SOURCE = contextily.providers.CartoDB.Positron
```

### 1.4 Raster Map Pattern
```python
import rasterio, numpy as np
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import geopandas as gpd
from rasterio.mask import mask as rio_mask
from shapely.geometry import box

# Always clip to analysis area
with rasterio.open(raster_path) as src:
    bounds = analysis_gdf.to_crs(src.crs).total_bounds
    pad = 0.05 * max(bounds[2]-bounds[0], bounds[3]-bounds[1])
    clip_geom = [box(bounds[0]-pad, bounds[1]-pad, bounds[2]+pad, bounds[3]+pad).__geo_interface__]
    data, transform = rio_mask(src, clip_geom, crop=True)
    data = data[0].astype(float)
    nodata = src.nodata
    if nodata is not None:
        data[data == nodata] = np.nan  # NEVER render NoData as black

fig, ax = plt.subplots(figsize=(12, 10))
ax.set_facecolor("white")
extent = rasterio.transform.array_bounds(data.shape[0], data.shape[1], transform)
ax.imshow(data, extent=[extent[0], extent[2], extent[1], extent[3]],
          cmap="gray", interpolation="nearest")

# Overlay analysis boundary
analysis_gdf.to_crs(src.crs).boundary.plot(
    ax=ax, edgecolor="#cc0000", linewidth=1.5)

# Scale bar
ax.add_artist(ScaleBar(1, units="m", location="lower right"))

# North arrow
ax.annotate("", xy=(0.97, 0.15), xycoords="axes fraction",
            xytext=(0.97, 0.08),
            arrowprops=dict(arrowstyle="->", lw=2, color="black"))
ax.text(0.97, 0.16, "N", transform=ax.transAxes,
        ha="center", fontsize=12, fontweight="bold")

fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
```

### 1.5 Vector Map Pattern (with contextily basemap)
```python
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

fig, ax = plt.subplots(figsize=(12, 10))

# Always reproject to Web Mercator for contextily
gdf_web = gdf.to_crs(epsg=3857)
gdf_web.plot(ax=ax, color=fill_color,
             edgecolor="#555555", linewidth=0.35, alpha=0.8)

ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom="auto")

ax.add_artist(ScaleBar(1, units="m", location="lower right"))
ax.annotate("", xy=(0.97, 0.15), xycoords="axes fraction",
            xytext=(0.97, 0.08),
            arrowprops=dict(arrowstyle="->", lw=2, color="black"))
ax.text(0.97, 0.16, "N", transform=ax.transAxes,
        ha="center", fontsize=12, fontweight="bold")
ax.set_axis_off()
ax.set_title("Descriptive Title", fontsize=14, fontweight="bold")

fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
```

---

## 2. Established Cartography Scripts (Use These — Do Not Reinvent)

| Script | Use For |
|---|---|
| `scripts/core/analyze_choropleth.py` | Any vector choropleth (income, rates, scores, z-scores) |
| `scripts/core/analyze_bivariate.py` | Two-variable bivariate choropleth (3×3 Stevens) |
| `scripts/core/overlay_points.py` | Points overlaid on a polygon/raster base |
| `scripts/core/compute_spatial_autocorrelation.py` | LISA cluster maps |
| `scripts/core/compute_hotspots.py` | Gi* hotspot maps |
| `scripts/core/analyze_dot_density.py` | Dot density for raw counts |
| `scripts/core/analyze_proportional_symbols.py` | Proportional circles for raw counts |
| `scripts/core/analyze_small_multiples.py` | Grid comparison of multiple variables |
| `scripts/core/analyze_uncertainty.py` | Two-panel estimate + MOE reliability |
| `scripts/core/render_web_map.py` | Interactive Folium web maps |

**Style registry:** Read `config/map_styles.json` before every map. Scripts auto-resolve field names to palettes via the `domain_palette_map`. Use `--inset` for locator maps, `--labels` for feature labels with halos, `--pattern` for print-accessible hatching.

**Style sidecar:** Every map script writes a `.style.json` sidecar alongside the PNG. This records the palette, classification, breaks, and colors so QGIS packages can reproduce the same styling. Do not skip this.

---

## 3. Cartographic Validation Gate

After generating every map PNG, call:
```python
from scripts.core.validate_cartography import validate_map
result = validate_map(output_path)
if not result["pass"]:
    raise RuntimeError(f"Map failed cartographic validation: {result['reason']}")
```

`validate_cartography.py` checks:
- File size > 50KB (blank maps are tiny)
- Not >90% single color (empty/failed render)
- Not >30% black pixels (NoData artifact)

If validation fails, fix the map before writing outputs or scoring.

---

## 4. Interactive Web Maps

Every analysis that ships to the portfolio site MUST include at least one interactive web map (`outputs/web/*.html`). Use Folium:

```python
import folium
import geopandas as gpd

m = folium.Map(location=[lat, lon], zoom_start=10,
               tiles="CartoDB positron")

# Add layers with toggle
folium.GeoJson(
    gdf.__geo_interface__,
    name="Layer Name",
    style_function=lambda f: {
        "fillColor": "#3182bd",
        "color": "#555555",
        "weight": 0.5,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(fields=["field1", "field2"])
).add_to(m)

folium.LayerControl().add_to(m)
m.save("outputs/web/map_name.html")
```

---

## 5. QA Scorecard Standards

The 30-point rubric weights:

| Category | Max Points | Key Requirements |
|---|---|---|
| Spatial statistics | 8 | Moran's I / Gi* / regression or morphometrics |
| Maps (quantity) | 6 | ≥4 maps; each must pass validate_cartography.py |
| Maps (quality) | 4 | Required elements present per map family (see §1.1) |
| **Charts** | **3** | **Paired charts per §1.4 rule; each must pass validate_cartography.py --charts-dir** |
| Interactive web map | 3 | ≥1 Folium HTML with layer toggle |
| Report | 4 | Pyramid Principle, findings first, methodology section |
| Data catalog | 2 | data_catalog.json with all outputs documented |
| QGIS package | 2 | .qgs + data/ gpkgs |
| **ArcGIS Pro package** | **2** | **.gdb + .lyrx layers + manifest; validate_arcgis_package.py passes** |
| Handoff files | 1 | cartography + analysis + publishing handoffs |

**Client-ready threshold: ≥28/35** (raised from 22/30 with charts + ArcGIS Pro added)
**An agent must never self-score this high if any map or chart fails `validate_cartography.py`, or if the ArcGIS Pro package fails `validate_arcgis_package.py`.**

### 5.1 Pairing rule for charts (mandatory)

Every **choropleth** must ship with a paired **distribution** chart (histogram / KDE / box) and a **comparison** chart (top-N bar / lollipop) on the same field. Every **bivariate** map must ship with a paired **scatter+OLS** on the same X/Y. Every **change-over-time** analysis must ship with a **line** chart; use `small_multiples` when comparing more than four geographies.

See `docs/wiki/standards/CHART_DESIGN_STANDARD.md` for the full rule and chart families.

### 5.2 ArcGIS Pro package minimum

Every ArcGIS Pro package must contain:
- `data/project.gdb/` — file geodatabase with every processed layer
- `layers/*.lyrx` — one styled layer file per map, generated from `.style.json` sidecars (no hand editing)
- `manifest.json`, `review-spec.json`, `review-notes.md`, `README.md`
- `make_aprx.py` helper (or pre-built `<slug>.aprx` when arcpy was available)

See `docs/wiki/standards/ARCGIS_PRO_PACKAGE_STANDARD.md`.

### 5.3 ArcGIS Online publishing discipline

When a project brief sets `outputs.publish_targets: ["arcgis_online"]`:
- Always run `publish_arcgis_online.py --dry-run` first and inspect `outputs/arcgis/publish-status.json` before a real upload.
- Default sharing is **PRIVATE**; promote to `ORG` / `PUBLIC` only when the brief sets `publish_sharing`.
- Credentials read from `.env`; never logged, never committed.

---

## 6. Output Directory Structure

```
analyses/<project-id>/
  data/                          # raw inputs
  data_catalog.json              # required
  outputs/
    maps/                        # PNG maps (≥4, all validated) + .style.json sidecars
    charts/                      # PNG + SVG charts (per pairing rule) + sidecars
    web/                         # Folium HTML interactive maps (≥1)
    reports/
      analysis_report.md         # required
      demo_report.html           # optional combined HTML report (demo uses this)
    spatial_stats/               # JSON handoff files
    qa_scorecard.md              # required, honest score
    qgis/
      data/                      # GeoPackages
      *.qgs                      # QGIS project file
    arcgis/
      data/
        project.gdb/             # file geodatabase
      layers/
        *.lyrx                   # styled ArcGIS Pro layer files
      charts/                    # charts copied for Pro layout embedding
      make_aprx.py               # helper to build .aprx inside Pro
      <slug>.aprx                # present only when arcpy was available
      publish-status.json        # present only when AGOL publishing ran
    solution_graph.png           # DAG of the analysis flow (PNG + SVG + JSON + Mermaid)
```

---

## 7. Report Structure (Pyramid Principle)

Every `analysis_report.md` must follow this order:
1. **Key Findings** (3–5 bullets, specific numbers, up top — not buried)
2. **Morphometrics / Summary Stats table**
3. **Methodology** (what tools, what parameters, why)
4. **Detailed Findings** (section per major analysis)
5. **Validation** (compare to known values, note discrepancies)
6. **Caveats & Limitations**
7. **Output File Inventory**

---

## 8. New Pipeline Checklist

Before shipping a new pipeline or analysis type, verify:
- [ ] Maps route through established scripts OR follow §1 patterns exactly
- [ ] All maps pass `validate_cartography.py`
- [ ] At least one Folium interactive map generated
- [ ] Report follows Pyramid Principle
- [ ] QA score reflects actual output quality (not aspirational)
- [ ] `data_catalog.json` written
- [ ] QGIS package built
- [ ] Registered in `analyses/registry.json`
