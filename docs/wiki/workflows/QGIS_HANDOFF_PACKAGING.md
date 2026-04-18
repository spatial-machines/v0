# QGIS Handoff Packaging Workflow

Purpose:
package analysis outputs into a portable QGIS project file for handoff to a client, collaborator, or internal reviewer
ensure the package is self-contained, documented, and can be opened without access to the firm's internal systems
Typical Use Cases
delivering a spatial analysis package to a client who uses QGIS or open-source GIS
handing off a reviewable project to an internal colleague
archiving a project in a format that can be reopened years later without proprietary dependencies
providing a GIS-ready supplement to a review site or report delivery
Inputs
approved analysis outputs (layers, tables, maps) that have passed structural QA
project brief specifying delivery requirements
methodology note and provenance metadata per
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
style definitions (symbology, classification, labeling) for thematic layers
any supporting reference files (basemaps, boundary context, legends)
Preconditions
all outputs have passed
qa-review/STRUCTURAL_QA_CHECKLIST.md
interpretive review is complete if the package includes narrative or labeled maps
the publishing readiness gates in
standards/PUBLISHING_READINESS_STANDARD.md
have been assessed
the delivery CRS is confirmed
internal-only fields and sensitive data have been removed
Preferred Tools
QGIS for project assembly and style configuration
GeoPackage as the preferred data container (single-file, portable, open standard)
GeoPandas for pre-export data preparation if needed
GDAL/OGR for format conversion if source data is not already in GeoPackage
Execution Order
Phase 1: Data Preparation
Collect all layers to be included in the package.
Convert all layers to GeoPackage format if not already.
one GeoPackage per project is preferred for simplicity
store all vector layers as tables within the GeoPackage
raster layers may remain as separate GeoTIFF files if they are too large for the GeoPackage
Reproject all layers to the approved delivery CRS.
Remove internal-only fields, debug columns, and sensitive attributes.
Rename fields to client-friendly names if the project requires it (document the mapping).
Validate geometry of all vector layers (no null geometries, no topology errors).
Phase 2: Project Assembly
Create a new QGIS project file (.qgs — plain XML; the firm canonical format per docs/QGIS_FORMAT_RESOLUTION.md).
Add all layers from the GeoPackage to the project.
Set the project CRS to the delivery CRS.
Apply approved symbology and classification to each thematic layer:
match the classification method and color scale to the approved map designs
save styles into the GeoPackage using QGIS "Save Style to Database" if the recipient will benefit from embedded styles
Configure labeling for key features if the project requires labeled maps.
Add basemap or context layers if the package should be immediately usable:
prefer offline-capable basemaps (e.g., a boundary context layer) over online tile services that may not work for the recipient
Organize the layer panel: group layers logically, set default visibility.
Set a sensible default extent (the study area, not the full globe).
Phase 3: Documentation
Create a README file (plain text or Markdown) for inclusion in the package folder:
project description
layer inventory with field definitions
CRS and vintage information
source citations and attribution (OSM ODbL where applicable)
methodology summary or link to the full methodology note
known limitations
contact information for questions
Include the full methodology note if the project requires it.
Include any supporting documents (variable dictionaries, classification rationale, crosswalk tables).
Every review package must also include a review-notes.md file with:
validation status (PASS / PASS WITH WARNINGS / REWORK NEEDED) per
workflows/VALIDATION_AND_QA_STAGE.md
list of all warnings with plain-language explanations
data coverage notes (percentage of features with full data per field)
instructions for opening the package in QGIS
suggested review order (which layers the reviewer should inspect first)
the thematic field and symbology method used for the initial styling
Phase 4: Validation
Close and reopen the QGIS project to verify all layers load correctly from relative paths.
Verify that no layers reference absolute paths to the firm's internal file system.
Verify that all layers display with the intended symbology.
Verify that the project opens without errors or missing-layer warnings.
If the package will be shared via ZIP archive, create the archive and test opening it from a different location.
Check total file size against delivery constraints (email limits, client storage).
Phase 5: Delivery
Deliver the package via the approved channel (file share, email, cloud storage).
Include a brief cover note explaining what the package contains and how to open it.
Archive the package in the project folder.
Reviewer Guidance
This section is for the person receiving the package — a client, collaborator, or internal reviewer opening the QGIS project on their own machine. Producers can skip this section; reviewers should read it before opening the package.
Setup
Copy or extract the package folder to a local directory. Do not rename internal files or folders.
Open project.qgs in QGIS 3.22 or later.
All layers should load automatically from relative paths within the package. If any layer fails to load, check that the folder structure is intact.
Orientation
Read review-notes.md first — it documents QA status, known caveats, data coverage, and the thematic field used for the initial styling.
The layer panel is organized into groups:
Review Layers — primary analysis layer(s) and secondary cross-check layers
Reference Layers — boundaries, basemaps, and context
The primary analysis layer has thematic styling applied (graduated colors on the most reviewable field). The legend shows class breaks. This styling is a starting point; restyle as needed.
Inspection sequence
Start with the primary analysis layer. Check geometry coverage, field values, and the thematic pattern.
Open the attribute table — click features to inspect individual field values.
If secondary layers are present, cross-check them against the primary layer.
Cross-reference the spatial view with reports in the reports/ subfolder.
Note any issues with data completeness, unexpected patterns, or styling problems.
Reporting findings
Report findings back to the lead analyst or project contact listed in the README.
Include specific feature IDs (e.g., GEOID values) when reporting spatial issues.
Note whether issues are data problems, styling problems, or methodology questions — these route to different team members.
Layer and Styling Conventions
These conventions govern how layers, fields, and styles are configured in the QGIS project. They are applied automatically by the generation pipeline but are documented here for reviewers and for manual package assembly. The full technical contract for the auto-generation pipeline lives in
docs/QGIS_PROJECT_CONTRACT.md
this section is the operational summary.
Layer naming
use human-readable names ("Project Census Tracts" with the geographic scope spelled out, not "tracts_joined" or other internal codes)
include the geographic scope and data type in the name
suffix with "(Demo Subset)" for partial or demo data layers
Layer roles
Layers are tagged with one of three roles that govern grouping and styling:
primary_analysis
— main review layer; receives thematic styling; placed in the Review Layers group
secondary_review
— supporting layers for cross-checking; placed in the Review Layers group
reference
— context layers (boundaries, basemaps); placed in the Reference Layers group
Field roles and thematic styling
Fields are auto-classified by column name and type. The primary thematic field is selected in priority order: percent > count > measure. Within each role, the field with the highest non-null coverage is preferred.
percent fields (water_pct, vacancy_rate): graduated renderer, quantile method, 5 classes, YlOrRd ramp
count fields (total_pop, pop_total): graduated renderer, natural breaks method, 5 classes, YlGnBu ramp
area fields (land_area_sqm): graduated renderer, equal interval method, 5 classes, Greens ramp
measure fields (other numeric): graduated renderer, equal interval method, 5 classes, Greens ramp
id fields (GEOID, FIPS): not styled
label fields (NAME, tract_name): used for labels when feature count is below 100
Default symbology: semi-transparent fill (alpha 200), outlines in (80, 80, 80) at 0.26 mm width.
The cartographic design rules that these defaults express live in
standards/CARTOGRAPHY_STANDARD.md
the QGIS-specific defaults above are how the auto-generation pipeline implements those rules for the review-package use case. Reviewers may restyle in QGIS; the initial map is a starting point, not the final cartographic deliverable.
CRS
project CRS matches the primary data layer (typically EPSG:4269 for Census data) per
standards/CRS_SELECTION_STANDARD.md
data is not reprojected during packaging — original CRS is preserved
the CRS is recorded in review-notes.md
File formats inside the package
GeoPackage (.gpkg) for spatial data
CSV for tabular summaries
PNG for static maps and charts
Markdown and HTML for reports
.qgs (plain XML) for the QGIS project file itself, per
docs/QGIS_FORMAT_RESOLUTION.md
Validation Checks
all layers load from relative paths within the package folder
no references to firm internal file systems or databases
all layers display with intended symbology
field names are client-appropriate (no internal codes without a dictionary)
CRS is consistent across all layers and matches the delivery CRS
README and methodology note are present
attribution requirements are met
file size is manageable for the delivery channel
Common Failure Modes
layers referencing absolute paths to the analyst's local machine
including online tile basemaps that require internet access the recipient may not have
forgetting to embed styles, so the recipient sees default QGIS symbology
leaving internal field names (e.g., "tmp_join_key") in the deliverable
not testing the package from a different directory or machine
delivering a .qgz file when the pipeline and downstream consumers expect .qgs (the firm canonical format is plain XML .qgs, which is diffable and matches the live runtime)
omitting the README, leaving the recipient unable to interpret the package
raster files outside the package folder that break relative paths
Escalate When
the client requires a proprietary format (e.g., .mxd, .aprx) that QGIS cannot produce
the package exceeds reasonable file-size limits
the client has specific QGIS version requirements
the package includes raster data that is too large for GeoPackage
attribution or licensing restrictions affect what can be included
Outputs
QGIS project file (.qgs — plain XML, firm canonical format)
GeoPackage containing all vector layers (and styles if embedded)
raster files (GeoTIFF) if applicable
README with layer inventory and metadata
methodology note
optional: ZIP archive of the complete package
Related Standards
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
standards/PUBLISHING_READINESS_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/OPEN_EXECUTION_STACK_STANDARD.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
qa-review/MAP_QA_CHECKLIST.md
Sources
QGIS documentation (https://docs.qgis.org)
GeoPackage specification (https://www.geopackage.org)
firm delivery methodology notes
Trust Level
Draft Workflow Needs Testing
