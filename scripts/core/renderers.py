"""Sidecar-to-renderer translation shared across QGIS / ArcGIS Pro / AGOL.

A `.style.json` sidecar captures a map's styling decisions (palette,
classification, breaks, RGB colors). This module converts that into:

  - `lyrx_renderer(sidecar)` — ArcGIS Pro .lyrx CIM renderer dict
  - `agol_renderer(sidecar)` — ArcGIS Online Web Map renderer dict
    (wrapped in the `drawingInfo.renderer` shape used by hosted feature layers)

QGIS-side translation already lives in `write_qgis_project.py`; keeping it
separate preserves that file's existing contract.

Design goals:
  - Pure Python; no GIS / Esri imports.
  - Deterministic — the same sidecar always produces the same output so
    the three packagers render identically.
  - Only handles the three map families we support today:
    * thematic_choropleth  -> CIMClassBreaksRenderer / classBreaks
    * thematic_categorical -> CIMUniqueValueRenderer / uniqueValue
    * point_overlay        -> CIMSimpleRenderer / simple
  - Unknown families fall back to a simple single-symbol renderer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))


# ── Palette resolution ──────────────────────────────────────────────

_COLOR_RAMPS_CACHE: dict | None = None


def _color_ramps() -> dict:
    """Load pre-computed 5-stop RGB ramps from config/map_styles.json."""
    global _COLOR_RAMPS_CACHE
    if _COLOR_RAMPS_CACHE is None:
        path = SCRIPTS_CORE.parents[1] / "config" / "map_styles.json"
        if path.exists():
            data = json.loads(path.read_text())
            _COLOR_RAMPS_CACHE = data.get("color_ramps_rgb", {})
        else:
            _COLOR_RAMPS_CACHE = {}
    return _COLOR_RAMPS_CACHE


def ramp_colors(palette: str, k: int) -> list[list[int]]:
    """Return k RGB triples [0–255] for a named matplotlib colormap.

    Uses the cached 5-stop ramps first (fast, no matplotlib dep); falls
    back to a linear interpolation over the stops when k != len(stops).
    """
    ramps = _color_ramps()
    if palette not in ramps:
        # Safe fallback — gray ramp.
        base = [[240, 240, 240], [180, 180, 180], [120, 120, 120],
                [80, 80, 80], [40, 40, 40]]
    else:
        base = ramps[palette]

    if k == len(base):
        return [list(c) for c in base]

    # Linear interpolate
    result = []
    for i in range(k):
        pos = i * (len(base) - 1) / max(1, k - 1)
        lo = int(pos)
        hi = min(lo + 1, len(base) - 1)
        frac = pos - lo
        c = [
            int(round(base[lo][j] + (base[hi][j] - base[lo][j]) * frac))
            for j in range(3)
        ]
        result.append(c)
    return result


def sidecar_colors(sidecar: dict) -> list[list[int]]:
    """Extract the effective RGB color list from a sidecar.

    Precedence:
      1. sidecar["colors_rgb"] (explicit)
      2. ramp_colors(palette, k)
    """
    explicit = sidecar.get("colors_rgb")
    if explicit and isinstance(explicit, list):
        return [list(c) for c in explicit]
    palette = sidecar.get("palette")
    k = sidecar.get("k") or len(sidecar.get("breaks", [])) - 1 or 5
    return ramp_colors(palette or "viridis", max(1, k))


def _rgb_to_cim(rgb: list[int], alpha: int = 255) -> dict:
    """Esri CIM color block in RGBA [0,255]."""
    r, g, b = rgb[:3]
    return {
        "type": "CIMRGBColor",
        "values": [float(r), float(g), float(b), float(alpha)],
    }


def _rgb_to_agol(rgb: list[int], alpha: int = 255) -> list[int]:
    """ArcGIS Online Web Map renderer color = [r, g, b, a]."""
    return [int(rgb[0]), int(rgb[1]), int(rgb[2]), int(alpha)]


# ── LYRX (ArcGIS Pro) ───────────────────────────────────────────────

def lyrx_renderer(sidecar: dict) -> dict:
    """Return the CIM renderer dict for a .lyrx layer from a sidecar."""
    family = sidecar.get("map_family", "")
    field = sidecar.get("field")
    geom = _geom_kind(family)

    if family == "thematic_choropleth" and field:
        return _cim_class_breaks(sidecar, field, geom)
    if family == "thematic_categorical":
        return _cim_unique_value(sidecar, field or "", geom)
    return _cim_simple(sidecar, geom)


def _geom_kind(family: str) -> str:
    if family == "point_overlay":
        return "point"
    if family in ("thematic_choropleth", "thematic_categorical", "reference"):
        return "polygon"
    return "polygon"


def _polygon_symbol(rgb: list[int], outline_rgb=(85, 85, 85), outline_width=0.4) -> dict:
    return {
        "type": "CIMPolygonSymbol",
        "symbolLayers": [
            {
                "type": "CIMSolidStroke",
                "enable": True,
                "capStyle": "Round",
                "joinStyle": "Round",
                "lineStyle3D": "Strip",
                "miterLimit": 10,
                "width": outline_width,
                "color": _rgb_to_cim(list(outline_rgb)),
            },
            {
                "type": "CIMSolidFill",
                "enable": True,
                "color": _rgb_to_cim(rgb),
            },
        ],
    }


def _point_symbol(rgb: list[int], size: float = 6.0) -> dict:
    return {
        "type": "CIMPointSymbol",
        "symbolLayers": [
            {
                "type": "CIMVectorMarker",
                "enable": True,
                "size": size,
                "colorLocked": False,
                "anchorPointUnits": "Relative",
                "billboardMode3D": "FaceNearPlane",
                "frame": {"xmin": -5, "ymin": -5, "xmax": 5, "ymax": 5},
                "markerGraphics": [
                    {
                        "type": "CIMMarkerGraphic",
                        "geometry": {"x": 0, "y": 0},
                        "symbol": {
                            "type": "CIMPolygonSymbol",
                            "symbolLayers": [
                                {
                                    "type": "CIMSolidStroke",
                                    "enable": True,
                                    "width": 0.5,
                                    "color": _rgb_to_cim([26, 26, 26]),
                                },
                                {
                                    "type": "CIMSolidFill",
                                    "enable": True,
                                    "color": _rgb_to_cim(rgb),
                                },
                            ],
                        },
                    }
                ],
                "scaleSymbolsProportionally": True,
                "respectFrame": True,
            }
        ],
        "haloSize": 1,
        "scaleX": 1,
        "angleAlignment": "Display",
    }


def _symbol_for(geom: str, rgb: list[int]) -> dict:
    return _point_symbol(rgb) if geom == "point" else _polygon_symbol(rgb)


def _cim_simple(sidecar: dict, geom: str) -> dict:
    rgb = sidecar_colors(sidecar)[0] if sidecar.get("palette") else [150, 180, 210]
    return {
        "type": "CIMSimpleRenderer",
        "patch": "Default",
        "symbol": {
            "type": "CIMSymbolReference",
            "symbol": _symbol_for(geom, rgb),
        },
    }


def _cim_class_breaks(sidecar: dict, field: str, geom: str) -> dict:
    breaks = sidecar.get("breaks") or []
    colors = sidecar_colors(sidecar)

    if not breaks or len(breaks) < 2:
        return _cim_simple(sidecar, geom)

    n_classes = len(breaks) - 1
    if len(colors) < n_classes:
        colors = ramp_colors(sidecar.get("palette", "viridis"), n_classes)
    colors = colors[:n_classes]

    groups = []
    for i, color in enumerate(colors):
        lo = breaks[i]
        hi = breaks[i + 1]
        groups.append({
            "type": "CIMClassBreak",
            "label": _break_label(lo, hi),
            "description": "",
            "patch": "Default",
            "symbol": {
                "type": "CIMSymbolReference",
                "symbol": _symbol_for(geom, color),
            },
            "upperBound": float(hi),
        })

    return {
        "type": "CIMClassBreaksRenderer",
        "classBreakType": "GraduatedColor",
        "classificationMethod": _classification_method(sidecar.get("scheme")),
        "defaultLabel": "<other>",
        "defaultSymbol": {
            "type": "CIMSymbolReference",
            "symbol": _symbol_for(geom, [208, 208, 208]),
        },
        "field": field,
        "minimumBreak": float(breaks[0]),
        "numberFormat": {
            "type": "CIMNumericFormat",
            "alignmentOption": "esriAlignRight",
            "alignmentWidth": 0,
            "roundingOption": "esriRoundNumberOfDecimals",
            "roundingValue": 2,
        },
        "showClassGaps": False,
        "showInAscendingOrder": True,
        "breaks": groups,
    }


def _cim_unique_value(sidecar: dict, field: str, geom: str) -> dict:
    cat_map = sidecar.get("categorical_map") or {}
    groups = []
    for label, hex_or_rgb in cat_map.items():
        rgb = _coerce_rgb(hex_or_rgb)
        groups.append({
            "type": "CIMUniqueValueClass",
            "label": label,
            "patch": "Default",
            "symbol": {
                "type": "CIMSymbolReference",
                "symbol": _symbol_for(geom, rgb),
            },
            "values": [{"type": "CIMUniqueValue", "fieldValues": [label]}],
            "visible": True,
        })
    return {
        "type": "CIMUniqueValueRenderer",
        "colorRamp": None,
        "defaultLabel": "<other>",
        "defaultSymbol": {
            "type": "CIMSymbolReference",
            "symbol": _symbol_for(geom, [208, 208, 208]),
        },
        "fields": [field] if field else [],
        "groups": [
            {
                "type": "CIMUniqueValueGroup",
                "classes": groups,
                "heading": field or "",
            }
        ],
        "useDefaultSymbol": True,
    }


def _classification_method(scheme: str | None) -> str:
    return {
        "natural_breaks": "NaturalBreaks",
        "quantile": "Quantile",
        "quantiles": "Quantile",
        "equal_interval": "EqualInterval",
        "manual": "Manual",
    }.get((scheme or "").lower(), "NaturalBreaks")


def _break_label(lo, hi) -> str:
    def fmt(x):
        if isinstance(x, float):
            return f"{x:,.2f}".rstrip("0").rstrip(".")
        return str(x)
    return f"{fmt(lo)} \u2013 {fmt(hi)}"


def _coerce_rgb(value) -> list[int]:
    """Accept `#rrggbb`, `[r,g,b]`, or `[r,g,b,a]`."""
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        return [int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)]
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return [int(v) for v in value[:3]]
    return [128, 128, 128]


# ── ArcGIS Online Web Map renderer ──────────────────────────────────

def agol_renderer(sidecar: dict) -> dict:
    """Return a renderer dict suitable for ArcGIS Online hosted feature
    layer `drawingInfo.renderer`.
    """
    family = sidecar.get("map_family", "")
    field = sidecar.get("field")
    geom = _geom_kind(family)

    if family == "thematic_choropleth" and field:
        return _agol_class_breaks(sidecar, field, geom)
    if family == "thematic_categorical":
        return _agol_unique_value(sidecar, field or "", geom)
    return _agol_simple(sidecar, geom)


def _agol_polygon_symbol(rgb, outline=(85, 85, 85), outline_width=0.4):
    return {
        "type": "esriSFS",
        "style": "esriSFSSolid",
        "color": _rgb_to_agol(rgb, alpha=220),
        "outline": {
            "type": "esriSLS",
            "style": "esriSLSSolid",
            "color": _rgb_to_agol(list(outline), alpha=255),
            "width": outline_width,
        },
    }


def _agol_point_symbol(rgb, size=6):
    return {
        "type": "esriSMS",
        "style": "esriSMSCircle",
        "color": _rgb_to_agol(rgb),
        "size": size,
        "angle": 0,
        "xoffset": 0,
        "yoffset": 0,
        "outline": {
            "type": "esriSLS",
            "style": "esriSLSSolid",
            "color": _rgb_to_agol([26, 26, 26]),
            "width": 0.5,
        },
    }


def _agol_symbol_for(geom, rgb):
    return _agol_point_symbol(rgb) if geom == "point" else _agol_polygon_symbol(rgb)


def _agol_simple(sidecar, geom):
    rgb = sidecar_colors(sidecar)[0] if sidecar.get("palette") else [150, 180, 210]
    return {
        "type": "simple",
        "label": sidecar.get("legend_title") or sidecar.get("title") or "",
        "description": "",
        "symbol": _agol_symbol_for(geom, rgb),
    }


def _agol_class_breaks(sidecar, field, geom):
    breaks = sidecar.get("breaks") or []
    colors = sidecar_colors(sidecar)
    if not breaks or len(breaks) < 2:
        return _agol_simple(sidecar, geom)

    n_classes = len(breaks) - 1
    if len(colors) < n_classes:
        colors = ramp_colors(sidecar.get("palette", "viridis"), n_classes)
    colors = colors[:n_classes]

    infos = []
    for i, color in enumerate(colors):
        lo = breaks[i]
        hi = breaks[i + 1]
        infos.append({
            "classMaxValue": float(hi),
            "label": _break_label(lo, hi),
            "description": "",
            "symbol": _agol_symbol_for(geom, color),
        })

    return {
        "type": "classBreaks",
        "field": field,
        "classificationMethod": {
            "natural_breaks": "esriClassifyNaturalBreaks",
            "quantile": "esriClassifyQuantile",
            "quantiles": "esriClassifyQuantile",
            "equal_interval": "esriClassifyEqualInterval",
        }.get((sidecar.get("scheme") or "").lower(), "esriClassifyNaturalBreaks"),
        "minValue": float(breaks[0]),
        "classBreakInfos": infos,
    }


def _agol_unique_value(sidecar, field, geom):
    cat_map = sidecar.get("categorical_map") or {}
    infos = []
    for label, hex_or_rgb in cat_map.items():
        rgb = _coerce_rgb(hex_or_rgb)
        infos.append({
            "value": label,
            "label": label,
            "description": "",
            "symbol": _agol_symbol_for(geom, rgb),
        })
    return {
        "type": "uniqueValue",
        "field1": field,
        "field2": None,
        "field3": None,
        "fieldDelimiter": ",",
        "defaultSymbol": _agol_symbol_for(geom, [208, 208, 208]),
        "defaultLabel": "<other>",
        "uniqueValueInfos": infos,
    }
