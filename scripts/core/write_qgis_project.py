"""Generate a styled QGIS .qgs project file using PyQGIS (headless).

Produces a valid QGIS 3.x project with:
  - Graduated or categorized styling driven by .style.json sidecars or auto-introspection
  - OpenStreetMap / CartoDB basemap as bottom layer
  - Auto-zoom to data extent
  - Layer grouping (Analysis Layers / Basemap)
  - Relative paths for full portability

Requires: QGIS 3.x with Python bindings (qgis.core).
Does NOT launch a GUI.

Usage:
    python scripts/core/write_qgis_project.py \\
        --gpkg data/file1.gpkg data/file2.gpkg \\
        --title "My Analysis" --basemap carto-light \\
        -o outputs/qgis/project.qgs

    python scripts/core/write_qgis_project.py \\
        --gpkg data/tracts.gpkg \\
        --style-dir outputs/maps/ \\
        --title "Styled Review" --basemap osm \\
        -o outputs/qgis/project.qgs
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCategorizedSymbolRenderer,
    QgsFillSymbol,
    QgsGraduatedSymbolRenderer,
    QgsLayerTreeGroup,
    QgsMarkerSymbol,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
    QgsReferencedRectangle,
    QgsRendererCategory,
    QgsRendererRange,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_CORE))

from style_utils import (
    load_styles,
    resolve_palette,
    get_categorical_palette,
    get_rgb_ramp,
    compute_breaks,
    classify_field,
    is_percent_field,
    NUMERIC_TYPES,
)


BASEMAP_URLS = {
    "osm": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "carto-light": "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
    "carto-dark": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
}

BASEMAP_NAMES = {
    "osm": "OpenStreetMap",
    "carto-light": "CartoDB Positron",
    "carto-dark": "CartoDB Dark Matter",
}


# ── GeoPackage introspection ─────────────────────────────────────────

def _guess_geometry_type(gpkg_path: str) -> str:
    lower = gpkg_path.lower()
    point_keywords = [
        "station", "point", "fqhc", "store", "grocery", "poi",
        "chipotle", "competitor", "location", "site", "scored", "fire",
    ]
    for kw in point_keywords:
        if kw in lower:
            return "Point"
    return "Polygon"


def _introspect_gpkg(gpkg_path: str, layer_name: str) -> dict:
    """Read field info and data extent from a GeoPackage via sqlite3."""
    result = {"fields": [], "extent": None, "feature_count": 0, "thematic_field": None}
    try:
        conn = sqlite3.connect(gpkg_path)
        cols = conn.execute(f'PRAGMA table_info("{layer_name}")').fetchall()
        for col in cols:
            cid, name, ctype, notnull, default, pk = col
            role = classify_field(name, ctype)
            if role == "geometry":
                continue
            info = {"name": name, "type": ctype, "role": role}
            if ctype.upper().split("(")[0].strip() in NUMERIC_TYPES:
                try:
                    row = conn.execute(
                        f'SELECT count("{name}"), min("{name}"), max("{name}"), avg("{name}") '
                        f'FROM "{layer_name}" WHERE "{name}" IS NOT NULL'
                    ).fetchone()
                    info["non_null_count"] = row[0]
                    info["min"] = row[1]
                    info["max"] = row[2]
                    info["mean"] = round(row[3], 4) if row[3] is not None else None
                except Exception:
                    pass
            result["fields"].append(info)

        try:
            result["feature_count"] = conn.execute(
                f'SELECT count(*) FROM "{layer_name}"'
            ).fetchone()[0]
        except Exception:
            pass

        try:
            ext = conn.execute(
                'SELECT min_x, min_y, max_x, max_y FROM gpkg_contents WHERE table_name=?',
                (layer_name,)
            ).fetchone()
            if ext and all(e is not None for e in ext):
                result["extent"] = {
                    "xmin": ext[0], "ymin": ext[1],
                    "xmax": ext[2], "ymax": ext[3],
                }
        except Exception:
            pass

        for priority_role in ["percent", "count", "measure"]:
            candidates = [
                f for f in result["fields"]
                if f["role"] == priority_role and f.get("non_null_count", 0) > 0
            ]
            if candidates:
                result["thematic_field"] = max(
                    candidates, key=lambda f: f.get("non_null_count", 0)
                )
                break

        conn.close()
    except Exception:
        pass
    return result


def _read_values(gpkg_path: str, layer_name: str, field_name: str) -> list[float]:
    """Read all non-null numeric values for a field from a GeoPackage."""
    values = []
    try:
        conn = sqlite3.connect(gpkg_path)
        rows = conn.execute(
            f'SELECT "{field_name}" FROM "{layer_name}" WHERE "{field_name}" IS NOT NULL'
        ).fetchall()
        for row in rows:
            try:
                values.append(float(row[0]))
            except (ValueError, TypeError):
                pass
        conn.close()
    except Exception:
        pass
    return sorted(values)


# ── Known categorical fields ─────────────────────────────────────────
# Maps field names in the GeoPackage to palette names in map_styles.json.
# When a layer has one of these fields, use categorized styling automatically.
CATEGORICAL_FIELD_MAP = {
    "hotspot_class": "hotspot",
    "hotspot_class_raw": "hotspot",
    "gi_bin": "hotspot",
    "lisa_cluster": "lisa_cluster",
    "cluster": "lisa_cluster",
    "land_use": "land_use",
    "land_use_class": "land_use",
}


# ── Style sidecar loading ────────────────────────────────────────────

def _find_style_sidecar(style_dir: Path | None, gpkg_stem: str) -> dict | None:
    """Look for a .style.json sidecar that matches a GeoPackage layer.

    Matching priority:
      1. Sidecar whose source_gpkg basename matches the gpkg_stem exactly
      2. Sidecar whose filename contains the gpkg_stem
    Avoids cross-matching (e.g. hotspot sidecar matching the base tracts layer).
    """
    if not style_dir or not style_dir.exists():
        return None

    candidates = []
    for sidecar in style_dir.glob("*.style.json"):
        try:
            data = json.loads(sidecar.read_text())
        except Exception:
            continue
        src = data.get("source_gpkg", "")
        src_stem = Path(src).stem if src else ""
        sidecar_stem = sidecar.stem.replace(".style", "")

        # Exact match: sidecar's source gpkg has the same stem as our layer
        if src_stem == gpkg_stem:
            candidates.append((0, sidecar_stem, data))
        # Filename match: sidecar filename contains the gpkg stem
        elif gpkg_stem in sidecar_stem:
            candidates.append((1, sidecar_stem, data))

    if not candidates:
        return None

    # Return the best match (lowest priority number, then shortest name for specificity)
    candidates.sort(key=lambda c: (c[0], len(c[1])))
    return candidates[0][2]


def _find_categorical_field(gpkg_path: str, layer_name: str) -> tuple[str, str] | None:
    """Check if a GeoPackage layer has a known categorical field.

    Returns (field_name, palette_name) or None.
    """
    try:
        conn = sqlite3.connect(gpkg_path)
        cols = conn.execute(f'PRAGMA table_info("{layer_name}")').fetchall()
        conn.close()
        for col in cols:
            name = col[1]
            if name.lower() in CATEGORICAL_FIELD_MAP:
                return name, CATEGORICAL_FIELD_MAP[name.lower()]
        return None
    except Exception:
        return None


def _resolve_category_field(
    gpkg_path: str, layer_name: str,
    sidecar_field: str, category_labels: list[str],
) -> str | None:
    """Find which field actually holds the category values.

    The sidecar may say field="poverty_rate" but the categorical labels
    like "Hot Spot (99%)" live in a different field (hotspot_class).
    Check the sidecar's field first, then search TEXT fields for a match.

    Returns None if no field in the layer contains the expected categories.
    """
    try:
        conn = sqlite3.connect(gpkg_path)
        # Check if the sidecar's field has these category values
        try:
            vals = conn.execute(
                f'SELECT DISTINCT "{sidecar_field}" FROM "{layer_name}"'
            ).fetchall()
            actual = {str(v[0]) for v in vals if v[0] is not None}
            if category_labels[0] in actual:
                conn.close()
                return sidecar_field
        except Exception:
            pass

        # Search TEXT columns for one that contains the category values
        cols = conn.execute(f'PRAGMA table_info("{layer_name}")').fetchall()
        for col in cols:
            cid, name, ctype, notnull, default, pk = col
            if ctype != "TEXT":
                continue
            try:
                vals = conn.execute(
                    f'SELECT DISTINCT "{name}" FROM "{layer_name}"'
                ).fetchall()
                actual = {str(v[0]) for v in vals if v[0] is not None}
                if category_labels[0] in actual:
                    conn.close()
                    return name
            except Exception:
                continue
        conn.close()
    except Exception:
        pass
    # No field in this layer holds the expected categories
    return None


# ── PyQGIS renderer builders ────────────────────────────────────────

def _build_graduated_renderer(
    vlayer: QgsVectorLayer,
    field_name: str,
    colors_rgb: list[list[int]],
    method: str = "natural_breaks",
    k: int = 5,
    breaks: list[float] | None = None,
) -> QgsGraduatedSymbolRenderer:
    """Build a graduated symbol renderer with quantile/equal-interval/natural-breaks."""
    renderer = QgsGraduatedSymbolRenderer(field_name)

    # Compute breaks from data if not provided
    if breaks is None:
        values = []
        for feat in vlayer.getFeatures():
            val = feat[field_name]
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        values.sort()
        if not values:
            return renderer
        breaks = compute_breaks(values, k, method)

    n_classes = len(breaks) - 1
    colors = colors_rgb[:n_classes] if len(colors_rgb) >= n_classes else colors_rgb

    # Pad colors if we have fewer than needed
    while len(colors) < n_classes:
        colors.append([200, 200, 200])

    is_pct = is_percent_field(field_name)

    for i in range(n_classes):
        lo, hi = breaks[i], breaks[i + 1]

        symbol = QgsFillSymbol.createSimple({
            "color": f"{colors[i][0]},{colors[i][1]},{colors[i][2]},200",
            "outline_color": "255,255,255,255",
            "outline_width": "0.2",
            "outline_style": "solid",
        })

        suffix = "%" if is_pct else ""
        if all(abs(b - round(b)) < 0.01 for b in breaks):
            label = f"{int(round(lo)):,}\u2013{int(round(hi)):,}{suffix}"
        elif max(abs(b) for b in breaks) >= 10:
            label = f"{lo:.1f}\u2013{hi:.1f}{suffix}"
        else:
            label = f"{lo:.2f}\u2013{hi:.2f}{suffix}"

        rng = QgsRendererRange(lo, hi, symbol, label)
        renderer.addClassRange(rng)

    renderer.setClassAttribute(field_name)
    return renderer


def _build_categorized_renderer(
    field_name: str,
    category_colors: dict[str, str],
) -> QgsCategorizedSymbolRenderer:
    """Build a categorized renderer for categorical data (hotspot, LISA, etc.)."""
    renderer = QgsCategorizedSymbolRenderer(field_name)

    for label, hex_color in category_colors.items():
        hc = hex_color.lstrip("#")
        r, g, b = int(hc[0:2], 16), int(hc[2:4], 16), int(hc[4:6], 16)

        symbol = QgsFillSymbol.createSimple({
            "color": f"{r},{g},{b},200",
            "outline_color": "255,255,255,255",
            "outline_width": "0.15",
            "outline_style": "solid",
        })

        cat = QgsRendererCategory(label, symbol, label, True)
        renderer.addCategory(cat)

    return renderer


def _build_single_renderer(geometry_type: str = "Polygon") -> QgsFillSymbol | QgsMarkerSymbol:
    """Neutral single-symbol fill for layers without thematic styling."""
    if geometry_type == "Point":
        return QgsMarkerSymbol.createSimple({
            "color": "210,210,210,128",
            "outline_color": "60,60,60,255",
            "size": "2.6",
            "name": "circle",
        })
    return QgsFillSymbol.createSimple({
        "color": "210,210,210,128",
        "outline_color": "60,60,60,255",
        "outline_width": "0.2",
        "outline_style": "solid",
    })


# ── Basemap layer ────────────────────────────────────────────────────

def _add_basemap(project: QgsProject, basemap: str) -> QgsRasterLayer | None:
    """Add an XYZ tile basemap layer to the project."""
    url = BASEMAP_URLS.get(basemap)
    if not url:
        return None
    display_name = BASEMAP_NAMES.get(basemap, basemap)
    uri = f"type=xyz&url={url}&zmax=19&zmin=0"
    layer = QgsRasterLayer(uri, display_name, "wms")
    if not layer.isValid():
        print(f"  WARNING: basemap failed to load: {display_name}")
        return None
    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    return layer


# ── Main project builder ────────────────────────────────────────────

def build_qgs_from_gpkg(
    gpkg_paths: list[str | Path],
    title: str,
    output_path: str | Path,
    layer_names: list[str] | None = None,
    crs_epsg: int = 4269,
    qgis_version: str | None = None,
    basemap: str | None = "carto-light",
    style_dir: str | Path | None = None,
) -> Path:
    """High-level API: generate a styled .qgs from GeoPackage files.

    Looks for .style.json sidecars in style_dir to apply graduated/categorized
    styling. Falls back to auto-introspection of the GeoPackage if no sidecar found.
    """
    out_path = Path(output_path)
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    style_path = Path(style_dir) if style_dir else None

    QgsApplication.setPrefixPath("/usr", True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        project = QgsProject.instance()
        project.setTitle(title)

        project_crs = QgsCoordinateReferenceSystem(f"EPSG:{crs_epsg}")
        project.setCrs(project_crs)

        root = project.layerTreeRoot()

        # Create layer groups
        analysis_group = root.addGroup("Analysis Layers")
        combined_extent = None
        layer_count = 0

        for gpkg in gpkg_paths:
            gpkg = Path(gpkg)
            stem = gpkg.stem
            if layer_names and stem not in layer_names:
                continue

            display_name = stem.replace("_", " ").title()
            geom_type = _guess_geometry_type(str(gpkg))

            # Resolve absolute path for loading
            abs_gpkg = (out_dir / gpkg).resolve() if not gpkg.is_absolute() else gpkg
            if not abs_gpkg.exists():
                print(f"  WARNING: data not found: {abs_gpkg}")
                continue

            # Load vector layer
            uri = f"{abs_gpkg}|layername={stem}"
            vlayer = QgsVectorLayer(uri, display_name, "ogr")
            if not vlayer.isValid():
                print(f"  WARNING: layer failed to load: {uri}")
                continue

            # Don't override CRS — let QGIS read the native CRS from the GeoPackage.
            # Overriding can cause a CRS mismatch prompt when opening the project.

            # Build renderer — priority order:
            #   1. Known categorical field in the data (hotspot_class, lisa_cluster)
            #   2. Graduated sidecar (colors_rgb + field)
            #   3. Categorical sidecar (only if layer actually has matching categories)
            #   4. Auto-introspect numeric thematic field
            #   5. Single symbol fallback
            renderer_applied = False

            # ── Step 1: Check for known categorical fields ──
            cat_field = _find_categorical_field(str(abs_gpkg), stem)
            if cat_field:
                field_name, palette_name = cat_field
                cat_pal = get_categorical_palette(palette_name)
                if cat_pal and cat_pal.get("colors"):
                    renderer = _build_categorized_renderer(field_name, cat_pal["colors"])
                    vlayer.setRenderer(renderer)
                    renderer_applied = True
                    print(f"  styled: {display_name} — categorized on '{field_name}' "
                          f"({len(cat_pal['colors'])} categories, "
                          f"palette={palette_name})")

            # ── Step 2: Try style sidecar ──
            if not renderer_applied:
                sidecar = _find_style_sidecar(style_path, stem)

                if sidecar:
                    cat_map = sidecar.get("categorical_map")
                    if cat_map:
                        # Only apply categorical sidecar if the layer actually has
                        # a field containing these category values.
                        sidecar_field = sidecar.get("field", stem)
                        category_labels = list(cat_map.keys())
                        field = _resolve_category_field(
                            str(abs_gpkg), stem, sidecar_field, category_labels,
                        )
                        if field is not None:
                            if field != sidecar_field:
                                print(f"  sidecar field '{sidecar_field}' doesn't hold "
                                      f"categories, resolved to '{field}'")
                            renderer = _build_categorized_renderer(field, cat_map)
                            vlayer.setRenderer(renderer)
                            renderer_applied = True
                            print(f"  styled: {display_name} — categorized on '{field}' "
                                  f"({len(cat_map)} categories, from sidecar)")
                        else:
                            print(f"  skipped categorical sidecar for {display_name} — "
                                  f"no field holds categories like '{category_labels[0]}'")

                    if not renderer_applied and sidecar.get("colors_rgb") and sidecar.get("field"):
                        field = sidecar["field"]
                        breaks = sidecar.get("breaks")
                        if not breaks:
                            values = _read_values(str(abs_gpkg), stem, field)
                            if values:
                                k = sidecar.get("k", 5)
                                scheme = sidecar.get("scheme", "natural_breaks")
                                breaks = compute_breaks(values, k, scheme)

                        if breaks:
                            renderer = _build_graduated_renderer(
                                vlayer, field, sidecar["colors_rgb"],
                                method=sidecar.get("scheme", "natural_breaks"),
                                k=sidecar.get("k", 5),
                                breaks=breaks,
                            )
                            vlayer.setRenderer(renderer)
                            renderer_applied = True
                            print(f"  styled: {display_name} — graduated on '{field}' "
                                  f"({sidecar.get('scheme', 'natural_breaks')}, from sidecar)")

            # ── Step 3: Auto-introspect for numeric thematic field ──
            if not renderer_applied and geom_type == "Polygon":
                info = _introspect_gpkg(str(abs_gpkg), stem)
                thematic = info.get("thematic_field")
                if thematic:
                    field_name = thematic["name"]
                    palette = resolve_palette(field_name)
                    values = _read_values(str(abs_gpkg), stem, field_name)
                    if values:
                        k = palette.get("k", 5)
                        scheme = palette.get("scheme", "natural_breaks")
                        breaks = compute_breaks(values, k, scheme)
                        colors = get_rgb_ramp(palette.get("cmap", "viridis"), len(breaks) - 1)
                        renderer = _build_graduated_renderer(
                            vlayer, field_name, colors,
                            method=scheme, k=k, breaks=breaks,
                        )
                        vlayer.setRenderer(renderer)
                        renderer_applied = True
                        print(f"  styled: {display_name} — graduated on '{field_name}' "
                              f"({scheme}, auto-detected, palette={palette.get('name', '?')})")

            if not renderer_applied:
                symbol = _build_single_renderer(geom_type)
                vlayer.renderer().setSymbol(symbol)
                print(f"  styled: {display_name} — single symbol")

            # Add layer to project and group
            project.addMapLayer(vlayer, False)
            analysis_group.addLayer(vlayer)
            layer_count += 1

            # Track extent
            ext = vlayer.extent()
            if ext and not ext.isEmpty():
                if combined_extent is None:
                    combined_extent = QgsRectangle(ext)
                else:
                    combined_extent.combineExtentWith(ext)

            print(f"  added: {display_name} ({vlayer.featureCount()} features)")

        if layer_count == 0:
            raise ValueError(f"No layers loaded (filter={layer_names})")

        # Add basemap
        if basemap and basemap != "none":
            bm_layer = _add_basemap(project, basemap)
            if bm_layer:
                project.addMapLayer(bm_layer, False)
                basemap_group = root.addGroup("Basemap")
                basemap_group.addLayer(bm_layer)
                print(f"  added basemap: {BASEMAP_NAMES.get(basemap, basemap)}")

        # Set view extent with 5% padding
        if combined_extent and not combined_extent.isEmpty():
            w = combined_extent.width() * 0.05
            h = combined_extent.height() * 0.05
            combined_extent.grow(max(w, h))
            view = project.viewSettings()
            ref_extent = QgsReferencedRectangle(combined_extent, project_crs)
            view.setDefaultViewExtent(ref_extent)

        # Write project
        project.write(str(out_path.resolve()))

        # Post-process: rewrite absolute paths as relative for portability
        abs_dir = str(out_dir.resolve())
        qgs_text = out_path.read_text()
        qgs_text = qgs_text.replace(abs_dir + "/", "./")
        qgs_text = qgs_text.replace(abs_dir, ".")
        out_path.write_text(qgs_text)

        try:
            rel = out_path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = out_path
        print(f"\nwrote QGIS project -> {rel}")
        print(f"  title:   {title}")
        print(f"  CRS:     EPSG:{crs_epsg}")
        print(f"  layers:  {layer_count}")

        return out_path

    finally:
        qgs.exitQgis()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a styled QGIS .qgs project file (PyQGIS headless)."
    )
    parser.add_argument("--gpkg", nargs="+", required=True,
                        help="GeoPackage file(s), relative to output dir")
    parser.add_argument("--title", default="GIS Review Project", help="Project title")
    parser.add_argument("--layers", nargs="*", help="Filter: layer names to include (stems)")
    parser.add_argument("--crs", type=int, default=4269, help="Project CRS EPSG (default: 4269)")
    parser.add_argument("--basemap", default="carto-light",
                        choices=["osm", "carto-light", "carto-dark", "none"],
                        help="Basemap tile layer (default: carto-light)")
    parser.add_argument("--style-dir", help="Directory to search for .style.json sidecars")
    parser.add_argument("-o", "--output", required=True, help="Output .qgs path")
    args = parser.parse_args()

    build_qgs_from_gpkg(
        gpkg_paths=args.gpkg,
        title=args.title,
        output_path=args.output,
        layer_names=args.layers,
        crs_epsg=args.crs,
        basemap=args.basemap,
        style_dir=args.style_dir,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
