#!/usr/bin/env python3
"""list_projects.py — list all analysis projects in the registry.

Usage:
    python scripts/list_projects.py                 # all projects
    python scripts/list_projects.py --status active  # filter by status
    python scripts/list_projects.py --json           # machine-readable output
"""
import argparse
import json
import os
import sys

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "analyses", "registry.json")


def load_registry():
    path = os.path.normpath(REGISTRY_PATH)
    if not os.path.exists(path):
        print("ERROR: registry not found at", path, file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def format_table(projects):
    if not projects:
        print("  (no projects)")
        return
    # Column widths
    id_w = max(len(p["id"]) for p in projects)
    st_w = max(len(p.get("status", "?")) for p in projects)
    iso_w = max(len(p.get("isolation", "?")) for p in projects)
    geo_w = max(len(p.get("geography", "?")) for p in projects)
    hdr = f"  {'ID':<{id_w}}  {'STATUS':<{st_w}}  {'ISOLATION':<{iso_w}}  {'GEOGRAPHY':<{geo_w}}  CREATED"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for p in projects:
        print(
            f"  {p['id']:<{id_w}}  {p.get('status','?'):<{st_w}}  "
            f"{p.get('isolation','?'):<{iso_w}}  {p.get('geography','?'):<{geo_w}}  "
            f"{p.get('created','?')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="List analysis projects")
    parser.add_argument("--status", help="Filter by status (active, paused, archived, failed)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    reg = load_registry()
    projects = reg.get("analyses", [])

    if args.status:
        projects = [p for p in projects if p.get("status") == args.status]

    if args.json:
        print(json.dumps(projects, indent=2))
    else:
        print(f"\nAnalysis Projects ({len(projects)} total):\n")
        format_table(projects)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
