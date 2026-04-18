# CRS Selection Standard

Purpose:
define how the firm selects and manages coordinate reference systems
prevent silent CRS mismatches that corrupt spatial joins, area calculations, and distance measurements
make projection choices explicit, documented, and reproducible
Use When
Use this standard whenever a workflow involves:
combining layers from different sources
computing distances, areas, or buffers
performing spatial joins or overlay analysis
delivering outputs in a client-specified projection
ingesting or validating a new spatial dataset
Do Not Use When
Do not use this standard to force a single CRS on every project. The correct CRS depends on geography, purpose, and deliverable requirements.
Approved Rule
Every project must document its working CRS and delivery CRS before spatial analysis begins.
CRS Categories
Storage and exchange:
EPSG:4326 (WGS 84) for geographic coordinates when storing or exchanging point data
EPSG:4269 (NAD83) for Census and TIGER-sourced geometry
Analysis requiring distance or area:
use a projected CRS appropriate to the study area
for CONUS regional work, NAD83 / Conus Albers (EPSG:5070) is the default unless project needs differ
for state or metro-level work, the relevant State Plane zone (NAD83) is preferred
for small-area buffering and distance, UTM zones (NAD83 or WGS 84) are acceptable
Delivery:
match the client's requested CRS if specified
if unspecified, deliver in the working projected CRS with metadata
Selection Decision Tree
Is the study area within a single U.S. state or metro? Use the relevant State Plane zone.
Is the study area multi-state or national? Use EPSG:5070 (Conus Albers).
Is the work global or cross-border? Use an appropriate UTM zone or project-specific choice.
Is the output for web mapping only? Reproject to EPSG:3857 at delivery, not during analysis.
Is the source data in a geographic CRS? Reproject to the working CRS before any distance, area, or buffer operation.
Inputs
study area extent
source data CRS(s)
required spatial operations (buffer, area, distance, overlay)
client delivery requirements
Method Notes
Always verify the CRS of incoming data before joining or analyzing. Do not assume.
Use PyProj, GDAL, or PostGIS ST_Transform for reprojection. Do not reproject by manually editing .prj files.
When combining Census / TIGER data (NAD83) with web or GPS sources (WGS 84), the datum shift is sub-meter for CONUS and can be ignored for most firm workflows. Document when this assumption is made.
Never compute distances or areas in a geographic CRS (degrees). Reproject first.
Record the EPSG code, not just a CRS name, in all outputs and methodology notes.
If a client supplies data with no CRS or an unknown CRS, assign Tier 3 (Provisional) per the Source Readiness Standard and escalate.
Validation Rules
A workflow should fail this standard if:
no working CRS is documented
distance or area was computed in a geographic CRS
layers were joined without confirming CRS alignment
the output CRS differs from the documented delivery CRS without explanation
an EPSG code is missing from the methodology note
Human Review Gates
Escalate when:
the study area crosses UTM zones or State Plane zones
the client requires a CRS the firm has not used before
source data arrives with no CRS or a suspected incorrect CRS
datum differences might materially affect the analysis (e.g., cross-border work)
Common Failure Modes
computing buffer distances in EPSG:4326 and getting degree-unit results
joining layers in different CRSs without reprojecting
delivering in EPSG:3857 (Web Mercator) and having the client compute areas from it
assuming all Census data is in the same CRS without checking
silently reprojecting during export without recording the change
confusing NAD83 geographic (EPSG:4269) with NAD83 projected variants
Related Workflows
workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/GEOCODE_BUFFER_ENRICHMENT.md
workflows/SERVICE_AREA_ANALYSIS.md
workflows/WATERSHED_DELINEATION.md
Sources
EPSG Geodetic Parameter Registry (https://epsg.org)
PyProj documentation
Census Bureau TIGER / Line technical documentation
PROJ documentation (https://proj.org)
Trust Level
Production Standard
