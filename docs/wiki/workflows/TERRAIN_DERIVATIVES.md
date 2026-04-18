# Terrain Derivatives Workflow

Purpose:
produce slope, aspect, hillshade, curvature, and other terrain surface products from a DEM
support non-watershed projects that need terrain characterization without full hydrologic delineation
provide a standalone terrain-surface workflow that can be invoked independently of
workflows/WATERSHED_DELINEATION.md
Typical Use Cases
slope analysis for site suitability or grading assessment
aspect mapping for solar exposure or vegetation analysis
hillshade generation for cartographic visualization
terrain position index (TPI) or topographic wetness index (TWI) for landscape characterization
curvature analysis for erosion or landform mapping
viewshed or visibility analysis base preparation
Inputs
validated DEM (elevation raster)
approved working CRS per
standards/CRS_SELECTION_STANDARD.md
list of requested terrain derivatives
project-specific parameters (e.g., hillshade azimuth and altitude, curvature type)
Preconditions
the DEM source has been assigned a readiness tier per
standards/SOURCE_READINESS_STANDARD.md
for client-supplied DEMs, the intake validation in
data-sources/CLIENT_SUPPLIED_DEMS.md
has been completed
for USGS-sourced DEMs, the source page
data-sources/USGS_ELEVATION.md
has been reviewed
the working CRS is confirmed and is a projected CRS appropriate for the study area
the DEM resolution is documented and sufficient for the requested derivatives
Preferred Tools
WhiteboxTools (preferred for slope, aspect, curvature, hillshade, TPI, TWI)
GDAL (gdaldem for slope, aspect, hillshade; core raster I/O)
Rasterio for Python-native raster access and manipulation
QGIS-compatible Python workflows for visualization and verification
Execution Order
Phase 1: DEM Validation
Load the DEM and verify:
CRS matches the approved working CRS (reproject if needed)
resolution (cell size) is documented
extent covers the study area
elevation values are in expected units (meters or feet) and range
NoData values are properly defined, not masquerading as extreme elevations
Inspect for artifacts: flat areas, striping, edge effects, void fills.
If the DEM requires conditioning (void fill, smoothing), document what was applied and why.
Phase 2: Derivative Generation
Slope
: compute slope in the approved units (degrees or percent rise).
document which algorithm is used (Horn, Zevenbergen-Thorne, etc.)
verify output range is plausible (0 to ~90 degrees for degree slope)
Aspect
: compute aspect in degrees from north (0-360).
verify flat areas are handled (aspect is undefined for slope = 0; document how NoData or -1 values are assigned)
Hillshade
: compute hillshade with approved azimuth and altitude.
default: azimuth 315°, altitude 45° unless the project specifies otherwise
output is 0-255 grayscale
Curvature
(if requested): compute profile and/or plan curvature.
document the curvature type and sign convention
TPI / TWI
(if requested):
TPI: difference between a cell's elevation and the mean of its neighborhood; document the neighborhood radius
TWI: requires flow accumulation and slope; document whether the flow accumulation was computed specifically or reused from a hydrology workflow
Record all parameters (tool, algorithm, version, input CRS, output units) for each derivative.
Phase 3: Validation
Visually inspect each derivative against the source DEM and known terrain features.
Spot-check values at known locations (hilltops should have low slope, steep hillsides should have high slope, north-facing slopes should have aspect near 0/360).
Verify NoData handling: no spurious extreme values at DEM edges or void locations.
Confirm output CRS matches the input DEM CRS.
Confirm output resolution matches the input DEM resolution (no accidental resampling).
Phase 4: Output
Export derivatives in approved raster format (GeoTIFF preferred).
Include metadata: CRS, resolution, units, algorithm, tool version, source DEM identifier.
Package derivatives with a methodology note.
If the project is legal-grade, follow the additional requirements in
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
.
Validation Checks
slope values are within plausible range for the terrain
aspect values are 0-360 with flat areas handled explicitly
hillshade values are 0-255 with no unexpected NoData patches
output CRS and resolution match the input DEM
NoData cells in the DEM produce NoData in derivatives, not spurious values
all parameters and tool versions are documented
derivatives are visually consistent with expected terrain features
Common Failure Modes
computing slope from a DEM in geographic CRS (degrees), producing meaningless results because X/Y units differ from Z units
not documenting whether slope is in degrees or percent
flat-area artifacts in aspect (large patches of -1 or 0 where aspect is undefined)
hillshade with wrong azimuth making the terrain look inverted
accidentally resampling the DEM during reprojection, changing the effective resolution
treating a void-filled DEM as original data without noting the fill
not recording tool version, making the analysis non-reproducible
Escalate When
the DEM has visible artifacts that could affect derivative quality
the project is legal-grade and requires enhanced provenance
the study area includes flat terrain where aspect and curvature are poorly defined
the DEM resolution is coarser than the features the project needs to characterize
the client requests a derivative the firm has not produced before
Outputs
slope raster (degrees or percent, as specified)
aspect raster (degrees from north)
hillshade raster (0-255)
optional: curvature, TPI, TWI rasters
methodology note with parameters, tool versions, and CRS documentation
QA summary
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
(if applicable)
qa-review/HYDROLOGY_OUTPUT_QA.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
workflows/WATERSHED_DELINEATION.md
(related but separate workflow)
Sources
WhiteboxTools documentation (https://www.whiteboxgeo.com/manual/wbt_book/)
GDAL gdaldem documentation (https://gdal.org/programs/gdaldem.html)
Rasterio documentation (https://rasterio.readthedocs.io)
Horn, B.K.P. (1981) — Hill shading and the reflectance map (slope algorithm reference)
Trust Level
Validated Workflow Needs Testing
