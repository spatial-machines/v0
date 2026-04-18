#!/usr/bin/env python3
"""
GIS Tool Registry Ingestion Script
===================================
Downloads and transforms Penn State SpatialAnalysisAgent TOML/JSON tool definitions
into our structured tool registry format.

Run: python3 ingest_tools.py
Output: tool_registry.json, registry_by_category.json, registry_by_exec_route.json

Source: https://github.com/Teakinboyewa/SpatialAnalysisAgent
"""

import json
import re
import sys
import urllib.request
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ─── Config ──────────────────────────────────────────────────────────────────

SOURCE_URL = "https://raw.githubusercontent.com/Teakinboyewa/SpatialAnalysisAgent/master/SpatialAnalysisAgent/Tools_Documentation/qgis_tools_for_rag.json"
OUTPUT_DIR = Path(__file__).parent

# ─── Mapping Tables ───────────────────────────────────────────────────────────

CATEGORY_MAP = {
    # Terrain analysis
    "gdal:aspect": "terrain",
    "gdal:slope": "terrain",
    "gdal:hillshade": "terrain",
    "gdal:triterrainruggednessindex": "terrain",
    "gdal:tpitopographicpositionindex": "terrain",
    "gdal:roughness": "terrain",
    "gdal:colorrelief": "terrain",
    "gdal:contour": "terrain",
    "gdal:contour_polygon": "terrain",
    "gdal:fillnodata": "raster_ops",
    # Raster ops
    "gdal:cliprasterbyextent": "raster_ops",
    "gdal:cliprasterbymasklayer": "raster_ops",
    "gdal:merge": "raster_ops",
    "gdal:warpreproject": "raster_ops",
    "gdal:rastercalculator": "raster_ops",
    "gdal:polygonize": "raster_ops",
    "gdal:rasterize": "raster_ops",
    "gdal:buildvirtualraster": "raster_ops",
    "gdal:translate": "raster_ops",
    "gdal:retile": "raster_ops",
    "gdal:overviews": "raster_ops",
    "gdal:gdal2tiles": "raster_ops",
    "gdal:gdal2xyz": "raster_ops",
    "gdal:proximity": "raster_ops",
    "gdal:sieve": "raster_ops",
    "gdal:assignprojection": "raster_ops",
    "gdal:extractprojection": "raster_ops",
    # Interpolation
    "gdal:gridinversedistance": "interpolation",
    "gdal:gridinversedistancenearestneighbor": "interpolation",
    "gdal:gridlinear": "interpolation",
    "gdal:gridnearestneighbor": "interpolation",
    "gdal:gridaverage": "interpolation",
    "gdal:griddatametrics": "interpolation",
    "qgis:idwinterpolation": "interpolation",
    "qgis:tininterpolation": "interpolation",
    # Format conversion
    "gdal:convertformat": "format_conversion",
    "gdal:buildvirtualvector": "format_conversion",
    "gdal:dissolve": "vector_ops",
    "gdal:clipvectorbyextent": "vector_ops",
    "gdal:clipvectorbypolygon": "vector_ops",
    "gdal:buffervectors": "vector_ops",
    "gdal:executesql": "vector_ops",
    # 3D
    "3d:tessellate": "vector_ops",
    # Statistics
    "native:zonalstatisticsfb": "statistics",
    "native:basicstatisticsforfields": "statistics",
    "qgis:statisticsbycategories": "statistics",
    # Classification / remote sensing
    "grass7:i.segment": "classification",
    "grass7:i.cluster": "classification",
    "grass7:i.maxlik": "classification",
    "grass7:i.pca": "remote_sensing",
    # Hydrology
    "grass7:r.watershed": "hydrology",
    "grass7:r.basins.fill": "hydrology",
    "grass7:r.stream.extract": "hydrology",
    "grass7:r.fill.dir": "hydrology",
    "grass7:r.topidx": "hydrology",
    "grass7:r.water.outlet": "hydrology",
    # Network
    "grass7:v.net": "network",
    "grass7:v.net.path": "network",
    "grass7:v.net.salesman": "network",
    "grass7:v.net.distance": "network",
    "grass7:v.net.alloc": "network",
    "native:shortestpathpointtopoint": "network",
    "native:serviceareafromlayer": "network",
    "native:serviceareafrompoint": "network",
    # Visualization
    "native:heatmapkerneldensityestimation": "visualization",
    "qgis:createheatmaplayer": "visualization",
    "qgis:regularpoints": "statistics",
}

# Provider-level category defaults (used when tool_id not in CATEGORY_MAP)
PROVIDER_CATEGORY_DEFAULTS = {
    "gdal": "raster_ops",
    "native": "vector_ops",
    "grass7": "hydrology",
    "qgis": "statistics",
    "3d": "vector_ops",
}

