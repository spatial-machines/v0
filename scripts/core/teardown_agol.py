#!/usr/bin/env python3
"""Delete ArcGIS Online items previously published by publish_arcgis_online.py.

Reads ``<analysis_dir>/outputs/arcgis/publish-status.json``, connects with
the same credentials the publisher uses, and deletes every AGOL item
whose ``id`` field is set. Safe to re-run — already-deleted items are
reported as ``not_found`` and skipped.

Typical iteration loop:

    # 1. publish
    python scripts/core/publish_arcgis_online.py analyses/demo-sedgwick-poverty/ \\
        --title "Sedgwick Poverty Demo"

    # 2. inspect in AGOL web UI, eyeball renderers

    # 3. clean up
    python scripts/core/teardown_agol.py analyses/demo-sedgwick-poverty/ --dry-run
    python scripts/core/teardown_agol.py analyses/demo-sedgwick-poverty/

Credentials come from .env (AGOL_URL, AGOL_USER + AGOL_PASSWORD, or
AGOL_API_KEY), same as the publisher. Never logged.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))


def _load_dotenv(repo_root: Path) -> None:
    """Minimal dotenv loader — same semantics as publish_arcgis_online.py."""
    path = repo_root / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _connect():
    """Open an authenticated GIS connection or exit with a clear message."""
    try:
        from arcgis.gis import GIS  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "The 'arcgis' package is required. Install with: pip install arcgis"
        ) from exc
    url = os.environ.get("AGOL_URL", "https://www.arcgis.com")
    api_key = os.environ.get("AGOL_API_KEY")
    user = os.environ.get("AGOL_USER")
    pw = os.environ.get("AGOL_PASSWORD")
    if not api_key and not (user and pw):
        raise SystemExit(
            "AGOL credentials missing. Set AGOL_API_KEY, "
            "or both AGOL_USER and AGOL_PASSWORD, in your .env."
        )
    if api_key:
        return GIS(url, api_key=api_key)
    return GIS(url, user, pw)


def _delete_item(gis, item_id: str, dry_run: bool) -> dict:
    """Attempt to delete one AGOL item. Always returns a result record."""
    rec: dict = {"id": item_id, "status": "unknown"}
    try:
        item = gis.content.get(item_id)
    except Exception as exc:  # noqa: BLE001 — surface any AGOL API error
        rec["status"] = "get_failed"
        rec["error"] = str(exc)
        return rec
    if item is None:
        rec["status"] = "not_found"
        return rec
    rec["title"] = getattr(item, "title", "")
    rec["type"] = getattr(item, "type", "")
    if dry_run:
        rec["status"] = "would_delete"
        return rec
    try:
        ok = item.delete()
        rec["status"] = "deleted" if ok else "delete_returned_false"
    except Exception as exc:  # noqa: BLE001
        rec["status"] = "delete_failed"
        rec["error"] = str(exc)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Delete AGOL items referenced by publish-status.json.",
    )
    ap.add_argument("analysis_dir",
                    help="Analysis directory (e.g. analyses/demo-sedgwick-poverty)")
    ap.add_argument("--dry-run", action="store_true",
                    help="List what would be deleted, don't actually delete.")
    ap.add_argument("--status-file",
                    help="Override path to publish-status.json. Default: "
                         "<analysis_dir>/outputs/arcgis/publish-status.json")
    ap.add_argument("--keep-categories", nargs="*", default=[],
                    help="Categories to preserve (e.g. 'report' 'web_map'). "
                         "Items whose publish-status 'category' matches are "
                         "skipped. Useful for keeping the report item while "
                         "tearing down feature layers.")
    args = ap.parse_args()

    analysis_dir = Path(args.analysis_dir).resolve()
    status_path = (
        Path(args.status_file).resolve() if args.status_file
        else analysis_dir / "outputs" / "arcgis" / "publish-status.json"
    )
    if not status_path.exists():
        print(f"ERROR: status file not found: {status_path}", file=sys.stderr)
        return 1

    _load_dotenv(PROJECT_ROOT)
    status = json.loads(status_path.read_text(encoding="utf-8"))
    items = status.get("items", [])
    keep = set(args.keep_categories)
    targets = [
        item for item in items
        if item.get("id") and item.get("category") not in keep
    ]
    skipped = [item for item in items if item.get("category") in keep]
    no_id = [item for item in items if not item.get("id")]

    if not targets:
        print("Nothing to delete (no items with 'id' to tear down).")
        return 0

    action = "DRY-RUN" if args.dry_run else "DELETE"
    print(f"=== {action}: {len(targets)} item(s) from "
          f"{analysis_dir.name} ===")
    if skipped:
        print(f"  kept: {len(skipped)} item(s) "
              f"(categories: {sorted({i.get('category') for i in skipped})})")
    if no_id:
        print(f"  skipped: {len(no_id)} planned-but-not-published item(s)")

    gis = _connect()
    results = [_delete_item(gis, item["id"], args.dry_run) for item in targets]

    deleted = sum(1 for r in results if r["status"] == "deleted")
    would = sum(1 for r in results if r["status"] == "would_delete")
    not_found = sum(1 for r in results if r["status"] == "not_found")
    failed = sum(
        1 for r in results
        if r["status"] not in {"deleted", "would_delete", "not_found"}
    )

    for r in results:
        print(f"  [{r['status']:22}] {r['id']}  {r.get('title', '')}")
    print("---")
    print(f"Summary: deleted={deleted}, would_delete={would}, "
          f"not_found={not_found}, failed={failed}")

    teardown_path = status_path.parent / "teardown-status.json"
    teardown_path.write_text(
        json.dumps({
            "ran_at": datetime.now(UTC).isoformat(),
            "dry_run": args.dry_run,
            "source_status": str(status_path),
            "kept_categories": sorted(keep),
            "results": results,
            "summary": {
                "deleted": deleted,
                "would_delete": would,
                "not_found": not_found,
                "failed": failed,
            },
        }, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote: {teardown_path}")

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
