#!/usr/bin/env python3
"""
db_manager.py — PostGIS database management CLI for the GIS consulting firm.

Wraps postgis_utils.py with higher-level management operations:
  discover, prune, health, promote, describe, init-schemas, ensure-reference

Usage:
    python scripts/db_manager.py discover [--schema SCHEMA] [--search KEYWORD]
    python scripts/db_manager.py prune [--dry-run] [--older-than-days N]
    python scripts/db_manager.py health
    python scripts/db_manager.py promote --table SCRATCH_TABLE --to ANALYSES_TABLE [--description TEXT]
    python scripts/db_manager.py describe --table TABLE [--schema SCHEMA]
    python scripts/db_manager.py init-schemas
    python scripts/db_manager.py ensure-reference [--layer LAYER]
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import text

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
import postgis_utils

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = PROJECT_ROOT / "outputs" / "qa" / "db_inventory.json"
HEALTH_PATH = PROJECT_ROOT / "outputs" / "qa" / "db_health.json"
PRUNE_LOG_PATH = PROJECT_ROOT / "docs" / "memory" / "db_prune_log.jsonl"

REFERENCE_LAYERS = ["us_states", "us_counties", "us_tracts_2020"]


# ---------------------------------------------------------------------------
# _gis_meta bootstrap
# ---------------------------------------------------------------------------

_GIS_META_DDL = text("""
CREATE TABLE IF NOT EXISTS public._gis_meta (
    id              SERIAL PRIMARY KEY,
    table_schema    TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    description     TEXT,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    registered_by   TEXT,
    project_id      TEXT,
    promoted_from   TEXT,
    UNIQUE (table_schema, table_name)
)
""")


def _ensure_meta_table(engine):
    """Create public._gis_meta if it doesn't exist."""
    with engine.begin() as conn:
        conn.execute(_GIS_META_DDL)


# ---------------------------------------------------------------------------
# Subcommand: init-schemas
# ---------------------------------------------------------------------------

def cmd_init_schemas(args) -> int:
    """Ensure scratch, analyses, reference schemas and PostGIS extension exist."""
    engine = postgis_utils.connect()
    postgis_utils.ensure_schemas(engine)
    _ensure_meta_table(engine)
    print("Schemas ready: scratch, analyses, reference")
    print("PostGIS extension: installed")
    print("Meta table: public._gis_meta ready")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: discover
# ---------------------------------------------------------------------------

