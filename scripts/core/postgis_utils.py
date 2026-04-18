"""
postgis_utils.py — PostGIS backend utilities for the GIS consulting firm.

Use PostGIS when:
  - Feature count > 500k
  - Multi-project spatial joins
  - Queries that would overflow RAM

Environment variables (set in .env or shell):
  POSTGIS_HOST   — default: localhost
  POSTGIS_PORT   — default: 5432
  POSTGIS_DB     — default: gisdb
  POSTGIS_USER   — default: gis
  POSTGIS_PASS   — default: gis

Usage:
    from scripts.postgis_utils import connect, upload_layer, download_layer
    engine = connect()
    upload_layer(gdf, "my_layer", schema="analyses")
    gdf2 = download_layer("my_layer", schema="analyses")
"""

import os
import logging
from typing import Optional

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def connect() -> Engine:
    """
    Return a SQLAlchemy engine connected to PostGIS.

    Reads connection params from environment variables:
        POSTGIS_HOST, POSTGIS_PORT, POSTGIS_DB, POSTGIS_USER, POSTGIS_PASS

    Raises:
        SQLAlchemyError: if the connection cannot be established.
    """
    host = os.environ.get("POSTGIS_HOST", "localhost")
    port = os.environ.get("POSTGIS_PORT", "5432")
    db   = os.environ.get("POSTGIS_DB",   "gisdb")
    user = os.environ.get("POSTGIS_USER", "gis")
    pw   = os.environ.get("POSTGIS_PASS", "gis")

    url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"
    engine = create_engine(url, pool_pre_ping=True)

    # Verify connectivity eagerly so callers get a clear error up front
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("PostGIS connection OK — %s@%s:%s/%s", user, host, port, db)
    return engine


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_layer(
    gdf: gpd.GeoDataFrame,
    table_name: str,
    schema: str = "analyses",
    if_exists: str = "replace",
    engine: Optional[Engine] = None,
) -> None:
    """
    Upload a GeoDataFrame to PostGIS and register it in analyses.spatial_layers.

    Args:
        gdf:        GeoDataFrame to upload. Must have a geometry column.
        table_name: Destination table name (snake_case recommended).
        schema:     PostgreSQL schema. Default: 'analyses'.
        if_exists:  'replace' (drop+recreate), 'append', or 'fail'.
        engine:     Optional existing SQLAlchemy engine. Created if None.

    Raises:
        ValueError: if gdf has no geometry column.
    """
    if gdf.geometry is None or gdf.geometry.name not in gdf.columns:
        raise ValueError("GeoDataFrame must have an active geometry column.")

    if engine is None:
        engine = connect()

    # Ensure CRS is set; reproject to WGS84 if missing
    if gdf.crs is None:
        logger.warning("GeoDataFrame has no CRS — assuming EPSG:4326")
        gdf = gdf.set_crs("EPSG:4326")

    epsg = gdf.crs.to_epsg()

    logger.info(
        "Uploading %d features → %s.%s (if_exists=%s)",
        len(gdf), schema, table_name, if_exists,
    )

    gdf.to_postgis(
        table_name,
        engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
    )

    # Register / update in the layer catalog
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    geom_type = gdf.geometry.geom_type.iloc[0].upper() if len(gdf) > 0 else "UNKNOWN"

    upsert_sql = text("""
        INSERT INTO analyses.spatial_layers
            (layer_name, schema_name, table_name, geometry_type, crs_epsg,
             feature_count, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy, updated_at)
        VALUES
            (:layer_name, :schema_name, :table_name, :geometry_type, :crs_epsg,
             :feature_count, :bbox_minx, :bbox_miny, :bbox_maxx, :bbox_maxy, NOW())
        ON CONFLICT (schema_name, table_name)
        DO UPDATE SET
            geometry_type  = EXCLUDED.geometry_type,
            crs_epsg       = EXCLUDED.crs_epsg,
            feature_count  = EXCLUDED.feature_count,
            bbox_minx      = EXCLUDED.bbox_minx,
            bbox_miny      = EXCLUDED.bbox_miny,
            bbox_maxx      = EXCLUDED.bbox_maxx,
            bbox_maxy      = EXCLUDED.bbox_maxy,
            updated_at     = NOW()
    """)

    with engine.begin() as conn:
        conn.execute(upsert_sql, {
            "layer_name":    table_name,
            "schema_name":   schema,
            "table_name":    table_name,
            "geometry_type": geom_type,
            "crs_epsg":      epsg,
            "feature_count": len(gdf),
            "bbox_minx":     float(bounds[0]),
            "bbox_miny":     float(bounds[1]),
            "bbox_maxx":     float(bounds[2]),
            "bbox_maxy":     float(bounds[3]),
        })

    logger.info("Layer '%s.%s' registered in analyses.spatial_layers", schema, table_name)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_layer(
    table_name: str,
    schema: str = "analyses",
    where: Optional[str] = None,
    engine: Optional[Engine] = None,
) -> gpd.GeoDataFrame:
    """
    Read a PostGIS table back into a GeoDataFrame.

    Args:
        table_name: Table to read.
        schema:     PostgreSQL schema. Default: 'analyses'.
        where:      Optional SQL WHERE clause (without the WHERE keyword).
                    E.g. where="state_fips = '27'"
        engine:     Optional existing SQLAlchemy engine.

    Returns:
        GeoDataFrame with the full table contents (or filtered subset).
    """
    if engine is None:
        engine = connect()

    full_name = f'"{schema}"."{table_name}"'
    sql = f"SELECT * FROM {full_name}"
    if where:
        sql += f" WHERE {where}"

    logger.info("Downloading layer: %s", sql)
    gdf = gpd.read_postgis(sql, engine, geom_col="geometry")
    logger.info("Downloaded %d features from %s.%s", len(gdf), schema, table_name)
    return gdf


