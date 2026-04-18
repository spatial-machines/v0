# Service Area Analysis Workflow

Purpose:
generate drive-time or travel-distance polygons around one or more locations
enrich service areas with demographic, POI, or other spatial context
support accessibility, coverage, and market-reach questions
Typical Use Cases
how many people live within a 10-minute drive of a facility?
which competitor locations fall within a 15-minute drive-time polygon?
coverage gap analysis: areas not served within a threshold travel time
site comparison: demographic profile of competing service areas
accessibility equity analysis
Inputs
geocoded facility or site points (validated per
workflows/GEOCODE_BUFFER_ENRICHMENT.md
Phase 1)
approved travel-time or distance thresholds (e.g., 5, 10, 15 minutes)
travel mode (driving, walking, cycling)
network dataset or routing engine
approved enrichment layers
project-approved working CRS
Preconditions
site points are geocoded and validated
the CRS has been confirmed per
standards/CRS_SELECTION_STANDARD.md
the routing engine or network dataset is available and documented
travel-time thresholds and mode are explicitly approved
the team understands whether the output is Euclidean buffers (simpler, covered by
workflows/GEOCODE_BUFFER_ENRICHMENT.md
) or true network-based service areas (this workflow)
Preferred Tools
Open-stack options (preferred):
OSRM (Open Source Routing Machine) for drive-time isochrones
Valhalla for multi-modal isochrones
pgRouting with PostGIS for database-native routing
openrouteservice API for hosted isochrone generation
Acceptable secondary options:
QGIS ORS Tools plugin
network analysis via NetworkX with OSM graph data (OSMnx)
Proprietary reference:
Esri Network Analyst / Business Analyst service areas may be used for client delivery validation but are not the default execution path
Execution Order
Phase 1: Network Preparation
Confirm the routing engine and its data vintage (e.g., OSRM built from a specific OSM extract date).
Confirm the travel mode and speed assumptions.
Document any limitations of the network data (e.g., missing local roads, no turn restrictions, no real-time traffic).
Phase 2: Isochrone Generation
Load the validated site points.
Reproject to the working CRS if the routing engine requires projected coordinates, or confirm the engine accepts geographic coordinates.
Generate isochrones (service area polygons) for each site at each approved threshold.
Record parameters used: travel mode, time thresholds, departure time assumptions, generalization tolerance.
Phase 3: Validation
Visually inspect isochrone shapes against the road network.
service areas should follow road corridors, not form perfect circles
if shapes look circular, the network may not be loading correctly
Spot-check travel times with a manual route query for at least 2-3 boundary points.
Compare isochrone extents across sites to confirm plausibility (similar settings should produce similar-scale areas in similar road environments).
Phase 4: Enrichment
Load approved enrichment layers (tracts, POIs, etc.).
Confirm CRS alignment between isochrones and enrichment layers.
Perform spatial intersection.
For tract enrichment:
use area-weighted or population-weighted allocation for partial overlaps
document the method
For POI enrichment:
count points within each isochrone
categorize by approved list
Compile enrichment summaries per threshold per site.
Phase 5: Output
Package service area polygons, enrichment summaries, and methodology notes.
If the client requires comparison across sites, produce a standardized comparison table.
Generate map-ready layers.
Validation Checks
isochrone shapes follow road network corridors, not circular buffers
travel-time thresholds match the approved specification
routing engine and data vintage are documented
enrichment allocation method for partial tracts is documented
all input sites produce an isochrone (or failures are documented)
no isochrones were generated using Euclidean distance when network distance was specified
Common Failure Modes
using Euclidean buffers when the project specifies drive-time analysis
not documenting the routing engine or its data vintage
assuming the routing engine includes real-time traffic when it does not
generating isochrones in a geographic CRS and getting distorted shapes
treating the isochrone boundary as precise (it is an approximation)
partial-tract enrichment without allocation, inflating demographic counts
confusing drive-time (minutes) with drive-distance (miles)
Escalate When
the client requires real-time or time-of-day traffic modeling
the routing engine's road network is visibly incomplete for the study area
isochrone results differ materially from a proprietary benchmark
the project involves walking or transit accessibility (network data quality varies significantly)
service areas cross international borders
the analysis will be used for regulatory or legal compliance
Outputs
service area (isochrone) polygons per site per threshold
enrichment summary table
comparison table across sites if applicable
routing engine and parameter documentation
methodology note
map-ready layers
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
Sources
OSRM documentation (https://project-osrm.org)
Valhalla documentation (https://valhalla.github.io/valhalla/)
openrouteservice documentation (https://openrouteservice.org)
pgRouting documentation (https://pgrouting.org)
OSMnx documentation (https://osmnx.readthedocs.io)
Trust Level
Draft Workflow Needs Testing
