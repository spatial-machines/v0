# PostGIS Toolkit

Toolkit Summary:
PostGIS is the spatial extension for PostgreSQL, providing spatial data types, spatial indexing, and hundreds of spatial functions.
The firm uses PostGIS as the primary spatial database for persistent storage, complex spatial queries, and large-dataset operations that exceed in-memory capacity.
PostGIS is the operational backbone for POI retrieval, large-scale spatial joins, and any workflow that benefits from SQL-based spatial logic.
Best Uses
storing and querying large spatial datasets with spatial indexes (GiST)
complex spatial queries: intersects, within, distance, nearest-neighbor on millions of features
POI retrieval and filtering against the firm's local OSM extract
spatial joins and aggregation at scale (tract-to-ZIP, enrichment of large feature sets)
concurrent multi-user or multi-agent access to shared reference layers
persistent storage of intermediate and final outputs across project lifecycle
CRS transformation via
ST_Transform()
geometry validation and repair (
ST_IsValid
,
ST_MakeValid
)
Avoid For
ad-hoc one-off analysis on small datasets (GeoPandas is faster to set up)
raster processing (use GDAL/Rasterio; PostGIS raster support exists but is not the firm's preferred path)
workflows where the analyst needs pandas-style tabular manipulation interleaved with spatial operations
quick visualization (use GeoPandas
.plot()
or QGIS instead)
situations where the database is not running or accessible
Core Operations
Spatial Predicates
ST_Intersects(a, b)
— do geometries share any space?
ST_Within(a, b)
— is a entirely inside b?
ST_Contains(a, b)
— does a entirely contain b?
ST_DWithin(a, b, distance)
— are a and b within the specified distance? (projected CRS or geography type)
Spatial Analysis
ST_Buffer(geom, distance)
— buffer a geometry
ST_Intersection(a, b)
— compute the geometric intersection
ST_Union(geom)
— aggregate dissolve
ST_Area(geom)
— compute area (use projected CRS or geography type)
ST_Distance(a, b)
— compute distance between geometries
ST_Centroid(geom)
— compute centroid
CRS and Geometry Management
ST_SRID(geom)
— get the SRID of a geometry column
ST_Transform(geom, srid)
— reproject geometry
ST_SetSRID(geom, srid)
— assign SRID without reprojecting
ST_IsValid(geom)
— check geometry validity
ST_MakeValid(geom)
— attempt to repair invalid geometry
I/O Integration
gpd.read_postgis(sql, conn)
— read query results into GeoPandas
gdf.to_postgis(name, conn)
— write a GeoDataFrame to PostGIS
QGIS native PostGIS connection for visualization
ogr2ogr for bulk import/export between file formats and PostGIS
Firm canonical wrapper:
scripts/postgis_utils.py
provides the firm's standard PostGIS interface. Public functions:
connect()
— return a SQLAlchemy engine using firm-configured environment variables
upload_layer(gdf, name, schema)
— upload a GeoDataFrame as a PostGIS table
download_layer(name, schema, where)
— download a layer (optionally filtered) into a GeoDataFrame
run_spatial_query(sql)
— execute arbitrary PostGIS SQL and return results as a GeoDataFrame
list_layers(schema)
— list registered layers with their feature counts and load timestamps
The wiki toolkit page describes what these functions do. The implementation lives in
scripts/postgis_utils.py
and the runnable code examples live in the firm handbook (the wiki canon does not embed code per the same precedent set by the cartography and spatial stats migrations).
Workflow Fit
The firm's concrete decision rule: use GeoPandas when feature count is below ~500,000 and the dataset fits in RAM. Use PostGIS when feature count exceeds ~500,000, when the workflow needs cross-project joins, when spatial indexes must persist between runs, or when the same large dataset is queried repeatedly across multiple analyses. The 500k threshold is approximate; let memory pressure and query frequency drive the decision when the count is borderline.
PostGIS is the preferred engine when:
the dataset has more than ~500,000 features (county-level parcels, national tract-level data, point clouds)
the workflow involves repeated or parameterized spatial queries (e.g., POI extraction for different study areas)
multiple team members or agents need to access the same data concurrently
the workflow benefits from spatial indexing for performance
complex spatial SQL is more readable than chained Python operations
multiple project datasets need to be joined without loading them all into Python at once
Switch to GeoPandas when:
the dataset has fewer than ~500,000 features and fits in RAM
the workflow is a linear pipeline with no need for persistent storage
the analyst needs interleaved pandas and spatial operations
quick iteration is more important than query optimization
Validation Expectations
When using PostGIS in a firm workflow:
always check
ST_SRID()
on all geometry columns before joining across tables
use
ST_Transform()
to align CRS before spatial predicates if SRIDs differ
run
ST_IsValid()
on unfamiliar imported layers
use
EXPLAIN ANALYZE
on slow queries to verify spatial index usage
confirm that spatial indexes exist on geometry columns used in predicates (
CREATE INDEX ... USING GIST
)
document the database, schema, and table name in the methodology note so the query is reproducible
record the PostGIS and PostgreSQL versions for legal-grade work
Performance conventions
Reproject before spatial operations on US data. Use
ST_Transform(geom, 5070)
(NAD83 / Conus Albers Equal Area) before any distance, area, or buffer operation on national or multi-state coverage. Operations on geographic (lat/lon) coordinates are dramatically slower and produce incorrect distance/area units. The general CRS rule lives in
standards/CRS_SELECTION_STANDARD.md
this is the PostGIS-specific operational implication.
Use ST_Centroid for spatial assignment when polygon-on-polygon containment is expensive. Point-in-polygon (
ST_Intersects(ST_Centroid(t.geometry), r.geometry)
) is materially faster than full polygon-polygon intersection for assignment-style queries that don't need true overlap geometry.
Run VACUUM ANALYZE after bulk loads. After uploading a large layer via
upload_layer()
or any equivalent bulk insert, run
VACUUM ANALYZE schema.table_name
so the planner has fresh statistics. Without this, subsequent queries on the new table can pick suboptimal execution plans.
Related Workflows
workflows/POSTGIS_POI_LANDSCAPE.md
— primary PostGIS workflow
workflows/TRACT_JOIN_AND_ENRICHMENT.md
— large-scale spatial joins
workflows/SERVICE_AREA_ANALYSIS.md
— pgRouting integration
workflows/WITHIN_DISTANCE_ENRICHMENT.md
— ST_DWithin and ST_Buffer
data-sources/LOCAL_POSTGIS.md
— the firm's PostGIS database
Sources
PostGIS documentation (https://postgis.net/documentation/)
PostgreSQL documentation (https://www.postgresql.org/docs/)
pgRouting documentation (https://pgrouting.org)
Trust Level
Validated Toolkit Page