# ---------------------------------------------------------------------------
# Arbitrary spatial query
# ---------------------------------------------------------------------------

def run_spatial_query(
    sql: str,
    engine: Optional[Engine] = None,
    geom_col: str = "geometry",
) -> gpd.GeoDataFrame:
    """
    Execute an arbitrary PostGIS SQL query and return a GeoDataFrame.

    The query must return a geometry column (name defaults to 'geometry').
    For non-spatial results, use pandas.read_sql() directly.

    Args:
        sql:      Full SQL statement. Must SELECT a geometry column.
        engine:   Optional existing SQLAlchemy engine.
        geom_col: Name of the geometry column in the result. Default: 'geometry'.

    Returns:
        GeoDataFrame of query results.

    Example:
        gdf = run_spatial_query(
            "SELECT a.geoid, a.geometry, b.value "
            "FROM analyses.tracts a "
            "JOIN analyses.acs_data b ON a.geoid = b.geoid"
        )
    """
    if engine is None:
        engine = connect()

    logger.info("Running spatial query: %.120s...", sql)
    gdf = gpd.read_postgis(sql, engine, geom_col=geom_col)
    logger.info("Query returned %d features", len(gdf))
    return gdf


# ---------------------------------------------------------------------------
# Layer listing
# ---------------------------------------------------------------------------

def list_layers(
    schema: str = "analyses",
    engine: Optional[Engine] = None,
) -> pd.DataFrame:
    """
    List all spatial tables registered in the given schema.

    Returns a DataFrame with columns:
        layer_name, table_name, geometry_type, crs_epsg,
        feature_count, loaded_at, updated_at, tags

    Args:
        schema:  Schema to query. Default: 'analyses'.
        engine:  Optional existing SQLAlchemy engine.
    """
    if engine is None:
        engine = connect()

    sql = text("""
        SELECT
            layer_name,
            table_name,
            geometry_type,
            crs_epsg,
            feature_count,
            source_file,
            project_id,
            loaded_at,
            updated_at,
            tags
        FROM analyses.spatial_layers
        WHERE schema_name = :schema
        ORDER BY loaded_at DESC
    """)

    with engine.connect() as conn:
        result = conn.execute(sql, {"schema": schema})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    logger.info("Found %d layers in schema '%s'", len(df), schema)
    return df


# ---------------------------------------------------------------------------
# Layer registration
# ---------------------------------------------------------------------------

def register_layer(
    engine: Engine,
    schema: str,
    table: str,
    description: str,
    registered_by: str,
    project_id: Optional[str] = None,
) -> None:
    """
    Insert or update a row in public._gis_meta for layer tracking.

    Args:
        engine:        SQLAlchemy engine.
        schema:        Table schema (scratch, analyses, reference).
        table:         Table name.
        description:   Human-readable description / provenance.
        registered_by: Agent or user who registered the layer.
        project_id:    Optional project identifier.
    """
    sql = text("""
        INSERT INTO public._gis_meta
            (table_schema, table_name, description, registered_by, project_id)
        VALUES
            (:schema, :table, :desc, :by, :pid)
        ON CONFLICT (table_schema, table_name)
        DO UPDATE SET
            description   = EXCLUDED.description,
            registered_by = EXCLUDED.registered_by,
            project_id    = COALESCE(EXCLUDED.project_id, public._gis_meta.project_id),
            registered_at = NOW()
    """)

    with engine.begin() as conn:
        conn.execute(sql, {
            "schema": schema,
            "table": table,
            "desc": description,
            "by": registered_by,
            "pid": project_id,
        })
    logger.info("Registered layer: %s.%s (by %s)", schema, table, registered_by)


