# QGIS Tool Knowledge for GIS Agents: Research Brief

**Date:** 2026-04-04  
**Prepared for:** Chris / GIS consulting firm multi-agent system  
**Question:** Should we ingest the Penn State SpatialAnalysisAgent TOML tool definitions, and how?

---

## 1. Executive Summary

**Short answer: Yes, ingest them — but transform them first.**

The Penn State repo documents ~300+ QGIS tools in a well-structured TOML format that is the best freely available machine-readable GIS tool knowledge base in existence. However, the tool definitions are written for QGIS-embedded execution (using `processing.run()` inside a QGIS session). For your headless Docker-based agent stack, you need to **transform the definitions**, not use them raw.

**The recommendation:**

1. **Clone the TOML files** from `SpatialAnalysisAgent/Tools_Documentation/QGIS_Tools/` — free to use (GPL-licensed).  
2. **Build a dual-layer tool registry**: a semantic description layer (what the tool does, parameters, use cases) AND an execution layer (pure Python implementation or GDAL CLI alternative).  
3. **Prioritize the ~60 GDAL tools and ~100 most-used GRASS/native tools** for your registry. Don't try to cover all 300+ on day one.  
4. **Use structured JSON over RAG for tool dispatch** in your multi-agent system. RAG is the right approach for "which tool should I use" (retrieval), but a structured tool catalog is better for "how do I call it" (execution).  
5. **Add `rasterstats`** to your Docker stack today — it's the single biggest gap relative to what the QGIS tools can do.

---

## 2. Penn State Repo: What's Actually In It

**Repository:** https://github.com/Teakinboyewa/SpatialAnalysisAgent  
**Paper:** Akinboyewa et al. 2024, "GIS Copilot: Towards an Autonomous GIS Agent for Spatial Analysis" (IJGIS)  
**Plugin page:** https://plugins.qgis.org/plugins/SpatialAnalysisAgent-master/

### Tool Count and Location

Tools live at: `SpatialAnalysisAgent/Tools_Documentation/QGIS_Tools/`

The Penn State lab's own website claims **"over 600 QGIS processing tools"** are supported. The TOML directory contains a subset with full structured documentation. Based on direct inspection of the GitHub tree, the documented tools break down as:

| Provider Prefix | Tools Documented | Category |
|---|---|---|
| `gdal_` | ~57 | Raster ops, terrain, vector conversion, format I/O |
| `grass7_` | ~150+ | Hydrology, image analysis, network, terrain, raster |
| `native_` | ~80+ | Core vector ops (buffer, clip, join, dissolve, etc.) |
| `qgis_` | ~30+ | Spatial analysis, heatmap, interpolation |
| `3d_` | 1 | 3D tessellation |
| **Total (est.)** | **~320** | Across all provider namespaces |

Plus 2 **customized tools** in a separate folder: `thematic_map_creation.toml` and a test tool — these are the team's own Python-library-based tools (geopandas, seaborn).

### Structure of Each TOML Definition

Every `.toml` file has the same schema:

```toml
tool_ID = "gdal:aspect"
tool_name = "Aspect"
brief_description = """One-sentence description of what it does."""
full_description = """Full description including algorithm derivation, default menu location."""
parameters = """
PARAM_NAME: Human-readable name. Description of what it controls. Type: [type] Default: value
...
"""
code_example = """
import processing
from qgis.core import QgsRasterLayer, QgsProject

def compute_aspect():
    # ... QGIS Python code using processing.run('gdal:aspect', parameters)
"""
```

**Key observation**: The `parameters` field is a freeform string (not structured key-value), which means you'd need to parse it with regex or LLM if you want typed parameter extraction. The `code_example` is always QGIS-embedded Python — not standalone.

**Example — `gdal:aspect`:**
- Generates slope aspect (compass direction) from elevation raster
- Parameters: INPUT (raster), BAND (int), TRIG_ANGLE (bool), ZERO_FLAT (bool), COMPUTE_EDGES (bool), ZEVENBERGEN (bool), OUTPUT (raster)
- Code: calls `processing.run('gdal:aspect', {...})`

**Example — `gdal:contour`:**
- Extracts contour lines from elevation raster
- Parameters: INPUT, BAND, INTERVAL (float, default 10.0), FIELD_NAME (string), OFFSET, CREATE_3D (bool), IGNORE_NODATA (bool), OUTPUT

**Example — `gdal:proximity`:**
- Raster distance surface from target pixels
- Parameters: INPUT (raster, must be rasterized), BAND, VALUES (target pixel list), UNITS (pixel vs georef), MAX_DISTANCE, REPLACE, NODATA, DATA_TYPE

