#!/usr/bin/env python3
"""Publish an analysis's File Geodatabase + styled layers to ArcGIS Online.

Scope is intentionally narrow: this uploads ONE File Geodatabase (the one
produced by `package_arcgis_pro.py`), publishes it as ONE hosted Feature
Service with N feature layers, applies per-layer renderers from the
`.style.json` sidecars in `outputs/maps/`, and assembles a Web Map that
ties them together.

What does NOT go to AGOL: map PNGs, chart PNGs, HTML report, ArcGIS Pro
`.lyrx` files, QGIS `.qgs`. Those are local deliverables. Anything published
to AGOL is also available locally; not everything local is mirrored to AGOL.

Default sharing level is PRIVATE. Use `--sharing org|public` to promote.

Credentials come from `.env`: AGOL_URL, AGOL_API_KEY, or AGOL_USER +
AGOL_PASSWORD. Never committed, never logged.

Usage:

    # Prerequisite — build the ArcGIS Pro package (produces the GDB we upload):
    python scripts/core/package_arcgis_pro.py analyses/my-project/ \\
        --title "My Project" \\
        --data-files analyses/my-project/data/processed/tracts.gpkg \\
        --style-dir  analyses/my-project/outputs/maps

    # Dry run — validates creds + introspects the GDB, no uploads
    python scripts/core/publish_arcgis_online.py analyses/my-project/ \\
        --title "My Project" --dry-run

    # Real upload, default PRIVATE
    python scripts/core/publish_arcgis_online.py analyses/my-project/ \\
        --title "My Project"

    # Promote to ORG-wide visibility
    python scripts/core/publish_arcgis_online.py analyses/my-project/ \\
        --title "My Project" --sharing org

Outputs:
    analyses/<project>/outputs/arcgis/publish-status.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from publishing.arcgis_online import ArcGISOnlineAdapter
from publishing.base import PublishRequest


def _load_dotenv(repo_root: Path) -> None:
    """Minimal .env loader: KEY=VALUE lines, respects existing env vars."""
    import os
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Publish an analysis's File Geodatabase to ArcGIS Online.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("analysis_dir")
    ap.add_argument("--title", required=True, help="Title prefix for all items")
    ap.add_argument("--description", default="",
                    help="Description applied to every item")
    ap.add_argument("--tags", nargs="*", default=[],
                    help="Additional tags applied to every item")
    ap.add_argument("--sharing", choices=["private", "org", "public"],
                    default="private",
                    help="Item sharing level (default: private)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate creds + introspect the GDB without uploading")
    ap.add_argument("--gdb",
                    help="Override GDB path (default: "
                         "<analysis_dir>/outputs/arcgis/data/project.gdb)")
    ap.add_argument("--style-dir",
                    help="Directory with .style.json sidecars "
                         "(default: <analysis_dir>/outputs/maps/)")
    args = ap.parse_args()

    _load_dotenv(PROJECT_ROOT)

    analysis = Path(args.analysis_dir).resolve()
    if not analysis.is_dir():
        print(f"ERROR: analysis dir not found: {analysis}", file=sys.stderr)
        return 2

    # Resolve GDB path; if missing, emit a clear "run package_arcgis_pro first"
    # message BEFORE hitting the adapter (which also checks).
    gdb_path = (Path(args.gdb).resolve() if args.gdb
                else analysis / "outputs" / "arcgis" / "data" / "project.gdb")
    if not gdb_path.exists():
        print(
            f"ERROR: no File Geodatabase at {gdb_path}\n"
            f"       Run the ArcGIS Pro packager first:\n"
            f"       python scripts/core/package_arcgis_pro.py {analysis} "
            f"--title \"{args.title}\" "
            f"--data-files {analysis}/data/processed/*.gpkg "
            f"--style-dir {analysis}/outputs/maps",
            file=sys.stderr,
        )
        return 2

    style_dir = (Path(args.style_dir).resolve() if args.style_dir
                 else analysis / "outputs" / "maps")

    request = PublishRequest(
        analysis_dir=analysis,
        title=args.title,
        description=args.description,
        tags=list(args.tags),
        sharing=args.sharing.upper(),
        dry_run=args.dry_run,
        style_dir=style_dir if style_dir.exists() else None,
        options={"gdb_file": str(gdb_path)},
    )

    adapter = ArcGISOnlineAdapter()
    result = adapter.publish(request) if not args.dry_run else adapter.validate(request)

    status_path = ArcGISOnlineAdapter._write_status(
        analysis_dir=analysis, target=adapter.target, result=result,
    )

    print(f"=== AGOL publish: {args.title} ({result.status}) ===")
    print(f"  request: {json.dumps(result.request, indent=2)}")
    print(f"  items:   {len(result.items)}")
    for it in result.items:
        mark = it.get("id") or it.get("state") or "planned"
        label = it.get("title") or it.get("layer_name") or it.get("source") or ""
        print(f"    [{mark}] ({it.get('category')}) {label}")
    if result.web_map_url:
        print(f"  web map: {result.web_map_url}")
    for w in result.warnings:
        print(f"  WARN:  {w}")
    for e in result.errors:
        print(f"  ERROR: {e}")
    print(f"  status file: {status_path}")

    return 0 if result.status in ("ok", "dry-run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
