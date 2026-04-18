# USGS Elevation Source Page

Source Summary:
The USGS 3D Elevation Program (3DEP) provides the primary public-domain elevation data for the United States.
Products include DEMs at 1-meter, 1/3 arc-second (~10 m), and 1 arc-second (~30 m) resolution, plus LiDAR point clouds for areas with 3DEP coverage.
The firm uses USGS elevation data for terrain derivatives, watershed delineation, and any project requiring a DEM where a client-supplied DEM is not provided.
Owner / Publisher:
U.S. Geological Survey (USGS), National Geospatial Program
Geography Support:
CONUS: near-complete coverage at 1/3 arc-second; growing coverage at 1-meter from 3DEP LiDAR
Alaska: 2 arc-second IFSAR-derived DEM; 3DEP LiDAR coverage expanding
Hawaii, territories: partial coverage; check availability before relying on USGS data
1-meter coverage varies by state and year; check the 3DEP availability index for the study area
Time Coverage:
the National Elevation Dataset (NED) is the legacy product, largely superseded by 3DEP
3DEP data vintage varies by area: most CONUS 1/3 arc-second data derives from 2000s-era NED with 3DEP updates where available
1-meter DEMs are tied to the LiDAR collection date, which varies by project (check metadata)
check the specific product's acquisition or publication date for the study area
Access Method:
USGS National Map download interface (https://apps.nationalmap.gov/downloader/)
USGS 3DEP web services and API
Amazon Web Services Open Data (s3://usgs-lidar-public for point clouds, s3://prd-tnm for DEMs)
Fetch Script:
`scripts/core/fetch_usgs_elevation.py` — search and download DEM tiles by bounding box
direct FTP/HTTPS download by tile
QGIS or GDAL can access USGS web map services for preview
File Formats:
GeoTIFF (primary DEM distribution)
LAS / LAZ (LiDAR point clouds)
IMG (legacy NED format; convert to GeoTIFF on ingestion)
Licensing / Usage Notes:
public domain federal data, no usage restrictions
attribution to USGS is standard practice
no licensing barriers to inclusion in client deliverables
Known Caveats:
1/3 arc-second data is in geographic CRS (NAD83, EPSG:4269) with elevation in meters; reproject to a projected CRS before computing slope or aspect
1-meter data is typically delivered in UTM zones (NAD83); confirm the zone for the study area
resolution alone does not guarantee quality; check metadata for acquisition method and accuracy
DEM tiles may have edge artifacts or differing acquisition dates at tile boundaries
hydro-enforced vs. bare-earth vs. first-return products exist; confirm which product is appropriate for the workflow
void areas may exist, especially in steep terrain or dense canopy; document void handling
LiDAR point clouds require processing before use as a DEM (classification, gridding); this is a separate workflow
Best-Fit Workflows:
workflows/WATERSHED_DELINEATION.md
workflows/TERRAIN_DERIVATIVES.md
site suitability analysis requiring slope or elevation context
flood risk or drainage analysis
viewshed or visibility analysis
Alternatives:
client-supplied DEMs (see
data-sources/CLIENT_SUPPLIED_DEMS.md
): may be higher resolution or more current for the specific site
SRTM (Shuttle Radar Topography Mission): global coverage at ~30 m but lower quality than 3DEP for CONUS
Copernicus DEM: global coverage at ~30 m and ~90 m; an alternative for non-U.S. work
state or county LiDAR programs: may offer higher resolution or more recent collections than 3DEP
Sources:
https://www.usgs.gov/3d-elevation-program
https://apps.nationalmap.gov/downloader/
USGS 3DEP product documentation
3DEP LiDAR coverage index (https://usgs.entwine.io)
Trust Level:
Production Source Page
