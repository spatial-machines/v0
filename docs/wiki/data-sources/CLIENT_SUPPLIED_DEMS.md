# Client-Supplied DEMs Source Page

Source Summary:
Clients occasionally provide their own digital elevation models for use in terrain analysis, watershed delineation, or site-specific work.
Client-supplied DEMs are not a standardized data product. They vary in format, resolution, CRS, quality, documentation, and provenance.
Every client-supplied DEM must go through an intake validation process before being used in a firm workflow.
Owner / Publisher:
the client or a surveyor / consultant engaged by the client
provenance may be unclear; the firm must request documentation
Geography Support:
project-specific; typically covers a small study area (a site, a parcel, a drainage basin)
extent is defined by the client's survey or acquisition scope
Time Coverage:
depends on the survey or acquisition date
may be current (recent LiDAR survey) or dated (legacy contour-derived DEM)
the firm must request and document the acquisition date
Access Method:
delivered by the client via file transfer (email, shared drive, cloud storage)
formats vary: GeoTIFF, IMG, ASCII grid, LAS/LAZ point clouds, contour shapefiles (requiring interpolation)
Licensing / Usage Notes:
usage terms depend on the client's agreement
the DEM may be proprietary survey data with restricted distribution
do not share client-supplied DEMs outside the project without explicit permission
do not load client-supplied DEMs into the firm's shared PostGIS database
Known Caveats:
CRS may be undocumented, incorrectly documented, or in a local coordinate system
elevation units may be meters, feet, or unspecified
the DEM may have been derived from contours (lower quality) rather than LiDAR (higher quality)
voids, NoData values, and edge artifacts are common
the DEM may cover only part of the study area required by the project
the horizontal and vertical accuracy may not be documented
if the DEM was produced by a surveyor, the survey methodology and standards may not be provided
some client-supplied DEMs are in formats that require conversion before use (e.g., ASCII grid, proprietary CAD formats)
Intake Validation Process
Every client-supplied DEM must pass these checks before entering a firm workflow:
1. Format and Readability
can the firm's open stack (GDAL, Rasterio) read the file?
if the format is proprietary or unusual, convert to GeoTIFF immediately and document the conversion
2. CRS Verification
is the CRS documented in the file metadata?
does the CRS match the project's expected study area when loaded on a map?
if the CRS is unknown, escalate to the client before proceeding per
standards/CRS_SELECTION_STANDARD.md
3. Elevation Unit Confirmation
are Z-values in meters or feet?
if unspecified, compare against a known benchmark (USGS DEM, known spot elevation) to infer units
document the unit determination method
4. Extent and Resolution
does the DEM cover the required study area?
what is the cell size (resolution)?
is the resolution sufficient for the planned analysis?
5. Quality Inspection
visual inspection for voids, striping, flat areas, edge artifacts, or interpolation smoothing
check the elevation range: are values plausible for the study area?
check for NoData cells that might need handling
6. Provenance Documentation
record: file name, source (who provided it), delivery date, acquisition date (if known), CRS, resolution, units, and any quality notes
assign source readiness tier per
standards/SOURCE_READINESS_STANDARD.md
:
if the DEM has documented provenance, known CRS, and reasonable quality: Tier 2 (Validated but Caveated)
if the DEM has poor documentation, unknown CRS, or quality concerns: Tier 3 (Provisional)
if nothing is known about the DEM: Tier 4 (Unreviewed); escalate before using
7. Escalation
if the CRS is unknown: stop and request clarification from the client
if the DEM has visible artifacts that could affect the analysis: document and escalate
if the project is legal-grade: require full provenance documentation from the client
Best-Fit Workflows
workflows/WATERSHED_DELINEATION.md
workflows/TERRAIN_DERIVATIVES.md
Alternatives
USGS 3DEP elevation products (see
data-sources/USGS_ELEVATION.md
): public-domain, documented, but may be lower resolution than a client's site-specific survey
state or county LiDAR programs: may offer recent, high-resolution alternatives
data-sources/LOCAL_FILES.md
— the general local-files intake pattern that this page specializes for DEM-specific concerns (elevation units, void handling, survey methodology)
Sources
firm DEM intake methodology notes
GDAL raster driver documentation (https://gdal.org/drivers/raster/)
Rasterio documentation (https://rasterio.readthedocs.io)
Trust Level
Validated Source Page Needs Source Validation (quality and documentation vary by client) Human Review Required