def cmd_discover(args) -> int:
    """List all layers in PostGIS with metadata."""
    engine = postgis_utils.connect()
    _ensure_meta_table(engine)

    sql = """
    SELECT
        t.schemaname                          AS schema,
        t.relname                             AS table_name,
        t.n_live_tup                          AS row_count,
        g.type                                AS geom_type,
        g.srid                                AS crs,
        COALESCE(d.description, m.description, '') AS description,
        GREATEST(t.last_analyze, t.last_autoanalyze,
                 t.last_vacuum, t.last_autovacuum) AS last_modified,
        m.registered_at,
        m.project_id
    FROM pg_stat_user_tables t
    LEFT JOIN geometry_columns g
        ON g.f_table_schema = t.schemaname
        AND g.f_table_name = t.relname
    LEFT JOIN pg_description d
        ON d.objoid = (
            SELECT c.oid FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = t.relname AND n.nspname = t.schemaname
        )
        AND d.objsubid = 0
    LEFT JOIN public._gis_meta m
        ON m.table_schema = t.schemaname
        AND m.table_name = t.relname
    WHERE t.schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    """

    params = {}

    if args.schema:
        sql += " AND t.schemaname = :schema"
        params["schema"] = args.schema

    if args.search:
        sql += " AND (t.relname ILIKE :kw OR COALESCE(d.description, m.description, '') ILIKE :kw)"
        params["kw"] = f"%{args.search}%"

    sql += " ORDER BY t.schemaname, t.relname"

    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())

    if not rows:
        print("No layers found.")
        return 0

    # Print table
    print(f"\n{'Schema':<12} {'Table':<35} {'Rows':>10} {'Geom Type':<18} {'CRS':>6} {'Description':<40}")
    print("-" * 125)
    for row in rows:
        r = dict(zip(columns, row))
        print(
            f"{r['schema']:<12} {r['table_name']:<35} {r['row_count'] or 0:>10} "
            f"{r['geom_type'] or 'N/A':<18} {r['crs'] or 'N/A':>6} "
            f"{(r['description'] or '')[:40]:<40}"
        )

    print(f"\nTotal: {len(rows)} tables")

    # Write inventory JSON
    inventory = []
    for row in rows:
        r = dict(zip(columns, row))
        inventory.append({
            "schema": r["schema"],
            "table_name": r["table_name"],
            "row_count": r["row_count"],
            "geom_type": r["geom_type"],
            "crs": r["crs"],
            "description": r["description"] or "",
            "last_modified": str(r["last_modified"]) if r["last_modified"] else None,
            "registered_at": str(r["registered_at"]) if r["registered_at"] else None,
            "project_id": r["project_id"],
        })

    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INVENTORY_PATH, "w") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "layers": inventory}, f, indent=2)
    print(f"\nInventory written to {INVENTORY_PATH}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: describe
# ---------------------------------------------------------------------------

def cmd_describe(args) -> int:
    """Show full metadata for one table."""
    engine = postgis_utils.connect()
    schema = args.schema or "analyses"
    table = args.table

    meta = postgis_utils.get_layer_metadata(engine, schema, table)

    print(f"\n--- {schema}.{table} ---")
    print(f"  Row count:      {meta['row_count']}")
    print(f"  Geometry type:  {meta['geom_type'] or 'N/A'}")
    print(f"  CRS (SRID):     {meta['srid'] or 'N/A'}")
    print(f"  Spatial index:  {'YES' if meta['has_spatial_index'] else 'NO'}")
    print(f"  Table size:     {meta['table_size']}")
    print(f"  Table comment:  {meta['comment'] or '(none)'}")
    print(f"  Columns ({len(meta['columns'])}):")
    for col in meta["columns"]:
        print(f"    - {col['name']}: {col['type']}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: health
# ---------------------------------------------------------------------------

def cmd_health(args) -> int:
    """Run a full DB health check."""
    engine = postgis_utils.connect()
    _ensure_meta_table(engine)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_reachable": True,
    }

    with engine.connect() as conn:
        # DB size
        row = conn.execute(text(
            "SELECT pg_size_pretty(pg_database_size(current_database())) AS db_size"
        )).fetchone()
        report["db_size"] = row[0]

        # Schema table counts
        for schema in ("scratch", "analyses", "reference"):
            row = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :s"
            ), {"s": schema}).fetchone()
            report[f"{schema}_table_count"] = row[0]

        # Tables missing spatial indexes
        missing_idx_sql = text("""
            SELECT g.f_table_schema, g.f_table_name, g.f_geometry_column
            FROM geometry_columns g
            WHERE NOT EXISTS (
                SELECT 1 FROM pg_indexes pi
                WHERE pi.schemaname = g.f_table_schema
                AND pi.tablename = g.f_table_name
                AND pi.indexdef ILIKE '%gist%'
            )
        """)
        missing_rows = conn.execute(missing_idx_sql).fetchall()
        report["missing_spatial_indexes"] = [
            {"schema": r[0], "table": r[1], "column": r[2]} for r in missing_rows
        ]

        # Table bloat estimate (dead tuples)
        bloat_sql = text("""
            SELECT schemaname, relname, n_dead_tup, n_live_tup
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 1000
            ORDER BY n_dead_tup DESC
            LIMIT 10
        """)
        bloat_rows = conn.execute(bloat_sql).fetchall()
        report["bloated_tables"] = [
            {"schema": r[0], "table": r[1], "dead_tuples": r[2], "live_tuples": r[3]}
            for r in bloat_rows
        ]

        # Unregistered tables (in managed schemas but not in _gis_meta)
        unreg_sql = text("""
            SELECT t.schemaname, t.relname
            FROM pg_stat_user_tables t
            WHERE t.schemaname IN ('scratch', 'analyses', 'reference')
            AND NOT EXISTS (
                SELECT 1 FROM public._gis_meta m
                WHERE m.table_schema = t.schemaname AND m.table_name = t.relname
            )
        """)
        unreg_rows = conn.execute(unreg_sql).fetchall()
        report["unregistered_tables"] = [
            {"schema": r[0], "table": r[1]} for r in unreg_rows
        ]

    # Print summary
    print("\n=== PostGIS Health Check ===")
    print(f"  DB reachable:          YES")
    print(f"  DB size:               {report['db_size']}")
    print(f"  scratch tables:        {report['scratch_table_count']}")
    print(f"  analyses tables:       {report['analyses_table_count']}")
    print(f"  reference tables:      {report['reference_table_count']}")
    print(f"  Missing spatial idx:   {len(report['missing_spatial_indexes'])}")
    if report["missing_spatial_indexes"]:
        for m in report["missing_spatial_indexes"]:
            print(f"    ! {m['schema']}.{m['table']}.{m['column']}")
    print(f"  Bloated tables:        {len(report['bloated_tables'])}")
    print(f"  Unregistered tables:   {len(report['unregistered_tables'])}")
    if report["unregistered_tables"]:
        for u in report["unregistered_tables"]:
            print(f"    ? {u['schema']}.{u['table']}")

    # Write health JSON
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nHealth report written to {HEALTH_PATH}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: prune
# ---------------------------------------------------------------------------