**Example — `gdal:hillshade`:**
- Generates shaded relief from DEM
- Parameters: INPUT, BAND, Z_FACTOR (1.0), SCALE (1.0), AZIMUTH (315°), ALTITUDE (45°), COMPUTE_EDGES, ZEVENBERGEN, COMBINED, MULTIDIRECTIONAL

**Quality assessment**: The definitions are good — clear descriptions, complete parameter lists, working code examples. The code examples use hardcoded paths (`D:/Data/`) which is sloppy but the structure is otherwise clean. Quality is roughly uniform across tool providers.

**What's missing from the TOMLs:**
- No Python-native equivalents (everything assumes QGIS)
- No tagged categories (you have to infer raster vs vector from tool ID prefix)
- Parameter descriptions are prose strings, not typed schemas
- Some TOMLs have empty `parameters = ""` (clip by mask layer is an example — probably a generation artifact)

---

## 3. QGIS Processing Framework: Full Scope

QGIS processing has ~6 core providers plus optional plugins:

| Provider | Algorithm Count | Key Domain |
|---|---|---|
| `native:` (QGIS C++) | ~243–316 | Vector analysis, spatial joins, geometry ops |
| `grass:` (GRASS GIS) | ~306–307 | Hydrology, image processing, network analysis |
| `sagang:` (SAGA Next Gen) | ~509–589 | Terrain, statistics, advanced morphometry |
| `gdal:` (GDAL/OGR) | ~56–57 | Raster I/O, terrain, vector conversion |
| `qgis:` (QGIS Python) | ~35–50 | Heatmap, interpolation, spatial analysis |
| `3d:` | 1 | 3D mesh |
| `pdal:` (Point clouds) | 17 | LiDAR processing |

**Total core (without SAGA):** ~700–750 algorithms  
**Total with SAGA:** ~1,250–1,300 algorithms  
**Total with third-party plugins** (WhiteboxTools=546, QNEAT3=14, Networks=48, etc.): **~2,000+**

The Penn State TOMLs cover roughly the top 320 most-used tools across gdal, grass, native, and qgis namespaces. SAGA tools are largely absent from the documentation, which is appropriate — SAGA is rarely needed for consulting-style workflows.

**Provider namespaces that matter most for your work:**
- `native:` — buffer, clip, dissolve, spatial join, extract by attribute/location, fix geometries, reproject, zonal statistics (vector), field calculator
- `gdal:` — terrain analysis, raster clip/merge/warp, contours, format conversion, proximity
- `grass:` — watershed, network analysis, image classification, viewshed

---

## 4. Python Equivalence Map

### Tier 1: Fully Replicable in Pure Python (Your Current Stack)

These QGIS tools have **direct, production-quality Python equivalents** with geopandas/shapely/rasterio:

| QGIS Tool | Python Equivalent | Notes |
|---|---|---|
| `native:buffer` | `gdf.buffer(distance)` | Full equivalent |
| `native:dissolve` | `gdf.dissolve(by='field')` | Full equivalent |
| `native:clip` | `geopandas.clip(gdf, mask)` | Full equivalent |
| `native:intersection` | `geopandas.overlay(how='intersection')` | Full equivalent |
| `native:union` | `geopandas.overlay(how='union')` | Full equivalent |
| `native:difference` | `geopandas.overlay(how='difference')` | Full equivalent |
| `native:joinattributesbylocation` | `geopandas.sjoin()` | Full equivalent |
| `native:reprojectlayer` | `gdf.to_crs(crs)` | Full equivalent |
| `native:fixgeometries` | `gdf.make_valid()` | Shapely 2.0 |
| `native:centroids` | `gdf.centroid` | Full equivalent |
| `native:extractbyattribute` | `gdf[gdf.col == val]` | Full equivalent |
| `native:extractbylocation` | `geopandas.sjoin()` variants | Full equivalent |
| `native:fieldcalculator` | pandas apply/assign | Full equivalent |
| `native:addautoincrementalfield` | `enumerate()` | Trivial |
| `gdal:warpreproject` | `rasterio.warp.reproject()` | Full equivalent |
| `gdal:cliprasterbymasklayer` | `rasterio.mask.mask()` | Full equivalent |
| `gdal:cliprasterbyextent` | `rasterio.mask` with bounds | Full equivalent |
| `gdal:merge` | `rasterio.merge()` | Full equivalent |
| `gdal:rastercalculator` | `numpy` + `rasterio` | Full equivalent |
| `gdal:polygonize` | `rasterio.features.shapes()` | Full equivalent |
| `gdal:rasterize` | `rasterio.features.rasterize()` | Full equivalent |
| `gdal:translate` | `gdal.Translate()` or `rasterio.open/write` | Full equivalent |
| `native:spatialindex` | `gdf.sindex` | geopandas auto-manages |
| `native:deleteholes` | `shapely.remove_holes()` | Shapely 2.0 |

