# Within-Distance Enrichment Workflow

Purpose:
select and summarize features within a specified distance of existing target geometry
produce enrichment profiles (demographic counts, POI counts, infrastructure inventories) around points, lines, or polygons that are already geocoded or defined
provide the reusable spatial-selection-by-distance pattern that other workflows invoke as a sub-step
Typical Use Cases
what is the population within 1 mile of an existing facility point?
how many competitors or amenities are within 3 miles of each site in a set?
what is the demographic profile of the area within a half-mile of a proposed transit corridor?
enriching a point or polygon layer with surrounding context for comparison or ranking
Relationship to Other Workflows
This workflow assumes the target geometry already exists and is validated.
If the target geometry starts as addresses and needs geocoding, start with
workflows/GEOCODE_BUFFER_ENRICHMENT.md
, which includes geocoding (Phase 1) and buffering (Phase 2) before calling the enrichment logic documented here.
If the distance metric is travel time over a road network rather than Euclidean distance, use
workflows/SERVICE_AREA_ANALYSIS.md
instead.
This workflow is the reusable enrichment step that both of those workflows invoke once geometry and distance zones are ready.
Inputs
validated target geometry (points, lines, or polygons)
approved distance thresholds with units (e.g., 1 mi, 3 mi, 5 mi; or 400 m, 800 m)
approved enrichment layers:
demographic: enriched tract or block-group layer (from
workflows/TRACT_JOIN_AND_ENRICHMENT.md
)
POI: cleaned POI layer (from
workflows/POSTGIS_POI_LANDSCAPE.md
)
other: parcels, infrastructure, environmental layers as project requires
project-approved working CRS
metric classification per
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
Preconditions
the working CRS has been confirmed per
standards/CRS_SELECTION_STANDARD.md
the target geometry is in the working CRS (not in a geographic CRS unless verified)
enrichment layers are available, in the working CRS, and their source readiness tier is assigned
distance thresholds and units are explicitly approved by the project lead
Preferred Tools
GeoPandas with Shapely for buffering and spatial joins
PostGIS ST_DWithin, ST_Buffer, ST_Intersection for database workflows
pandas for tabular summarization after spatial selection
Execution Order
Phase 1: Buffer Generation
Confirm the target geometry CRS is projected (not geographic).
Generate buffer polygons at each approved distance threshold.
If multiple thresholds are needed, produce either:
concentric rings (donut polygons for each band: 0-1 mi, 1-3 mi, 3-5 mi)
nested polygons (cumulative: 0-1 mi, 0-3 mi, 0-5 mi)
as specified by the project.
Validate buffer geometry: no zero-area buffers, no degree-unit artifacts, no self-intersections.
Phase 2: Feature Selection
For each enrichment layer, select features that intersect or fall within each buffer zone.
For point enrichment layers (POIs, facilities):
select points within each buffer zone
assign each point to the correct band if using concentric rings
For polygon enrichment layers (tracts, parcels):
identify polygons that intersect the buffer
classify each intersecting polygon as:
fully contained: the polygon is entirely within the buffer
partially overlapping: the polygon is clipped by the buffer boundary
Document the selection method used.
Phase 3: Aggregation
For point features:
count by category per buffer zone
produce summary tables
For polygon features with additive counts:
for fully contained polygons, use the full value
for partially overlapping polygons, apply the approved allocation method:
area-weighted: apportion the count by the share of the polygon's area within the buffer
population-weighted: use a sub-geography allocation (e.g., block-level weights) if available
full-polygon inclusion: count the full polygon value if the project approves this simplification (document the decision)
sum the allocated counts per buffer zone
For rates and shares:
aggregate the numerator and denominator separately using the methods above
recompute the rate at the buffer-zone level per
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
For medians and non-additive metrics:
do not sum or average
use a documented approximation or exclude from the buffer-zone summary
label any approximation clearly
Phase 4: Validation and Output
Validate that enrichment totals are plausible:
population within a 1-mile buffer of a suburban site should not exceed the county total
POI counts should be reasonable relative to the area
Spot-check at least 2-3 buffer zones by visual inspection on a map.
Compile the enrichment summary table: one row per target feature per buffer threshold.
Document the allocation method, distance units, and CRS in the methodology note.
Validation Checks
buffers were computed in a projected CRS (not degrees)
distance units match the project specification
partial-polygon allocation method is documented
rates were recomputed from aggregated components, not averaged
medians were handled per the aggregation standard
enrichment totals are plausible
every target feature has a result row (or a documented reason for absence)
Common Failure Modes
buffering in EPSG:4326 and getting degree-radius ellipses
counting a full tract's population for a 1-mile buffer that only clips a small corner
averaging tract-level rates instead of recomputing from numerators and denominators
mixing concentric rings and nested polygons without clarity
not documenting whether partial-polygon allocation is area-weighted, full-inclusion, or another method
double-counting POIs that fall in overlapping buffer zones when concentric rings are used
Escalate When
partial-polygon allocation materially changes the demographic profile of the buffer zone
the project requires population-weighted allocation but no sub-geography weights are available
enrichment results differ significantly between allocation methods
the buffer distance is very large relative to the enrichment geography (e.g., 10-mile buffer around tract-level data, where most tracts are partially clipped)
the project requires a non-Euclidean distance metric (travel time, walking distance)
Outputs
buffer polygons per target feature per threshold
enrichment summary table (demographic counts, rates, POI counts per buffer zone)
methodology note documenting distance units, CRS, allocation method, and metric handling
map-ready layers if required
Related Standards
standards/CRS_SELECTION_STANDARD.md
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
standards/OPEN_EXECUTION_STACK_STANDARD.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
Sources
GeoPandas spatial join and overlay documentation
PostGIS ST_DWithin and ST_Intersection documentation
Shapely buffer documentation
firm enrichment workflow notes
Trust Level
Draft Workflow Needs Testing