def cmd_prune(args) -> int:
    """Drop stale scratch tables."""
    engine = postgis_utils.connect()
    dry_run = args.dry_run
    older_than_days = args.older_than_days

    sql = text("""
        SELECT
            t.relname AS table_name,
            t.n_live_tup AS row_count,
            GREATEST(t.last_analyze, t.last_autoanalyze,
                     t.last_vacuum, t.last_autovacuum) AS last_activity
        FROM pg_stat_user_tables t
        WHERE t.schemaname = 'scratch'
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()

    now = datetime.now(timezone.utc)
    candidates = []
    for r in rows:
        table_name, row_count, last_activity = r
        if last_activity is None:
            # No activity recorded — treat as stale
            age_days = older_than_days + 1
        else:
            if last_activity.tzinfo is None:
                from datetime import timezone as tz
                last_activity = last_activity.replace(tzinfo=tz.utc)
            age_days = (now - last_activity).days

        if age_days >= older_than_days:
            candidates.append({
                "table": table_name,
                "row_count": row_count,
                "age_days": age_days,
                "last_activity": str(last_activity) if last_activity else None,
            })

    if not candidates:
        print(f"No scratch tables older than {older_than_days} days.")
        return 0

    print(f"\n{'DRY RUN — ' if dry_run else ''}Scratch tables to prune (>{older_than_days} days):\n")
    for c in candidates:
        print(f"  scratch.{c['table']:<35} rows={c['row_count']:<10} age={c['age_days']}d")

    if not dry_run:
        for c in candidates:
            postgis_utils.drop_table(engine, "scratch", c["table"], dry_run=False)
            print(f"  DROPPED: scratch.{c['table']}")

        # Log to prune log
        PRUNE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PRUNE_LOG_PATH, "a") as f:
            for c in candidates:
                entry = {
                    "timestamp": now.isoformat(),
                    "action": "drop",
                    "schema": "scratch",
                    "table": c["table"],
                    "row_count": c["row_count"],
                    "age_days": c["age_days"],
                }
                f.write(json.dumps(entry) + "\n")
        print(f"\nPrune log updated: {PRUNE_LOG_PATH}")
    else:
        print(f"\nDry run — no tables dropped. Remove --dry-run to execute.")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: promote
# ---------------------------------------------------------------------------

def cmd_promote(args) -> int:
    """Move a table from scratch.* to analyses.*."""
    engine = postgis_utils.connect()
    _ensure_meta_table(engine)

    source_table = args.table
    dest_table = args.to
    description = args.description or ""

    # Verify source is in scratch
    with engine.connect() as conn:
        exists = conn.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'scratch' AND table_name = :t"
        ), {"t": source_table}).fetchone()

    if not exists:
        print(f"ERROR: scratch.{source_table} does not exist.")
        return 1

    # Ensure analyses schema exists
    postgis_utils.ensure_schemas(engine)

    # Move the table
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    comment = f"{description} | promoted from scratch.{source_table} at {now_str}"

    with engine.begin() as conn:
        # ALTER TABLE SET SCHEMA moves the table
        conn.execute(text(
            f'ALTER TABLE scratch."{source_table}" SET SCHEMA analyses'
        ))
        # Rename if target name differs
        if source_table != dest_table:
            conn.execute(text(
                f'ALTER TABLE analyses."{source_table}" RENAME TO "{dest_table}"'
            ))
        # Set table comment
        conn.execute(text(
            f"COMMENT ON TABLE analyses.\"{dest_table}\" IS :comment"
        ), {"comment": comment})

    # Register in _gis_meta
    postgis_utils.register_layer(
        engine, "analyses", dest_table, description,
        registered_by="db-manager",
        project_id=None,
    )

    # Update promoted_from
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE public._gis_meta SET promoted_from = :src "
            "WHERE table_schema = 'analyses' AND table_name = :dst"
        ), {"src": f"scratch.{source_table}", "dst": dest_table})

    print(f"Promoted: scratch.{source_table} → analyses.{dest_table}")
    if description:
        print(f"Description: {description}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: ensure-reference
# ---------------------------------------------------------------------------

def cmd_ensure_reference(args) -> int:
    """Check if reference layers exist and report missing ones."""
    engine = postgis_utils.connect()
    postgis_utils.ensure_schemas(engine)

    layers_to_check = [args.layer] if args.layer else REFERENCE_LAYERS

    with engine.connect() as conn:
        for layer in layers_to_check:
            exists = conn.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'reference' AND table_name = :t"
            ), {"t": layer}).fetchone()

            if exists:
                print(f"  ✓ reference.{layer} — present")
            else:
                print(f"  ✗ reference.{layer} — MISSING")
                print(f"    To populate: python scripts/retrieve_tiger.py "
                      f"--layer {layer} --schema reference --table {layer}")

    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PostGIS database manager — discover, prune, health, promote, describe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # discover
    p_disc = sub.add_parser("discover", help="List all layers in PostGIS with metadata")
    p_disc.add_argument("--schema", default=None, help="Filter by schema (scratch, analyses, reference)")
    p_disc.add_argument("--search", default=None, help="Keyword search in table names and descriptions")

    # prune
    p_prune = sub.add_parser("prune", help="Drop stale scratch tables")
    p_prune.add_argument("--dry-run", action="store_true", default=True,
                         help="Show what would be pruned without dropping (default: True)")
    p_prune.add_argument("--no-dry-run", action="store_false", dest="dry_run",
                         help="Actually drop the tables")
    p_prune.add_argument("--older-than-days", type=int, default=7,
                         help="Prune tables older than N days (default: 7)")

    # health
    sub.add_parser("health", help="Run a full DB health check")

    # promote
    p_prom = sub.add_parser("promote", help="Move a table from scratch to analyses")
    p_prom.add_argument("--table", required=True, help="Source table name in scratch schema")
    p_prom.add_argument("--to", required=True, help="Destination table name in analyses schema")
    p_prom.add_argument("--description", default="", help="Table description / provenance note")

    # describe
    p_desc = sub.add_parser("describe", help="Show full metadata for one table")
    p_desc.add_argument("--table", required=True, help="Table name")
    p_desc.add_argument("--schema", default=None, help="Schema (default: analyses)")

    # init-schemas
    sub.add_parser("init-schemas", help="Ensure schemas and PostGIS extension exist")

    # ensure-reference
    p_ref = sub.add_parser("ensure-reference", help="Check reference layers")
    p_ref.add_argument("--layer", default=None, help="Specific layer to check (default: all)")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DISPATCH = {
    "discover": cmd_discover,
    "prune": cmd_prune,
    "health": cmd_health,
    "promote": cmd_promote,
    "describe": cmd_describe,
    "init-schemas": cmd_init_schemas,
    "ensure-reference": cmd_ensure_reference,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    handler = DISPATCH.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    try:
        return handler(args)
    except Exception as e:
        logger.error("Error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