### Tier 2: Replicable with Additional Python Libraries (Not Currently in Stack)

These tools need libraries you **should add to your Docker image**:

| QGIS Tool | Python Library | Notes |
|---|---|---|
| `native:zonalstatisticsfb` | `rasterstats` | **CRITICAL GAP. Add now.** |
| `gdal:aspect` | `richdem` or `rio-terrain` | Pure Python DEM analysis |
| `gdal:slope` | `richdem` | Full equivalent |
| `gdal:hillshade` | `richdem` or `earthpy` | Full equivalent |
| `gdal:triterrainruggednessindex` | `richdem` | |
| `gdal:tpitopographicpositionindex` | `richdem` | |
| `gdal:roughness` | `richdem` | |
| `gdal:contour` | `matplotlib.contour` → shapely / `richdem` | Usable |
| `gdal:proximity` | `scipy.ndimage.distance_transform_edt` | After rasterize |
| `gdal:fillnodata` | `scipy.interpolate` / `rasterio.fill` | Partial |
| `gdal:gridinversedistance` | `scipy.interpolate` (IDW) | DIY required |
| `gdal:gridlinear` | `scipy.interpolate.LinearNDInterpolator` | Full equivalent |
| `gdal:gridnearestneighbor` | `scipy.interpolate.NearestNDInterpolator` | Full equivalent |
| `gdal:sieve` | `rasterio.features.sieve()` | Built-in! |
| `native:heatmapkerneldensityestimation` | `sklearn.neighbors.KernelDensity` | |
| `native:randomextract` | `gdf.sample()` | Trivial |
| `qgis:kriging` | `pykrige` | Add library |
| `native:pointsalonggeometry` | `shapely.line.interpolate` | Manual |

### Tier 3: Requires GDAL CLI or Subprocess (Available Headlessly)

These tools are best called as subprocesses against GDAL command-line tools, which **are available in your rasterio Docker environment**:

| QGIS Tool | Headless Equivalent |
|---|---|
| `gdal:buildvirtualraster` | `gdalbuildvrt` CLI via subprocess |
| `gdal:gdal2tiles` | `gdal2tiles.py` CLI |
| `gdal:retile` | `gdal_retile.py` CLI |
| `gdal:overviews` | `gdaladdo` CLI |
| `gdal:gdalinfo` | `gdalinfo` CLI or `rasterio.open()` |
| `gdal:ogrinfo` | `ogrinfo` CLI or geopandas |

### Tier 4: Needs QGIS Running (But Possible Headlessly with qgis-headless)

These have no clean pure-Python equivalent but work in headless QGIS (`qgis-headless` Docker image):

| Tool | Why Needs QGIS |
|---|---|
| `native:voronoipolygons` | Complex Voronoi — scipy.Voronoi is alternative |
| `native:topologicalcoloring` | Graph coloring specific |
| Advanced graph network tools | QNEAT3 plugin algorithms |

### Tier 5: Requires GRASS or SAGA (Significant Overhead)

Only worth setting up if you regularly need these:

| Tool | Use Case | Alternative |
|---|---|---|
| `grass7:r.watershed` | Hydrology, catchment delineation | `whitebox-tools` Python wrapper |
| `grass7:r.cost` | Least-cost path analysis | `scikit-image.graph.route_through_array` |
| `grass7:v.net.*` | Advanced network routing | `networkx` or `osmnx` for most cases |
| `grass7:i.segment` | Image segmentation | `scikit-image` |
| SAGA terrain tools | Advanced terrain morphometry | `richdem` covers most |

**Bottom line:** ~60% of the Penn State-documented tools can be replicated in your current stack or with 2-3 additional libraries (`rasterstats`, `richdem`, `pykrige`). The remainder require GDAL CLI (already available), QGIS headless, or GRASS — which you should treat as optional backends.

---

## 5. Recommended Architecture

### The Problem with Straight RAG over TOMLs

Penn State's approach — FAISS vector index over all TOML files, retrieved by user query — works for their use case (a human-facing QGIS plugin). For your multi-agent system it has problems:

1. **The code examples are wrong for your runtime**: every `code_example` calls `processing.run()` inside QGIS. Your agents would generate broken code.
2. **No execution routing**: RAG retrieval doesn't distinguish "I can do this in pure Python" from "this needs GDAL CLI." An agent needs to know the route to take.
3. **Parameter descriptions are prose strings**: not parseable without another LLM call.
4. **600+ documents is noisy for RAG**: retrieval precision drops when the corpus is large and tools are similar (e.g., 8 different grid interpolation tools).