# ---------------------------------------------------------------------------
# Schema management
# ---------------------------------------------------------------------------

def ensure_schemas(engine: Engine) -> None:
    """
    Create scratch, analyses, reference schemas and install PostGIS extension.

    Idempotent — safe to call on every startup.
    """
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis CASCADE"))
        for schema in ("scratch", "analyses", "reference"):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    logger.info("Schemas ensured: scratch, analyses, reference (PostGIS installed)")


# ---------------------------------------------------------------------------
# Layer metadata
# ---------------------------------------------------------------------------

def get_layer_metadata(engine: Engine, schema: str, table: str) -> dict:
    """
    Return detailed metadata for a single table.

    Returns:
        dict with keys: row_count, geom_type, srid, columns, has_spatial_index,
                        table_size, comment
    """
    meta = {
        "schema": schema,
        "table": table,
        "row_count": 0,
        "geom_type": None,
        "srid": None,
        "columns": [],
        "has_spatial_index": False,
        "table_size": "0 bytes",
        "comment": None,
    }

    with engine.connect() as conn:
        # Row count
        row = conn.execute(text(
            f'SELECT COUNT(*) FROM "{schema}"."{table}"'
        )).fetchone()
        meta["row_count"] = row[0]

        # Geometry info
        row = conn.execute(text(
            "SELECT type, srid FROM geometry_columns "
            "WHERE f_table_schema = :s AND f_table_name = :t"
        ), {"s": schema, "t": table}).fetchone()
        if row:
            meta["geom_type"] = row[0]
            meta["srid"] = row[1]

        # Columns
        rows = conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = :s AND table_name = :t ORDER BY ordinal_position"
        ), {"s": schema, "t": table}).fetchall()
        meta["columns"] = [{"name": r[0], "type": r[1]} for r in rows]

        # Spatial index check
        row = conn.execute(text(
            "SELECT 1 FROM pg_indexes "
            "WHERE schemaname = :s AND tablename = :t AND indexdef ILIKE '%%gist%%'"
        ), {"s": schema, "t": table}).fetchone()
        meta["has_spatial_index"] = row is not None

        # Table size
        row = conn.execute(text(
            "SELECT pg_size_pretty(pg_total_relation_size(:full))"
        ), {"full": f"{schema}.{table}"}).fetchone()
        meta["table_size"] = row[0]

        # Table comment
        row = conn.execute(text(
            "SELECT obj_description(c.oid) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relname = :t AND n.nspname = :s"
        ), {"s": schema, "t": table}).fetchone()
        if row:
            meta["comment"] = row[0]

    return meta


# ---------------------------------------------------------------------------
# Drop table
# ---------------------------------------------------------------------------

def drop_table(
    engine: Engine,
    schema: str,
    table: str,
    *,
    dry_run: bool = True,
) -> None:
    """
    Drop a table from PostGIS. Always dry_run=True by default.

    Args:
        engine:  SQLAlchemy engine.
        schema:  Table schema.
        table:   Table name.
        dry_run: If True, only log what would be dropped.
    """
    full_name = f'"{schema}"."{table}"'
    if dry_run:
        logger.info("DRY RUN — would drop %s", full_name)
        return

    with engine.begin() as conn:
        # Remove from _gis_meta first
        conn.execute(text(
            "DELETE FROM public._gis_meta WHERE table_schema = :s AND table_name = :t"
        ), {"s": schema, "t": table})
        conn.execute(text(f"DROP TABLE IF EXISTS {full_name}"))
    logger.info("Dropped table: %s", full_name)


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="PostGIS utilities — list layers")
    parser.add_argument("--schema", default="analyses", help="Schema to list")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    layers = list_layers(schema=args.schema)
    if args.json:
        print(layers.to_json(orient="records", indent=2, default_handler=str))
    else:
        print(layers.to_string(index=False))
