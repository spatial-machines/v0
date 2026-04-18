#!/usr/bin/env python3
"""Structured activity logger for pipeline stage tracking.

Appends JSONL entries to runs/activity.log so every agent action is
machine-readable after the fact. Call at stage start and stage end.

Usage (from other scripts — import and call):
    from log_activity import log_stage_start, log_stage_end, log_event

    run_id = log_stage_start(
        project_dir="analyses/my-project",
        role="data-retrieval",
        stage="retrieval",
        description="Fetching Census ACS poverty data",
    )
    # ... do work ...
    log_stage_end(
        project_dir="analyses/my-project",
        run_id=run_id,
        role="data-retrieval",
        stage="retrieval",
        status="completed",
        outputs=["data/raw/poverty.csv"],
        scripts_used=["fetch_acs_data.py"],
        notes="Retrieved 150 tracts",
    )

Usage (CLI — for agent use):
    python scripts/core/log_activity.py start \\
        --project analyses/my-project --role data-retrieval \\
        --stage retrieval --description "Fetching Census ACS data"

    python scripts/core/log_activity.py end \\
        --project analyses/my-project --role data-retrieval \\
        --stage retrieval --status completed \\
        --scripts fetch_acs_data.py --outputs data/raw/poverty.csv

    python scripts/core/log_activity.py show \\
        --project analyses/my-project
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC
from pathlib import Path


def _activity_log_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / "runs" / "activity.log"


def _append(project_dir: str | Path, entry: dict) -> None:
    log_path = _activity_log_path(project_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def log_stage_start(
    project_dir: str | Path,
    role: str,
    stage: str,
    description: str = "",
) -> str:
    """Log the start of a pipeline stage. Returns a run_id for the end call."""
    run_id = str(uuid.uuid4())[:12]
    entry = {
        "event": "stage_start",
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "role": role,
        "stage": stage,
        "description": description,
    }
    _append(project_dir, entry)
    return run_id


def log_stage_end(
    project_dir: str | Path,
    run_id: str,
    role: str,
    stage: str,
    status: str = "completed",
    outputs: list[str] | None = None,
    scripts_used: list[str] | None = None,
    wiki_pages_consulted: list[str] | None = None,
    notes: str = "",
    errors: list[str] | None = None,
) -> None:
    """Log the end of a pipeline stage."""
    entry = {
        "event": "stage_end",
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "role": role,
        "stage": stage,
        "status": status,
        "outputs": outputs or [],
        "scripts_used": scripts_used or [],
        "wiki_pages_consulted": wiki_pages_consulted or [],
        "notes": notes,
        "errors": errors or [],
    }
    _append(project_dir, entry)


def log_event(
    project_dir: str | Path,
    role: str,
    event_type: str,
    message: str,
    **kwargs,
) -> None:
    """Log a freeform event (delegation, decision, warning, etc.)."""
    entry = {
        "event": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "role": role,
        "message": message,
        **kwargs,
    }
    _append(project_dir, entry)


def read_activity_log(project_dir: str | Path) -> list[dict]:
    """Read all entries from the activity log."""
    log_path = _activity_log_path(project_dir)
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


def format_activity_log(entries: list[dict]) -> str:
    """Format activity log entries as a human-readable timeline."""
    lines = []
    for e in entries:
        ts = e.get("timestamp", "")[:19].replace("T", " ")
        event = e.get("event", "?")
        role = e.get("role", "?")
        stage = e.get("stage", "")
        status = e.get("status", "")

        if event == "stage_start":
            desc = e.get("description", "")
            lines.append(f"  {ts}  START  {role:20s}  {stage:15s}  {desc}")
        elif event == "stage_end":
            scripts = ", ".join(e.get("scripts_used", []))
            n_outputs = len(e.get("outputs", []))
            errors = e.get("errors", [])
            status_icon = "OK" if status == "completed" else "FAIL" if status == "failed" else status.upper()
            line = f"  {ts}  {status_icon:5s}  {role:20s}  {stage:15s}  {n_outputs} outputs"
            if scripts:
                line += f"  scripts=[{scripts}]"
            if errors:
                line += f"  ERRORS: {errors}"
            lines.append(line)
        elif event == "delegation":
            target = e.get("target_role", "?")
            lines.append(f"  {ts}  DELEGATE  {role:17s}  -> {target}  {e.get('message', '')}")
        else:
            lines.append(f"  {ts}  {event:7s}  {role:20s}  {e.get('message', '')}")

    return "\n".join(lines) if lines else "  (no activity recorded)"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline activity logger.")
    sub = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = sub.add_parser("start", help="Log stage start")
    p_start.add_argument("--project", required=True, help="Project directory")
    p_start.add_argument("--role", required=True, help="Agent role")
    p_start.add_argument("--stage", required=True, help="Pipeline stage")
    p_start.add_argument("--description", default="", help="What this stage will do")

    # end
    p_end = sub.add_parser("end", help="Log stage end")
    p_end.add_argument("--project", required=True)
    p_end.add_argument("--run-id", required=True, help="Run ID from start")
    p_end.add_argument("--role", required=True)
    p_end.add_argument("--stage", required=True)
    p_end.add_argument("--status", default="completed", choices=["completed", "failed", "partial"])
    p_end.add_argument("--scripts", nargs="*", default=[], help="Scripts used")
    p_end.add_argument("--outputs", nargs="*", default=[], help="Output files")
    p_end.add_argument("--notes", default="")

    # show
    p_show = sub.add_parser("show", help="Show activity log")
    p_show.add_argument("--project", required=True)

    # event
    p_event = sub.add_parser("event", help="Log a freeform event")
    p_event.add_argument("--project", required=True)
    p_event.add_argument("--role", required=True)
    p_event.add_argument("--type", default="info", help="Event type")
    p_event.add_argument("--message", required=True)

    args = parser.parse_args()

    if args.command == "start":
        run_id = log_stage_start(args.project, args.role, args.stage, args.description)
        print(f"run_id={run_id}")
        return 0

    elif args.command == "end":
        log_stage_end(
            args.project, args.run_id, args.role, args.stage,
            status=args.status, outputs=args.outputs,
            scripts_used=args.scripts, notes=args.notes,
        )
        print(f"logged end: {args.role}/{args.stage} -> {args.status}")
        return 0

    elif args.command == "show":
        entries = read_activity_log(args.project)
        if not entries:
            print("No activity log found.")
            return 0
        print(f"Activity log: {len(entries)} entries\n")
        print(format_activity_log(entries))
        return 0

    elif args.command == "event":
        log_event(args.project, args.role, args.type, args.message)
        print(f"logged event: {args.role}/{args.type}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
