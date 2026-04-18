"""Package upstream outputs into a portable, styled ArcGIS Pro review folder.

Mirrors `package_qgis_review.py`. Produces `outputs/arcgis/` with:
  - data/project.gdb — file geodatabase (written via GDAL OpenFileGDB; no Esri license required)
  - layers/<name>.lyrx — one styled layer file per map (drag into any Pro project)
  - review-spec.json — machine-readable layer introspection
  - review-notes.md — field coverage + styling summary + how-to
  - manifest.json — file inventory
  - README.md — two load paths (Pro UI drag-drop and arcpy helper script)
  - make_aprx.py — helper Python script to auto-build .aprx inside Pro
  - <slug>.aprx — full ArcGIS Pro project, ONLY when arcpy is detected on
    the machine producing the package

Charts produced by the Cartography stage are copied into arcgis/charts/
so report layouts inside Pro can reference them.

Design notes:
  - No arcpy dependency on the OSS path. GDAL/Fiona's OpenFileGDB driver
    handles .gdb creation. ArcGIS Pro 3.x reads this without complaint.
  - The .lyrx format is pure JSON (Esri CIM schema); see lyrx_writer.py.
  - If arcpy *is* available (building this package from inside Pro),
    we additionally save a genuine .aprx via `aprx_scaffold.py`.

Usage:
    python scripts/core/package_arcgis_pro.py analyses/my-analysis/ \\
        --title "My Analysis" \\
        --data-files data/processed/tracts.gpkg \\
        --style-dir outputs/maps/ \\
        --charts-dir outputs/charts/
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import datetime as _dt_datetime, UTC as _dt_UTC  # aliased to survive `import arcpy` rebinding
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from lyrx_writer import write_lyrx
from aprx_scaffold import (
    arcpy_available,
    build_aprx_with_arcpy,
    write_make_aprx_helper,
)


TEMPLATE_APRX = PROJECT_ROOT / "templates" / "arcgis" / "project_template.aprx"


def _gpkg_layers(gpkg_path: Path) -> list[tuple[str, int]]:
    """Return [(layer_name, feature_count), ...] for a GeoPackage."""
    out: list[tuple[str, int]] = []
    try:
        conn = sqlite3.connect(str(gpkg_path))
        rows = conn.execute(
            "SELECT table_name FROM gpkg_contents WHERE data_type='features'"
        ).fetchall()
        for (table_name,) in rows:
            try:
                cnt = conn.execute(
                    f'SELECT count(*) FROM "{table_name}"'
                ).fetchone()[0]
            except sqlite3.DatabaseError:
                cnt = -1
            out.append((table_name, int(cnt)))
        conn.close()
    except sqlite3.DatabaseError as exc:
        raise RuntimeError(f"Not a valid GeoPackage: {gpkg_path} ({exc})")
    return out


def _copy_gpkg_to_gdb(
    gpkg_path: Path, gdb_path: Path, layer_names: Iterable[str],
) -> list[tuple[str, int]]:
    """Copy each layer from a GPKG into a File Geodatabase.

    Returns [(fc_name, feature_count), ...]. Two write paths, chosen by which
    libraries are available in the interpreter:

    - **arcpy path** — used when running under Pro's `arcgispro-py3` env. That
      env has arcpy but (by default) not fiona. Uses `arcpy.conversion.FeatureClassToFeatureClass`.
    - **fiona path** — used under the project venv. Uses the OpenFileGDB
      driver bundled with Fiona/pyogrio + GDAL 3.6+. No Esri license needed.
    """
    try:
        import arcpy  # noqa: F401 — presence check only
        return _copy_gpkg_to_gdb_arcpy(gpkg_path, gdb_path, layer_names)
    except ImportError:
        return _copy_gpkg_to_gdb_fiona(gpkg_path, gdb_path, layer_names)


def _copy_gpkg_to_gdb_arcpy(
    gpkg_path: Path, gdb_path: Path, layer_names: Iterable[str],
) -> list[tuple[str, int]]:
    """GDB write path using arcpy. Used when running under Pro's Python."""
    import arcpy

    if not gdb_path.exists():
        arcpy.management.CreateFileGDB(str(gdb_path.parent), gdb_path.name)

    written: list[tuple[str, int]] = []
    for layer in layer_names:
        fc_name = _sanitize_fc_name(layer)
        # arcpy reads GeoPackages via the main.<layer> OpenFileGDB-driver
        # feature class notation.
        src = f"{gpkg_path}\\main.{layer}"
        arcpy.conversion.FeatureClassToFeatureClass(
            in_features=src,
            out_path=str(gdb_path),
            out_name=fc_name,
        )
        count = int(arcpy.management.GetCount(str(gdb_path / fc_name))[0])
        written.append((fc_name, count))
    return written


