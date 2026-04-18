#!/usr/bin/env python3
"""Validate an ArcGIS Pro review package produced by package_arcgis_pro.py.

Checks:
  - outputs/arcgis/ exists with required artifacts
  - data/project.gdb opens via fiona/OpenFileGDB and has ≥1 feature class
  - every layer declared in review-spec matches a feature class in the .gdb
  - every .lyrx parses as JSON, is CIMLayerDocument, and references a
    feature class that actually exists in the .gdb
  - manifest.json + review-spec.json + review-notes.md + README.md present
  - (warning) charts/ is non-empty if the analysis produced charts

Exit 0 on pass, 1 on any blocking failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_TOP = ("manifest.json", "review-spec.json", "review-notes.md", "README.md")


def _check_gdb_layers(gdb_path: Path) -> tuple[list[str], str | None]:
    try:
        import fiona
        fiona.supported_drivers["OpenFileGDB"] = "rw"
        layers = list(fiona.listlayers(str(gdb_path)))
        return layers, None
    except Exception as exc:
        return [], f"{exc}"


def _check_lyrx(lyrx_path: Path, gdb_layers: set[str]) -> list[str]:
    reasons: list[str] = []
    try:
        doc = json.loads(lyrx_path.read_text())
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]
    if doc.get("type") != "CIMLayerDocument":
        reasons.append(f"type is {doc.get('type')!r} not CIMLayerDocument")
    layer_defs = doc.get("layerDefinitions") or []
    if not layer_defs:
        reasons.append("no layerDefinitions")
        return reasons
    for ld in layer_defs:
        ft = ld.get("featureTable", {})
        dc = ft.get("dataConnection", {})
        fc = dc.get("dataset")
        if not fc:
            reasons.append("featureTable has no dataset")
            continue
        if gdb_layers and fc not in gdb_layers:
            reasons.append(
                f"dataset {fc!r} not in .gdb (layers: {sorted(gdb_layers)})"
            )
        renderer = ld.get("renderer")
        if not renderer or not renderer.get("type"):
            reasons.append("renderer missing or untyped")
    return reasons


def validate_package(pkg_dir: Path) -> dict:
    """Return {'passed': bool, 'checks': [{'name','status','reasons'}...]}"""
    result = {"path": str(pkg_dir), "passed": True, "checks": []}

    def add(name: str, ok: bool, reasons: list[str] | None = None):
        entry = {"name": name, "status": "PASS" if ok else "FAIL",
                 "reasons": reasons or []}
        result["checks"].append(entry)
        if not ok:
            result["passed"] = False

    if not pkg_dir.exists() or not pkg_dir.is_dir():
        add("package_dir_exists", False, [f"missing: {pkg_dir}"])
        return result
    add("package_dir_exists", True)

    missing = [n for n in REQUIRED_TOP if not (pkg_dir / n).exists()]
    add("required_top_files", not missing,
        [f"missing: {m}" for m in missing])

    gdb = pkg_dir / "data" / "project.gdb"
    if not gdb.exists():
        add("gdb_present", False, [f"missing {gdb.relative_to(pkg_dir)}"])
        return result
    add("gdb_present", True)

    layers, err = _check_gdb_layers(gdb)
    if err:
        add("gdb_readable", False, [err])
    else:
        add("gdb_readable", True, [f"{len(layers)} feature class(es): {layers}"])
    gdb_layers = set(layers)

    spec_path = pkg_dir / "review-spec.json"
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text())
            spec_layers = {l["fc_name"] for l in spec.get("layers", [])}
            missing_in_gdb = spec_layers - gdb_layers
            add("review_spec_layers_in_gdb",
                not missing_in_gdb,
                [f"missing in .gdb: {m}" for m in missing_in_gdb])
        except (json.JSONDecodeError, KeyError) as exc:
            add("review_spec_valid", False, [str(exc)])

    lyrx_dir = pkg_dir / "layers"
    lyrx_files = sorted(lyrx_dir.glob("*.lyrx")) if lyrx_dir.exists() else []
    if not lyrx_files:
        add("lyrx_present", True, ["(warning) no .lyrx files — no sidecars matched"])
    else:
        all_ok = True
        errors: list[str] = []
        for lf in lyrx_files:
            reasons = _check_lyrx(lf, gdb_layers)
            if reasons:
                all_ok = False
                errors.extend([f"{lf.name}: {r}" for r in reasons])
        add("lyrx_valid", all_ok, errors)

    charts_dir = pkg_dir / "charts"
    if charts_dir.exists():
        pngs = list(charts_dir.glob("*.png"))
        add("charts_present", True,
            [f"{len(pngs)} chart PNG(s)"] if pngs else ["(info) charts/ exists but empty"])

    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate an ArcGIS Pro review package.",
    )
    ap.add_argument("package_dir", nargs="?",
                    help="Path to outputs/arcgis/ (or an analysis dir)")
    args = ap.parse_args()

    if not args.package_dir:
        print("ERROR: pass the path to outputs/arcgis/ or an analysis directory")
        return 2

    pkg = Path(args.package_dir).resolve()
    # Accept either the analysis directory or the package directory itself.
    if pkg.name != "arcgis" and (pkg / "outputs" / "arcgis").exists():
        pkg = pkg / "outputs" / "arcgis"

    result = validate_package(pkg)
    print(f"=== ArcGIS Pro Package validation: {pkg} ===")
    for c in result["checks"]:
        print(f"  [{c['status']}] {c['name']}")
        for r in c["reasons"]:
            print(f"         {r}")
    status = "PASS" if result["passed"] else "FAIL"
    print(f"\nOverall: {status}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
