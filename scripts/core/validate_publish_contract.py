#!/usr/bin/env python3
"""Validate that a project publish step satisfies the minimum delivery contract.

Checks:
- publishing handoff exists and has core fields
- publish audit exists and marks the project ready for human browsing
- project URL responds successfully when requested

Usage:
    python validate_publish_contract.py \
        --project-dir analyses/my-project \
        --project-url https://gis.example.com/my-project/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def fetch_status(url: str, timeout: int) -> dict:
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; GISAgentPublishValidator/1.0)"
            },
        )
        with urlopen(req, timeout=timeout) as resp:
            return {"ok": True, "status": getattr(resp, "status", 200)}
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc)}
    except URLError as exc:
        return {"ok": False, "status": None, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate publish contract for one project.")
    parser.add_argument("--project-dir", required=True, help="Path to project directory")
    parser.add_argument("--project-url", required=True, help="Expected project URL")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout seconds")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 1

    handoff_candidates = sorted((project_dir / "handoffs").glob("*publishing*.json"))
    audit_candidates = sorted((project_dir / "runs").glob("*publish*.json")) + sorted((project_dir / "runs").glob("*site_publish_audit*.json"))

    publishing_handoff_path = handoff_candidates[-1] if handoff_candidates else None
    audit_path = audit_candidates[-1] if audit_candidates else None

    publishing_handoff = load_json(publishing_handoff_path) if publishing_handoff_path else None
    audit = load_json(audit_path) if audit_path else None

    errors = []

    if not publishing_handoff_path:
        errors.append("publishing handoff not found")
    if not audit_path:
        errors.append("publish audit not found")

    if publishing_handoff:
        for key in ("handoff_type", "project_id", "project_url", "ready_for"):
            if not publishing_handoff.get(key):
                errors.append(f"publishing handoff missing {key}")
        if publishing_handoff.get("handoff_type") != "publishing":
            errors.append(f"unexpected publishing handoff type: {publishing_handoff.get('handoff_type')}")

    if audit:
        if audit.get("ready_for_human_browsing") is not True:
            errors.append("publish audit does not mark ready_for_human_browsing=true")

    url_check = fetch_status(args.project_url, args.timeout)
    if not url_check["ok"]:
        errors.append(f"project URL check failed: {url_check.get('status')} {url_check.get('error', '')}".strip())

    result = {
        "project_dir": str(project_dir),
        "project_url": args.project_url,
        "publishing_handoff": str(publishing_handoff_path) if publishing_handoff_path else None,
        "publish_audit": str(audit_path) if audit_path else None,
        "url_check": url_check,
        "ok": not errors,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"project: {project_dir.name}")
        print(f"url: {args.project_url}")
        print(f"ok: {result['ok']}")
        for err in errors:
            print(f"- {err}")

    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
