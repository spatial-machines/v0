# OpenStreetMap (OSM) Source Page

Source Summary:
OpenStreetMap is a collaborative, open-licensed geographic database covering the world.
The firm uses OSM primarily for POI data (shops, restaurants, services, amenities), road network geometry, building footprints, and land-use context.
OSM is not a single curated dataset. It is a community-maintained map with variable completeness and quality depending on geography and feature type.
Owner / Publisher:
OpenStreetMap Foundation
data contributed by volunteer mappers worldwide
Geography Support:
global coverage
completeness varies significantly by region: urban areas in the U.S. and Europe are well-mapped; rural areas, developing regions, and specialized feature categories may be sparse
no official administrative boundaries should be sourced from OSM for U.S. Census work; use TIGER for that
Time Coverage:
continuously updated
the firm's local PostGIS extract reflects the date of the import, not the live OSM state
for time-sensitive work, confirm the extract date or pull a fresh extract
Access Method:
Overpass API for targeted queries (https://overpass-turbo.eu) — preferred default
Local PostGIS database for bulk access (see data-sources/LOCAL_POSTGIS.md) — optional
Fetch Scripts:
`scripts/core/fetch_poi.py` — POI retrieval via Overpass API (default)
`scripts/core/fetch_poi_postgis.py` — POI retrieval via local PostGIS (optional)
Other methods:
Geofabrik regional extracts for bulk download (https://download.geofabrik.de)
BBBike extracts for custom bounding boxes (https://extract.bbbike.org)
osm2pgsql or imposm for loading extracts into PostGIS
Licensing / Usage Notes:
Open Database License (ODbL 1.0)
attribution required: "Data from OpenStreetMap contributors"
share-alike: derivative databases must be released under the same or compatible license
produced works (maps, reports) from OSM data do not need to be ODbL-licensed, but attribution is still required
verify compliance before including OSM-derived data in client deliverables
Known Caveats:
data quality is variable: some POI categories are well-tagged, others are sparse or inconsistently categorized
OSM tagging is freeform and community-governed; the same business type may appear under different tag combinations
POI completeness is not guaranteed: OSM may undercount businesses compared to commercial POI providers
road network quality is generally high in the U.S. but turn restrictions, speed limits, and access restrictions may be incomplete
building footprints are available in many areas but not universally
do not treat OSM as authoritative for property boundaries, parcel data, or legal boundaries
name fields may contain local-language names, abbreviations, or inconsistencies
Best-Fit Workflows:
workflows/POSTGIS_POI_LANDSCAPE.md
workflows/SERVICE_AREA_ANALYSIS.md
(road network for routing engines)
workflows/GEOCODE_BUFFER_ENRICHMENT.md
(POI enrichment layer)
Alternatives:
commercial POI providers (SafeGraph, Foursquare, etc.) for more complete business data
Google Places API for spot-checking (usage limits and licensing constraints)
TIGER / Line for road centerlines (authoritative for Census geography alignment)
county or municipal open-data portals for local business license or permit data
Sources:
https://www.openstreetmap.org
https://wiki.openstreetmap.org/wiki/Map_features (tagging reference)
https://wiki.openstreetmap.org/wiki/Overpass_API
https://download.geofabrik.de
ODbL license text (https://opendatacommons.org/licenses/odbl/1-0/)
Trust Level:
Validated Source Page
Needs Source Validation (completeness varies by feature type and geography)
