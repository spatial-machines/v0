# Living Atlas Source Page

Source Summary:
Esri's Living Atlas of the World is a curated collection of geographic information hosted on ArcGIS Online.
The firm treats Living Atlas as a discovery and reference layer, not as a primary analytical source.
Living Atlas content ranges from authoritative government data (republished) to community-contributed layers of variable quality.
Per
standards/OPEN_EXECUTION_STACK_STANDARD.md
, Living Atlas is an acceptable reference surface but not a default operational dependency.
Owner / Publisher:
Esri (platform host)
individual layer publishers vary: some are government agencies, some are Esri staff, some are community contributors
Geography Support:
global coverage for many layers
U.S. coverage for ACS, demographic, and infrastructure layers
variable coverage depending on the specific layer
Time Coverage:
varies by layer
some layers are updated regularly; others are static snapshots
ACS-derived layers in Living Atlas may lag behind the latest Census Bureau release
always verify the vintage of a Living Atlas layer before using it
Access Method:
ArcGIS Online web interface (https://livingatlas.arcgis.com)
ArcGIS REST API endpoints for programmatic access
some layers can be downloaded as shapefiles, CSVs, or GeoJSON
some layers are feature services only (cannot be downloaded in bulk without API scripting)
Licensing / Usage Notes:
most layers are marked "public" but individual usage terms vary by publisher
Esri subscriber content requires an ArcGIS Online organizational account
layers derived from federal data (Census, USGS, etc.) are typically public domain at origin, but the Living Atlas packaging may carry additional terms
check the specific layer's licensing before including in a client deliverable
Known Caveats:
Living Atlas layers are not primary sources; they are republished, often processed or simplified versions of upstream data
the processing and simplification methods applied by the publisher may not be documented
data vintage may be unclear or lag behind the authoritative source
schema and field names may differ from the original source
not all layers include metadata sufficient for firm workflow use
some layers use proprietary symbology that does not export to open formats
treating a Living Atlas layer as the source of record when the firm should go to the original publisher is a common error
Firm Source Readiness Guidance
layers traced to a known authoritative publisher (e.g., Census Bureau ACS data republished by Esri) may qualify as Tier 2 (Validated but Caveated) per
standards/SOURCE_READINESS_STANDARD.md
, provided the vintage and processing are documented
layers from community contributors or unknown publishers should be assigned Tier 3 (Provisional) or Tier 4 (Unreviewed)
no Living Atlas layer should be assigned Tier 1 (Production-Ready); always prefer the original source where available
Best-Fit Workflows:
source discovery and initial screening (finding what data exists for a study area)
visual reference and comparison (basemap context, thematic reference)
quick feasibility assessment before retrieving authoritative data
client delivery environment when the client uses ArcGIS Online
Alternatives:
Census Bureau ACS and TIGER products directly (preferred for demographic and boundary data)
USGS products directly (preferred for elevation and hydrologic data)
OSM via firm PostGIS (preferred for POI and road network data)
original publisher datasets in all cases where the firm needs production-grade inputs
Sources:
https://livingatlas.arcgis.com
Esri Living Atlas documentation
ArcGIS REST API documentation
Trust Level:
Validated Source Page
Needs Source Validation (layer quality varies significantly by publisher)