def _copy_gpkg_to_gdb_fiona(
    gpkg_path: Path, gdb_path: Path, layer_names: Iterable[str],
) -> list[tuple[str, int]]:
    """GDB write path using fiona + geopandas. Used under the project venv."""
    import fiona
    fiona.supported_drivers["OpenFileGDB"] = "rw"
    import geopandas as gpd

    written: list[tuple[str, int]] = []
    for layer in layer_names:
        gdf = gpd.read_file(gpkg_path, layer=layer)
        fc_name = _sanitize_fc_name(layer)
        gdf.to_file(gdb_path, layer=fc_name, driver="OpenFileGDB")
        written.append((fc_name, int(len(gdf))))
    return written


def _sanitize_fc_name(name: str) -> str:
    """File geodatabase feature class names can't start with a digit and
    may only contain letters, digits, and underscores."""
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    if safe and safe[0].isdigit():
        safe = "fc_" + safe
    return safe or "layer"


def _first_sidecar_attribution(style_dir: Path | None) -> str | None:
    """Scan sidecars for a source attribution line — used as the fallback
    attribution on the arcpy layout.
    """
    if not style_dir or not style_dir.exists():
        return None
    for sc in style_dir.glob("*.style.json"):
        data = None
        try:
            data = json.loads(sc.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data and data.get("attribution"):
            return str(data["attribution"])
    return None


def _sidecar_source_stem(data: dict) -> str | None:
    """Extract the source gpkg stem a sidecar points at, if any.

    Cartography scripts write one of two keys depending on vintage / author:
      - ``source_gpkg`` — full path to the gpkg the map was rendered from
      - ``source_layer`` — gpkg-relative or absolute path (one-off helpers)

    Either way the useful bit is ``Path(value).stem``.
    """
    for key in ("source_gpkg", "source_layer"):
        val = data.get(key)
        if val:
            # Tolerate both '/' and '\\' separators; Path handles either on nt.
            return Path(str(val).replace("\\", "/")).stem
    return None


def _plan_lyrx_from_sidecars(
    style_dir: Path,
    all_layers: list[tuple[Path, str, int]],
    layer_fields: dict[str, set[str]],
) -> tuple[list[dict], list[str]]:
    """Plan which sidecar styles which feature class.

    Returns ``(plans, warnings)`` where each ``plan`` is a dict:
        {"sidecar": Path, "fc": str, "data": dict, "match_via": str}

    Matching order:
      1. ``source_gpkg`` / ``source_layer`` stem (sanitized) == feature class
      2. sidecar's ``field`` exists as a column on some feature class
      3. sidecar has a ``categorical_map`` and one of its category columns
         exists on some feature class

    We iterate sidecars (not feature classes) because sidecars are named
    after MAPS (``poverty_rate_choropleth.style.json``) while feature
    classes are named after SOURCE DATA (``phila_tracts_enriched``).
    There's no common name to match on — the sidecar has to declare its
    target. All cartography scripts now write ``source_gpkg``; the helpers
    at ``_scripts/`` write ``source_layer``.
    """
    plans: list[dict] = []
    warnings: list[str] = []
    fc_by_name = {fc: idx for idx, (_g, fc, _c) in enumerate(all_layers)}

    for sc in sorted(style_dir.glob("*.style.json")):
        try:
            data = json.loads(sc.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"sidecar unreadable: {sc.name} ({exc})")
            continue

        # 1. explicit source pointer
        src_stem = _sidecar_source_stem(data)
        if src_stem:
            fc_guess = _sanitize_fc_name(src_stem)
            if fc_guess in fc_by_name:
                plans.append({
                    "sidecar": sc, "fc": fc_guess, "data": data,
                    "match_via": "source_gpkg/source_layer",
                })
                continue

        # 2. field-column presence
        field = data.get("field")
        if field:
            field_hits = [fc for fc, cols in layer_fields.items() if field in cols]
            if len(field_hits) == 1:
                plans.append({
                    "sidecar": sc, "fc": field_hits[0], "data": data,
                    "match_via": f"field='{field}'",
                })
                continue
            elif len(field_hits) > 1:
                # Ambiguous — skip rather than guess and apply to the wrong FC.
                warnings.append(
                    f"sidecar {sc.name}: field '{field}' present on "
                    f"{len(field_hits)} feature classes ({field_hits}); "
                    f"set 'source_gpkg' in the sidecar to disambiguate"
                )
                continue

        # 3. Categorical fallback — ONLY when the sidecar has no field set but
        #    does have a categorical_map. This is narrow on purpose: if a
        #    sidecar names a specific field (even a wrong one), we honor it or
        #    skip rather than guess a different column. Producing a styled
        #    .lyrx pointed at the wrong column is worse than producing none.
        cat_map = data.get("categorical_map") or data.get("categories")
        if cat_map and not field:
            category_cols = {"hotspot_class", "lisa_cluster", "cluster", "class"}
            match = next(
                ((fc, next(iter(category_cols & cols)))
                 for fc, cols in layer_fields.items()
                 if category_cols & cols),
                None,
            )
            if match:
                plans.append({
                    "sidecar": sc, "fc": match[0], "data": data,
                    "match_via": f"category column '{match[1]}'",
                })
                continue
            warnings.append(
                f"sidecar {sc.name}: categorical sidecar with no field set "
                f"and no feature class has a recognized category column "
                f"({sorted(category_cols)})"
            )
            continue

        if field:
            warnings.append(
                f"sidecar {sc.name}: field '{field}' is not a column on any "
                f"feature class in the package; set 'source_gpkg' in the "
                f"sidecar or include the data file"
            )
        else:
            warnings.append(
                f"sidecar {sc.name}: no source_gpkg, no field, no "
                f"categorical_map \u2014 can't resolve a target feature class"
            )
    return plans, warnings


def _write_review_notes(
    out_dir: Path,
    title: str,
    gdb_rel: Path,
    gpkg_copies: list[Path],
    layer_entries: list[dict],
    lyrx_entries: list[dict],
) -> Path:
    lines = [
        f"# ArcGIS Pro Review — {title}\n",
        f"Generated: {_dt_datetime.now(_dt_UTC).strftime('%Y-%m-%d %H:%M UTC')}\n",
        "",
        "## Data\n",
        f"- File geodatabase: `{gdb_rel}`",
    ]
    for (fc, count) in layer_entries:
        lines.append(f"  - `{fc}` — {count:,} features")
    if gpkg_copies:
        lines.append("- Source GeoPackages (included for reference):")
        for p in gpkg_copies:
            lines.append(f"  - `{p}`")

    lines += ["", "## Styled layers (.lyrx)\n"]
    if not lyrx_entries:
        lines.append("_No .lyrx files generated (no style sidecars found)._")
    for entry in lyrx_entries:
        lines.append(
            f"- `{entry['lyrx']}` — source layer `{entry['layer']}`"
            f"{', palette=' + entry['palette'] if entry.get('palette') else ''}"
            f"{', breaks=' + str(entry['breaks']) if entry.get('breaks') else ''}"
        )

    lines += [
        "",
        "## Load into ArcGIS Pro\n",
        "**Option A — drag-and-drop (easiest):**",
        "1. Open ArcGIS Pro and create or open any project.",
        "2. In the *Catalog* pane, browse to this folder.",
        f"3. Drag each `.lyrx` from `layers/` onto your map. Each layer loads already styled.",
        "4. The underlying data is `data/project.gdb`; layers reference it relatively.",
        "",
        "**Option B — one-shot helper:**",
        "1. Open ArcGIS Pro, open a new or existing project, show the *Python* window.",
        "2. Drag `make_aprx.py` from this folder into the Python window and run it.",
        "3. A ready-to-share `.aprx` is saved next to `make_aprx.py`.",
        "",
        "## What to look for\n",
        "1. **Symbology** — each layer should render with the same palette as the static maps in `../maps/`.",
        "2. **Field coverage** — check the review-spec for low-coverage fields.",
        "3. **CRS** — the .gdb preserves the source CRS; re-project inside Pro if needed.",
        "4. **Charts** — any SVGs in `charts/` can be embedded in layout frames.",
        "",
    ]
    path = out_dir / "review-notes.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def package_arcgis_pro(
    analysis_dir: Path,
    *,
    analysis_title: str,
    gpkg_files: list[Path],
    style_dir: Path | None = None,
    charts_dir: Path | None = None,
    include_gpkg_copies: bool = True,
) -> dict:
    """Produce `outputs/arcgis/` for the analysis.

    Returns a summary dict.
    """
    out_dir = analysis_dir / "outputs" / "arcgis"
    data_dir = out_dir / "data"
    layers_dir = out_dir / "layers"
    charts_out = out_dir / "charts"
    for d in (out_dir, data_dir, layers_dir):
        d.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Build the file geodatabase
    gdb_path = data_dir / "project.gdb"
    if gdb_path.exists():
        shutil.rmtree(gdb_path)

    all_layers: list[tuple[Path, str, int]] = []   # (gpkg, fc_name, count)
    for gpkg in gpkg_files:
        if not gpkg.exists():
            errors.append(f"source gpkg not found: {gpkg}")
            continue
        try:
            layers = _gpkg_layers(gpkg)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        if not layers:
            warnings.append(f"no feature layers in {gpkg.name}")
            continue
        try:
            written = _copy_gpkg_to_gdb(gpkg, gdb_path, [ln for ln, _ in layers])
        except Exception as exc:
            errors.append(f"gdb write failed for {gpkg.name}: {exc}")
            continue
        for (fc_name, count) in written:
            all_layers.append((gpkg, fc_name, count))

    if include_gpkg_copies:
        gpkg_copy_rels: list[Path] = []
        for gpkg in gpkg_files:
            if gpkg.exists():
                dest = data_dir / gpkg.name
                shutil.copy2(gpkg, dest)
                gpkg_copy_rels.append(Path("data") / gpkg.name)
    else:
        gpkg_copy_rels = []

    # 2. Write .lyrx per styled map — sidecar-driven.
    #
    # Sidecars are named after MAPS (poverty_rate_choropleth.style.json),
    # feature classes are named after SOURCE DATA (phila_tracts_enriched).
    # Match by sidecar.source_gpkg stem → FC name, falling back to field
    # presence on the FC column set. See _plan_lyrx_from_sidecars.
    lyrx_entries: list[dict] = []
    lyrx_paths: list[Path] = []

    if style_dir and Path(style_dir).exists():
        # Pre-read column sets for each feature class. We read from the
        # source GPKG (not the GDB) because sqlite3 can open gpkgs anywhere
        # without fiona/gdal; the column set is identical either way.
        layer_fields: dict[str, set[str]] = {}
        for (gpkg, fc_name, _count) in all_layers:
            try:
                conn = sqlite3.connect(str(gpkg))
                # The FC was sanitized from the original gpkg layer name,
                # but the column list is unchanged. Use the original layer
                # name for the PRAGMA (gpkg side), key the dict by fc_name
                # (gdb side).
                src_layer = gpkg.stem
                cols = {r[1] for r in conn.execute(
                    f'PRAGMA table_info("{src_layer}")'
                )}
                conn.close()
                layer_fields[fc_name] = cols
            except sqlite3.DatabaseError:
                layer_fields[fc_name] = set()

        plans, plan_warnings = _plan_lyrx_from_sidecars(
            Path(style_dir), all_layers, layer_fields,
        )
        warnings.extend(plan_warnings)

        for plan in plans:
            sidecar: Path = plan["sidecar"]
            fc_name: str = plan["fc"]
            sc_data: dict = plan["data"]
            lyrx_name = sidecar.stem.replace(".style", "") + ".lyrx"
            lyrx_path = layers_dir / lyrx_name
            try:
                write_lyrx(
                    sidecar_path=sidecar,
                    data_path=str(Path("..") / "data" / "project.gdb"),
                    layer_name=fc_name,
                    output=lyrx_path,
                    workspace_type="OpenFileGDB",
                    lyrx_name=sc_data.get("title") or sidecar.stem,
                )
            except Exception as exc:
                warnings.append(
                    f"lyrx generation failed for {sidecar.name} \u2192 {fc_name}: {exc}"
                )
                continue
            lyrx_paths.append(lyrx_path)
            lyrx_entries.append({
                "lyrx": str(lyrx_path.relative_to(out_dir)),
                "layer": fc_name,
                "sidecar": str(sidecar),
                "match_via": plan["match_via"],
                "palette": sc_data.get("palette"),
                "breaks": sc_data.get("breaks"),
            })

        matched_fcs = {p["fc"] for p in plans}
        for (_g, fc, _c) in all_layers:
            if fc not in matched_fcs:
                warnings.append(
                    f"no sidecar matched feature class '{fc}' \u2014 no .lyrx produced"
                )
    else:
        warnings.append("no style-dir provided; skipping .lyrx generation")

    # 3. Copy charts if provided
    copied_charts: list[str] = []
    if charts_dir and Path(charts_dir).exists():
        charts_out.mkdir(exist_ok=True)
        for pattern in ("*.png", "*.svg", "*.style.json"):
            for f in Path(charts_dir).glob(pattern):
                dest = charts_out / f.name
                shutil.copy2(f, dest)
                copied_charts.append(str(dest.relative_to(out_dir)))

    # 4. review-spec.json
    review_spec = {
        "version": "1.0",
        "title": analysis_title,
        "generated_at": _dt_datetime.now(_dt_UTC).isoformat(),
        "gdb": "data/project.gdb",
        "layers": [
            {
                "fc_name": fc,
                "source_gpkg": gpkg.name,
                "feature_count": count,
            }
            for (gpkg, fc, count) in all_layers
        ],
        "lyrx_layers": lyrx_entries,
        "charts_copied": copied_charts,
    }
    (out_dir / "review-spec.json").write_text(json.dumps(review_spec, indent=2), encoding="utf-8")

    # 5. review-notes.md
    layer_entries = [(fc, count) for (_g, fc, count) in all_layers]
    _write_review_notes(
        out_dir, analysis_title,
        Path("data/project.gdb"),
        gpkg_copy_rels,
        layer_entries,
        lyrx_entries,
    )

    # 6. make_aprx.py helper
    slug = analysis_dir.name.replace("-", "_")
    output_aprx = out_dir / f"{slug}.aprx"
    helper = out_dir / "make_aprx.py"
    if lyrx_paths:
        write_make_aprx_helper(
            output_py=helper,
            title=analysis_title,
            gdb_path=gdb_path,
            lyrx_files=lyrx_paths,
            output_aprx=output_aprx,
        )

    # 7. Optional arcpy-built .aprx (when producing from inside ArcGIS Pro)
    aprx_built = False
    aprx_layout_enhanced = False
    aprx_attribution = _first_sidecar_attribution(Path(style_dir) if style_dir else None)
    if arcpy_available() and lyrx_paths and TEMPLATE_APRX.exists():
        try:
            build_result = build_aprx_with_arcpy(
                template_aprx=TEMPLATE_APRX,
                output_aprx=output_aprx,
                title=analysis_title,
                gdb_path=gdb_path,
                lyrx_files=lyrx_paths,
                attribution=aprx_attribution,
            )
            aprx_built = True
            aprx_layout_enhanced = bool(build_result.get("layout_enhanced"))
            for w in build_result.get("warnings", []):
                warnings.append(f"arcpy: {w}")
        except Exception as exc:
            warnings.append(f"arcpy .aprx build failed: {exc}")
    elif arcpy_available() and not TEMPLATE_APRX.exists():
        warnings.append(
            f"arcpy detected but template not found at {TEMPLATE_APRX.relative_to(PROJECT_ROOT)} "
            "— run templates/arcgis/bootstrap_template.py from inside Pro once to create it, "
            "then re-package. In the meantime, make_aprx.py works."
        )

    # 8. README
    readme_lines = [
        f"# {analysis_title} — ArcGIS Pro Package\n",
        f"Self-contained ArcGIS Pro review package for `{analysis_dir.name}`.\n",
        "## What's inside\n",
        "- `data/project.gdb` — file geodatabase with all analysis layers",
        "- `layers/*.lyrx` — styled layer files, one per thematic map",
        "- `charts/` — statistical charts (PNG + SVG) for layout embedding" if copied_charts else "",
        "- `review-spec.json` — machine-readable layer introspection",
        "- `review-notes.md` — field coverage and load instructions",
        "- `manifest.json` — file inventory with sizes",
        "- `make_aprx.py` — one-click helper to build `.aprx` inside Pro" if lyrx_paths else "",
        f"- `{output_aprx.name}` — ArcGIS Pro project" if aprx_built else "",
        "",
        "## Quick start\n",
        "**Easiest:** drag any `.lyrx` from `layers/` into an open ArcGIS Pro map. Layer loads pre-styled.",
        "",
        "**Build a full project:** from inside ArcGIS Pro, open the Python window and run `make_aprx.py`.",
        "",
        "## Requirements\n",
        "- ArcGIS Pro 3.1 or newer (reads the included CIM schema 3.1.0)",
        "- No arcpy required to *consume* this package — only to rebuild the .aprx.",
        "",
        f"---\n*Generated {_dt_datetime.now(_dt_UTC).strftime('%Y-%m-%d')} by spatial-machines*\n",
    ]
    (out_dir / "README.md").write_text("\n".join(l for l in readme_lines if l), encoding="utf-8")

    # 9. manifest
    all_files = []
    total_size = 0
    for f in out_dir.rglob("*"):
        if f.is_file() and f.name != "manifest.json":
            size = f.stat().st_size
            total_size += size
            rel = f.relative_to(out_dir)
            cat = (
                "data" if str(rel).startswith("data/")
                else "layer" if rel.suffix == ".lyrx"
                else "chart" if str(rel).startswith("charts/")
                else "project" if rel.suffix == ".aprx"
                else "script" if rel.suffix == ".py"
                else "documentation"
            )
            all_files.append({"path": str(rel), "size_bytes": size, "category": cat})

    manifest = {
        "package_name": analysis_dir.name,
        "title": analysis_title,
        "created_at": _dt_datetime.now(_dt_UTC).isoformat(),
        "total_files": len(all_files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "files": all_files,
        "arcpy_built_aprx": aprx_built,
        "warnings": warnings,
        "errors": errors,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "status": "ok" if not errors else "partial" if lyrx_entries or all_layers else "error",
        "gdb": str((data_dir / "project.gdb").relative_to(analysis_dir)),
        "layer_count": len(all_layers),
        "lyrx_count": len(lyrx_entries),
        "chart_count": len(copied_charts),
        "aprx_built": aprx_built,
        "aprx_layout_enhanced": aprx_layout_enhanced,
        "size_mb": round(total_size / (1024 * 1024), 2),
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Package outputs into a portable ArcGIS Pro review folder."
    )
    p.add_argument("analysis_dir")
    p.add_argument("--title", default="GIS Review Project")
    p.add_argument("--data-files", nargs="+", required=True,
                   help="GeoPackage files to include")
    p.add_argument("--style-dir",
                   help="Directory with .style.json sidecars from cartography")
    p.add_argument("--charts-dir",
                   help="Directory with chart PNG/SVG/sidecars to embed")
    p.add_argument("--no-gpkg-copies", action="store_true",
                   help="Don't copy source GeoPackages into data/ (smaller package)")
    args = p.parse_args()

    analysis_dir = Path(args.analysis_dir).resolve()
    gpkgs = [Path(f).resolve() for f in args.data_files]

    result = package_arcgis_pro(
        analysis_dir=analysis_dir,
        analysis_title=args.title,
        gpkg_files=gpkgs,
        style_dir=Path(args.style_dir) if args.style_dir else None,
        charts_dir=Path(args.charts_dir) if args.charts_dir else None,
        include_gpkg_copies=not args.no_gpkg_copies,
    )

    print(f"=== ArcGIS Pro Package: {analysis_dir.name} ===")
    print(f"  status:      {result['status']}")
    print(f"  gdb:         {result.get('gdb', 'N/A')}")
    print(f"  layers:      {result['layer_count']}")
    print(f"  lyrx:        {result['lyrx_count']}")
    print(f"  charts:      {result['chart_count']}")
    print(f"  aprx built:  {result['aprx_built']}"
          + (" (layout enhanced)" if result.get("aprx_layout_enhanced") else ""))
    print(f"  size:        {result['size_mb']} MB")
    for w in result.get("warnings", []):
        print(f"  WARN: {w}")
    for e in result.get("errors", []):
        print(f"  ERROR: {e}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
