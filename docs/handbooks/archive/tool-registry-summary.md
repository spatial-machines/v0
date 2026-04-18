# GIS Tool Registry Summary

**Date:** 2026-04-04  
**Registry:** `projects/gis-agent/tool-registry/tool_registry.json`  
**Source:** Penn State SpatialAnalysisAgent (Akinboyewa et al. 2024)

---

## Totals

| Metric | Count |
|--------|-------|
| **Total tools ingested** | **679** |
| Tools with full descriptions | 369 |
| Tools with Python equivalents | 56 |
| Tools patched with manual descriptions | 16 |

---

## Breakdown by Category

| Category | Count | Notes |
|----------|-------|-------|
| `raster_ops` | 225 | Clip, merge, warp, proximity, band math, rasterize |
| `terrain` | 157 | Slope, aspect, hillshade, TPI, TRI, viewshed, contours |
| `vector_ops` | 152 | Buffer, dissolve, clip, overlay, spatial join |
| `remote_sensing` | 36 | Imagery classification, NDVI, spectral analysis (GRASS i.* tools) |
| `network` | 31 | Routing, service area, shortest path, connectivity |
| `format_conversion` | 28 | Format conversion, OGR utilities, virtual datasets |
| `statistics` | 16 | Zonal statistics, field statistics, summaries |
| `hydrology` | 12 | Watershed, flow accumulation, stream extraction, TWI |
| `interpolation` | 10 | IDW, kriging, TIN, linear interpolation |
| `visualization` | 7 | Heatmap, KDE density surfaces |
| `classification` | 5 | Image segmentation, k-means, supervised classification |

---

## Breakdown by Exec Route

| Exec Route | Count | When Agents Should Use |
|-----------|-------|------------------------|
| `grass` | 306 | GRASS GIS session — hydrology, image analysis, network |
| `pure_python` | 269 | Direct geopandas/shapely — fastest, no extra deps |
| `qgis_headless` | 52 | Headless QGIS — complex multi-step analysis |
| `rasterio` | 42 | rasterio/richdem/numpy — terrain and raster ops |
| `gdal_cli` | 10 | GDAL command-line via subprocess |

---

## Breakdown by Provider

| Provider | Count | Domain |
|----------|-------|--------|
| `grass7` | 306 | Hydrology, network, image analysis, terrain |
| `native` | 265 | Core vector ops (QGIS built-in C++) |
| `gdal` | 56 | Raster/vector I/O, terrain, format conversion |
| `qgis` | 51 | QGIS Python analysis algorithms |
| `3d` | 1 | 3D mesh/polygon tessellation |

---

## Source Quality

| Quality | Count | Description |
|---------|-------|-------------|
| `good` | 369 | Full description + parameters from source JSON |
| `minimal` | 294 | GRASS tool IDs only (source JSON has a data bug — see note) |
| `patched` | 16 | Key GRASS + native tools with manually researched descriptions |

> **Known data issue:** The Penn State source JSON has all 306 GRASS tool descriptions incorrectly 
> overwritten with the `gdal:warpreproject` text. The 12 highest-value GRASS tools are manually patched.
> Category and exec_route for GRASS tools are inferred from module prefix (r.*, v.*, i.*, etc.) and 
> tool name keywords. GRASS parameters in the source JSON are similarly corrupt (all show warp params).

---

## Top 20 Most Useful Tools for Consulting Work

These are the highest-frequency tools in typical GIS consulting workflows, ordered by estimated usage:

