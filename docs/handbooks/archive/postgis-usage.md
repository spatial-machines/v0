# PostGIS Usage Guide

_When to use PostGIS vs geopandas, and how to run spatial queries at scale._

---

## When to Use PostGIS vs geopandas

**Use geopandas** (the default) when:
- Feature count is **< 500k** and all data fits in RAM
- Analysis is self-contained to a single project
- Quick iteration — geopandas loads faster for small-medium data
- You need numpy/scipy integration that's awkward via SQL

**Use PostGIS** when:
- Feature count exceeds **500k features** (parcel data, national tracts, point clouds)
- You need **multi-project joins** — e.g., join 5 separate project datasets without loading them all into Python
- Analysis requires a **spatial index** that geopandas can't efficiently maintain in RAM
- You're generating **vector tiles** via Martin (Martin reads directly from PostGIS)
- Queries involve **repeated access** to the same large dataset across multiple analysis runs

**Rule of thumb:** If you're doing county-level US analysis (~3,000 features), use geopandas. If you're doing national tract-level analysis (~74,000 features) with multiple joins, PostGIS. If you're working with parcel data or points in the millions, PostGIS is non-negotiable.

---

## Setup

```bash
# Start PostGIS
docker compose -f docker/docker-compose.postgis.yml up -d

# Verify it's running
docker compose -f docker/docker-compose.postgis.yml ps

# Connect with psql
docker exec -it <container> psql -U gis -d gisdb
```

Environment variables (set in `.env` or shell):
```
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGIS_DB=gisdb
POSTGIS_USER=gis
POSTGIS_PASS=gis
```

---

## Python API (postgis_utils.py)

```python
from scripts.postgis_utils import connect, upload_layer, download_layer, run_spatial_query, list_layers

# Connect
engine = connect()

# Upload a GeoDataFrame
upload_layer(gdf, "mn_tracts", schema="analyses")

# Download a layer (optionally filtered)
tracts = download_layer("mn_tracts", schema="analyses", where="state_fips = '27'")

# Run arbitrary PostGIS SQL
result = run_spatial_query("""
    SELECT a.geoid, a.geometry, b.poverty_rate
    FROM analyses.mn_tracts a
    JOIN analyses.acs_poverty b ON a.geoid = b.geoid
    WHERE b.poverty_rate > 0.20
""")

# List all registered layers
layers = list_layers(schema="analyses")
print(layers[["layer_name", "feature_count", "loaded_at"]])
```

---

## Example Queries

### 1. Spatial Join at Scale — Hospitals to Counties

Find the county for each hospital in a national dataset of 6,000+ hospitals.
This kind of cross-join is slow in geopandas at scale; PostGIS handles it with
a spatial index automatically.

```sql
-- Upload both layers first via postgis_utils.upload_layer()

SELECT
    h.name                          AS hospital_name,
    h.type                          AS hospital_type,
    c.geoid                         AS county_geoid,
    c.namelsad                      AS county_name,
    c.state_fips,
    h.geometry
FROM analyses.hospitals h
JOIN analyses.us_counties c
  ON ST_Within(h.geometry, ST_Transform(c.geometry, ST_SRID(h.geometry)))
ORDER BY c.state_fips, c.namelsad;
```

```python
# Python equivalent
result = run_spatial_query("""
    SELECT h.name, c.geoid, c.namelsad, c.state_fips, h.geometry
    FROM analyses.hospitals h
    JOIN analyses.us_counties c
      ON ST_Within(h.geometry, ST_Transform(c.geometry, ST_SRID(h.geometry)))
""")
```

---

### 2. Buffer Analysis — FQHC Service Areas

Generate 10-mile buffers around Federally Qualified Health Centers and find
tracts with NO coverage — healthcare deserts.

```sql
-- Create buffered service areas
WITH fqhc_buffers AS (
    SELECT
        fqhc_id,
        name,
        ST_Buffer(
            ST_Transform(geometry, 5070),   -- project to Albers Equal Area
            16093.4                          -- 10 miles in meters
        ) AS buffer_geom
    FROM analyses.fqhcs
),
-- Find tracts that don't intersect any buffer
uncovered_tracts AS (
    SELECT t.geoid, t.namelsad, t.state_fips, t.geometry
    FROM analyses.tracts t
    WHERE NOT EXISTS (
        SELECT 1
        FROM fqhc_buffers b
        WHERE ST_Intersects(
            ST_Transform(t.geometry, 5070),
            b.buffer_geom
        )
    )
)
SELECT
    geoid,
    namelsad,
    state_fips,
    geometry,
    TRUE AS healthcare_desert
FROM uncovered_tracts
ORDER BY state_fips;
```

