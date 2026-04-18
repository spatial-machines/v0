# Geocode, Buffer, and Enrichment Workflow

Purpose:
convert addresses or place names to point geometries, buffer them, and enrich the buffers with demographic, POI, or other spatial context
produce a within-distance profile around one or more candidate locations
Typical Use Cases
site analysis: what is within 1, 3, or 5 miles of a candidate location?
trade-area demographic profiling
competitor proximity analysis
amenity or service access screening
client-supplied address lists that need spatial context
Inputs
address list or point coordinates
approved buffer distances (with units)
approved enrichment layers (tracts, POIs, parcels, etc.)
project-approved working CRS
Preconditions
the working CRS has been confirmed per
standards/CRS_SELECTION_STANDARD.md
enrichment layers are available and their source readiness tier is assigned per
standards/SOURCE_READINESS_STANDARD.md
buffer distances and units are explicitly approved (miles, meters, drive-time minutes are not interchangeable)
Preferred Tools
GeoPandas with Shapely for buffering and spatial joins
geocoding: Census Geocoder, Nominatim, or firm-approved geocoding service
PostGIS ST_Buffer and ST_Intersects for database workflows
PyProj for CRS handling
Execution Order
Phase 1: Geocoding
Confirm the input address format (street, city, state, ZIP).
Submit addresses to the approved geocoding service.
Record the match quality for each result:
exact match
interpolated / approximate match
ZIP-centroid fallback
no match
Flag addresses with match quality below exact for human review.
Load geocoded points as a GeoDataFrame or PostGIS point layer.
Assign or verify the CRS (geocoders typically return WGS 84 / EPSG:4326).
Phase 2: Buffering
Reproject points to the approved projected CRS before buffering.
Generate buffers at each approved distance.
Verify buffer units match the project specification (do not buffer in degrees).
If multiple buffer rings are needed (1 mi, 3 mi, 5 mi), produce concentric rings or nested polygons as specified.
Phase 3: Enrichment
Load the approved enrichment layers (e.g., enriched tract layer, POI layer).
Confirm the enrichment layers are in the same CRS as the buffers.
Perform spatial intersection or point-in-polygon between buffers and enrichment layers.
For tract enrichment:
use area-weighted interpolation or population-weighted allocation for tracts that partially overlap the buffer
document the allocation method
do not count a full tract if only a sliver intersects
For POI enrichment:
count points within each buffer ring
categorize by approved category list
Compile enrichment summaries per buffer ring per site.
Phase 4: Validation and Output
Validate that all sites have geocoded results (or documented failures).
Validate that buffer geometry is plausible (no zero-area buffers, no degree-unit artifacts).
Validate that enrichment counts are reasonable.
Package outputs: enrichment summary table, buffer geometry, map-ready layers.
Validation Checks
geocode match rate is documented
no buffers were computed in a geographic CRS
buffer distances match the approved specification
partial-tract handling is documented (area-weighted, clipped, or full-tract)
enrichment totals are plausible relative to the geography
all sites are accounted for in the output (including geocode failures)
Common Failure Modes
buffering in EPSG:4326 and getting degree-radius ellipses instead of distance-based circles
treating ZIP-centroid geocodes as precise site locations
counting full tracts for a 1-mile buffer that only clips a tract corner
mixing buffer distance units (miles in the spec, meters in the code)
silently dropping sites that failed geocoding
not documenting the geocoding service or match quality
Escalate When
geocode match rate falls below 80%
multiple sites resolve to ZIP centroids only
the client requests drive-time buffers (this is a different workflow:
workflows/SERVICE_AREA_ANALYSIS.md
)
partial-tract allocation materially changes the demographic profile
the address list contains non-U.S. or ambiguous addresses
Outputs
geocoded point layer with match-quality field
buffer polygons at each approved distance
enrichment summary table (demographics, POI counts, etc.)
methodology note documenting geocoder, CRS, buffer method, and allocation approach
map-ready layers if required
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md
— general processing conventions this workflow specializes for geocoded points and buffer-based spatial joins
Sources
Census Geocoder API documentation (https://geocoding.geo.census.gov/geocoder/)
Nominatim documentation (https://nominatim.org/release-docs/latest/)
GeoPandas spatial join documentation
Shapely buffer documentation
Trust Level
Draft Workflow Needs Testing
