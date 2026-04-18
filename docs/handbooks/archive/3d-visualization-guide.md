# 3D Terrain Visualization Guide

_Part of the GIS Agent Handbook Series_

---

## When to Use 3D Terrain

3D terrain visualization is a powerful storytelling tool — but it has real costs (complexity, accessibility, performance). Use it deliberately.

### ✅ Good use cases

| Scenario | Why 3D helps |
|---|---|
| Elevation-dependent phenomena | Flood risk, habitat, viewsheds — elevation IS the story |
| Topographically isolated communities | Showing why a valley town has limited healthcare access |
| Environmental justice + terrain | Industrial siting in low-elevation or enclosed basins |
| Public-facing engagement pieces | Interactive terrain grabs attention at community meetings |
| Wildfire risk or watershed analysis | Steep slopes + thematic data = compelling combined view |

### ❌ When NOT to use 3D

- **Statistical comparisons across many tracts** — use choropleth. Depth perception distorts area.
- **Print deliverables** — PNG previews have significant perspective distortion at page scale.
- **Flat plains or coastal lowlands** — vertical exaggeration needed to see anything creates false impression of rugged terrain.
- **Accessibility-first requirements** — screen readers and low-vision users get nothing from 3D.
- **Fast turnaround without iterative client input** — 3D parameter choices (exaggeration, angle) often need tuning.

### 🤔 Middle ground

Pair a 3D terrain view with a flat choropleth in a side-by-side or tab layout. Let users toggle. The 3D earns its place as a "wow" entry point while the flat map carries the analytical weight.

---

## Script Reference

### `render_3d_terrain.py`

**Location:** `scripts/render_3d_terrain.py`

Generates a PNG preview (matplotlib 3D) and/or a self-contained MapLibre GL JS HTML viewer with deck.gl TerrainLayer. All open source, no API keys required.

#### Full argument reference

| Argument | Required | Default | Description |
|---|---|---|---|
| `--dem` | ✅ | — | Input DEM GeoTIFF path |
| `--overlay` | ❌ | — | GeoPackage for thematic color overlay |
| `--overlay-col` | ❌ | — | Column in overlay to drive color ramp |
| `--output-html` | ❌* | — | Output self-contained HTML file |
| `--output-png` | ❌* | — | Output matplotlib PNG preview |
| `--title` | ❌ | `"3D Terrain Visualization"` | Map title |
| `--exaggeration` | ❌ | `2.0` | Vertical scale factor |

*At least one output required.

#### Examples

```bash
# Quick PNG preview
python scripts/render_3d_terrain.py \
    --dem data/rasters/mn_dem.tif \
    --output-png outputs/terrain/mn_preview.png \
    --title "Minnesota Elevation" \
    --exaggeration 3.0

# Full interactive HTML with poverty overlay
python scripts/render_3d_terrain.py \
    --dem data/rasters/mn_dem.tif \
    --overlay analyses/mn-poverty-change/data/processed/tracts.gpkg \
    --overlay-col pct_poverty_2022 \
    --output-html outputs/terrain/mn_poverty_terrain.html \
    --output-png  outputs/terrain/mn_poverty_terrain.png \
    --title "Minnesota Poverty Rate Over Terrain" \
    --exaggeration 2.5
```

#### Output files

| File | Description |
|---|---|
| `*.html` | Self-contained HTML page (embed in report site or open standalone) |
| `*.png` | Matplotlib 3D perspective preview (good for PDF reports) |
| `*.log.json` | Run log with DEM metadata, bounds, elevation range |

#### Vertical exaggeration guide

| Terrain type | Recommended exaggeration |
|---|---|
| High mountains (Rockies, Cascades) | 1.0 – 1.5 |
| Moderate relief (Appalachians, Ozarks) | 2.0 – 3.0 |
| Low rolling plains (Midwest) | 3.0 – 5.0 |
| Coastal plains, deltas | 5.0 – 8.0 |

---

## MapLibre GL JS + deck.gl Setup

### Why this stack?

| Component | License | Notes |
|---|---|---|
| **MapLibre GL JS** | BSD-3-Clause | Open source fork of Mapbox GL JS (pre-v2). No API key needed. |
| **deck.gl** | Apache 2.0 | Uber open source WebGL visualization framework. TerrainLayer is built-in. |
| **CARTO Basemaps** | Free/ODbL | Free raster tiles from CartoDB. Dark basemap included by default. |

No Mapbox, no proprietary APIs, no paid tokens required.

### How the script loads them

Both libraries load from the `unpkg` CDN at pinned versions:

```html
<!-- MapLibre GL JS (BSD-3-Clause) -->
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>

<!-- deck.gl (Apache 2.0) -->
<script src="https://unpkg.com/deck.gl@9.0.28/dist.min.js"></script>
```

The output is a single `.html` file with no external dependencies at runtime (the DEM is embedded as a base64 data URI).