```python
# Python — returns healthcare desert tracts as GeoDataFrame
deserts = run_spatial_query("""
    WITH fqhc_buffers AS (
        SELECT ST_Buffer(ST_Transform(geometry, 5070), 16093.4) AS buffer_geom
        FROM analyses.fqhcs
    )
    SELECT t.geoid, t.namelsad, t.state_fips, t.geometry
    FROM analyses.tracts t
    WHERE NOT EXISTS (
        SELECT 1 FROM fqhc_buffers b
        WHERE ST_Intersects(ST_Transform(t.geometry, 5070), b.buffer_geom)
    )
""")
```

---

### 3. Zonal Statistics via SQL — Mean Poverty Rate by HUD Region

Aggregate tract-level ACS poverty rates up to HUD regions without loading
all tracts into Python. This is the PostGIS alternative to rasterstats for
vector-on-vector zonal aggregation.

```sql
SELECT
    r.region_name,
    r.region_code,
    COUNT(t.geoid)                              AS tract_count,
    ROUND(AVG(p.poverty_rate)::numeric, 4)      AS mean_poverty_rate,
    ROUND(MIN(p.poverty_rate)::numeric, 4)      AS min_poverty_rate,
    ROUND(MAX(p.poverty_rate)::numeric, 4)      AS max_poverty_rate,
    ROUND(STDDEV(p.poverty_rate)::numeric, 4)   AS stddev_poverty_rate,
    -- Weighted by tract population
    ROUND(
        (SUM(p.poverty_rate * p.total_pop) / NULLIF(SUM(p.total_pop), 0))::numeric,
        4
    ) AS pop_weighted_poverty_rate,
    r.geometry
FROM analyses.hud_regions r
JOIN analyses.tracts t
  ON ST_Intersects(
      ST_Centroid(t.geometry),   -- use centroid for clean assignment
      r.geometry
  )
JOIN analyses.acs_poverty p ON t.geoid = p.geoid
WHERE p.total_pop > 0
GROUP BY r.region_name, r.region_code, r.geometry
ORDER BY pop_weighted_poverty_rate DESC;
```

```python
# Returns a GeoDataFrame with region polygons + aggregated statistics
regional_summary = run_spatial_query("""
    SELECT
        r.region_name,
        COUNT(t.geoid) AS tract_count,
        ROUND(AVG(p.poverty_rate)::numeric, 4) AS mean_poverty_rate,
        ROUND(
            (SUM(p.poverty_rate * p.total_pop) / NULLIF(SUM(p.total_pop), 0))::numeric, 4
        ) AS pop_weighted_poverty_rate,
        r.geometry
    FROM analyses.hud_regions r
    JOIN analyses.tracts t ON ST_Intersects(ST_Centroid(t.geometry), r.geometry)
    JOIN analyses.acs_poverty p ON t.geoid = p.geoid
    WHERE p.total_pop > 0
    GROUP BY r.region_name, r.geometry
    ORDER BY pop_weighted_poverty_rate DESC
""")
```

---

## Performance Tips

- **Always reproject before spatial operations.** Use `ST_Transform(geom, 5070)` (Albers Equal Area) for US analysis. Operations on geographic (lat/lon) coordinates are much slower.
- **Spatial indexes are automatic** for columns created by geopandas `to_postgis()`. For manually created tables, run `CREATE INDEX ON analyses.my_table USING GIST (geometry);`
- **Use ST_Centroid for assignments** (point-in-polygon is faster than polygon-polygon intersection).
- **EXPLAIN ANALYZE** before running large queries: `EXPLAIN ANALYZE SELECT ...`
- **Vacuum after bulk loads:** `VACUUM ANALYZE analyses.my_table;`

---

## Integration with the Agent Pipeline

The `data-processing` agent should call `upload_layer()` when a layer exceeds the 500k-feature threshold. The `spatial-stats` agent should use `run_spatial_query()` for large spatial joins. The `cartography` agent should use `download_layer()` to pull processed results for rendering.
