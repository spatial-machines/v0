"""Generate a QGIS .qgs project file using PyQGIS (no GUI).

Uses the host QGIS Python bindings to create a fully valid project file
with real layer metadata, extents, and provider details.  The resulting
.qgs file opens in QGIS with a functional layer (attribute table works,
zoom-to-layer works, graduated styling works).

Requires: QGIS 3.x installed with Python bindings (qgis.core).
Does NOT launch a GUI — runs headless via QgsApplication.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Force offscreen rendering for headless operation
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Bootstrap PyQGIS headless ------------------------------------------------
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsVectorLayer,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a QGIS .qgs project file via PyQGIS (headless)."
    )
    parser.add_argument("package_dir", help="Path to the QGIS review package directory")
    parser.add_argument("--title", default="GIS Review Project", help="Project title")
    parser.add_argument(
        "--layers", required=True,
        help="JSON file or inline JSON array describing layers. "
             "Each layer: {name, path, layer_name?, crs_epsg?, geometry_type?}",
    )
    parser.add_argument("--crs", type=int, default=4269, help="Project CRS EPSG code (default: 4269)")
    parser.add_argument("-o", "--output", default=None, help="Output .qgs filename (default: project.qgs)")
    args = parser.parse_args()

    pkg_dir = Path(args.package_dir).expanduser().resolve()
    if not pkg_dir.exists():
        print(f"ERROR: package directory does not exist: {pkg_dir}", file=sys.stderr)
        return 1

    # Parse layer specs
    layers_input = args.layers
    if Path(layers_input).exists():
        layer_specs = json.loads(Path(layers_input).read_text())
    else:
        layer_specs = json.loads(layers_input)

    # Init headless QGIS
    QgsApplication.setPrefixPath("/usr", True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        project = QgsProject.instance()
        project.setTitle(args.title)

        # Set project CRS
        project_crs = QgsCoordinateReferenceSystem(f"EPSG:{args.crs}")
        project.setCrs(project_crs)

        out_name = args.output or "project.qgs"
        out_path = pkg_dir / out_name

        for spec in layer_specs:
            # Build the data source URI — use absolute path for loading,
            # then save with relative paths.
            gpkg_path = pkg_dir / spec["path"]
            if not gpkg_path.exists():
                print(f"WARNING: layer data not found: {gpkg_path}")
                continue

            layer_name = spec.get("layer_name", gpkg_path.stem)
            uri = f"{gpkg_path}|layername={layer_name}"

            display_name = spec.get("name", layer_name)
            vlayer = QgsVectorLayer(uri, display_name, "ogr")

            if not vlayer.isValid():
                print(f"WARNING: layer failed to load: {uri}")
                continue

            # Set layer CRS if specified
            lyr_crs_epsg = spec.get("crs_epsg", args.crs)
            lyr_crs = QgsCoordinateReferenceSystem(f"EPSG:{lyr_crs_epsg}")
            vlayer.setCrs(lyr_crs)

            project.addMapLayer(vlayer)
            print(f"  added layer: {display_name} ({vlayer.featureCount()} features)")

        # Write project with relative paths
        project.write(str(out_path))

        # Post-process: rewrite datasource paths as relative to package dir
        # PyQGIS writes absolute paths; we need relative for portability.
        qgs_text = out_path.read_text()
        abs_pkg = str(pkg_dir)
        # Replace absolute package dir with relative marker
        qgs_text = qgs_text.replace(abs_pkg + "/", "./")
        qgs_text = qgs_text.replace(abs_pkg, ".")
        out_path.write_text(qgs_text)

        try:
            rel = out_path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = out_path
        print(f"wrote QGIS project -> {rel}")
        print(f"  title:   {args.title}")
        print(f"  layers:  {len(layer_specs)}")
        print(f"  CRS:     EPSG:{args.crs}")

    finally:
        qgs.exitQgis()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
