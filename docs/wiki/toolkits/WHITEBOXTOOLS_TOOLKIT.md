# WhiteboxTools Toolkit

Toolkit Summary:
WhiteboxTools is an open-source geospatial analysis platform with over 500 tools focused on geomorphometry, hydrology, terrain analysis, and raster/LiDAR processing.
It is written in Rust for performance and provides a command-line interface, a Python frontend (whitebox-tools or whitebox-workflows), and a QGIS plugin.
The firm uses WhiteboxTools as a complement to GDAL for advanced terrain and hydrologic analysis that goes beyond basic slope/aspect/hillshade.

Best Uses
- hydrologic preprocessing: breach/fill depressions, flow direction, flow accumulation, stream extraction
- watershed delineation and sub-basin extraction
- terrain analysis: slope, aspect, curvature, wetness index, topographic position index, relative elevation
- geomorphometric indices: terrain ruggedness, surface roughness, deviation from mean elevation
- LiDAR point cloud processing: classification, ground filtering, DEM generation from LAS/LAZ
- stream network analysis: Strahler order, Horton statistics, longest flow path
- cost-distance and least-cost path analysis
- hillslope and landform classification
- raster math and conditional operations

Avoid For
- vector-heavy analysis with tabular joins and attribute manipulation (use GeoPandas)
- format conversion and basic raster operations (use GDAL — simpler for routine I/O tasks)
- network routing and travel-time analysis (use OSRM, Valhalla, or pgRouting)
- map styling and cartographic output (use QGIS)
- SQL-based spatial queries (use PostGIS)

Core Operations

### Hydrologic Preprocessing
```
whitebox_tools -r=BreachDepressions -i=dem.tif -o=dem_breached.tif
whitebox_tools -r=FillDepressions -i=dem.tif -o=dem_filled.tif
whitebox_tools -r=D8Pointer -i=dem_breached.tif -o=flow_dir.tif
whitebox_tools -r=D8FlowAccumulation -i=flow_dir.tif -o=flow_accum.tif --pntr
```

### Stream Extraction and Watershed Delineation
```
whitebox_tools -r=ExtractStreams -i=flow_accum.tif -o=streams.tif --threshold=1000
whitebox_tools -r=Watershed -d8_pntr=flow_dir.tif --pour_pts=outlets.shp -o=watersheds.tif
whitebox_tools -r=Basins -d8_pntr=flow_dir.tif -o=basins.tif
```

### Terrain Analysis
```
whitebox_tools -r=Slope -i=dem.tif -o=slope.tif --units=degrees
whitebox_tools -r=Aspect -i=dem.tif -o=aspect.tif
whitebox_tools -r=PlanCurvature -i=dem.tif -o=plan_curv.tif
whitebox_tools -r=ProfileCurvature -i=dem.tif -o=prof_curv.tif
whitebox_tools -r=WetnessIndex -i=dem.tif -o=twi.tif
whitebox_tools -r=RelativeTopographicPosition -i=dem.tif -o=rtp.tif --filterx=11 --filtery=11
whitebox_tools -r=DeviationFromMeanElevation -i=dem.tif -o=dev_mean.tif --filterx=11 --filtery=11
```

### LiDAR Processing
```
whitebox_tools -r=LidarInfo -i=input.las
whitebox_tools -r=LidarGroundPointFilter -i=input.las -o=ground.las --radius=2.0 --slope=30
whitebox_tools -r=LidarIdwInterpolation -i=ground.las -o=dem.tif --resolution=1.0
```

### Python Frontend
```python
from whitebox import WhiteboxTools

wbt = WhiteboxTools()
wbt.set_working_dir("/path/to/data")
wbt.breach_depressions("dem.tif", "dem_breached.tif")
wbt.d8_pointer("dem_breached.tif", "flow_dir.tif")
wbt.d8_flow_accumulation("flow_dir.tif", "flow_accum.tif", pntr=True)
wbt.extract_streams("flow_accum.tif", "streams.tif", threshold=1000)
```

Workflow Fit

Use WhiteboxTools when:
- the workflow requires hydrologic preprocessing beyond basic GDAL terrain derivatives
- watershed delineation, stream extraction, or flow analysis is needed
- advanced geomorphometric indices are part of the analysis
- LiDAR point cloud processing is needed to generate a DEM
- cost-distance or terrain-surface-based routing is part of the workflow

Use GDAL instead when:
- only slope, aspect, or hillshade are needed (gdaldem is simpler)
- format conversion or reprojection is the main task
- the operation does not require hydrologic or geomorphometric algorithms

Use Rasterio instead when:
- pixel-level raster algebra or array operations in Python are needed
- reading raster data into NumPy arrays for custom computation
- raster I/O with fine-grained control over windows, bands, and metadata

Validation Expectations
When using WhiteboxTools in a firm workflow:
- document the tool version (WhiteboxTools version and the specific tool name)
- verify input DEM CRS and resolution before processing
- for hydrologic work: confirm whether the DEM is breached or filled and document the method
- check output rasters for NoData artifacts, especially at tile edges or study-area boundaries
- compare stream extraction results against known hydrography (NHD or local reference) for plausibility
- for LiDAR work: document the point classification and ground filtering parameters used
- confirm that output CRS and resolution match expectations

Related Workflows
- `workflows/WATERSHED_DELINEATION.md` — primary use of WhiteboxTools hydrologic preprocessing
- `workflows/TERRAIN_DERIVATIVES.md` — terrain analysis support (complement to GDAL)

Related Toolkits
- `toolkits/GDAL_OGR_TOOLKIT.md` — format conversion and basic terrain derivatives
- `toolkits/RASTERIO_TOOLKIT.md` — Python raster I/O and array operations

Related Data Sources
- `data-sources/USGS_ELEVATION.md` — primary DEM source for terrain and hydrology work
- `data-sources/CLIENT_SUPPLIED_DEMS.md` — client-provided elevation data

Sources
WhiteboxTools documentation: https://www.whiteboxgeo.com/manual/wbt_book/
WhiteboxTools GitHub: https://github.com/jblindsay/whitebox-tools
Python frontend (whitebox): https://pypi.org/project/whitebox/
QGIS plugin: available through the QGIS Plugin Manager

Trust Level
Validated Toolkit Page