| # | Tool ID | Category | Exec Route | Python Equivalent |
|---|---------|----------|-----------|-------------------|
| 1 | `native:buffer` | vector_ops | pure_python | `gdf.buffer(distance)` |
| 2 | `native:clip` | vector_ops | pure_python | `geopandas.clip(gdf, mask)` |
| 3 | `native:dissolve` | vector_ops | pure_python | `gdf.dissolve(by='field')` |
| 4 | `native:intersection` | vector_ops | pure_python | `geopandas.overlay(how='intersection')` |
| 5 | `native:joinattributesbylocation` | vector_ops | pure_python | `geopandas.sjoin(gdf1, gdf2)` |
| 6 | `native:reprojectlayer` | vector_ops | pure_python | `gdf.to_crs(epsg=4326)` |
| 7 | `native:zonalstatisticsfb` | statistics | pure_python | `rasterstats.zonal_stats(gdf, raster)` |
| 8 | `native:extractbyattribute` | vector_ops | pure_python | `gdf[gdf['field'] == val]` |
| 9 | `native:extractbylocation` | vector_ops | pure_python | `geopandas.sjoin()` variants |
| 10 | `native:fixgeometries` | vector_ops | pure_python | `gdf.geometry.make_valid()` |
| 11 | `gdal:cliprasterbymasklayer` | raster_ops | rasterio | `rasterio.mask.mask(src, shapes, crop=True)` |
| 12 | `gdal:aspect` | terrain | rasterio | `richdem.TerrainAttribute(dem, 'aspect')` |
| 13 | `gdal:slope` | terrain | rasterio | `richdem.TerrainAttribute(dem, 'slope_degrees')` |
| 14 | `gdal:hillshade` | terrain | rasterio | `richdem.TerrainAttribute(dem, 'hillshade')` |
| 15 | `gdal:merge` | raster_ops | rasterio | `rasterio.merge.merge([src1, src2])` |
| 16 | `gdal:contour` | terrain | rasterio | `matplotlib.contour()` → shapely |
| 17 | `gdal:warpreproject` | raster_ops | rasterio | `rasterio.warp.reproject(source, dest)` |
| 18 | `gdal:proximity` | raster_ops | rasterio | `scipy.ndimage.distance_transform_edt()` |
| 19 | `gdal:rastercalculator` | raster_ops | rasterio | `numpy` operations on rasterio arrays |
| 20 | `grass7:r.watershed` | hydrology | grass | whitebox-tools or GRASS r.watershed |

---

## Key Python Libraries to Install

Based on tool coverage, install these to unlock the highest-value tools:

```bash
pip install rasterstats      # native:zonalstatisticsfb — CRITICAL
pip install richdem          # gdal:aspect/slope/hillshade/TRI/TPI — HIGH
pip install rasterio         # most gdal:* raster tools — likely already installed
pip install geopandas        # most native:* vector tools — likely already installed
pip install scipy            # gdal:proximity, gdal:grid* interpolation — MEDIUM
pip install pykrige          # kriging interpolation — OPTIONAL
```

---

## How to Query the Registry

### Find a tool for a task:
```bash
python3 projects/gis-agent/tool-registry/tool_lookup.py --search "slope analysis"
python3 projects/gis-agent/tool-registry/tool_lookup.py --search "watershed" --exec-route grass
```

### Filter by exec route (headless/no-QGIS):
```bash
python3 projects/gis-agent/tool-registry/tool_lookup.py --exec-route pure_python --category vector_ops
python3 projects/gis-agent/tool-registry/tool_lookup.py --exec-route rasterio
```

### Look up a specific tool:
```bash
python3 projects/gis-agent/tool-registry/tool_lookup.py --id gdal:aspect --verbose
```

### In Python agent code:
```python
from projects.gis_agent.tool_registry.tool_lookup import GISToolRegistry

reg = GISToolRegistry("/path/to/tool_registry.json")
tool = reg.get("gdal:aspect")
print(tool["python_equivalent"])  # → richdem.TerrainAttribute(...)
print(tool["exec_route"])         # → rasterio

# Search in agent reasoning
candidates = reg.search("clip raster to study area", exec_route="rasterio")
```

---

## Registry Update Procedure

```bash
# Re-download and rebuild from Penn State source
cd projects/gis-agent/tool-registry/
python3 ingest_tools.py

# Or with local cached copy
curl -s "https://raw.githubusercontent.com/Teakinboyewa/SpatialAnalysisAgent/master/SpatialAnalysisAgent/Tools_Documentation/qgis_tools_for_rag.json" -o /tmp/qgis_tools_raw.json
python3 ingest_tools.py /tmp/qgis_tools_raw.json
```

---

*Generated by tool-registry-build subagent on 2026-04-04.*