# Keyword → category overrides (applied to description text)
KEYWORD_CATEGORY_MAP = [
    (["watershed", "hydrology", "flow direction", "accumulation", "drainage", "basin", "catchment", "stream network"], "hydrology"),
    (["slope", "aspect", "hillshade", "elevation", "dem ", "terrain", "roughness", "ruggedness", "tpi", "tri", "topographic"], "terrain"),
    (["interpolat", "kriging", "idw", "inverse distance", "tin ", "spline"], "interpolation"),
    (["buffer", "dissolve", "clip", "union", "intersection", "overlay", "join", "merge vector", "centroid", "reproject layer", "fix geomet", "spatial index", "voronoi", "convex hull", "simplif", "select by", "extract by", "delete holes", "difference", "symmetrical difference", "affine transform", "rotate", "translate geometry", "grid layer", "points along", "random points", "create grid"], "vector_ops"),
    (["raster", "pixel", "band", "nodata", "mosaic", "warp", "resampl", "virtual raster", "tif", "geotiff"], "raster_ops"),
    (["network", "route", "shortest path", "service area", "graph", "connectivity", "topology"], "network"),
    (["classify", "classification", "supervised", "unsupervised", "kmeans", "segmentation", "machine learning"], "classification"),
    (["statistic", "zonal", "summary", "mean", "median", "standard deviation", "variance", "histogram", "regression", "correlation"], "statistics"),
    (["heatmap", "kernel density", "map render", "print layout", "choropleth", "visualiz", "symbology"], "visualization"),
    (["convert", "format", "export", "import", "gpkg", "shapefile", "geojson", "kml", "csv", "sql", "ogr2ogr"], "format_conversion"),
    (["ndvi", "satellite", "sentinel", "landsat", "multispectral", "band combin", "radiometric", "image classif", "remote sens", "spectral", "sar", "imagery"], "remote_sensing"),
    (["contour", "aspect", "slope", "hillshade", "roughness", "ruggedness", "tpi", "tri", "color relief"], "terrain"),
]

# Exec route mapping
# GRASS module prefix → default category (when description is unavailable)
GRASS_MODULE_CATEGORY = {
    "r": "raster_ops",    # r.* = raster tools (overridden by keywords when desc available)
    "v": "vector_ops",    # v.* = vector tools
    "i": "remote_sensing", # i.* = imagery/remote sensing
    "g": "format_conversion", # g.* = general/utility
    "m": "statistics",   # m.* = measurement tools
}


def get_exec_route(tool_id: str, description: str) -> str:
    provider = tool_id.split(":")[0]
    name = tool_id.split(":")[-1].lower()
    desc_lower = description.lower()

    # grass7 tools
    if provider == "grass7":
        return "grass"

    # 3d tools
    if provider == "3d":
        return "qgis_headless"

    # qgis tools
    if provider == "qgis":
        return "qgis_headless"

    # native tools → pure_python
    if provider == "native":
        return "pure_python"

    # gdal tools → further differentiation
    if provider == "gdal":
        # Format conversion / utility tools → gdal_cli
        format_keywords = ["convertformat", "buildvirtualraster", "buildvirtualvector",
                           "gdal2tiles", "retile", "overviews", "gdal2xyz",
                           "executesql", "extractprojection", "assignprojection"]
        if name in format_keywords:
            return "gdal_cli"
        # Terrain/raster analysis → rasterio
        terrain_keywords = ["aspect", "slope", "hillshade", "roughness", "tri", "tpi",
                            "colorrelief", "contour", "fillnodata", "proximity",
                            "polygonize", "rasterize", "sieve", "warp", "translate",
                            "clipraster", "merge", "rastercalculator", "grid"]
        if any(k in name for k in terrain_keywords):
            return "rasterio"
        # Vector operations via gdal/ogr → pure_python
        vector_keywords = ["clipvector", "buffervectors", "dissolve"]
        if any(k in name for k in vector_keywords):
            return "pure_python"
        return "rasterio"  # default for gdal

    return "qgis_headless"  # fallback