### TerrainLayer: Terrarium encoding

deck.gl's `TerrainLayer` decodes elevation from an RGB-encoded PNG using the **Terrarium** scheme:

```
elevation = (R * 256 + G + B/256) - 32768   (meters)
```

The script encodes the DEM into this format using `rasterio` + `Pillow` (`PIL`). The encoded PNG is embedded inline as a base64 data URI.

The `elevationDecoder` config in the script:
```js
elevationDecoder: {
  rScaler: 256,
  gScaler: 1,
  bScaler: 1 / 256,
  offset: -32768,
}
```

### MapboxOverlay adapter

deck.gl's `MapboxOverlay` class provides a MapLibre/Mapbox-compatible control that synchronizes deck.gl rendering with the map camera. This is the recommended integration path as of deck.gl v9:

```js
const deckOverlay = new deck.MapboxOverlay({ layers: [terrainLayer, overlayLayer] });
map.addControl(deckOverlay);
```

---

## Open Source Tile Serving Options

For production use cases where you want to serve real tilesets (not embedded base64), here are open source options:

### Option 1: gdal2tiles (local file export)

Export your DEM as an XYZ tile pyramid:

```bash
# Install: usually bundled with GDAL
gdal2tiles.py \
  --zoom=6-12 \
  --resampling=bilinear \
  --tiledriver=PNG \
  data/rasters/mn_dem.tif \
  outputs/terrain/tiles/
```

Then serve with any static web server:
```bash
python -m http.server 8080
# → access tiles at http://localhost:8080/tiles/{z}/{x}/{y}.png
```

### Option 2: TiTiler (FastAPI tile server)

[TiTiler](https://developmentseed.org/titiler/) is an open source (MIT) cloud-optimized GeoTIFF tile server:

```bash
pip install titiler
uvicorn titiler.application.main:app --reload
# Tiles: http://localhost:8000/cog/tiles/{z}/{x}/{y}.png?url=<cog_url>
```

Pairs well with Cloud Optimized GeoTIFFs (COG). Convert your DEM:
```bash
gdal_translate -of GTiff -co TILED=YES -co COPY_SRC_OVERVIEWS=YES -co COMPRESS=LZW \
  dem.tif dem_cog.tif
```

### Option 3: Martin (vector tile server, Rust)

For vector overlays as PMTiles or PostGIS:

```bash
martin --config martin.yaml
```

### Option 4: PMTiles (single-file tile archive)

[PMTiles](https://github.com/protomaps/PMTiles) (BSD-2-Clause) stores an entire tile pyramid in one file, accessible via HTTP range requests — no tile server needed:

```bash
pip install pmtiles
```

Bundle your tiles and serve from S3 or any CDN that supports byte-range requests.

---

## Dependency Notes

### Required Python packages

```
rasterio        # DEM reading and reprojection
numpy           # Array math
matplotlib      # PNG 3D preview
Pillow          # Terrarium PNG encoding (PIL)
geopandas       # Overlay GeoPackage loading (optional)
```

Install:
```bash
pip install rasterio numpy matplotlib Pillow geopandas
```

Or in the Docker environment:
```bash
docker compose -f docker/docker-compose.yml run --rm gis-worker \
  pip install Pillow  # rasterio/numpy/geopandas already included
```

### Graceful degradation

- If `Pillow` is unavailable, the HTML is still generated but without the embedded DEM — terrain rendering will not work in-browser.
- If `geopandas` is unavailable, the script continues without the overlay layer.
- If `matplotlib` is unavailable, only the HTML output is generated.

---

## Integration with GIS Agent Workflow

3D terrain visualization fits naturally after raster analysis steps:

```
1. retrieve_tiger.py        → study area boundaries
2. terrain_analysis.py      → hillshade, slope, aspect from DEM
3. contour_generation.py    → contour lines for base context
4. analyze_choropleth.py    → thematic analysis (poverty, etc.)
5. render_3d_terrain.py     → 3D viewer combining DEM + thematic overlay  ← HERE
6. build_site.py            → embed HTML in report mini-site
```

The `.log.json` output from `render_3d_terrain.py` follows the standard GIS Agent log schema and can be included in handoff chains.

---

## Cartographic Cautions

1. **Label choropleth values clearly** — in 3D, color + elevation compete visually. Always include a legend.
2. **Avoid hot colorscales on terrain** — red-hot elevation + red-hot thematic overlay is confusing. The script uses RdYlBu for thematic data by default.
3. **Exaggeration disclaimer** — if sharing 3D previews in reports, note the exaggeration factor so readers don't misinterpret the terrain's actual steepness.
4. **Mobile performance** — deck.gl TerrainLayer is GPU-intensive. Test on mobile before client delivery.
5. **Accessibility** — always include a flat-map equivalent alongside any 3D visualization.

---

_Last updated: 2026-04-03_
