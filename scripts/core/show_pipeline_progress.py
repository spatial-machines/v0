#!/usr/bin/env python3
"""Pipeline progress viewer — shows real-time and historical stage status.

Reads the activity log and handoff artifacts to show which pipeline stages
are done, in progress, or pending. Run this at any time during or after
an analysis to see where things stand.

Usage:
    python scripts/core/show_pipeline_progress.py analyses/my-project/

    # Watch mode — re-check every 5 seconds
    python scripts/core/show_pipeline_progress.py analyses/my-project/ --watch
"""
from __future__ import annotations

import json
import time
from datetime import datetime, UTC
from pathlib import Path

PIPELINE_STAGES = [
    {"stage": "intake",       "role": "lead-analyst",     "label": "0. Intake & Scoping"},
    {"stage": "retrieval",    "role": "data-retrieval",   "label": "1. Data Retrieval"},
    {"stage": "processing",   "role": "data-processing",  "label": "2. Data Processing"},
    {"stage": "analysis",     "role": "spatial-stats",    "label": "3. Analysis"},
    {"stage": "cartography",  "role": "cartography",      "label": "4. Cartography"},
    {"stage": "validation",   "role": "validation-qa",    "label": "5. Validation"},
    {"stage": "reporting",    "role": "report-writer",    "label": "6. Reporting"},
    {"stage": "packaging",    "role": "site-publisher",   "label": "7. Delivery Packaging"},
    {"stage": "peer-review",  "role": "peer-reviewer",    "label": "8. Peer Review"},
    {"stage": "delivery",     "role": "lead-analyst",     "label": "9. Synthesis & Delivery"},
]

STATUS_ICONS = {
    "completed": "\u2705",  # green check
    "running":   "\u23f3",  # hourglass
    "failed":    "\u274c",  # red X
    "partial":   "\u26a0\ufe0f",  # warning
    "pending":   "\u2b1c",  # white square
}


def _read_activity_log(project_dir: Path) -> list[dict]:
    log_path = project_dir / "runs" / "activity.log"
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _read_handoffs(project_dir: Path) -> dict:
    """Read handoff files and return {handoff_type: data}."""
    runs_dir = project_dir / "runs"
    if not runs_dir.exists():
        return {}
    handoffs = {}
    for f in runs_dir.glob("*.json"):
        if f.name == "activity.log":
            continue
        try:
            data = json.loads(f.read_text())
            ht = data.get("handoff_type")
            if ht:
                handoffs[ht] = data
        except (json.JSONDecodeError, KeyError):
            pass
    return handoffs


def _compute_stage_status(entries: list[dict], handoffs: dict) -> list[dict]:
    """Determine status of each pipeline stage."""
    # Build stage status from activity log
    stage_events = {}
    for e in entries:
        stage = e.get("stage")
        if stage:
            if stage not in stage_events:
                stage_events[stage] = {"starts": [], "ends": []}
            if e["event"] == "stage_start":
                stage_events[stage]["starts"].append(e)
            elif e["event"] == "stage_end":
                stage_events[stage]["ends"].append(e)

    # Map handoff types to stages
    handoff_stage_map = {
        "provenance": "retrieval",
        "processing": "processing",
        "analysis": "analysis",
        "validation": "validation",
        "reporting": "reporting",
        "lead-analyst": "delivery",
        "qgis-bridge": "packaging",
    }

    results = []
    for stage_def in PIPELINE_STAGES:
        stage_name = stage_def["stage"]
        status = "pending"
        start_time = None
        end_time = None
        duration = None
        scripts = []
        outputs = []
        errors = []

        # Check activity log
        if stage_name in stage_events:
            starts = stage_events[stage_name]["starts"]
            ends = stage_events[stage_name]["ends"]
            if starts:
                start_time = starts[-1].get("timestamp")
            if ends:
                last_end = ends[-1]
                end_time = last_end.get("timestamp")
                status = last_end.get("status", "completed")
                scripts = last_end.get("scripts_used", [])
                outputs = last_end.get("outputs", [])
                errors = last_end.get("errors", [])
            elif starts:
                status = "running"

        # Also check handoff artifacts (backup if activity log wasn't used)
        for ht, ht_stage in handoff_stage_map.items():
            if ht_stage == stage_name and ht in handoffs and status == "pending":
                status = "completed"
                if not end_time:
                    end_time = handoffs[ht].get("created_at")

        # Compute duration
        if start_time and end_time:
            try:
                t0 = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                duration = (t1 - t0).total_seconds()
            except (ValueError, TypeError):
                pass

        results.append({
            **stage_def,
            "status": status,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "scripts_used": scripts,
            "output_count": len(outputs),
            "errors": errors,
        })

    return results


def _format_progress(project_dir: Path, stages: list[dict]) -> str:
    lines = [
        f"  Pipeline Progress: {project_dir.name}",
        f"  {'=' * 60}",
        "",
    ]

    completed = sum(1 for s in stages if s["status"] == "completed")
    total = len(stages)
    pct = round(100 * completed / total) if total else 0

    lines.append(f"  Overall: {completed}/{total} stages complete ({pct}%)")
    lines.append("")

    for s in stages:
        icon = STATUS_ICONS.get(s["status"], "?")
        label = s["label"]
        role = s["role"]

        if s["duration_seconds"] is not None:
            dur = f"{s['duration_seconds']:.0f}s"
        elif s["status"] == "running" and s["start_time"]:
            try:
                t0 = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
                elapsed = (datetime.now(UTC) - t0).total_seconds()
                dur = f"{elapsed:.0f}s (running)"
            except (ValueError, TypeError):
                dur = "running"
        else:
            dur = ""

        line = f"  {icon} {label:30s}  {role:20s}"
        if dur:
            line += f"  {dur}"
        if s["scripts_used"]:
            line += f"  [{', '.join(s['scripts_used'])}]"
        if s["errors"]:
            line += f"  ERRORS: {len(s['errors'])}"

        lines.append(line)

    # Output summary
    total_outputs = sum(s["output_count"] for s in stages)
    total_errors = sum(len(s["errors"]) for s in stages)
    lines.append("")
    lines.append(f"  {'=' * 60}")
    lines.append(f"  Outputs: {total_outputs} | Errors: {total_errors}")

    return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Show pipeline progress for an analysis.")
    parser.add_argument("project_dir", help="Path to analysis directory")
    parser.add_argument("--watch", action="store_true", help="Re-check every 5 seconds")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Project directory not found: {project_dir}")
        return 1

    while True:
        entries = _read_activity_log(project_dir)
        handoffs = _read_handoffs(project_dir)
        stages = _compute_stage_status(entries, handoffs)

        if args.json:
            print(json.dumps(stages, indent=2))
        else:
            print("\033[2J\033[H" if args.watch else "")  # clear screen in watch mode
            print(_format_progress(project_dir, stages))

        if not args.watch:
            break

        time.sleep(5)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
