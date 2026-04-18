"""
publish_tiles.py — Publish a GeoPackage or PostGIS layer as vector tiles.

Publishes via Martin tile server (self-hosted, open source, backed by PostGIS).
Optionally generates a .pmtiles file for offline/static distribution.

Requirements:
    - PostGIS running (docker compose -f docker/docker-compose.postgis.yml up -d)
    - Martin running  (docker compose -f docker/docker-compose.tiles.yml up -d)
    - tippecanoe installed (optional, for high-quality PMTiles generation)
    - pmtiles Python package (fallback for PMTiles generation)

Usage:
    # Publish a GeoPackage layer to Martin
    python scripts/publish_tiles.py \\
        --input data/processed/tracts.gpkg \\
        --layer-name mn_tracts

    # Publish and also save a PMTiles file for offline delivery
    python scripts/publish_tiles.py \\
        --input data/processed/tracts.gpkg \\
        --layer-name mn_tracts \\
        --min-zoom 4 --max-zoom 14 \\
        --output-pmtiles outputs/tiles/mn_tracts.pmtiles

    # Publish a PostGIS table already loaded in the database
    python scripts/publish_tiles.py \\
        --input analyses.mn_tracts \\
        --layer-name mn_tracts

Output:
    - Tile endpoint URL printed to stdout
    - Optional .pmtiles file at --output-pmtiles
    - JSON log at <output-pmtiles>.log.json (or tile_publish.log.json)
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd

# Add project root to path so scripts can import each other
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.postgis_utils import connect, upload_layer

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MARTIN_BASE_URL = os.environ.get("MARTIN_BASE_URL", "http://localhost:3000")
POSTGIS_SCHEMA = "analyses"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_postgis_table(input_str: str) -> bool:
    """Return True if input looks like schema.table (not a file path)."""
    p = Path(input_str)
    return not p.suffix and "." in input_str


def _load_geopackage(path: str) -> gpd.GeoDataFrame:
    """Load a GeoPackage (first layer, or the only layer)."""
    import fiona
    layers = fiona.listlayers(path)
    if len(layers) == 0:
        raise ValueError(f"No layers found in {path}")
    if len(layers) > 1:
        logger.warning(
            "GeoPackage has %d layers. Using first: '%s'. "
            "Use --input layer-name to select a specific layer.",
            len(layers), layers[0]
        )
    return gpd.read_file(path, layer=layers[0])


def _upload_to_postgis(gdf: gpd.GeoDataFrame, table_name: str) -> None:
    """Upload GeoDataFrame to PostGIS analyses schema."""
    engine = connect()
    upload_layer(gdf, table_name, schema=POSTGIS_SCHEMA, engine=engine)
    logger.info("Layer '%s' uploaded to PostGIS schema '%s'", table_name, POSTGIS_SCHEMA)


def _martin_tile_url(layer_name: str) -> str:
    """Return the Martin tile endpoint URL for a PostGIS layer."""
    # Martin auto-discovers public tables; uses schema.table format
    return f"{MARTIN_BASE_URL}/{POSTGIS_SCHEMA}.{layer_name}/{{z}}/{{x}}/{{y}}"


def _generate_pmtiles_tippecanoe(
    geojson_path: str,
    output_path: str,
    layer_name: str,
    min_zoom: int,
    max_zoom: int,
) -> None:
    """Generate PMTiles using tippecanoe (preferred, higher quality)."""
    cmd = [
        "tippecanoe",
        "--output", output_path,
        "--layer", layer_name,
        f"--minimum-zoom={min_zoom}",
        f"--maximum-zoom={max_zoom}",
        "--force",
        "--no-tile-size-limit",
        "--simplification=2",
        "--drop-densest-as-needed",
        geojson_path,
    ]
    logger.info("Running tippecanoe: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"tippecanoe failed:\n{result.stderr}")
    logger.info("PMTiles written to %s", output_path)


def _generate_pmtiles_python(
    gdf: gpd.GeoDataFrame,
    output_path: str,
    layer_name: str,
    min_zoom: int,
    max_zoom: int,
) -> None:
    """Generate PMTiles using the pmtiles Python package (fallback)."""
    try:
        import pmtiles.writer as pm_writer  # type: ignore
    except ImportError:
        raise ImportError(
            "pmtiles package not installed. "
            "Run: pip install pmtiles  or install tippecanoe for better results."
        )

    logger.info(
        "Generating PMTiles via pmtiles Python package "
        "(zoom %d-%d, %d features)…",
        min_zoom, max_zoom, len(gdf)
    )

    # pmtiles Python package works with GeoJSON
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False, mode="w") as f:
        tmp_geojson = f.name
        gdf.to_crs("EPSG:4326").to_file(f.name, driver="GeoJSON")

    try:
        pm_writer.write_pmtiles(
            tmp_geojson,
            output_path,
            minzoom=min_zoom,
            maxzoom=max_zoom,
            layer_name=layer_name,
        )
        logger.info("PMTiles written to %s", output_path)
    finally:
        os.unlink(tmp_geojson)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a GeoPackage or PostGIS layer as vector tiles via Martin."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to a GeoPackage (.gpkg) OR a PostGIS table in 'schema.table' format."
    )
    parser.add_argument(
        "--layer-name", required=True,
        help="Layer name used in Martin tile endpoint and PMTiles file."
    )
    parser.add_argument(
        "--min-zoom", type=int, default=4,
        help="Minimum tile zoom level. Default: 4."
    )
    parser.add_argument(
        "--max-zoom", type=int, default=14,
        help="Maximum tile zoom level. Default: 14."
    )
    parser.add_argument(
        "--output-pmtiles", default=None,
        help="Optional path for .pmtiles output file (offline/static distribution)."
    )
    parser.add_argument(
        "--martin-url", default=None,
        help="Martin base URL. Default: MARTIN_BASE_URL env var or http://localhost:3000"
    )
    args = parser.parse_args()

    if args.martin_url:
        global MARTIN_BASE_URL
        MARTIN_BASE_URL = args.martin_url

    started_at = datetime.utcnow().isoformat() + "Z"
    log_data = {
        "started_at":    started_at,
        "input":         args.input,
        "layer_name":    args.layer_name,
        "min_zoom":      args.min_zoom,
        "max_zoom":      args.max_zoom,
        "output_pmtiles": args.output_pmtiles,
        "steps":         [],
    }

    gdf = None

    # Step 1: load data
    if _is_postgis_table(args.input):
        # Already in PostGIS — just build the URL
        log_data["steps"].append({"step": "source", "type": "postgis", "table": args.input})
        table_name = args.input.split(".")[-1]
        logger.info("Using existing PostGIS table: %s", args.input)
    else:
        # GeoPackage → upload to PostGIS
        if not Path(args.input).exists():
            logger.error("Input file not found: %s", args.input)
            sys.exit(1)

        logger.info("Loading GeoPackage: %s", args.input)
        gdf = _load_geopackage(args.input)
        log_data["steps"].append({
            "step": "load_gpkg", "path": args.input,
            "features": len(gdf), "crs": str(gdf.crs)
        })

        table_name = args.layer_name.lower().replace("-", "_")
        _upload_to_postgis(gdf, table_name)
        log_data["steps"].append({
            "step": "upload_postgis", "schema": POSTGIS_SCHEMA, "table": table_name
        })

    # Step 2: build Martin tile URL
    tile_url = _martin_tile_url(table_name)
    log_data["tile_url"] = tile_url
    log_data["steps"].append({"step": "martin_url", "url": tile_url})
    logger.info("✅ Tile endpoint: %s", tile_url)

    # Step 3: optional PMTiles generation
    if args.output_pmtiles:
        output_path = args.output_pmtiles
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if gdf is None:
            # Need to load from PostGIS for PMTiles generation
            from scripts.postgis_utils import download_layer
            engine = connect()
            schema_part = args.input.split(".")[0] if "." in args.input else POSTGIS_SCHEMA
            gdf = download_layer(table_name, schema=schema_part, engine=engine)

        # Try tippecanoe first (better quality), fall back to Python
        if shutil.which("tippecanoe"):
            with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
                tmp_geojson = f.name
            try:
                gdf.to_crs("EPSG:4326").to_file(tmp_geojson, driver="GeoJSON")
                _generate_pmtiles_tippecanoe(
                    tmp_geojson, output_path, args.layer_name,
                    args.min_zoom, args.max_zoom
                )
                log_data["steps"].append({
                    "step": "pmtiles", "method": "tippecanoe", "output": output_path
                })
            finally:
                os.unlink(tmp_geojson)
        else:
            logger.warning(
                "tippecanoe not found — falling back to pmtiles Python package. "
                "Install tippecanoe for higher quality tiles."
            )
            _generate_pmtiles_python(
                gdf, output_path, args.layer_name,
                args.min_zoom, args.max_zoom
            )
            log_data["steps"].append({
                "step": "pmtiles", "method": "python_pmtiles", "output": output_path
            })

        log_data["pmtiles_path"] = output_path
        logger.info("✅ PMTiles saved: %s", output_path)

    # Write JSON log
    log_data["finished_at"] = datetime.utcnow().isoformat() + "Z"
    if args.output_pmtiles:
        log_path = Path(args.output_pmtiles).with_suffix(".log.json")
    else:
        log_path = Path("tile_publish.log.json")
    log_path.write_text(json.dumps(log_data, indent=2))
    logger.info("Log written: %s", log_path)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Layer: {args.layer_name}")
    print(f"  Tile endpoint: {tile_url}")
    if args.output_pmtiles:
        print(f"  PMTiles: {args.output_pmtiles}")
    print(f"{'='*60}\n")
    print("Add to MapLibre GL JS:")
    print(f'  map.addSource("{args.layer_name}", {{')
    print(f'    type: "vector",')
    print(f'    tiles: ["{tile_url}"],')
    print(f'    minzoom: {args.min_zoom},')
    print(f'    maxzoom: {args.max_zoom}')
    print(f'  }});')


if __name__ == "__main__":
    main()
