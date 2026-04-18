#!/usr/bin/env python3
"""Validate GIS pipeline handoff artifacts against minimum contract rules.

This is a pragmatic contract validator, not a full schema engine.
It checks:
- required top-level fields
- presence of provenance/runtime metadata
- stage-specific minimum fields

Usage:
    python validate_handoffs.py --handoff-dir analyses/my-project/handoffs
    python validate_handoffs.py --handoff-dir analyses/my-project/handoffs --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BASE_REQUIRED = ["handoff_type", "run_id", "summary", "created_at", "ready_for", "provenance"]

TYPE_REQUIRED = {
    "processing": ["output_files", "processing_steps"],
    "analysis": ["output_files", "analysis_outputs"],
    "validation": ["overall_status", "checks", "output_files"],
    "reporting": ["output_files", "report_files"],
    "publishing": ["artifact_files", "project_id", "project_url", "publish_audit"],
    "lead": ["artifacts", "stages_ran", "qa_summary"],
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc)}


def has_value(payload: dict, key: str) -> bool:
    if key not in payload:
        return False
    value = payload.get(key)
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def validate_provenance(payload: dict) -> list[str]:
    errors = []
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        return ["missing provenance object"]

    runtime = provenance.get("runtime")
    if not isinstance(runtime, dict):
        return ["missing provenance.runtime"]

    for key in ("agent_id", "model_id"):
        value = runtime.get(key)
        if not value:
            errors.append(f"missing provenance.runtime.{key}")

    return errors


def validate_stage_specific(payload: dict) -> list[str]:
    handoff_type = payload.get("handoff_type")
    required = TYPE_REQUIRED.get(handoff_type, [])
    errors = [f"missing {field}" for field in required if not has_value(payload, field)]

    if handoff_type == "publishing":
        publish_audit = payload.get("publish_audit") or {}
        if not isinstance(publish_audit, dict):
            errors.append("publish_audit must be an object")
        else:
            if publish_audit.get("ready_for_human_browsing") is False:
                errors.append("publish_audit.ready_for_human_browsing is false")

    if handoff_type == "validation":
        status = payload.get("overall_status")
        if status not in {"PASS", "PASS WITH WARNINGS", "REWORK NEEDED", "FAIL", "FAILURE"}:
            errors.append(f"unexpected overall_status: {status}")

    return errors


def validate_file(path: Path) -> dict:
    payload = load_json(path)
    errors = []

    if "_parse_error" in payload:
        return {
            "path": str(path),
            "ok": False,
            "handoff_type": None,
            "errors": [f"invalid json: {payload['_parse_error']}"],
        }

    for field in BASE_REQUIRED:
        if not has_value(payload, field):
            errors.append(f"missing {field}")

    errors.extend(validate_provenance(payload))
    errors.extend(validate_stage_specific(payload))

    return {
        "path": str(path),
        "ok": not errors,
        "handoff_type": payload.get("handoff_type"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GIS handoff artifacts.")
    parser.add_argument("--handoff-dir", required=True, help="Directory containing handoff JSON files")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    handoff_dir = Path(args.handoff_dir).expanduser().resolve()
    if not handoff_dir.exists():
        print(f"ERROR: handoff directory not found: {handoff_dir}", file=sys.stderr)
        return 1

    files = sorted(p for p in handoff_dir.glob("*.json") if p.is_file())
    results = [validate_file(path) for path in files]
    failures = [r for r in results if not r["ok"]]

    summary = {
        "handoff_dir": str(handoff_dir),
        "files_checked": len(results),
        "failures": len(failures),
        "ok": len(failures) == 0,
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"handoffs checked: {summary['files_checked']}")
        print(f"failures: {summary['failures']}")
        for item in failures:
            print(f"- {Path(item['path']).name}")
            for err in item["errors"]:
                print(f"  - {err}")

    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
