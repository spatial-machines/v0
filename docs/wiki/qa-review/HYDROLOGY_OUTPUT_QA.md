# Hydrology Output QA Checklist

Purpose:
provide a dedicated review checklist for watershed delineation, terrain derivative, and related hydrologic outputs
catch the domain-specific errors that structural QA alone cannot detect
validate outputs before they are used in client delivery, environmental analysis, or legal-grade work
Use When
Use this checklist when reviewing any output from:
workflows/WATERSHED_DELINEATION.md
workflows/TERRAIN_DERIVATIVES.md
any workflow that produces flow direction, flow accumulation, stream network, or drainage-area outputs
any terrain analysis where the results will support hydrologic or environmental conclusions
Do Not Use When
Do not use this checklist for:
demographic or vector-only outputs (use
qa-review/STRUCTURAL_QA_CHECKLIST.md
)
map cartography review (use
qa-review/MAP_QA_CHECKLIST.md
)
Core Hydrology Checks
DEM Source Validation
DEM source is identified (USGS 3DEP, client-supplied, other)
DEM source readiness tier is assigned per
standards/SOURCE_READINESS_STANDARD.md
DEM resolution is documented and appropriate for the analysis scale
DEM CRS is projected and in expected units; elevation Z-units are documented (meters, feet)
NoData values are properly defined and do not appear as real elevations
DEM vintage or acquisition date is recorded
any DEM conditioning applied (void fill, breach, smooth) is documented with parameters
Flow Direction and Accumulation
flow direction algorithm is documented (D8, D-infinity, or other)
flow direction raster visually aligns with expected drainage patterns
flow accumulation highlights recognizable stream channels
no unexpected flat areas or circular flow patterns
the tool and version used are recorded
Pour Point and Watershed
pour point location is documented with coordinates and rationale
if the pour point was snapped to a high-accumulation cell, the snap distance and logic are recorded
the delineated watershed boundary is visually plausible against terrain
the watershed does not include areas obviously outside the drainage basin
the watershed does not miss areas obviously inside the drainage basin
watershed area is plausible relative to known benchmarks or prior studies
if multiple pour points were used, each watershed is individually validated
Terrain Derivatives
slope values are in the documented units (degrees or percent) and within plausible range
aspect values are 0-360 with flat areas handled (NoData or -1, documented)
hillshade uses the documented azimuth and altitude; terrain does not appear inverted
curvature, TPI, or TWI outputs (if produced) have documented parameters and plausible value ranges
no edge artifacts or NoData-boundary artifacts in derivative outputs
derivative CRS and resolution match the source DEM
Reproducibility
all processing steps are documented in order
tool names, versions, and parameters are recorded for every step
the analysis can be re-run from the documented steps and produce the same result
intermediate outputs are preserved if the project is legal-grade per
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
Escalate When
the watershed boundary is sensitive to small changes in pour-point location
the DEM has visible artifacts (striping, voids, flat fills) that could affect results
the analysis will be used in legal, regulatory, or evidentiary contexts
the delineated watershed area differs materially from prior studies or client expectations
slope or aspect outputs show large patches of uniform value that suggest processing errors
the pour point was manually placed rather than derived from an approved method
Common Failure Modes
using a DEM in geographic CRS where X/Y are degrees and Z is meters, producing incorrect slope
accepting a machine-delineated watershed without visual inspection
not documenting the DEM conditioning method, making the analysis non-reproducible
snap distance too large, moving the pour point to a different drainage
NoData masquerading as zero elevation, creating false sinks
hillshade with azimuth and altitude swapped, producing an inverted terrain appearance
treating WhiteboxTools or GDAL defaults as documented parameters (always record explicitly)
Relationship to Other QA Pages
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first for general file and geometry integrity
workflows/WATERSHED_DELINEATION.md
— the primary workflow this review validates
workflows/TERRAIN_DERIVATIVES.md
— the derivative workflow this review covers
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
— imposes additional requirements if the output is legal-grade
standards/CRS_SELECTION_STANDARD.md
— governs CRS choices for terrain work
Trust Level
Validated QA Page Needs Testing Human Review Required
