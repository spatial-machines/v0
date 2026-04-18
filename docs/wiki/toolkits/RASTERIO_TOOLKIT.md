# Rasterio Toolkit

Toolkit Summary:
Rasterio is a Python library for reading, writing, and analyzing geospatial raster data.
It wraps GDAL but provides a more Pythonic API with direct access to raster data as NumPy arrays.
The firm uses Rasterio when Python-native raster I/O, array operations, or pixel-level analysis is needed, complementing GDAL's command-line tools and WhiteboxTools' specialized algorithms.

Best Uses
- reading raster data into NumPy arrays for custom computation
- writing NumPy arrays back to GeoTIFF or other raster formats with correct georeferencing
- raster algebra: arithmetic between bands or rasters (NDVI, normalized indices, difference surfaces)
- windowed reading of large rasters (processing a raster in tiles without loading the entire file into memory)
- extracting raster values at point locations (sampling)
- zonal statistics using rasterstats or manual masking
- raster masking and clipping with vector geometry
- inspecting raster metadata (CRS, bounds, resolution, NoData, band count)
- creating raster outputs from analysis pipelines that produce NumPy arrays

Avoid For
- command-line batch processing and format conversion (use GDAL directly — gdalwarp, gdal_translate, ogr2ogr)
- terrain derivatives (slope, aspect, hillshade) when gdaldem or WhiteboxTools is sufficient
- hydrologic preprocessing and stream extraction (use WhiteboxTools)
- vector operations (use GeoPandas)
- large-scale spatial queries (use PostGIS)
- map styling and cartographic output (use QGIS)

Core Operations

### Reading Rasters
```python
import rasterio

with rasterio.open("dem.tif") as src:
    print(src.crs)          # CRS
    print(src.bounds)       # spatial extent
    print(src.res)          # pixel resolution
    print(src.shape)        # (rows, cols)
    print(src.nodata)       # NoData value
    print(src.count)        # number of bands
    data = src.read(1)      # read band 1 as NumPy array
    profile = src.profile   # metadata dict for writing
```

### Writing Rasters
```python
import numpy as np

profile.update(dtype=rasterio.float32, count=1)

with rasterio.open("output.tif", "w", **profile) as dst:
    dst.write(result_array.astype(rasterio.float32), 1)
```

### Raster Algebra
```python
with rasterio.open("band4.tif") as nir, rasterio.open("band3.tif") as red:
    nir_data = nir.read(1).astype(float)
    red_data = red.read(1).astype(float)
    ndvi = (nir_data - red_data) / (nir_data + red_data + 1e-10)
```

### Windowed Reading (Large Rasters)
```python
from rasterio.windows import Window

with rasterio.open("large_raster.tif") as src:
    for ji, window in src.block_windows(1):
        data = src.read(1, window=window)
        # process tile
```

### Point Sampling
```python
import rasterio

coords = [(lon1, lat1), (lon2, lat2), (lon3, lat3)]

with rasterio.open("dem.tif") as src:
    values = list(src.sample(coords))
```

### Masking with Vector Geometry
```python
import rasterio
from rasterio.mask import mask
import geopandas as gpd

gdf = gpd.read_file("study_area.gpkg")
shapes = gdf.geometry.values

with rasterio.open("dem.tif") as src:
    out_image, out_transform = mask(src, shapes, crop=True)
    out_meta = src.meta.copy()
    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })

with rasterio.open("clipped.tif", "w", **out_meta) as dst:
    dst.write(out_image)
```

### Zonal Statistics (with rasterstats)
```python
from rasterstats import zonal_stats
import geopandas as gpd

gdf = gpd.read_file("zones.gpkg")
stats = zonal_stats(gdf, "dem.tif", stats=["mean", "min", "max", "std", "count"])
```

Workflow Fit

Use Rasterio when:
- the workflow requires reading raster data into Python for custom array-level computation
- raster algebra or derived indices are needed (NDVI, difference surfaces, normalized scores)
- point sampling from a raster surface is part of the pipeline
- zonal statistics are needed for vector zones against a raster surface
- writing analysis results as new georeferenced rasters
- the analyst needs fine-grained control over windowed reading for large files

Use GDAL instead when:
- the task is format conversion, reprojection, or resampling (gdalwarp, gdal_translate)
- command-line batch processing is the most efficient approach
- basic terrain derivatives (slope, aspect, hillshade) via gdaldem are sufficient

Use WhiteboxTools instead when:
- the task involves hydrologic preprocessing, stream extraction, or watershed delineation
- advanced geomorphometric indices are needed
- LiDAR point cloud processing is required

Validation Expectations
When using Rasterio in a firm workflow:
- always check `src.crs` before spatial operations — confirm the raster is in the expected CRS
- check `src.nodata` and handle NoData values explicitly in array operations (mask or replace before arithmetic)
- after writing output rasters, reopen and verify CRS, extent, resolution, and that values are plausible
- for raster algebra: confirm input rasters have the same CRS, extent, and resolution before performing operations
- when masking with vector geometry: confirm the vector and raster are in the same CRS
- for zonal statistics: verify that zone geometry and raster CRS match
- document the Rasterio version and any key parameters used

Related Workflows
- `workflows/TERRAIN_DERIVATIVES.md` — terrain analysis that may use Rasterio for custom derivatives
- `workflows/WATERSHED_DELINEATION.md` — hydrologic work where Rasterio may handle I/O alongside WhiteboxTools
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — raster output packaging

Related Toolkits
- `toolkits/GDAL_OGR_TOOLKIT.md` — underlying library; use GDAL directly for command-line operations
- `toolkits/WHITEBOXTOOLS_TOOLKIT.md` — specialized terrain and hydrology algorithms
- `toolkits/GEOPANDAS_TOOLKIT.md` — vector counterpart for tabular spatial analysis

Related Data Sources
- `data-sources/USGS_ELEVATION.md` — primary DEM source for raster analysis
- `data-sources/CLIENT_SUPPLIED_DEMS.md` — client-provided elevation and surface data

Sources
Rasterio documentation: https://rasterio.readthedocs.io/
Rasterio GitHub: https://github.com/rasterio/rasterio
rasterstats documentation: https://pythonhosted.org/rasterstats/
NumPy documentation: https://numpy.org/doc/

Trust Level
Validated Toolkit Page
