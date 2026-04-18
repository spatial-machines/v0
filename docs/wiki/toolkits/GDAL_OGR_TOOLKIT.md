# GDAL / OGR Toolkit

Toolkit Summary:
GDAL (Geospatial Data Abstraction Library) is the foundational open-source library for raster and vector geospatial data translation and processing.
OGR is the vector component of GDAL. In practice the library is distributed as one package and the firm refers to it as GDAL/OGR.
Nearly every tool in the firm's open stack (GeoPandas, Rasterio, PostGIS, QGIS) depends on GDAL under the hood for format support and reprojection.
The firm uses GDAL/OGR directly for format conversion, reprojection, raster processing (gdaldem, gdalwarp), and batch operations that benefit from command-line automation.
Best Uses
format conversion: shapefile ↔ GeoPackage ↔ GeoJSON ↔ PostGIS ↔ CSV (ogr2ogr)
raster format conversion: GeoTIFF ↔ IMG ↔ ASCII grid ↔ VRT (gdal_translate)
raster reprojection and resampling (gdalwarp)
terrain derivatives: slope, aspect, hillshade, color-relief (gdaldem)
raster information inspection (gdalinfo)
vector information inspection (ogrinfo)
batch processing via shell scripts
building virtual raster mosaics (gdalbuildvrt)
raster statistics and overviews (gdaladdo)
clipping rasters to study areas (gdalwarp with cutline)
Avoid For
interactive spatial analysis with tabular manipulation (use GeoPandas)
complex multi-step spatial SQL queries (use PostGIS)
Python-native raster array operations (use Rasterio, which wraps GDAL but provides a more Pythonic API)
map styling and cartographic output (use QGIS)
network analysis (use pgRouting or OSRM)
Core Operations
Vector (OGR)
ogr2ogr — format conversion and transformation
ogr2ogr -f "GPKG" output.gpkg input.shp
— shapefile to GeoPackage
ogr2ogr -f "GeoJSON" output.geojson input.gpkg
— GeoPackage to GeoJSON
ogr2ogr -f "PostgreSQL" PG:"dbname=..." input.gpkg
— load into PostGIS
-t_srs EPSG:5070
— reproject during conversion
-sql "SELECT * FROM layer WHERE pop > 1000"
— filter during conversion
-clipdst clip.gpkg
— clip to a boundary during conversion
ogrinfo — inspect vector data
ogrinfo -al -so input.gpkg
— summary of all layers (field names, geometry type, CRS, feature count)
Raster (GDAL)
gdalinfo — inspect raster data
gdalinfo input.tif
— CRS, resolution, extent, band info, statistics, NoData value
gdal_translate — format conversion
gdal_translate -of GTiff input.img output.tif
— IMG to GeoTIFF
gdalwarp — reprojection, resampling, clipping
gdalwarp -t_srs EPSG:5070 input.tif output.tif
— reproject
gdalwarp -tr 10 10 input.tif output.tif
— resample to 10m resolution
gdalwarp -cutline study_area.gpkg -crop_to_cutline input.tif clipped.tif
— clip to study area
gdaldem — terrain derivatives
gdaldem slope input.tif slope.tif
— compute slope
gdaldem aspect input.tif aspect.tif
— compute aspect
gdaldem hillshade input.tif hillshade.tif -az 315 -alt 45
— compute hillshade
gdalbuildvrt — virtual raster mosaic
gdalbuildvrt mosaic.vrt tile1.tif tile2.tif tile3.tif
— build a virtual mosaic without copying data
Workflow Fit
Use GDAL/OGR directly when:
converting between formats as a data preparation step
batch-processing many files via shell scripts
reprojecting rasters before analysis
generating terrain derivatives from DEMs
inspecting unfamiliar files to determine CRS, extent, and schema
clipping large rasters to a study area before loading into Python
Use Rasterio instead when:
working with raster data in Python and needing array-level access
performing raster algebra or pixel-level operations
reading raster data into NumPy arrays for analysis
Use GeoPandas instead when:
performing vector analysis with pandas-style data manipulation
Validation Expectations
When using GDAL/OGR in a firm workflow:
always run
gdalinfo
or
ogrinfo
on inputs to verify CRS, extent, and schema before processing
verify the output CRS matches expectations after any reprojection
document the GDAL version used (legal-grade work requires this)
check that NoData values are preserved correctly through transformations
verify raster resolution after resampling (did the cell size change as intended?)
confirm feature counts before and after ogr2ogr conversions (no silent row loss)
Related Workflows
workflows/WATERSHED_DELINEATION.md
— raster preprocessing with GDAL
workflows/TERRAIN_DERIVATIVES.md
— gdaldem for slope/aspect/hillshade
workflows/QGIS_HANDOFF_PACKAGING.md
— format conversion for delivery
workflows/TRACT_JOIN_AND_ENRICHMENT.md
— ogr2ogr for data preparation
toolkits/GEOPANDAS_TOOLKIT.md
— GeoPandas uses GDAL/Fiona for I/O
toolkits/POSTGIS_TOOLKIT.md
— ogr2ogr for PostGIS import/export
Sources
GDAL documentation (https://gdal.org)
GDAL command-line utilities reference (https://gdal.org/programs/)
OGR SQL dialect reference (https://gdal.org/user/ogr_sql_dialect.html)
Trust Level
Validated Toolkit Page