# Python equivalents for Tier 1 tools
PYTHON_EQUIVALENTS = {
    "native:buffer": "gdf.buffer(distance, cap_style=1, join_style=1)",
    "native:dissolve": "gdf.dissolve(by='field')",
    "native:clip": "geopandas.clip(gdf, mask_gdf)",
    "native:intersection": "geopandas.overlay(gdf1, gdf2, how='intersection')",
    "native:union": "geopandas.overlay(gdf1, gdf2, how='union')",
    "native:difference": "geopandas.overlay(gdf1, gdf2, how='difference')",
    "native:symmetricaldifference": "geopandas.overlay(gdf1, gdf2, how='symmetric_difference')",
    "native:joinattributesbylocation": "geopandas.sjoin(gdf1, gdf2, how='left', predicate='intersects')",
    "native:reprojectlayer": "gdf.to_crs(epsg=4326)",
    "native:fixgeometries": "gdf.geometry.make_valid()",
    "native:centroids": "gdf.copy(); gdf['geometry'] = gdf.centroid",
    "native:extractbyattribute": "gdf[gdf['field'] == value]",
    "native:extractbylocation": "geopandas.sjoin(gdf, mask_gdf, predicate='intersects').drop_duplicates('index_right')",
    "native:fieldcalculator": "gdf['new_col'] = gdf.apply(lambda row: expression, axis=1)",
    "native:addautoincrementalfield": "gdf.reset_index(drop=True); gdf['AUTO_ID'] = range(len(gdf))",
    "native:spatialindex": "gdf.sindex  # auto-managed by geopandas",
    "native:deleteholes": "from shapely.ops import unary_union; gdf.geometry.apply(lambda g: g.buffer(0))",
    "native:mergevectorlayers": "geopandas.pd.concat([gdf1, gdf2], ignore_index=True)",
    "native:countpointsinpolygon": "geopandas.sjoin(points, polygons, predicate='within').groupby('index_right').size()",
    "native:creategrid": "shapely + geopandas grid construction with bounding box division",
    "native:randomextract": "gdf.sample(n=n_features, random_state=42)",
    "native:convexhull": "gdf.convex_hull",
    "native:voronoipolygons": "from scipy.spatial import Voronoi; shapely.ops.voronoi_diagram(geom_collection)",
    "native:simplifygeometries": "gdf.simplify(tolerance)",
    "native:multiparttosingleparts": "gdf.explode(index_parts=False)",
    "native:pointonsurface": "gdf.representative_point()",
    "native:boundingboxes": "gdf.envelope",
    "native:zonalstatisticsfb": "rasterstats.zonal_stats(gdf, raster_path, stats=['mean','sum','min','max','count'])",
    "native:heatmapkerneldensityestimation": "sklearn.neighbors.KernelDensity(bandwidth=...).fit(coords); predict on grid",
    "native:linestopolygons": "shapely.geometry.Polygon(list(line.coords))",
    "native:polygonstolines": "gdf.boundary",
    "native:pointstopath": "shapely.geometry.LineString(sorted_points)",
    "gdal:aspect": "richdem.TerrainAttribute(dem_array, attrib='aspect_presflatness')",
    "gdal:slope": "richdem.TerrainAttribute(dem_array, attrib='slope_degrees')",
    "gdal:hillshade": "richdem.TerrainAttribute(dem_array, attrib='hillshade')",
    "gdal:triterrainruggednessindex": "richdem.TerrainAttribute(dem_array, attrib='TRI')",
    "gdal:tpitopographicpositionindex": "richdem.TerrainAttribute(dem_array, attrib='TPI')",
    "gdal:roughness": "richdem.TerrainAttribute(dem_array, attrib='roughness')",
    "gdal:contour": "matplotlib.contour(x, y, z, levels=levels) → shapely.geometry.LineString extraction",
    "gdal:cliprasterbymasklayer": "rasterio.mask.mask(src, shapes, crop=True)",
    "gdal:cliprasterbyextent": "rasterio.mask.mask(src, [box(*bounds)], crop=True)",
    "gdal:merge": "rasterio.merge.merge([src1, src2, ...])",
    "gdal:warpreproject": "rasterio.warp.reproject(source, destination, src_crs=..., dst_crs=...)",
    "gdal:rastercalculator": "numpy operations on rasterio-read arrays",
    "gdal:polygonize": "rasterio.features.shapes(array, transform=transform)",
    "gdal:rasterize": "rasterio.features.rasterize([(geom, val) for ...], out_shape=..., transform=...)",
    "gdal:translate": "rasterio.open(src) → rasterio.open(dst, 'w', ...)",
    "gdal:sieve": "rasterio.features.sieve(array, size=min_pixels)",
    "gdal:proximity": "scipy.ndimage.distance_transform_edt(binary_raster) * pixel_size",
    "gdal:fillnodata": "rasterio.fill.fillnodata(array, mask=mask, max_search_distance=dist)",
    "gdal:buildvirtualraster": "gdalbuildvrt CLI: subprocess.run(['gdalbuildvrt', 'out.vrt'] + input_files)",
    "gdal:convertformat": "geopandas.read_file(src).to_file(dst, driver='GPKG')",
    "gdal:clipvectorbyextent": "gdf.cx[xmin:xmax, ymin:ymax]",
    "gdal:clipvectorbypolygon": "geopandas.clip(gdf, mask_gdf)",
    "gdal:buffervectors": "gdf.buffer(distance)",
    "gdal:dissolve": "gdf.dissolve(by='field', aggfunc='first')",
    "gdal:gridinversedistance": "scipy.interpolate.griddata(points, values, grid_points, method='linear')",
    "gdal:gridlinear": "scipy.interpolate.LinearNDInterpolator(points, values)(grid_points)",
    "gdal:gridnearestneighbor": "scipy.interpolate.NearestNDInterpolator(points, values)(grid_points)",
}

# Python libs per exec_route/tool
PYTHON_LIBS_MAP = {
    "richdem": ["gdal:aspect", "gdal:slope", "gdal:hillshade", "gdal:triterrainruggednessindex",
                "gdal:tpitopographicpositionindex", "gdal:roughness"],
    "rasterio": ["gdal:cliprasterbymasklayer", "gdal:cliprasterbyextent", "gdal:merge",
                 "gdal:warpreproject", "gdal:rastercalculator", "gdal:polygonize",
                 "gdal:rasterize", "gdal:translate", "gdal:sieve", "gdal:fillnodata"],
    "rasterstats": ["native:zonalstatisticsfb"],
    "scipy": ["gdal:proximity", "gdal:fillnodata", "gdal:gridinversedistance",
              "gdal:gridlinear", "gdal:gridnearestneighbor"],
    "geopandas": ["native:buffer", "native:dissolve", "native:clip", "native:intersection",
                  "native:union", "native:difference", "native:joinattributesbylocation",
                  "native:reprojectlayer", "native:fixgeometries", "native:mergevectorlayers"],
    "shapely": ["native:convexhull", "native:voronoipolygons", "native:simplifygeometries",
                "native:centroids", "native:pointonsurface", "native:boundingboxes"],
    "matplotlib": ["gdal:contour", "gdal:contour_polygon"],
    "sklearn": ["native:heatmapkerneldensityestimation"],
    "subprocess+gdal": ["gdal:buildvirtualraster", "gdal:gdal2tiles", "gdal:retile"],
}

