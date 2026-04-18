#!/usr/bin/env python3
"""Revision Loop Orchestrator — runs peer review and manages REVISE cycles.

Repeatedly invokes run_peer_review.py and inspects its verdict.  When the
verdict is REVISE, the script writes a revision_request.json that tells the
lead analyst exactly which agents to re-task and in what order.  It does NOT
automatically invoke other agents — the lead analyst reads the request and
delegates.

Exits:
    0 — PASS (analysis approved for delivery)
    1 — internal error
    2 — REJECT or max-revisions exceeded (escalation required)

Usage:
    python run_revision_loop.py --project-id chicago-food-access
    python run_revision_loop.py --project-id ks-healthcare-access --max-revisions 3
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_peer_review(project_id: str) -> int:
    """Run run_peer_review.py and return its exit code."""
    cmd = [sys.executable, str(SCRIPTS_DIR / "run_peer_review.py"), "--project-id", project_id]
    result = subprocess.run(cmd)
    return result.returncode


def read_peer_review_json(project_id: str) -> dict[str, Any] | None:
    """Read the peer_review.json produced by the last review run."""
    path = ANALYSES_DIR / project_id / "outputs" / "qa" / f"{project_id}_peer_review.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    print(f"  Written → {path}")


def build_critique_summary(review: dict) -> str:
    """One-paragraph human-readable summary of the review."""
    verdict = review.get("verdict", "UNKNOWN")
    findings = review.get("findings", [])
    non_pass = [f for f in findings if f.get("severity") not in ("PASS", "INFO")]
    if not non_pass:
        return f"Verdict: {verdict}. No actionable findings."
    parts = [f"{f.get('dimension','?')}: {f.get('finding','')[:120]}" for f in non_pass]
    return f"Verdict: {verdict}. Issues: " + " | ".join(parts)


def log_lesson(message: str, project_id: str) -> None:
    """Call log_lesson.py to record a lesson."""
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "log_lesson.py"),
        message,
        "--category", "qa",
        "--tags", f"peer-review,{project_id}",
    ]
    subprocess.run(cmd)


def write_escalation(project_id: str, review: dict, critique_history: list[dict]) -> Path:
    """Write an escalation JSON and return its path."""
    qa_dir = ANALYSES_DIR / project_id / "outputs" / "qa"
    path = qa_dir / f"{project_id}_escalation.json"
    escalation = {
        "schema": "escalation-v1",
        "project_id": project_id,
        "escalated_at": datetime.now(UTC).isoformat(),
        "reason": review.get("verdict", "UNKNOWN"),
        "latest_review": review,
        "critique_history": critique_history,
        "for_human": (
            f"Project {project_id} could not pass peer review. "
            f"See routing_action and critique_history for details."
        ),
    }
    write_json(path, escalation)
    return path


def write_revision_request(
    project_id: str,
    revision_number: int,
    review: dict,
) -> Path:
    """Write a revision_request JSON for the lead analyst."""
    qa_dir = ANALYSES_DIR / project_id / "outputs" / "qa"
    path = qa_dir / f"{project_id}_revision_{revision_number}.json"
    request = {
        "schema": "revision-request-v1",
        "project_id": project_id,
        "revision_number": revision_number,
        "requested_at": datetime.now(UTC).isoformat(),
        "routing_action": review.get("routing_action"),
        "critique_summary": build_critique_summary(review),
        "for_lead_analyst": (
            "Read this file. Delegate to each agent listed in routing_action.re_route "
            "in priority order. Re-run run_revision_loop.py after all agents complete."
        ),
    }
    write_json(path, request)
    return path


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Orchestrate the peer-review revision loop.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "This script does NOT automatically invoke other agents.\n"
            "It produces revision_request.json files that the lead analyst\n"
            "reads and acts on — delegating to the agents listed in\n"
            "routing_action.re_route in priority order.\n\n"
            "After all agents complete their revisions, re-run this script\n"
            "to trigger the next peer review cycle."
        ),
    )
    parser.add_argument("--project-id", required=True, help="Project ID (analyses/ directory name)")
    parser.add_argument("--max-revisions", type=int, default=2, help="Max revision cycles before escalation (default: 2)")
    args = parser.parse_args()

    project_id = args.project_id
    max_revisions = args.max_revisions
    project_dir = ANALYSES_DIR / project_id

    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    critique_history: list[dict] = []
    revision_count = 0

    while True:
        print(f"\n{'=' * 60}")
        print(f"Revision Loop — cycle {revision_count} (max {max_revisions})")
        print(f"{'=' * 60}\n")

        # Step 1: Run peer review
        exit_code = run_peer_review(project_id)
        if exit_code not in (0, 1):
            print(f"ERROR: run_peer_review.py exited with code {exit_code}", file=sys.stderr)
            return 1

        # Step 2: Read the review JSON
        review = read_peer_review_json(project_id)
        if review is None:
            print("ERROR: Could not read peer_review.json after review run.", file=sys.stderr)
            return 1

        critique_history.append(review)
        verdict = review.get("verdict", "UNKNOWN")

        # Step 3: PASS
        if verdict == "PASS":
            print(f"\n✅ PASS — {project_id} approved for delivery.")
            if revision_count > 0:
                log_lesson(
                    f"Peer review passed after {revision_count} revision(s) — {build_critique_summary(review)}",
                    project_id,
                )
            return 0

        # Step 4: REJECT
        if verdict == "REJECT":
            print(f"\n❌ REJECT — {project_id} has fatal flaws. Escalating.")
            fatal = [f for f in review.get("findings", []) if f.get("severity") == "BLOCKING"]
            for f in fatal:
                print(f"  FATAL: {f.get('finding', '')[:200]}")
            esc_path = write_escalation(project_id, review, critique_history)
            print(f"\n⚠️  Escalation written: {esc_path}")
            return 2

        # Step 5 / 6: REVISE
        if verdict == "REVISE":
            if revision_count >= max_revisions:
                # Step 6: exceeded max revisions — escalate
                print(f"\n⚠️  REVISE after {revision_count} cycle(s) — max revisions exceeded. Escalating.")
                esc_path = write_escalation(project_id, review, critique_history)
                print(f"  Escalation written: {esc_path}")
                log_lesson(
                    f"Could not pass peer review after {revision_count} revision(s) for {project_id} — recurring issues: {build_critique_summary(review)}",
                    project_id,
                )
                return 2

            # Step 5: write revision request for lead analyst
            revision_count += 1
            routing = review.get("routing_action", {})
            if routing:
                # Update revision_number in routing to match current cycle
                routing["revision_number"] = revision_count

            req_path = write_revision_request(project_id, revision_count, review)
            print(f"\n⚠️  REVISE — revision {revision_count}/{max_revisions}")
            print(f"  Revision request: {req_path}")

            re_route = (routing or {}).get("re_route", [])
            if re_route:
                print("\n  Routing instructions:")
                for entry in re_route:
                    print(f"    [{entry.get('priority','-')}] {entry.get('agent','?')}: {entry.get('instruction','')[:120]}")

            print(f"\n  Lead analyst: delegate to listed agents, then re-run this script.")
            # In a fully automated system, the loop would continue after agents
            # complete.  For now, we exit so the lead analyst can act.
            return 0

        # Unknown verdict
        print(f"ERROR: Unexpected verdict '{verdict}'", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
