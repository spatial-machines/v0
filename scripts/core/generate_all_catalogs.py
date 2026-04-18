#!/usr/bin/env python3
"""Generate data_catalog.json for every active analysis in registry.json.

Scans data/processed/ and outputs/*.gpkg for each active analysis,
then writes analyses/{id}/data_catalog.json.

Usage:
    python generate_all_catalogs.py [--base-dir /path/to/gis-agent]
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path so we can import sibling module
sys.path.insert(0, str(Path(__file__).parent))
from write_data_catalog import build_catalog


def find_gpkgs(analysis_dir):
    """Find all GeoPackage files in an analysis directory."""
    gpkgs = []
    # Primary: data/processed/
    processed = analysis_dir / "data" / "processed"
    if processed.exists():
        gpkgs.extend(sorted(processed.glob("*.gpkg")))
    # Secondary: outputs/*.gpkg (but not qgis/ copies)
    outputs = analysis_dir / "outputs"
    if outputs.exists():
        for gpkg in sorted(outputs.rglob("*.gpkg")):
            # Skip qgis/ directory (those are copies)
            if "qgis" in gpkg.parts:
                continue
            # Skip if same filename already found in processed
            if not any(g.name == gpkg.name for g in gpkgs):
                gpkgs.append(gpkg)
    return gpkgs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate data catalogs for all analyses")
    parser.add_argument('--base-dir', default=str(Path(__file__).resolve().parents[2]),
                        help='GIS agent base directory')
    args = parser.parse_args()

    base = Path(args.base_dir)
    registry_path = base / "analyses" / "registry.json"

    with open(registry_path) as f:
        registry = json.load(f)

    generated = 0
    skipped = 0

    for entry in registry.get("analyses", []):
        pid = entry["id"]
        status = entry.get("status", "active")

        if status != "active":
            print(f"  SKIP {pid} (status={status})")
            skipped += 1
            continue

        analysis_dir = base / "analyses" / pid
        if not analysis_dir.exists():
            print(f"  SKIP {pid} (dir not found)")
            skipped += 1
            continue

        gpkgs = find_gpkgs(analysis_dir)
        if not gpkgs:
            print(f"  SKIP {pid} (no gpkg files)")
            skipped += 1
            continue

        print(f"  Cataloging {pid} ({len(gpkgs)} gpkg files)...")
        catalog = build_catalog([str(g) for g in gpkgs])

        output_path = analysis_dir / "data_catalog.json"
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        print(f"    → {output_path.name}: {len(catalog['layers'])} layers")
        generated += 1

    print(f"\nDone: {generated} catalogs generated, {skipped} skipped")


if __name__ == "__main__":
    raise SystemExit(main())
