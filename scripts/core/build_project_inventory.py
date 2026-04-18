#!/usr/bin/env python3
"""Build a machine-readable project inventory for reuse-first discovery.

Scans a single analysis directory and writes `inventory.json` at the project root.
The inventory summarizes:
- project metadata
- raw data manifests and inspection sidecars
- processed datasets
- outputs and reports
- handoffs present
- simple reuse hints for lead-analyst / data-retrieval

Usage:
    python build_project_inventory.py --project-dir analyses/my-project
    python build_project_inventory.py --project-dir analyses/my-project --output analyses/my-project/inventory.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def collect_raw_assets(project_dir: Path) -> list[dict]:
    raw_dir = project_dir / "data" / "raw"
    if not raw_dir.exists():
        return []

    manifests = {p.name: p for p in raw_dir.glob("*.manifest.json")}
    inspections = {p.name: p for p in raw_dir.glob("*.inspection.json")}
    sidecars = {p.name: p for p in raw_dir.glob("*.json")}
    rows: list[dict] = []

    for asset in sorted(p for p in raw_dir.iterdir() if p.is_file() and not p.name.endswith(".json")):
        manifest_path = manifests.get(f"{asset.stem}.manifest.json")
        inspect_path = inspections.get(f"{asset.stem}.inspection.json")
        manifest = load_json(manifest_path) if manifest_path else None
        inspection = load_json(inspect_path) if inspect_path else None
        related_sidecars = [
            rel(p, project_dir)
            for name, p in sorted(sidecars.items())
            if name.startswith(f"{asset.name}.") and name not in {
                f"{asset.stem}.manifest.json",
                f"{asset.stem}.inspection.json",
            }
        ]
        rows.append(
            {
                "path": rel(asset, project_dir),
                "name": asset.name,
                "size_bytes": asset.stat().st_size,
                "modified_at": datetime.fromtimestamp(asset.stat().st_mtime, tz=timezone.utc).isoformat(),
                "manifest_path": rel(manifest_path, project_dir) if manifest_path else None,
                "inspection_path": rel(inspect_path, project_dir) if inspect_path else None,
                "source": (manifest or {}).get("source") or (manifest or {}).get("url"),
                "dataset_type": (manifest or {}).get("dataset_type"),
                "vintage": (manifest or {}).get("vintage") or (manifest or {}).get("year"),
                "geometry_type": (inspection or {}).get("geometry_type"),
                "feature_count": (inspection or {}).get("feature_count"),
                "columns": (inspection or {}).get("columns"),
                "related_sidecars": related_sidecars,
            }
        )

    return rows


def collect_processed_assets(project_dir: Path) -> list[dict]:
    processed_dir = project_dir / "data" / "processed"
    if not processed_dir.exists():
        return []

    rows: list[dict] = []
    for asset in sorted(p for p in processed_dir.rglob("*") if p.is_file()):
        rows.append(
            {
                "path": rel(asset, project_dir),
                "name": asset.name,
                "size_bytes": asset.stat().st_size,
                "modified_at": datetime.fromtimestamp(asset.stat().st_mtime, tz=timezone.utc).isoformat(),
                "extension": asset.suffix.lower(),
            }
        )
    return rows


def collect_outputs(project_dir: Path) -> dict:
    outputs_dir = project_dir / "outputs"
    buckets: dict[str, list[dict]] = {}
    if not outputs_dir.exists():
        return buckets

    for category_dir in sorted(p for p in outputs_dir.iterdir() if p.is_dir()):
        entries = []
        for asset in sorted(p for p in category_dir.rglob("*") if p.is_file()):
            entries.append(
                {
                    "path": rel(asset, project_dir),
                    "name": asset.name,
                    "size_bytes": asset.stat().st_size,
                    "extension": asset.suffix.lower(),
                }
            )
        buckets[category_dir.name] = entries
    return buckets


def collect_handoffs(project_dir: Path) -> list[dict]:
    handoffs_dir = project_dir / "handoffs"
    if not handoffs_dir.exists():
        return []

    rows: list[dict] = []
    for path in sorted(handoffs_dir.glob("*.json")):
        payload = load_json(path) or {}
        rows.append(
            {
                "path": rel(path, project_dir),
                "name": path.name,
                "stage": payload.get("stage") or payload.get("handoff_type"),
                "status": payload.get("status") or payload.get("overall_status"),
                "agent_id": ((payload.get("provenance") or {}).get("runtime") or {}).get("agent_id"),
                "model_id": ((payload.get("provenance") or {}).get("runtime") or {}).get("model_id"),
            }
        )
    return rows


def derive_reuse_hints(raw_assets: list[dict], processed_assets: list[dict], outputs: dict) -> dict:
    hints = {
        "has_raw_vector": any(a["name"].lower().endswith((".gpkg", ".geojson", ".shp", ".zip")) for a in raw_assets),
        "has_raw_tabular": any(a["name"].lower().endswith((".csv", ".xlsx", ".parquet")) for a in raw_assets),
        "has_processed_geopackage": any(a["name"].lower().endswith(".gpkg") for a in processed_assets),
        "has_report": bool(outputs.get("reports")),
        "has_map": bool(outputs.get("maps")),
        "has_validation": bool(outputs.get("validation")),
    }
    return hints


def build_inventory(project_dir: Path) -> dict:
    manifest = load_json(project_dir / "manifest.json") or {}
    project_brief = load_json(project_dir / "project_brief.json") or {}
    data_catalog = load_json(project_dir / "data_catalog.json")
    raw_assets = collect_raw_assets(project_dir)
    processed_assets = collect_processed_assets(project_dir)
    outputs = collect_outputs(project_dir)
    handoffs = collect_handoffs(project_dir)

    inventory = {
        "inventory_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "project_id": manifest.get("project_id") or project_dir.name,
            "project_title": project_brief.get("project_title") or manifest.get("name") or project_dir.name,
            "status": manifest.get("status"),
            "geography": manifest.get("geography"),
            "boundary_type": manifest.get("boundary_type"),
            "fips": manifest.get("fips"),
            "notes": manifest.get("notes"),
        },
        "raw_assets": raw_assets,
        "processed_assets": processed_assets,
        "outputs": outputs,
        "handoffs": handoffs,
        "data_catalog_present": data_catalog is not None,
        "reuse_hints": derive_reuse_hints(raw_assets, processed_assets, outputs),
    }
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a machine-readable project inventory.")
    parser.add_argument("--project-dir", required=True, help="Path to an analysis project directory")
    parser.add_argument("--output", help="Output JSON path (default: <project-dir>/inventory.json)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        raise SystemExit(f"ERROR: project directory not found: {project_dir}")

    out = Path(args.output).expanduser().resolve() if args.output else project_dir / "inventory.json"
    inventory = build_inventory(project_dir)
    out.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"inventory {out}")
    print(
        "summary "
        + json.dumps(
            {
                "project_id": inventory["project"]["project_id"],
                "raw_assets": len(inventory["raw_assets"]),
                "processed_assets": len(inventory["processed_assets"]),
                "output_categories": len(inventory["outputs"]),
                "handoffs": len(inventory["handoffs"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