# Use cases per tool category
USE_CASES_BY_CATEGORY = {
    "terrain": [
        "DEM analysis for site suitability studies",
        "Environmental modeling requiring slope/aspect inputs",
        "Terrain visualization for client deliverables",
        "Erosion risk and geohazard assessment",
    ],
    "raster_ops": [
        "Clipping national datasets to study area extents",
        "Mosaicking tiled raster datasets (DEM tiles, NLCD, etc.)",
        "Raster preprocessing for image analysis pipelines",
        "Format conversion for interoperability with other systems",
    ],
    "vector_ops": [
        "Spatial selection and attribute-based filtering",
        "Overlay analysis for multi-criteria site suitability",
        "Data preparation and cleaning for GIS workflows",
        "Geometry repair and validation before spatial joins",
    ],
    "hydrology": [
        "Watershed and catchment delineation for stormwater analysis",
        "Stream network extraction from DEMs",
        "Flood risk modeling and inundation mapping",
        "Water quality analysis by drainage basin",
    ],
    "interpolation": [
        "Creating continuous surfaces from point sampling data",
        "Spatial interpolation of environmental measurements",
        "Filling data gaps in meteorological or soil datasets",
        "Generating smooth raster outputs from irregular point data",
    ],
    "network": [
        "Service area and accessibility analysis",
        "Routing and logistics optimization",
        "Connectivity and infrastructure gap analysis",
        "Emergency response time mapping",
    ],
    "statistics": [
        "Zonal summarization of raster values within polygons",
        "Spatial autocorrelation and clustering analysis",
        "Population-weighted demographic aggregation",
        "Environmental exposure assessment by census unit",
    ],
    "classification": [
        "Land use / land cover classification from satellite imagery",
        "Habitat classification for environmental consulting",
        "Change detection between time periods",
        "Automated feature extraction from imagery",
    ],
    "visualization": [
        "Generating client-ready choropleth maps",
        "Density surface mapping for point data",
        "Map layout production for reports",
        "Interactive web map preparation",
    ],
    "format_conversion": [
        "Converting between GIS file formats (SHP → GPKG, etc.)",
        "Data exchange with client systems requiring specific formats",
        "Building virtual datasets for multi-file raster management",
        "SQL-based spatial data querying and export",
    ],
    "remote_sensing": [
        "NDVI and vegetation index calculation from multispectral imagery",
        "Land cover change detection over time",
        "Impervious surface mapping from satellite data",
        "Environmental monitoring with Sentinel/Landsat imagery",
    ],
}

# Tool-specific use cases for high-value tools
TOOL_SPECIFIC_USE_CASES = {
    "gdal:aspect": ["Solar radiation modeling and solar panel siting", "Slope facing analysis for vegetation modeling", "Hillside erosion risk assessment", "Agricultural exposure analysis by aspect"],
    "gdal:slope": ["Landslide susceptibility mapping", "Construction suitability analysis", "Trail and road routing constraints", "Soil erosion potential modeling"],
    "gdal:hillshade": ["Client-ready terrain visualization", "Map base layer for elevation context", "Shaded relief for topographic reporting", "Draping imagery over terrain for 3D-style views"],
    "gdal:contour": ["Topographic map generation for engineering reports", "Elevation interval analysis for site planning", "Floodplain delineation support", "Client deliverable contour maps"],
    "gdal:cliprasterbymasklayer": ["Extracting county or watershed-level raster data from national datasets", "Study area data preparation", "Reducing raster file sizes for processing efficiency", "Clipping DEMs, NLCD, or imagery to client boundaries"],
    "gdal:merge": ["Mosaicking USGS DEM tiles into a seamless elevation surface", "Combining Landsat scene tiles", "Building statewide raster from county tiles", "Merging precipitation or climate raster tiles"],
    "gdal:proximity": ["Continuous distance raster from roads or services", "Accessibility surface for site suitability", "Wildfire or hazard proximity analysis", "Environmental buffer analysis as alternative to vector buffers"],
    "native:buffer": ["Service area approximation from facilities", "Environmental setback compliance mapping", "Viewshed and noise impact zones", "Impact assessment around infrastructure"],
    "native:dissolve": ["Aggregating parcel data to block or census level", "Merging adjacent features with same attribute value", "Simplifying boundary datasets for client visualization", "Creating regional summaries from local polygons"],
    "native:clip": ["Extracting features within study area", "County or watershed boundary data extraction", "Limiting analysis to client project area", "Data preparation for scoped environmental analysis"],
    "native:intersection": ["Overlay analysis combining two feature datasets", "Land use within watershed or flood zone", "Zoning and parcel overlap analysis", "Environmental constraint mapping"],
    "native:joinattributesbylocation": ["Assigning census demographics to service areas", "Attaching environmental measurements to administrative boundaries", "Spatial join for multi-source data integration", "Linking point observations to polygon features"],
    "native:reprojectlayer": ["Standardizing CRS across multi-source datasets", "Converting to client-required projection", "Preparing data for accurate distance/area calculations", "Aligning layers for overlay analysis"],
    "native:zonalstatisticsfb": ["Average NDVI by county or watershed", "Mean elevation per service area", "Sum of impervious surface per census tract", "Population-weighted environmental exposure metrics"],
    "native:heatmapkerneldensityestimation": ["Crime density mapping for public safety analysis", "Event or incident density visualization", "Service demand density for facility planning", "Environmental phenomenon concentration mapping"],
    "grass7:r.watershed": ["Catchment delineation for stormwater consulting", "Automated drainage network extraction", "Hydrologic connectivity analysis", "Basin delineation for water quality studies"],
}

