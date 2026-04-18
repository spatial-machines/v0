"""Write an ArcGIS Pro .lyrx layer file from a .style.json sidecar.

The `.lyrx` format is a documented JSON bundle (Esri CIM schema) that
ArcGIS Pro can consume via `File > Import > Layer` or drag-drop. Writing
it as pure Python means we never need arcpy to produce styled layers.

Reference: https://github.com/Esri/cim-spec  (CIMLayerDocument schema)

Usage:
    from lyrx_writer import write_lyrx
    write_lyrx(
        sidecar_path="outputs/maps/poverty_choropleth.style.json",
        data_path="data/tracts.gpkg",   # relative to the .lyrx
        layer_name="tracts",
        output="outputs/arcgis/layers/poverty_choropleth.lyrx",
        workspace_type="OpenFileGDB",   # or "GPKG"
    )
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from renderers import lyrx_renderer


LYRX_VERSION = "3.1.0"  # matches ArcGIS Pro 3.1+


def _feature_table(data_path: str, layer_name: str, workspace_type: str) -> dict:
    """Build the CIM featureTable for a feature class or GPKG layer."""
    workspace_factory = {
        "OpenFileGDB": "FileGDB",
        "FileGDB": "FileGDB",
        "GPKG": "Sql",
        "Shapefile": "Shapefile",
    }.get(workspace_type, "FileGDB")

    return {
        "type": "CIMFeatureTable",
        "displayField": "",
        "editable": True,
        "dataConnection": {
            "type": "CIMStandardDataConnection",
            "workspaceConnectionString": f"DATABASE={data_path}",
            "workspaceFactory": workspace_factory,
            "dataset": layer_name,
            "datasetType": "esriDTFeatureClass",
        },
        "studyAreaSpatialRel": "esriSpatialRelUndefined",
        "searchOrder": "esriSearchOrderSpatial",
    }


def write_lyrx(
    sidecar_path: str | Path,
    data_path: str,
    layer_name: str,
    output: str | Path,
    *,
    workspace_type: str = "OpenFileGDB",
    lyrx_name: str | None = None,
) -> Path:
    """Write a styled .lyrx file from a style sidecar."""
    sidecar = json.loads(Path(sidecar_path).read_text())
    renderer = lyrx_renderer(sidecar)

    family = sidecar.get("map_family", "")
    geom_type = {
        "thematic_choropleth": "esriGeometryPolygon",
        "thematic_categorical": "esriGeometryPolygon",
        "reference": "esriGeometryPolygon",
        "point_overlay": "esriGeometryPoint",
    }.get(family, "esriGeometryPolygon")

    display_name = (
        lyrx_name
        or sidecar.get("title")
        or sidecar.get("legend_title")
        or Path(str(sidecar_path)).stem.replace(".style", "")
    )

    feature_layer = {
        "type": "CIMFeatureLayer",
        "name": display_name,
        "uRI": f"CIMPATH=map/{layer_name}.xml",
        "sourceModifiedTime": {"type": "TimeInstant"},
        "useSourceMetadata": True,
        "description": sidecar.get("attribution", ""),
        "layerElevation": {
            "type": "CIMLayerElevationSurface",
            "elevationSurfaceLayerURI": "CIMPATH=Map/WorldElevation3D_Terrain3D.xml",
        },
        "expanded": True,
        "layerType": "Operational",
        "showLegends": True,
        "visibility": True,
        "displayCacheType": "Permanent",
        "maxDisplayCacheAge": 5,
        "showPopups": True,
        "serviceLayerID": -1,
        "refreshRate": -1,
        "refreshRateUnit": "esriTimeUnitsSeconds",
        "blendingMode": "Alpha",
        "featureTable": _feature_table(data_path, layer_name, workspace_type),
        "htmlPopupEnabled": True,
        "selectable": True,
        "featureCacheType": "Session",
        "renderer": renderer,
        "scaleSymbols": True,
        "snappable": True,
    }

    doc = {
        "type": "CIMLayerDocument",
        "version": LYRX_VERSION,
        "build": 41740,
        "layers": [feature_layer["uRI"]],
        "layerDefinitions": [feature_layer],
        "binaryReferences": [],
        "elevationSurfaces": [],
        "rGBColorProfile": "sRGB IEC61966-2.1",
        "cMYKColorProfile": "U.S. Web Coated (SWOP) v2",
        "metadataURI": "CIMPATH=Metadata/00000000000000000000000000000000.xml",
        "metadata": {
            "type": "CIMGenericXMLNode",
            "xml": (
                "<metadata xml:lang=\"en\"><Esri><CreaDate>0</CreaDate>"
                "<SyncOnce>TRUE</SyncOnce></Esri></metadata>"
            ),
            "children": [],
        },
    }

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2))
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Write an ArcGIS Pro .lyrx file from a style sidecar."
    )
    ap.add_argument("--sidecar", required=True)
    ap.add_argument("--data", required=True,
                    help="Path to .gdb or .gpkg (relative to the .lyrx)")
    ap.add_argument("--layer", required=True,
                    help="Feature class / layer name")
    ap.add_argument("--output", required=True)
    ap.add_argument("--workspace",
                    choices=["OpenFileGDB", "FileGDB", "GPKG", "Shapefile"],
                    default="OpenFileGDB")
    ap.add_argument("--name", help="Override display name")
    args = ap.parse_args()

    path = write_lyrx(
        sidecar_path=args.sidecar,
        data_path=args.data,
        layer_name=args.layer,
        output=args.output,
        workspace_type=args.workspace,
        lyrx_name=args.name,
    )
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
