# PostGIS POI Landscape Workflow

Purpose:
retrieve, structure, analyze, and communicate a point-of-interest landscape using the firm's local PostGIS / OSM stack
Typical Use Cases
business landscape analysis
competitor mapping
amenity inventory
corridor or district POI context
market or site context analysis
Inputs
project brief
study area geometry or bounding logic
approved POI category list
approved output format
Preconditions
the project has confirmed the study area
the project has an explicit POI category list or tag logic
the local PostGIS source has been validated as live
Preferred Tools
local PostGIS
SQL query workflows
GeoPandas for extraction and shaping
firm POI retrieval and validation scripts
Execution Order
Define the study area clearly.
Define the POI category or tag logic explicitly.
Query the local PostGIS source for matching features.
Validate geometry type, category consistency, and duplicates.
Normalize category labels if needed.
Join POIs to the relevant geography if the project requires areal summaries.
Produce:
raw POI layer
cleaned POI layer
category counts
areal summaries if needed
Generate reviewable tables and maps.
Package the outputs for QGIS or publication if required.
Validation Checks
the query logic matches the approved category scope
the study area is correct
duplicates are handled explicitly
category names are normalized
the output count is plausible
Common Failure Modes
unclear tag logic
mixing categories that should be separate
counting duplicate or overlapping POIs
failing to distinguish source raw data from cleaned analysis outputs
creating maps before validating the extracted set
Escalate When
category logic is ambiguous
the study area is still changing
the extracted results look implausibly sparse or dense
a client needs a more formal taxonomy than OSM tags alone support
Outputs
cleaned POI feature layer
category summary table
optional areal enrichment outputs
reviewable maps
QGIS-ready package if required
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
workflows/POI_CATEGORY_NORMALIZATION.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
qa-review/POI_EXTRACTION_QA.md
data-sources/OSM.md
data-sources/LOCAL_POSTGIS.md
Sources
local PostGIS / OSM stack
PostGIS documentation
OSM tagging references
Trust Level
Validated Workflow Needs Testing