# Related tools map
RELATED_TOOLS = {
    "gdal:aspect": ["gdal:slope", "gdal:hillshade", "gdal:roughness", "gdal:triterrainruggednessindex"],
    "gdal:slope": ["gdal:aspect", "gdal:hillshade", "gdal:roughness", "gdal:tpitopographicpositionindex"],
    "gdal:hillshade": ["gdal:aspect", "gdal:slope", "gdal:colorrelief", "gdal:contour"],
    "gdal:roughness": ["gdal:triterrainruggednessindex", "gdal:tpitopographicpositionindex", "gdal:slope"],
    "gdal:contour": ["gdal:contour_polygon", "gdal:aspect", "gdal:slope", "gdal:hillshade"],
    "gdal:contour_polygon": ["gdal:contour", "gdal:aspect"],
    "gdal:cliprasterbymasklayer": ["gdal:cliprasterbyextent", "gdal:warpreproject", "gdal:merge"],
    "gdal:cliprasterbyextent": ["gdal:cliprasterbymasklayer", "gdal:warpreproject"],
    "gdal:merge": ["gdal:buildvirtualraster", "gdal:cliprasterbymasklayer", "gdal:warpreproject"],
    "gdal:warpreproject": ["gdal:cliprasterbymasklayer", "gdal:merge", "native:reprojectlayer"],
    "gdal:proximity": ["native:buffer", "gdal:rasterize", "gdal:slope"],
    "gdal:polygonize": ["gdal:rasterize", "gdal:sieve"],
    "gdal:rasterize": ["gdal:polygonize", "gdal:proximity"],
    "gdal:gridinversedistance": ["gdal:gridlinear", "gdal:gridnearestneighbor", "qgis:idwinterpolation"],
    "gdal:gridlinear": ["gdal:gridinversedistance", "gdal:gridnearestneighbor"],
    "gdal:gridnearestneighbor": ["gdal:gridinversedistance", "gdal:gridlinear"],
    "native:buffer": ["native:dissolve", "native:clip", "gdal:proximity"],
    "native:dissolve": ["native:clip", "native:intersection", "gdal:dissolve"],
    "native:clip": ["native:intersection", "native:extractbylocation", "gdal:clipvectorbypolygon"],
    "native:intersection": ["native:union", "native:difference", "native:clip"],
    "native:union": ["native:intersection", "native:dissolve", "native:difference"],
    "native:difference": ["native:intersection", "native:union"],
    "native:joinattributesbylocation": ["native:extractbylocation", "native:countpointsinpolygon"],
    "native:reprojectlayer": ["gdal:warpreproject", "native:clip"],
    "native:zonalstatisticsfb": ["native:joinattributesbylocation", "gdal:rastercalculator"],
    "native:heatmapkerneldensityestimation": ["native:countpointsinpolygon", "qgis:idwinterpolation"],
}

# ─── Parameter Parsing ────────────────────────────────────────────────────────

