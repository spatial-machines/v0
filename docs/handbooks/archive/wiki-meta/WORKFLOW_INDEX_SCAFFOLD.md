# GIS Workflow Index Scaffold

This is the first-pass workflow map for the firm wiki.
It is based on recurring workflow families emphasized across:
ArcGIS Pro analysis and workflow systems
QGIS processing and model-design patterns
PostGIS spatial database workflows
GDAL / OGR vector and raster processing families
GeoPandas geospatial dataframe workflows
WhiteboxTools terrain and hydrology workflows
Census / ACS data-retrieval patterns
The goal is not to list every GIS function. The goal is to define the main workflow families the firm should know how to execute.
A. Project and Data Intake
project scoping and question decomposition
data inventory and source review
client data intake and validation
study area definition
geography selection
CRS and units review
B. Data Acquisition and Staging
ACS / Census retrieval
TIGER / boundary retrieval
Living Atlas review and source tracing
OSM / POI retrieval
local PostGIS extraction
client-file ingestion
DEM acquisition or validation
geocoding candidate acquisition
C. Data Engineering
schema normalization
CRS harmonization
field cleaning and standardization
geometry repair
spatial indexing
joins and enrichment
crosswalk construction
inventory generation
D. Vector Analysis
overlay analysis
clipping and masking
dissolves and aggregation
nearest-neighbor and proximity
within-distance selection
point-in-polygon enrichment
polygon ranking and comparison
E. Raster and Surface Analysis
raster preprocessing
reprojection and resampling
raster algebra
interpolation
terrain derivation
suitability surfaces
raster summaries to polygons
F. Hydrology
DEM conditioning
sink filling and breach handling
flow direction and accumulation
pour-point validation
watershed delineation
stream extraction
slope and aspect derivation
hydrologic QA
G. Network and Accessibility
geocoding and candidate review
route analysis
service area analysis
drive-time or distance catchments
origin-destination summaries
accessibility comparisons
H. Demographics and Market Analysis
ACS demographic inventory
tract / block-group enrichment
tract-to-ZIP / ZCTA aggregation
decade trend analysis
demographic shift analysis
density and growth metrics
trade area support
market ranking and peer comparison
I. POI and Business Landscape
POI category definition
POI retrieval from PostGIS
competitor landscape mapping
business density analysis
clustering and hotspot review
POI enrichment by geography
J. Imagery, Remote Sensing, and Change
image interpretation
classification
object detection
change detection
feature extraction
multidimensional raster workflows
stereo or measurement workflows
K. 3D, LiDAR, and Point Clouds
point-cloud ingestion
terrain model generation
feature extraction from LiDAR
surface comparison
visibility and viewshed
L. Cartography and Communication
choropleth design
graduated symbols
bivariate maps
annotation and labeling
map QA
chart and table outputs
client memo drafting
M. Publishing and Delivery
review-site build and verification
web map packaging
QGIS project packaging
export bundles
metadata and citations
delivery QA
N. QA, Review, and Governance
structural validation
interpretive review
source provenance checks
reproducibility checks
legal-grade review gates
publish readiness checks
O. Automation and Reuse
model designer workflows
task automation
script orchestration
reusable playbooks
project inventory reuse
workflow templates
First Pages To Create
Create these first:
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
standards/TREND_ANALYSIS_STANDARD.md
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
workflows/DECADE_TREND_ANALYSIS.md
workflows/POSTGIS_POI_LANDSCAPE.md
workflows/WATERSHED_DELINEATION.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
Promotion Notes
Not every category above should become a production-standard page immediately. Use this index to:
identify the next missing workflow
cluster research
prevent duplicate pages
This index is the map. The standards and workflow pages are the operational content.
