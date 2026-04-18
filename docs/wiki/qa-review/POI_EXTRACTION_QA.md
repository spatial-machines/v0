# POI Extraction QA Checklist

Purpose:
provide a dedicated review checklist for point-of-interest extractions from PostGIS, OSM, or other POI sources
catch the specific errors that arise from tag ambiguity, duplicate features, and coverage gaps
validate POI outputs before they are used in landscape analysis, enrichment, or client delivery
Use When
Use this checklist when reviewing any POI extraction output, including:
business landscape analysis
competitor or amenity inventories
POI counts within buffers, service areas, or other geographies
category summary tables derived from POI data
any POI layer destined for a map or client deliverable
Do Not Use When
Do not use this checklist for:
Census demographic data or boundary layers (use
qa-review/STRUCTURAL_QA_CHECKLIST.md
)
non-POI vector features such as roads, parcels, or administrative boundaries
Core POI Review Checks
Query and Category Logic
the SQL query, Overpass query, or extraction filter matches the approved category specification
the approved POI category list is documented and the extraction was limited to those categories
tag logic is explicit: which OSM tags, PostGIS columns, or source fields define each category
ambiguous categories have been resolved (e.g., "restaurant" vs. "fast food" vs. "cafe" distinction is clear)
the extraction did not silently include or exclude categories beyond the approved scope
Study Area Alignment
the extraction covers the correct study area and does not extend beyond or fall short
the bounding box or clip geometry matches the project-approved geography
if the study area has an irregular shape, the extraction was clipped to it (not just a rectangular bounding box)
Duplicate Handling
the output has been checked for duplicate features at the same location
the deduplication logic is documented (e.g., same name + same coordinates within 50 meters)
POIs that legitimately share a location (e.g., businesses in the same building) are handled appropriately
if the source contains both point and polygon representations of the same feature, only one is counted
Geometry Validation
all POI features have valid point geometry
features with null or empty geometry have been removed or flagged
the CRS is documented and consistent
coordinate values are plausible for the study area (no obvious geocoding errors placing a POI in the wrong state or country)
Completeness Assessment
the total POI count is plausible for the study area and category
counts are compared against a rough expectation (local knowledge, commercial POI count benchmarks, or a quick web search)
if the count seems implausibly low, possible causes are investigated:
OSM coverage gaps for the area or category
overly restrictive tag logic
stale PostGIS extract
if the count seems implausibly high, possible causes are investigated:
overly broad tag logic
duplicate features
including categories that should be excluded
Category Normalization
raw source categories (OSM tags, PostGIS labels) have been mapped to the firm's approved category labels
the mapping is documented in a lookup table or code comment
unmapped categories have been handled explicitly (assigned to a catchall, excluded, or escalated)
the normalized category labels are consistent with prior firm projects using the same source
Source Freshness
the vintage or extract date of the POI source is documented
if the local PostGIS extract is more than 6 months old for the relevant area, the staleness risk is noted
if a fresh Overpass or Geofabrik extract was pulled, the pull date is recorded
Escalate When
the POI count is more than 50% above or below expectations for the study area
the client requires a formal taxonomy that OSM tags alone cannot reliably support
multiple POI sources give materially different counts for the same category and area
the extraction reveals a significant coverage gap in the firm's PostGIS database for the study area
a category definition is ambiguous and the resolution could materially change the analysis
Common Failure Modes
using a tag like
amenity=restaurant
without including
cuisine=*
sub-tags when the project requires cuisine breakdowns
counting polygon features and point features separately, inflating the total
extracting from a stale PostGIS table and presenting results as current
not documenting the tag-to-category mapping, making the extraction non-reproducible
missing a major chain or brand because it uses non-standard OSM tagging
including POIs outside the study area because the clip was a bounding box, not the actual polygon
presenting raw OSM tag labels in client-facing outputs instead of normalized category names
Relationship to Other QA Pages
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first for general data integrity
workflows/POSTGIS_POI_LANDSCAPE.md
— the workflow this review validates
data-sources/OSM.md
— source caveats for OSM-derived POI data
data-sources/LOCAL_POSTGIS.md
— source caveats for the firm PostGIS database
standards/SOURCE_READINESS_STANDARD.md
— governs source tier assignment
Trust Level
Validated QA Page Needs Testing