def parse_parameters(params_str: str) -> list:
    """Parse prose parameter string into structured list of dicts."""
    if not params_str or not params_str.strip():
        return []

    # Split on parameter names (ALLCAPS word followed by colon)
    # Pattern: PARAM_NAME: Label. Description. Type: [...] Default: value
    params = []
    
    # Remove "outputs = " section if present
    params_str = re.split(r'\boutputs\s*=\s*', params_str)[0]
    
    # Also remove "Name: Label. Description. Type: Type" header row if present
    params_str = re.sub(r'^Name:\s*Label\.\s*Description\.\s*Type:\s*Type\s*', '', params_str.strip())

    # Split by lines that start with an ALL_CAPS parameter name followed by colon
    # We split on newlines followed by an uppercase word + colon
    param_lines = re.split(r'\n(?=[A-Z][A-Z0-9_]+:\s)', params_str.strip())
    
    for line in param_lines:
        line = line.strip()
        if not line:
            continue

        # Extract param name
        name_match = re.match(r'^([A-Z][A-Z0-9_]+):\s*(.+)', line, re.DOTALL)
        if not name_match:
            continue

        param_name = name_match.group(1)
        rest = name_match.group(2).strip()

        # Extract type
        type_match = re.search(r'Type:\s*\[([^\]]+)\]', rest)
        param_type = type_match.group(1).strip() if type_match else "string"

        # Extract default
        default_match = re.search(r'Default:\s*([^\n]+?)(?:\s+(?:Type:|$|\n))', rest + "\n")
        param_default = default_match.group(1).strip() if default_match else None

        # Is optional?
        is_optional = "optional" in rest.lower() or "(optional)" in rest.lower()
        is_required = not is_optional and param_name not in ["OPTIONS", "EXTRA"]

        # Extract human-readable label (text before period)
        label_match = re.match(r'^([^.]+?)(?:\.|$)', rest)
        label = label_match.group(1).strip() if label_match else param_name

        # Get description (everything after first period up to Type:)
        desc_match = re.search(r'^[^.]+\.\s*(.*?)(?:\s*Type:)', rest, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else rest

        # Clean up description
        description = re.sub(r'\s+', ' ', description).strip()
        if not description:
            description = label

        params.append({
            "name": param_name,
            "label": label,
            "type": param_type,
            "description": description[:300],  # truncate very long descriptions
            "default": param_default,
            "required": is_required,
            "optional": is_optional,
        })

    return params


def clean_code_example(code: str) -> str:
    """Strip hardcoded paths and QGIS project boilerplate from code examples."""
    if not code:
        return ""

    # Strip hardcoded Windows paths
    code = re.sub(r"'[A-Z]:/[^']*\.(tif|shp|gpkg|vrt|prj|wld|txt|csv|kml|geojson)'",
                  "'path/to/input_file'", code)
    code = re.sub(r'"[A-Z]:/[^"]*\.(tif|shp|gpkg|vrt|prj|wld|txt|csv|kml|geojson)"',
                  '"path/to/input_file"', code)
    code = re.sub(r"'D:/[^']*'", "'path/to/data'", code)
    code = re.sub(r"'C:/[^']*'", "'path/to/output'", code)

    # Truncate at reasonable length (keep first ~30 lines)
    lines = code.split('\n')
    if len(lines) > 40:
        code = '\n'.join(lines[:40]) + '\n# ... (truncated)'

    return code.strip()


def infer_category(tool_id: str, description: str) -> str:
    """Infer category from tool_id and description text."""
    if tool_id in CATEGORY_MAP:
        return CATEGORY_MAP[tool_id]

    provider = tool_id.split(":")[0]

    # For grass tools with no useful description, use module prefix mapping
    _GRASS_MINIMAL_MARKER = "GRASS GIS tool:"
    if provider == "grass7" and (not description or _GRASS_CORRUPT_MARKER in description or description.startswith(_GRASS_MINIMAL_MARKER)):
        module_name = tool_id.split(":")[-1]  # e.g., "r.watershed"
        module_prefix = module_name.split(".")[0] if "." in module_name else ""
        # Use specific tool-name keywords
        name_lower = module_name.lower()
        if any(k in name_lower for k in ["watershed", "water", "hydro", "stream", "basin", "fill.dir", "topidx", "flow"]):
            return "hydrology"
        if any(k in name_lower for k in ["net", "path", "salesman", "distance", "alloc", "bridge"]):
            return "network"
        if any(k in name_lower for k in ["segment", "cluster", "maxlik", "classif"]):
            return "classification"
        if module_prefix == "i":
            return "remote_sensing"
        if module_prefix == "v":
            return "vector_ops"
        if module_prefix == "r":
            # r.* tools: further differentiate
            if any(k in name_lower for k in ["slope", "aspect", "viewshed", "roughness", "hillshade", "tpi", "tri", "drain"]):
                return "terrain"
            return "raster_ops"
        return GRASS_MODULE_CATEGORY.get(module_prefix, "raster_ops")

    desc_lower = (description or "").lower()

    for keywords, cat in KEYWORD_CATEGORY_MAP:
        if any(k in desc_lower for k in keywords):
            return cat

    return PROVIDER_CATEGORY_DEFAULTS.get(provider, "statistics")


def get_python_libs(tool_id: str, exec_route: str) -> list:
    """Get relevant Python libraries for a tool."""
    libs = []
    for lib, tools in PYTHON_LIBS_MAP.items():
        if tool_id in tools:
            libs.append(lib)

    # Add defaults by exec_route
    if exec_route == "pure_python" and not libs:
        provider = tool_id.split(":")[0]
        if provider == "native":
            libs = ["geopandas", "shapely"]
    elif exec_route == "rasterio" and not libs:
        libs = ["rasterio", "numpy"]
    elif exec_route == "grass":
        libs = ["grass-session"]
    elif exec_route == "gdal_cli":
        libs = ["subprocess", "gdal"]

    return libs


def get_related_tools(tool_id: str, all_tool_ids: set) -> list:
    """Get related tools, only including those in the registry."""
    related = RELATED_TOOLS.get(tool_id, [])
    return [t for t in related if t in all_tool_ids]


# Known-bad source description (applies to all 306 grass7 tools in this JSON)
_GRASS_CORRUPT_MARKER = "Reprojects a raster layer into another Coordinate Reference System"


def transform_tool(raw: dict, all_tool_ids: set) -> dict:
    """Transform a raw JSON tool entry into our registry schema."""
    tool_id = raw.get("tool_id", "")
    tool_name = raw.get("toolname", tool_id.split(":")[-1].replace("_", " ").title())
    description = raw.get("tool_description", "")
    params_str = raw.get("parameters", "")
    code = raw.get("code_example", "")

    # Provider
    provider = tool_id.split(":")[0] if ":" in tool_id else "unknown"

    # Detect corrupt grass7 descriptions and fix
    source_quality = "good"
    if provider == "grass7" and _GRASS_CORRUPT_MARKER in description:
        description = ""
        source_quality = "corrupt_description"

    # Also detect corrupt native descriptions (centroid desc for non-centroid tools)
    _NATIVE_CENTROID_CORRUPT = "creates a new point layer, with points representing the centroid"
    if provider == "native" and _NATIVE_CENTROID_CORRUPT in description:
        if tool_id not in ("native:centroids", "native:pointonsurface"):
            description = ""
            source_quality = "corrupt_description"

    # Apply known patches for GRASS tools (and others if needed)
    patch = GRASS_TOOL_PATCHES.get(tool_id, {})
    if patch.get("full_description"):
        description = patch["full_description"]
        source_quality = "patched"
    elif not description and provider == "grass7":
        # Generate a minimal description from tool name
        tname = tool_id.split(":")[-1]
        description = f"GRASS GIS tool: {tname}. Refer to GRASS documentation for full details."
        source_quality = "minimal"

    # Brief description (first sentence)
    if patch.get("brief_description"):
        brief = patch["brief_description"]
    else:
        brief = description.split("\n")[0].split(". ")[0].strip()
        if len(brief) > 200:
            brief = brief[:200] + "..."

    # Category — check patch first
    if patch.get("category"):
        category = patch["category"]
    else:
        category = infer_category(tool_id, description)

    # Exec route
    exec_route = get_exec_route(tool_id, description)

    # Parse parameters
    parameters = parse_parameters(params_str)

    # Python equivalent
    python_equivalent = PYTHON_EQUIVALENTS.get(tool_id, "")

    # Python libs
    python_libs = get_python_libs(tool_id, exec_route)

    # Use cases — check patch first
    if patch.get("use_cases"):
        use_cases = patch["use_cases"]
    else:
        use_cases = TOOL_SPECIFIC_USE_CASES.get(
            tool_id,
            USE_CASES_BY_CATEGORY.get(category, ["GIS analysis and spatial data processing"])
        )

    # Related tools
    related = get_related_tools(tool_id, all_tool_ids)

    # Clean code example
    clean_code = clean_code_example(code)

    return {
        "tool_id": tool_id,
        "tool_name": tool_name,
        "provider": provider,
        "category": category,
        "brief_description": brief,
        "full_description": description.strip(),
        "parameters": parameters,
        "exec_route": exec_route,
        "python_equivalent": python_equivalent,
        "python_libs": python_libs,
        "use_cases": use_cases,
        "related_tools": related,
        "source": "penn_state_json",
        "source_quality": source_quality,
        "original_code_example": clean_code,
    }


# ─── GRASS Tool Patches ─────────────────────────────────────────────────────────
# The source JSON has corrupt descriptions for all grass7 tools (all show gdal:warp text).
# We patch known high-value GRASS tools with correct descriptions.

# Patches also cover native tools with wrong descriptions in source JSON
GRASS_TOOL_PATCHES = {
    # ── Native tool patches (source JSON has mismatched descriptions) ──
    "native:clip": {
        "brief_description": "Clips a vector layer using the features of an overlay polygon layer. Only the parts of the features in the input layer that fall within the polygons of the overlay layer will be added to the resulting layer.",
        "full_description": "Clips a vector layer using the features of an overlay polygon layer. Only the parts of the features in the input layer that fall within the polygons of the overlay layer will be added to the resulting layer. Equivalent to geopandas.clip().",
        "category": "vector_ops",
        "use_cases": ["Extracting features within study area boundary", "County or watershed boundary data extraction", "Limiting analysis to client project area", "Data preparation for scoped environmental analysis"],
    },
    "native:intersection": {
        "brief_description": "Extracts the overlapping portions of features in the input and overlay layers. Features in the output layer represent areas where both input features existed.",
        "full_description": "Extracts the overlapping portions of features in the Input and Overlay layers. Features in the output layer represent areas where both input features existed, combining attributes from both layers.",
        "category": "vector_ops",
        "use_cases": ["Overlay analysis combining two feature datasets", "Land use within watershed or flood zone", "Zoning and parcel overlap analysis", "Environmental constraint mapping"],
    },
    "native:reprojectlayer": {
        "brief_description": "Reprojects a vector layer into a different Coordinate Reference System (CRS). Creates a copy of the layer with geometries reprojected to the target CRS.",
        "full_description": "Reprojects a vector layer in a different CRS. The output layer will have the same content as the input layer, but with geometries reprojected to the target CRS. Equivalent to gdf.to_crs().",
        "category": "vector_ops",
        "use_cases": ["Standardizing CRS across multi-source datasets", "Converting to client-required projection", "Preparing data for accurate distance/area calculations", "Aligning layers for overlay analysis"],
    },
    "native:joinattributesbylocation": {
        "brief_description": "Joins attributes from one vector layer to another by spatial relationship. Features in the output layer are matched and attributes joined based on spatial predicates (intersects, within, contains, etc.).",
        "full_description": "Takes an input vector layer and creates a new vector layer that is an extended version of the input one, with additional attributes in its attribute table. The additional attributes and their values are taken from a second vector layer. A spatial criteria is applied to select the values from the second layer that are added to each feature from the first layer.",
        "category": "vector_ops",
        "use_cases": ["Assigning census demographics to service areas", "Attaching environmental measurements to administrative boundaries", "Spatial join for multi-source data integration", "Linking point observations to polygon features"],
    },
    # ── GRASS tool patches ──
    "grass7:r.watershed": {
        "brief_description": "Calculates hydrological parameters and RUSLE factors from a DEM — watershed basins, flow direction, flow accumulation, slope length, and stream segments.",
        "full_description": "Calculates hydrological parameters including watershed basin boundaries, drainage direction, flow accumulation, stream segments, and slope length factor (LS factor for RUSLE) from a digital elevation model. Core GRASS GIS hydrology tool.",
        "category": "hydrology",
        "use_cases": ["Catchment delineation for stormwater consulting", "Automated drainage network extraction", "Hydrologic connectivity analysis", "Basin delineation for water quality studies"],
    },
    "grass7:r.stream.extract": {
        "brief_description": "Extracts stream networks from a DEM using flow accumulation thresholds.",
        "full_description": "Extracts stream networks from a DEM based on minimum upstream area (flow accumulation threshold). Produces both raster and vector stream networks.",
        "category": "hydrology",
        "use_cases": ["Stream network delineation for watershed analysis", "Drainage density mapping", "Riparian buffer zone delineation", "Hydrologic modeling input preparation"],
    },
    "grass7:r.fill.dir": {
        "brief_description": "Fills sinks in a raster digital elevation model to create a hydrologically conditioned DEM.",
        "full_description": "Fills depressions (sinks) in a DEM so that water can flow continuously downhill. Essential preprocessing step before watershed delineation.",
        "category": "hydrology",
        "use_cases": ["DEM preprocessing for hydrologic analysis", "Removing artifacts from elevation data", "Enabling proper flow routing", "Conditioning DEMs from LIDAR or SRTM"],
    },
    "grass7:r.cost": {
        "brief_description": "Creates a raster showing the cumulative cost of moving from each cell to the nearest source cell, using a cost surface.",
        "full_description": "Computes the cumulative cost of moving across a raster landscape from each cell to one or more source cells, considering a friction (cost) surface. Used for least-cost path analysis.",
        "category": "network",
        "use_cases": ["Wildlife corridor and habitat connectivity analysis", "Least-cost path routing through terrain", "Emergency vehicle access modeling", "Utility line routing optimization"],
    },
    "grass7:r.viewshed": {
        "brief_description": "Computes a viewshed raster from a DEM — identifies which cells are visible from a given observer point.",
        "full_description": "Computes visibility analysis from one or more observer points across a DEM. Output raster marks visible (1) and non-visible (0) cells.",
        "category": "terrain",
        "use_cases": ["Tower and antenna placement optimization", "Wind turbine visual impact assessment", "Military/security sightline analysis", "Scenic viewpoint identification"],
    },
    "grass7:r.slope.aspect": {
        "brief_description": "Generates slope, aspect, and curvature rasters from a DEM in a single operation.",
        "full_description": "Calculates slope, aspect, and optionally curvature from a digital elevation model. More comprehensive than gdal:slope/aspect as it produces multiple terrain attributes in one run.",
        "category": "terrain",
        "use_cases": ["Multi-attribute terrain analysis", "Geomorphometric mapping", "Erosion and stability modeling", "Terrain-based habitat characterization"],
    },
    "grass7:r.mapcalc": {
        "brief_description": "Performs algebraic operations on raster maps — GRASS's raster calculator supporting complex map algebra expressions.",
        "full_description": "GRASS raster algebra engine for performing arithmetic, logical, and conditional operations on rasters. Equivalent to ArcGIS Raster Calculator.",
        "category": "raster_ops",
        "use_cases": ["Band math and index calculation (NDVI, NDWI)", "Conditional raster reclassification", "Multi-layer raster combination", "Creating derived raster products"],
    },
    "grass7:i.segment": {
        "brief_description": "Segments a satellite image into homogeneous objects using region-growing algorithm for object-based image analysis (OBIA).",
        "full_description": "Performs image segmentation using a region-growing algorithm. Groups adjacent pixels with similar spectral characteristics into objects (segments) for OBIA workflows.",
        "category": "classification",
        "use_cases": ["Object-based land cover mapping", "Agricultural field delineation from imagery", "Urban morphology analysis", "Preprocessing for machine learning classification"],
    },
    "grass7:v.net.path": {
        "brief_description": "Finds shortest paths between pairs of nodes in a vector network.",
        "full_description": "Computes shortest paths between specified origin-destination pairs in a vector network using Dijkstra's algorithm.",
        "category": "network",
        "use_cases": ["Routing analysis for logistics", "Emergency response route planning", "Pedestrian accessibility mapping", "Service delivery optimization"],
    },
    "grass7:v.net.salesman": {
        "brief_description": "Solves the Traveling Salesman Problem — finds the optimal route visiting multiple stops in a network.",
        "full_description": "Finds an optimal route that visits a set of stops in a network with minimum total cost. Useful for service vehicle routing.",
        "category": "network",
        "use_cases": ["Delivery route optimization", "Field inspection routing", "Service area vehicle scheduling", "Multi-stop site visit planning"],
    },
    "grass7:i.cluster": {
        "brief_description": "Performs unsupervised classification of satellite imagery using k-means clustering.",
        "full_description": "Groups satellite image pixels into spectral clusters using iterative k-means algorithm. Used as the first step in unsupervised image classification.",
        "category": "classification",
        "use_cases": ["Unsupervised land cover classification", "Image exploratory analysis", "Training data generation for supervised classification", "Change detection between image dates"],
    },
    "grass7:r.topidx": {
        "brief_description": "Computes the topographic wetness index (TWI) from a DEM — indicates soil moisture accumulation potential.",
        "full_description": "Calculates the topographic wetness index (ln(a/tan(beta))) which represents the tendency of each cell to accumulate water based on upslope contributing area and local slope.",
        "category": "hydrology",
        "use_cases": ["Soil moisture potential mapping", "Wetland delineation support", "RUSLE-based erosion modeling", "Landscape ecology hydrologic characterization"],
    },
    "grass7:v.to.rast": {
        "brief_description": "Converts vector features (points, lines, areas) to raster format.",
        "full_description": "Converts vector geometry to raster representation. Equivalent to gdal:rasterize but within the GRASS environment.",
        "category": "raster_ops",
        "use_cases": ["Rasterizing vector boundaries for raster analysis", "Creating categorical rasters from polygon attributes", "Preparing masks for raster operations"],
    },
}


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(source_file=None):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting tool registry ingestion...")

    # Load source data
    if source_file and Path(source_file).exists():
        print(f"Loading from local file: {source_file}")
        with open(source_file) as f:
            raw_tools = json.load(f)
    else:
        print(f"Downloading from: {SOURCE_URL}")
        with urllib.request.urlopen(SOURCE_URL) as response:
            raw_tools = json.load(response)

    print(f"Loaded {len(raw_tools)} tools from source")

    # Build set of all tool IDs for cross-reference
    all_tool_ids = {t["tool_id"] for t in raw_tools}

    # Transform all tools
    registry = []
    for raw in raw_tools:
        try:
            transformed = transform_tool(raw, all_tool_ids)
            registry.append(transformed)
        except Exception as e:
            print(f"  Warning: failed to transform {raw.get('tool_id', '?')}: {e}")

    print(f"Transformed {len(registry)} tools successfully")

    # ── Save full registry ──
    registry_path = OUTPUT_DIR / "tool_registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"Saved: {registry_path}")

    # ── Save by category ──
    by_category = defaultdict(list)
    for tool in registry:
        by_category[tool["category"]].append(tool)

    cat_path = OUTPUT_DIR / "registry_by_category.json"
    with open(cat_path, "w") as f:
        json.dump(dict(sorted(by_category.items())), f, indent=2, ensure_ascii=False)
    print(f"Saved: {cat_path}")

    # ── Save by exec_route ──
    by_route = defaultdict(list)
    for tool in registry:
        by_route[tool["exec_route"]].append(tool)

    route_path = OUTPUT_DIR / "registry_by_exec_route.json"
    with open(route_path, "w") as f:
        json.dump(dict(sorted(by_route.items())), f, indent=2, ensure_ascii=False)
    print(f"Saved: {route_path}")

    # ── Print summary ──
    print("\n── Category Breakdown ──────────────────")
    for cat, tools in sorted(by_category.items()):
        print(f"  {cat:<25} {len(tools):>4} tools")

    print("\n── Exec Route Breakdown ────────────────")
    for route, tools in sorted(by_route.items()):
        print(f"  {route:<20} {len(tools):>4} tools")

    print(f"\nTotal: {len(registry)} tools")
    return registry, by_category, by_route


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else None
    main(source)
