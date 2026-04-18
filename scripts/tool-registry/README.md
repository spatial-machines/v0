# GIS Tool Registry

**Version:** 1.0 | **Ingested:** 2026-04-04 | **Tools:** 679

A structured, queryable registry of GIS tools for the multi-agent GIS consulting system. Transformed from the Penn State SpatialAnalysisAgent TOML/JSON documentation.

---

## Files

| File | Description |
|------|-------------|
| `tool_registry.json` | Full registry — array of 679 tool objects |
| `registry_by_category.json` | Same tools grouped by `category` |
| `registry_by_exec_route.json` | Same tools grouped by `exec_route` |
| `tool_lookup.py` | CLI + Python API for querying the registry |
| `ingest_tools.py` | Ingestion/transformation script (re-run to update) |

---

## Tool Schema

Each tool entry follows this schema:

```json
{
  "tool_id": "gdal:aspect",
  "tool_name": "aspect",
  "provider": "gdal",
  "category": "terrain",
  "brief_description": "One-sentence description.",
  "full_description": "Full description with algorithm details.",
  "parameters": [
    {
      "name": "INPUT",
      "label": "Input layer",
      "type": "raster",
      "description": "Input elevation raster layer.",
      "default": null,
      "required": true,
      "optional": false
    }
  ],
  "exec_route": "rasterio",
  "python_equivalent": "richdem.TerrainAttribute(dem_array, attrib='aspect_presflatness')",
  "python_libs": ["richdem"],
  "use_cases": [
    "Solar radiation modeling and solar panel siting",
    "Slope facing analysis for vegetation modeling"
  ],
  "related_tools": ["gdal:slope", "gdal:hillshade"],
  "source": "penn_state_json",
  "source_quality": "good",
  "original_code_example": "..."
}
```

---

## Categories

| Category | Count | Description |
|----------|-------|-------------|
| `terrain` | 157 | DEM derivatives — slope, aspect, hillshade, TPI, TRI, viewshed |
| `raster_ops` | 225 | Raster clip, merge, warp, reproject, band math, proximity |
| `vector_ops` | 152 | Buffer, clip, dissolve, intersect, spatial join, fix geometries |
| `hydrology` | 12 | Watershed, flow accumulation, stream extraction |
| `network` | 31 | Routing, service area, shortest path, connectivity |
| `interpolation` | 10 | IDW, kriging, TIN, linear interpolation |
| `remote_sensing` | 36 | Image classification, NDVI, spectral analysis, OBIA |
| `classification` | 5 | Unsupervised/supervised classification, segmentation |
| `statistics` | 16 | Zonal stats, field statistics, summaries |
| `format_conversion` | 28 | Convert between GIS formats, OGR utility tools |
| `visualization` | 7 | Heatmap, KDE, map rendering |

---

## Exec Routes

| Route | Count | When to Use |
|-------|-------|-------------|
| `pure_python` | 269 | Direct geopandas/shapely implementation — fastest, no dependencies |
| `grass` | 306 | Requires GRASS GIS session — hydrology, network, raster analysis |
| `qgis_headless` | 52 | Requires headless QGIS — complex analysis tools |
| `rasterio` | 42 | rasterio/numpy/richdem — terrain and raster processing |
| `gdal_cli` | 10 | GDAL command-line tools via subprocess |

---

## Source Quality

| Quality | Count | Meaning |
|---------|-------|---------|
| `good` | 373 | Full description, parameters, code example from Penn State JSON |
| `minimal` | 294 | GRASS tools with only name available (source JSON has a data bug) |
| `patched` | 12 | Key GRASS tools with manually added descriptions |

> **Note:** The Penn State source JSON has a data quality issue where all 306 GRASS tool
> descriptions are incorrectly replaced with the `gdal:warpreproject` description. The 
> 12 highest-value GRASS tools are patched with correct descriptions. Others have minimal
> entries with tool IDs that can be used for GRASS documentation lookup.

---

## Querying the Registry

### Python API

```python
from tool_lookup import GISToolRegistry

reg = GISToolRegistry()

# Search by keyword
tools = reg.search("watershed delineation")
tools = reg.search("slope analysis", exec_route="rasterio")
tools = reg.search("buffer", category="vector_ops", max_results=5)

# Get by exact ID
tool = reg.get("gdal:aspect")
print(tool["python_equivalent"])   # richdem.TerrainAttribute(...)
print(tool["exec_route"])          # rasterio

# Filter
terrain_tools = reg.filter(category="terrain", exec_route="rasterio")
pure_python_tools = reg.filter(exec_route="pure_python")
with_pyeq = reg.filter(has_python_equivalent=True)

# Summary
summary = reg.summary()
print(summary["total_tools"])       # 679
print(summary["by_category"])       # {'terrain': 157, ...}
```

### CLI

```bash
# Search by keyword
python3 tool_lookup.py --search "slope analysis"
python3 tool_lookup.py --search "buffer" --exec-route pure_python

# Filter by category or exec route
python3 tool_lookup.py --category terrain
python3 tool_lookup.py --exec-route rasterio --max-results 20

# Get a specific tool
python3 tool_lookup.py --id gdal:aspect --verbose

# Browse
python3 tool_lookup.py --list-categories
python3 tool_lookup.py --top20

# JSON output (for piping to other tools)
python3 tool_lookup.py --search "interpolation" --json-output | jq '.[].tool_id'
```

---

## Updating the Registry

When Penn State publishes updates or you want to re-ingest:

```bash
# Re-download and transform (fetches fresh from GitHub)
python3 ingest_tools.py

# Or use a locally downloaded file
curl -s "https://raw.githubusercontent.com/Teakinboyewa/SpatialAnalysisAgent/master/SpatialAnalysisAgent/Tools_Documentation/qgis_tools_for_rag.json" -o /tmp/qgis_tools_raw.json
python3 ingest_tools.py /tmp/qgis_tools_raw.json
```

### Adding Custom Tools

To add custom tools to the registry, append entries to `tool_registry.json` manually or extend `ingest_tools.py` to pull from an additional source. Custom tools should use `"source": "custom"`.

---

## Design Notes

### Why Not Raw TOML/RAG?

The Penn State system uses FAISS vector search over raw TOML files. For our agent system:

1. **Code examples are QGIS-specific** — all call `processing.run()` inside QGIS. Our agents would generate broken code.
2. **No execution routing** — RAG can't distinguish "do this in geopandas" vs "needs GRASS."
3. **Parameters are prose** — we parse them into structured objects for reliable code generation.

### Architecture Role

This registry is **Layer 2** in the 3-layer tool knowledge system:
- **Layer 1**: Semantic search (chromadb/FAISS over brief descriptions) → "which tool?"
- **Layer 2**: This registry → "how to call it, what Python to use" (exact key lookup)
- **Layer 3**: Code examples library → few-shot samples for LLM code generation

---

## Source

**Repository:** https://github.com/Teakinboyewa/SpatialAnalysisAgent  
**Paper:** Akinboyewa et al. (2024). *GIS Copilot: Towards an Autonomous GIS Agent for Spatial Analysis.* IJGIS. doi:10.1080/17538947.2025.2497489  
**License:** GPL-3.0
