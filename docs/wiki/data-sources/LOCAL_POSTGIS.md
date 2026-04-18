# Local PostGIS Source Page

Source Summary:
The firm maintains a local PostgreSQL / PostGIS database that serves as the primary spatial data warehouse for reusable reference layers.
The database holds OSM extracts, firm-curated boundary layers, POI datasets, and other reference geometry used across projects.
This is not a single upstream data source. It is a managed local store that ingests and organizes data from multiple upstream providers.
Owner / Publisher:
firm-managed
upstream data providers include OpenStreetMap, Census Bureau, and other public or licensed sources depending on what has been loaded
Geography Support:
depends on what has been loaded
typical contents: CONUS coverage for OSM POI and road network, Census tract and ZCTA geometry for project-relevant states, project-specific boundary layers
confirm current coverage before relying on it for a new project
Time Coverage:
depends on the load date of each dataset
OSM extracts reflect the date they were imported; they are not auto-updated
Census geometry reflects the vintage loaded
check the database metadata or the DBA for current state
Access Method:
direct SQL queries via psql, DBeaver, or programmatic clients (psycopg2, SQLAlchemy)
PostGIS spatial functions (ST_Intersects, ST_Within, ST_Buffer, ST_Transform, etc.)
GeoPandas read_postgis() for Python workflows
QGIS native PostGIS connection for visualization and ad-hoc queries
Licensing / Usage Notes:
OSM-derived data carries ODbL license; attribution and share-alike required
Census-derived data is public domain
client-supplied data loaded into PostGIS retains the client's original usage terms; do not mix client data into shared reference tables
Known Caveats:
the database is only as current as its last load; do not assume OSM data reflects today's map
schema and table naming may vary; check the current catalog before querying
large spatial queries without a bounding box or spatial index filter can be slow
geometry validity is not guaranteed on all imported layers; run ST_IsValid checks on unfamiliar tables
coordinate reference system may vary by table; always check ST_SRID before joining across tables
the database is a local resource; it is not replicated or backed up to cloud by default
Best-Fit Workflows:
workflows/POSTGIS_POI_LANDSCAPE.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/GEOCODE_BUFFER_ENRICHMENT.md
workflows/SERVICE_AREA_ANALYSIS.md
Alternatives:
direct OSM download via Overpass API or Geofabrik extracts (if the local database is stale or missing coverage)
direct Census download for boundary geometry
cloud-hosted PostGIS or managed spatial databases for remote team access
Sources:
PostGIS documentation (https://postgis.net/documentation/)
PostgreSQL documentation (https://www.postgresql.org/docs/)
OpenStreetMap data documentation (https://wiki.openstreetmap.org)
firm database catalog and internal documentation
Trust Level:
Validated Source Page
Needs Source Validation (coverage and freshness vary by table)
