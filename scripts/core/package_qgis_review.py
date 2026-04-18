"""Package upstream outputs into a portable, styled QGIS review folder.

Creates outputs/qgis/ with:
  - data/ subfolder with GeoPackage copies
  - Styled .qgs project file (graduated renderers, basemap, auto-zoom)
  - review-spec.json (field classification, thematic field, symbology)
  - review-notes.md (validation status, field coverage, what to look for)
  - manifest.json (file inventory with sizes)
  - README.md (how to open and use)

Usage:
    python scripts/core/package_qgis_review.py analyses/my-analysis/ \\
        --title "My Analysis" \\
        --data-files data/processed/tracts.gpkg \\
        --style-dir outputs/maps/
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_CORE))

from style_utils import classify_field, NUMERIC_TYPES


def _introspect_for_review_spec(gpkg_path: Path, layer_name: str) -> dict:
    """Build a review spec entry from a GeoPackage layer."""
    spec = {"gpkg": gpkg_path.name, "layer_name": layer_name, "fields": []}
    try:
        conn = sqlite3.connect(str(gpkg_path))
        cols = conn.execute(f'PRAGMA table_info("{layer_name}")').fetchall()
        row_count = conn.execute(f'SELECT count(*) FROM "{layer_name}"').fetchone()[0]
        spec["feature_count"] = row_count

        for col in cols:
            cid, name, ctype, notnull, default, pk = col
            role = classify_field(name, ctype)
            if role == "geometry":
                continue
            info = {"name": name, "type": ctype, "role": role}
            if ctype.upper().split("(")[0].strip() in NUMERIC_TYPES:
                try:
                    stats = conn.execute(
                        f'SELECT count("{name}"), min("{name}"), max("{name}"), avg("{name}") '
                        f'FROM "{layer_name}" WHERE "{name}" IS NOT NULL'
                    ).fetchone()
                    info["non_null_count"] = stats[0]
                    info["null_count"] = row_count - stats[0]
                    info["coverage_pct"] = round(100 * stats[0] / row_count, 1) if row_count else 0
                    info["min"] = stats[1]
                    info["max"] = stats[2]
                    info["mean"] = round(stats[3], 4) if stats[3] is not None else None
                except Exception:
                    pass
            else:
                try:
                    nn = conn.execute(f'SELECT count("{name}") FROM "{layer_name}" WHERE "{name}" IS NOT NULL').fetchone()[0]
                    info["non_null_count"] = nn
                    info["coverage_pct"] = round(100 * nn / row_count, 1) if row_count else 0
                except Exception:
                    pass
            spec["fields"].append(info)

        # Extent
        try:
            ext = conn.execute(
                'SELECT min_x, min_y, max_x, max_y FROM gpkg_contents WHERE table_name=?',
                (layer_name,)
            ).fetchone()
            if ext and all(e is not None for e in ext):
                spec["extent"] = {"xmin": ext[0], "ymin": ext[1], "xmax": ext[2], "ymax": ext[3]}
        except Exception:
            pass

        # SRS
        try:
            srs = conn.execute(
                'SELECT srs_id FROM gpkg_contents WHERE table_name=?', (layer_name,)
            ).fetchone()
            if srs:
                spec["srs_id"] = srs[0]
        except Exception:
            pass

        conn.close()
    except Exception as e:
        spec["introspection_error"] = str(e)
    return spec


def _write_review_notes(
    qgis_dir: Path,
    title: str,
    specs: list[dict],
    style_sidecars: list[dict],
) -> Path:
    """Generate review-notes.md with field coverage and guidance."""
    lines = [
        f"# Review Notes — {title}\n",
        f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n",
        "",
        "## Layers\n",
    ]

    for spec in specs:
        fc = spec.get("feature_count", "?")
        srs = spec.get("srs_id", "unknown")
        lines.append(f"### {spec['layer_name']} ({fc} features, EPSG:{srs})\n")

        if spec.get("fields"):
            lines.append("| Field | Type | Role | Coverage | Min | Max |")
            lines.append("|---|---|---|---|---|---|")
            for f in spec["fields"]:
                cov = f"{f.get('coverage_pct', '?')}%" if 'coverage_pct' in f else "?"
                fmin = f.get("min", "")
                fmax = f.get("max", "")
                if isinstance(fmin, float):
                    fmin = f"{fmin:.2f}"
                if isinstance(fmax, float):
                    fmax = f"{fmax:.2f}"
                lines.append(f"| {f['name']} | {f['type']} | {f['role']} | {cov} | {fmin} | {fmax} |")
            lines.append("")

    if style_sidecars:
        lines.append("## Styling Applied\n")
        for sc in style_sidecars:
            field = sc.get("field", "N/A")
            palette = sc.get("palette", "N/A")
            scheme = sc.get("scheme", "N/A")
            lines.append(f"- **{field}**: palette={palette}, classification={scheme}")
        lines.append("")

    lines.extend([
        "## What to Look For\n",
        "1. **Geometry quality** — are polygons rendering cleanly without gaps or overlaps?",
        "2. **Field completeness** — check the coverage column above for any low-coverage fields",
        "3. **Thematic consistency** — does the graduated color pattern match expectations?",
        "4. **Spatial extent** — is the full study area represented without unexpected gaps?",
        "5. **Outliers** — are there extreme values that dominate the color ramp?",
        "",
    ])

    notes_path = qgis_dir / "review-notes.md"
    notes_path.write_text("\n".join(lines), encoding="utf-8")
    return notes_path


def package_qgis(
    analysis_dir: Path,
    analysis_name: str,
    analysis_title: str,
    gpkg_files: list[Path],
    crs_epsg: int = 4269,
    style_dir: Path | None = None,
    basemap: str = "carto-light",
) -> dict:
    """Package gpkg files into outputs/qgis/ with styled .qgs, review-spec, notes, manifest."""
    from qgis_env import build_qgs_hybrid

    qgis_dir = analysis_dir / "outputs" / "qgis"
    data_dir = qgis_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    errors = []

    for src in gpkg_files:
        if not src.exists():
            errors.append(f"source not found: {src}")
            continue
        dest = data_dir / src.name
        shutil.copy2(src, dest)
        copied.append(dest)

    if not copied:
        errors.append("no gpkg files copied")
        return {"status": "error", "errors": errors, "files": 0}

    # Generate styled .qgs — hybrid: in-process PyQGIS if available,
    # else subprocess via an external QGIS python (OSGeo4W / standalone).
    slug = analysis_dir.name.replace("-", "_")
    qgs_path = qgis_dir / f"{slug}.qgs"
    rel_gpkg_paths = [Path("data") / f.name for f in copied]

    qgs_result = build_qgs_hybrid(
        gpkg_paths=rel_gpkg_paths,
        title=analysis_title,
        output_path=qgs_path,
        crs_epsg=crs_epsg,
        basemap=basemap,
        style_dir=str(style_dir) if style_dir else None,
    )
    if qgs_result["path"] == "failed":
        errors.append(f"qgs generation failed: {qgs_result.get('error')}")

    # Build review-spec.json
    specs = []
    for gpkg in copied:
        spec = _introspect_for_review_spec(gpkg, gpkg.stem)
        specs.append(spec)

    review_spec = {
        "version": "1.0",
        "title": analysis_title,
        "generated_at": datetime.now(UTC).isoformat(),
        "layers": specs,
    }
    spec_path = qgis_dir / "review-spec.json"
    spec_path.write_text(json.dumps(review_spec, indent=2), encoding="utf-8")

    # Load style sidecars if available
    style_sidecars = []
    if style_dir and Path(style_dir).exists():
        for sc_file in Path(style_dir).glob("*.style.json"):
            try:
                style_sidecars.append(json.loads(sc_file.read_text()))
            except Exception:
                pass

    # Generate review-notes.md
    _write_review_notes(qgis_dir, analysis_title, specs, style_sidecars)

    # Generate manifest.json
    all_files = []
    total_size = 0
    for f in qgis_dir.rglob("*"):
        if f.is_file() and f.name != "manifest.json":
            size = f.stat().st_size
            total_size += size
            all_files.append({
                "path": str(f.relative_to(qgis_dir)),
                "size_bytes": size,
                "category": "data" if "data/" in str(f.relative_to(qgis_dir)) else
                           "project" if f.suffix == ".qgs" else "documentation",
            })

    manifest = {
        "package_name": analysis_name,
        "title": analysis_title,
        "created_at": datetime.now(UTC).isoformat(),
        "total_files": len(all_files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "files": all_files,
    }
    manifest_path = qgis_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Write README.md
    readme_path = qgis_dir / "README.md"
    gpkg_list = "\n".join(f"  - `data/{f.name}`" for f in copied)
    readme_path.write_text(
        f"# {analysis_title} — QGIS Package\n\n"
        f"Self-contained QGIS review package for **{analysis_name}**.\n\n"
        f"## How to open\n\n"
        f"1. Open QGIS (>= 3.22)\n"
        f"2. File → Open Project → select `{slug}.qgs`\n"
        f"3. Layers load styled with graduated colors and a basemap\n"
        f"4. Map auto-zooms to the data extent\n\n"
        f"## What's inside\n\n"
        f"- `{slug}.qgs` — Styled QGIS project (graduated renderers, basemap, auto-zoom)\n"
        f"{gpkg_list}\n"
        f"- `review-spec.json` — Machine-readable field classification and stats\n"
        f"- `review-notes.md` — Field coverage table and review guidance\n"
        f"- `manifest.json` — File inventory with sizes\n"
        f"- `README.md` — This file\n\n"
        f"## Styling\n\n"
        f"The project file includes graduated color styling based on the cartography agent's decisions. "
        f"Colors, classification methods, and class breaks match the static maps in `outputs/maps/`.\n\n"
        f"## CRS\n\n"
        f"Project CRS: EPSG:{crs_epsg}\n\n"
        f"---\n"
        f"*Generated {datetime.now(UTC).strftime('%Y-%m-%d')} by spatial-machines*\n",
        encoding="utf-8",
    )

    return {
        "status": "ok" if not errors else "partial",
        "qgs": str(qgs_path.relative_to(analysis_dir)),
        "qgs_exists": qgs_path.exists(),
        "qgs_generation_path": qgs_result["path"],
        "qgs_interpreter": qgs_result.get("interpreter"),
        "files": len(copied),
        "size_mb": round(total_size / (1024 * 1024), 2),
        "review_spec": str(spec_path.relative_to(analysis_dir)),
        "errors": errors,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Package GeoPackage files into a styled QGIS review folder."
    )
    parser.add_argument("analysis_dir", help="Path to the analysis directory")
    parser.add_argument("--title", default="GIS Review Project", help="Project title")
    parser.add_argument("--data-files", nargs="+", required=True, help="GeoPackage files to include")
    parser.add_argument("--crs", type=int, default=4269, help="Project CRS EPSG (default: 4269)")
    parser.add_argument("--style-dir", help="Directory with .style.json sidecars from cartography")
    parser.add_argument("--basemap", default="carto-light",
                        choices=["osm", "carto-light", "carto-dark", "none"],
                        help="Basemap (default: carto-light)")
    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir).resolve()
    gpkg_files = [Path(f).resolve() for f in args.data_files]

    result = package_qgis(
        analysis_dir=analysis_dir,
        analysis_name=analysis_dir.name,
        analysis_title=args.title,
        gpkg_files=gpkg_files,
        crs_epsg=args.crs,
        style_dir=Path(args.style_dir) if args.style_dir else None,
        basemap=args.basemap,
    )

    print(f"=== QGIS Package: {analysis_dir.name} ===")
    print(f"  status:      {result['status']}")
    print(f"  files:       {result['files']} GeoPackages")
    print(f"  size:        {result.get('size_mb', 0)} MB")
    print(f"  project:     {result.get('qgs', 'N/A')}")
    print(f"  qgs built:   {result.get('qgs_exists')} "
          f"(via {result.get('qgs_generation_path', 'unknown')})")
    if result.get('qgs_interpreter') and result.get('qgs_generation_path') == 'subprocess':
        print(f"  interpreter: {result['qgs_interpreter']}")
    print(f"  review-spec: {result.get('review_spec', 'N/A')}")
    if result.get('errors'):
        for e in result['errors']:
            print(f"  ERROR: {e}")

    return 0 if result['status'] == 'ok' else 1


if __name__ == "__main__":
    raise SystemExit(main())
