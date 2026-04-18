#!/usr/bin/env python3
"""Search project inventories to support reuse-first retrieval.

Searches `analyses/*/inventory.json` and falls back to selected metadata files when
inventory files do not exist yet.

Usage:
    python search_project_inventory.py --analyses-dir analyses --query cafes
    python search_project_inventory.py --analyses-dir analyses --query postgis --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def coerce_inventory(project_dir: Path) -> dict:
    inv = load_json(project_dir / "inventory.json")
    if inv:
        return inv

    manifest = load_json(project_dir / "manifest.json") or {}
    brief = load_json(project_dir / "project_brief.json") or {}
    return {
        "project": {
            "project_id": manifest.get("project_id") or project_dir.name,
            "project_title": brief.get("project_title") or manifest.get("name") or project_dir.name,
            "status": manifest.get("status"),
            "geography": manifest.get("geography"),
            "notes": manifest.get("notes"),
        },
        "raw_assets": [],
        "processed_assets": [],
        "outputs": {},
        "handoffs": [],
        "_inventory_missing": True,
    }


def searchable_text(inv: dict) -> str:
    chunks = []
    project = inv.get("project") or {}
    for key in ("project_id", "project_title", "status", "geography", "notes"):
        val = project.get(key)
        if val:
            chunks.append(str(val))

    for asset in inv.get("raw_assets", []):
        for key in ("name", "source", "dataset_type", "vintage", "geometry_type", "path"):
            val = asset.get(key)
            if val:
                chunks.append(str(val))

    for asset in inv.get("processed_assets", []):
        for key in ("name", "path"):
            val = asset.get(key)
            if val:
                chunks.append(str(val))

    for category, items in (inv.get("outputs") or {}).items():
        chunks.append(category)
        for item in items:
            for key in ("name", "path"):
                val = item.get(key)
                if val:
                    chunks.append(str(val))

    return "\n".join(chunks).lower()


def build_result(inv: dict, query: str) -> dict:
    project = inv.get("project") or {}
    outputs = inv.get("outputs") or {}
    return {
        "project_id": project.get("project_id"),
        "project_title": project.get("project_title"),
        "status": project.get("status"),
        "geography": project.get("geography"),
        "inventory_present": not inv.get("_inventory_missing", False),
        "raw_asset_count": len(inv.get("raw_assets", [])),
        "processed_asset_count": len(inv.get("processed_assets", [])),
        "output_categories": sorted(outputs.keys()),
        "query": query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search project inventories for reuse candidates.")
    parser.add_argument("--analyses-dir", required=True, help="Path to analyses directory")
    parser.add_argument("--query", required=True, help="Search string")
    parser.add_argument("--status", help="Optional project status filter")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    analyses_dir = Path(args.analyses_dir).expanduser().resolve()
    if not analyses_dir.exists():
        raise SystemExit(f"ERROR: analyses directory not found: {analyses_dir}")

    needle = args.query.lower().strip()
    results = []
    for project_dir in sorted(p for p in analyses_dir.iterdir() if p.is_dir()):
        inv = coerce_inventory(project_dir)
        project = inv.get("project") or {}
        if args.status and project.get("status") != args.status:
            continue
        haystack = searchable_text(inv)
        if needle and needle not in haystack:
            continue
        results.append(build_result(inv, args.query))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"matches {len(results)}")
        for item in results:
            print(
                f"- {item['project_id']} | {item.get('status') or '?'} | "
                f"{item.get('geography') or '?'} | inventory={'yes' if item['inventory_present'] else 'no'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