### Recommended Architecture: 3-Layer Tool Knowledge System

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: Semantic Index (what tools exist, what they do)   │
│  - Vector embeddings of tool_name + brief_description       │
│  - Used by: "which tool should I use for X?" queries        │
│  - ~300 documents, dense retrieval (FAISS/chromadb)         │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: Tool Registry (structured JSON, how to call)      │
│  - Augmented TOML content + Python equivalents              │
│  - Keys: tool_id, description, params, python_impl,         │
│          exec_route (pure_python/gdal_cli/qgis_headless)    │
│  - Used by: code generation after tool is selected          │
│  - Fetched by exact key lookup (not RAG)                    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: Code Examples Library (few-shot samples)          │
│  - Your actual working scripts augmented with tool patterns │
│  - Used by: LLM code generation context (few-shot)          │
│  - ~50 high-quality examples, hand-curated                  │
└─────────────────────────────────────────────────────────────┘
```

### Build Plan

**Step 1: Transform the TOMLs (1-2 days)**

Write a Python script to:
1. Parse all TOML files → extract `tool_ID`, `tool_name`, `brief_description`, `parameters`
2. Add an `exec_route` field: `"pure_python"` | `"gdal_cli"` | `"rasterio"` | `"qgis_headless"` | `"grass"`
3. Add `python_equivalent` where applicable (from Tier 1/2 map above)
4. Output as `tool_registry.json` (one entry per tool)

**Step 2: Build the Semantic Index**

```python
from sentence_transformers import SentenceTransformer
import chromadb

# Embed: tool_name + brief_description (NOT the full parameters)
texts = [f"{t['tool_name']}: {t['brief_description']}" for t in tools]
# Store with metadata including exec_route for filtered retrieval
```

**Step 3: Agent Tool Selection Function**

```python
def select_tool(task_description: str, exec_routes: list = None) -> list[dict]:
    """
    Returns top-3 relevant tools from the semantic index.
    exec_routes filter: ['pure_python', 'rasterio'] for headless-only constraints.
    """
