# Watershed Delineation Workflow

Purpose:
define a defendable workflow for watershed delineation and terrain derivatives using an open, scriptable stack
support client work where hydrologic outputs must be reproducible and reviewable
Typical Use Cases
watershed delineation from client-supplied DEMs
slope and aspect derivation
hydrologic context for environmental or legal analysis
drainage area review around a candidate pour point
Inputs
project brief
DEM or terrain source
proposed pour point
approved coordinate reference system
any client constraints or supporting background documents
Preconditions
the DEM has been ingested and validated
the working CRS has been confirmed
the pour point is documented and reviewable
the project has read any legal-grade review or client-specific constraints
Preferred Tools
WhiteboxTools
GDAL
Rasterio
GeoPandas
QGIS-compatible Python workflows
Execution Order
Validate the DEM source, extent, resolution, and CRS.
Reproject only if the approved workflow requires it.
Inspect and validate the proposed pour point.
Condition the DEM if needed using an approved fill or breach workflow.
Compute flow direction and flow accumulation.
Snap or validate the pour point against realistic drainage logic if approved.
Delineate the watershed.
Derive slope and aspect if required.
Validate the watershed result against visible terrain and hydrologic expectations.
Package outputs, method notes, and QA notes.
Validation Checks
DEM metadata is recorded
CRS is explicit
pour point logic is documented
watershed boundary is visually plausible
slope and aspect outputs are in expected units and ranges
all major hydrology steps are reproducible
Common Failure Modes
using the wrong CRS or units
accepting an unrealistic pour point
skipping DEM conditioning where it materially matters
treating a technically generated watershed as legally sufficient without review
failing to preserve enough metadata for later challenge or reproduction
Escalate When
the project supports legal or regulatory analysis
the pour point is uncertain
the DEM quality is questionable
client instructions conflict with hydrologic logic
the watershed result is sensitive to small upstream assumptions
Outputs
validated DEM derivative set
watershed polygon
slope raster or summary
aspect raster or summary
method and QA note
reviewable project package
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
qa-review/HYDROLOGY_OUTPUT_QA.md
workflows/TERRAIN_DERIVATIVES.md
data-sources/USGS_ELEVATION.md
data-sources/CLIENT_SUPPLIED_DEMS.md
Sources
WhiteboxTools documentation
GDAL documentation
hydrology workflow references from QGIS and USGS
Trust Level
Validated Workflow Human Review Required Needs Testing
