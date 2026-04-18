#!/usr/bin/env python3
"""project_status.py — show detailed status for one or all projects.

Inspects the actual filesystem to report what each project contains
beyond what the registry records.

Usage:
    python scripts/project_status.py                    # all projects
    python scripts/project_status.py sd-tracts-demo     # one project
    python scripts/project_status.py --json              # machine-readable
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSES_DIR = ROOT / "analyses"
REGISTRY_PATH = ANALYSES_DIR / "registry.json"


def load_registry():
    if not REGISTRY_PATH.exists():
        print("ERROR: registry not found at", REGISTRY_PATH, file=sys.stderr)
        sys.exit(1)
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def dir_size_mb(path):
    """Return total size of directory in MB."""
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return round(total / (1024 * 1024), 2)


def count_files(path, pattern="*"):
    """Count files matching pattern recursively."""
    return len(list(Path(path).rglob(pattern))) if Path(path).exists() else 0


def inspect_project(entry):
    """Build a status dict for a single project."""
    pid = entry["id"]
    isolation = entry.get("isolation", "unknown")

    info = {
        "id": pid,
        "name": entry.get("name", ""),
        "status": entry.get("status", "unknown"),
        "isolation": isolation,
        "geography": entry.get("geography", ""),
        "created": entry.get("created", ""),
        "updated": entry.get("updated", ""),
        "client": entry.get("client", ""),
    }

    if isolation == "legacy":
        # Legacy project — top-level dirs
        info["directory"] = "(legacy — top-level data/, outputs/, runs/)"
        info["has_directory"] = True
        info["disk_mb"] = "n/a (shared directories)"
        info["artifacts"] = {
            "raw_files": count_files(ROOT / "data" / "raw"),
            "processed_files": count_files(ROOT / "data" / "processed"),
            "maps": count_files(ROOT / "outputs" / "maps"),
            "tables": count_files(ROOT / "outputs" / "tables"),
            "reports": count_files(ROOT / "outputs" / "reports"),
            "handoffs": count_files(ROOT / "runs", "*.json"),
        }
    else:
        project_dir = ANALYSES_DIR / pid
        info["directory"] = str(project_dir.relative_to(ROOT))
        info["has_directory"] = project_dir.exists()

        if project_dir.exists():
            info["disk_mb"] = dir_size_mb(project_dir)

            # Check manifest
            manifest_path = project_dir / "manifest.json"
            info["has_manifest"] = manifest_path.exists()
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                info["manifest_status"] = manifest.get("status", "unknown")

            info["artifacts"] = {
                "raw_files": count_files(project_dir / "data" / "raw"),
                "processed_files": count_files(project_dir / "data" / "processed"),
                "maps": count_files(project_dir / "outputs" / "maps"),
                "tables": count_files(project_dir / "outputs" / "tables"),
                "reports": count_files(project_dir / "outputs" / "reports"),
                "handoffs": count_files(project_dir / "runs", "*.json"),
                "qgis_packages": count_files(project_dir / "outputs" / "qgis"),
            }

            # Check for validation results
            val_dir = project_dir / "runs" / "validation"
            if val_dir.exists():
                info["validation_results"] = count_files(val_dir)

            # Check for retrospectives
            retro_dir = project_dir / "memory" / "retrospectives"
            if retro_dir.exists():
                info["retrospectives"] = count_files(retro_dir)
        else:
            info["disk_mb"] = 0
            info["artifacts"] = {}
            info["note"] = "Directory missing — may have been archived or removed"

    return info


def print_project(info):
    """Pretty-print a single project's status."""
    print(f"  Project:    {info['id']}")
    print(f"  Name:       {info.get('name', '')}")
    print(f"  Status:     {info['status']}")
    print(f"  Isolation:  {info['isolation']}")
    print(f"  Geography:  {info.get('geography', '')}")
    print(f"  Client:     {info.get('client', '')}")
    print(f"  Created:    {info.get('created', '')}")
    print(f"  Updated:    {info.get('updated', '')}")
    print(f"  Directory:  {info.get('directory', '')}")
    print(f"  Disk (MB):  {info.get('disk_mb', 'n/a')}")

    artifacts = info.get("artifacts", {})
    if artifacts:
        print("  Artifacts:")
        for k, v in artifacts.items():
            label = k.replace("_", " ").title()
            print(f"    {label}: {v}")

    if info.get("note"):
        print(f"  Note:       {info['note']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Show project status")
    parser.add_argument("project_id", nargs="?", help="Specific project ID (default: all)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    reg = load_registry()
    entries = reg.get("analyses", [])

    if args.project_id:
        entries = [e for e in entries if e["id"] == args.project_id]
        if not entries:
            print(f"ERROR: project '{args.project_id}' not found in registry", file=sys.stderr)
            return 1

    results = [inspect_project(e) for e in entries]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nProject Status Report ({len(results)} project(s)):\n")
        for r in results:
            print_project(r)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