```

**Step 4: Code Generation with Tool Context**

When an agent needs to perform an operation:
1. `select_tool(task)` → returns tool metadata with python_equivalent
2. Feed tool metadata + your code examples as context to code generation LLM
3. Code generation LLM writes Python that uses `python_equivalent`, not `processing.run()`

### Where to Store

In the workspace: `projects/gis-agent/tool-registry/`  
- `tool_registry.json` — full structured tool catalog  
- `tool_embeddings.pkl` — semantic vector index  
- `transform_tools.py` — ingestion/transformation script  
- `README.md` — how to update when new tools are added

### What to NOT Do

- Don't put the raw TOML `code_example` into your agent context — it will generate QGIS-specific code.
- Don't try to maintain 300+ Python implementations yourself. Write `python_equivalent` descriptions (prose or short code snippets) for the ~100 tools you'll actually use.
- Don't build an MCP server wrapping QGIS just to access these tools. The overhead is enormous for what's essentially a documentation problem.

---

## 6. Priority Gaps: Top 10 Tools/Capabilities to Add First

These are the highest-value additions given your current stack, ranked by frequency of use in consulting workflows:

### 1. **Zonal Statistics** (rasterstats)
**Gap rating: CRITICAL**  
Extract raster statistics (mean, sum, max, etc.) within polygon zones. Essential for population-weighted analysis, raster characterization of census units, environmental summaries. Your current stack has no equivalent.  
**Fix:** `pip install rasterstats` + write `zonal_stats.py` script.  
**Example use:** Average NDVI by county, mean elevation per service area, sum impervious surface per watershed.

### 2. **Raster Terrain Analysis** (richdem or rio-terrain)
**Gap rating: HIGH**  
Slope, aspect, hillshade, TPI, TRI from DEMs. You have DEM data available but no scripts to derive terrain derivatives.  
**Fix:** `pip install richdem` + `terrain_analysis.py` script covering slope/aspect/hillshade/TRI/TPI.  
**Example use:** Site suitability, environmental modeling, terrain visualization for clients.

### 3. **Raster Clip by Mask** (rasterio.mask)
**Gap rating: HIGH**  
Clip rasters to vector boundary extents. Every raster workflow needs this. You probably do this manually but have no agent-accessible script.  
**Fix:** Write `raster_clip.py` wrapping `rasterio.mask.mask()`.  
**Example use:** Clip national rasters to study area, extract county-level raster data.

### 4. **Raster Calculator / Band Math** (numpy + rasterio)
**Gap rating: HIGH**  
Compute band indices (NDVI = (NIR-RED)/(NIR+RED)), composite rasters, conditional raster operations.  
**Fix:** Write `raster_calc.py` with a flexible expression evaluator for common indices.  
**Example use:** NDVI from Landsat, impervious surface classification, suitability scoring.

### 5. **Raster Merge / Mosaic** (rasterio.merge)
**Gap rating: MEDIUM-HIGH**  
Combine multiple raster tiles into a single layer. Common when working with tiled data (USGS DEM tiles, NLCD tiles).  
**Fix:** Write `raster_mosaic.py` wrapping `rasterio.merge()`.

### 6. **Interpolation Surface** (scipy + possibly pykrige)
**Gap rating: MEDIUM-HIGH**  
Convert point observations to continuous surfaces. IDW and kriging are the workhorses of environmental consulting.  
**Fix:** Write `interpolation.py` with IDW (scipy) and optionally kriging (pykrige). Also document GDAL's `gdal:gridinversedistance` as an alternative.  
**Example use:** Interpolate weather stations to raster, soil sampling surfaces.

### 7. **Raster Proximity / Distance Surface** (scipy.ndimage)
**Gap rating: MEDIUM**  
Distance raster showing distance from each cell to nearest target feature. Used for suitability analysis, buffer alternatives when you need continuous distance.  
**Fix:** Write `raster_proximity.py`: rasterize features → `scipy.ndimage.distance_transform_edt()`.

### 8. **Contour Generation** (matplotlib / richdem)
**Gap rating: MEDIUM**  
Generate contour lines from a DEM. Common in client deliverables.  
**Fix:** Write `contour_generation.py` using matplotlib contours + shapely geometry extraction, or call `gdal_contour` via subprocess.

### 9. **Kernel Density Estimation (Continuous)** (sklearn or scipy)
**Gap rating: MEDIUM**  
Your hotspot/LISA analysis does statistical clustering. A smooth KDE raster is different — it's a continuous density surface for visualization. The Penn State repo specially calls this out as a customized tool.  
**Fix:** Write `kde_surface.py` using `sklearn.neighbors.KernelDensity` → rasterize to grid.  
**Example use:** Crime density maps, event density, facility coverage.

### 10. **Field Join / Attribute Transfer by Location** (geopandas sjoin)
**Gap rating: MEDIUM**  
You probably do this inline but don't have a clean agent-accessible script. Spatial join is one of the 5 most common GIS operations and agents should be able to call it as a named tool.  
**Fix:** Write `spatial_join.py` as a proper named script with clean parameter interface (input layer, join layer, how, predicate, fields to transfer).

---

## 7. Sources

1. **Penn State SpatialAnalysisAgent repo**: https://github.com/Teakinboyewa/SpatialAnalysisAgent  
   Direct inspection of TOML files: `gdal_aspect.toml`, `gdal_contour.toml`, `gdal_cliprasterbymasklayer.toml`, `gdal_proximity.toml`, `gdal_hillshade.toml`

2. **Penn State GIS Copilot paper page**: https://giscience.psu.edu/gis-copilot-towards-an-autonomous-gis-agent-for-spatial-analysis/  
   Published: Akinboyewa, T., Li, Z., Ning, H., & Lessani, M.N. (2024). doi: 10.1080/17538947.2025.2497489

3. **QGIS provider algorithm counts** (Feb 2024):  
   https://r-spatial.github.io/qgisprocess/articles/qgisprocess.html  
   - gdal: 57, grass: 307, native: 316, sagang: 589, qgis: 35, 3d: 1, pdal: 17

4. **Alternative counts with plugins** (qgisprocess CRAN docs):  
   https://cran.r-project.org/web/packages/qgisprocess/vignettes/qgisprocess.html  
   - WhiteboxTools: 546, NetworkGT: 33, QNEAT3: 14, pcraster: 102

5. **QGIS Processing Python console docs**:  
   https://docs.qgis.org/3.44/en/docs/user_manual/processing/console.html

6. **Penn State Autonomous GIS infrastructure vision (2025)**:  
   https://giscience.psu.edu/2025/04/13/autonomous-gis-as-infrastructure/  
   — Discusses MCP as future direction for AI-ready GIS resources

7. **LLM-Geo (autonomous GIS agent)**: https://github.com/gladcolor/LLM-Geo  
   — Alternative approach using direct Python generation without tool registry

---

*Brief prepared by subagent on 2026-04-04. All tool counts verified against live repo.*
