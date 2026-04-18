"""Write a Lead Analyst orchestration handoff artifact.

Declares the run ready for human review, references the run plan and
all upstream handoffs, includes pipeline status and synthesis summary.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

from handoff_utils import add_common_handoff_args, build_handoff_provenance

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"


def load_json(path_str: str | None) -> dict | None:
    if not path_str:
        return None
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Write a Lead Analyst orchestration handoff artifact."
    )
    parser.add_argument("run_id", help="Run identifier for the lead analyst run")
    parser.add_argument("summary", help="One-line summary of the orchestration outcome")
    parser.add_argument("--run-plan", help="Path to run plan JSON")
    parser.add_argument("--provenance", help="Path to provenance JSON")
    parser.add_argument("--processing-handoff", help="Path to processing handoff JSON")
    parser.add_argument("--analysis-handoff", help="Path to analysis handoff JSON")
    parser.add_argument("--validation-handoff", help="Path to validation handoff JSON")
    parser.add_argument("--reporting-handoff", help="Path to reporting handoff JSON")
    parser.add_argument(
        "--lead-summary",
        help="Path to the lead summary markdown produced by synthesize_run_summary.py"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for handoff (default: runs/)"
    )
    add_common_handoff_args(parser)
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    # Load run plan
    run_plan_ref = None
    if args.run_plan:
        plan = load_json(args.run_plan)
        if plan:
            run_plan_ref = {
                "run_id": plan.get("run_id", "unknown"),
                "task": plan.get("task", "unknown"),
                "geography": plan.get("geography", ""),
                "expected_stages": plan.get("expected_stages", []),
            }
        else:
            warnings.append(f"could not load run plan: {args.run_plan}")

    # Check each upstream stage
    stage_args = {
        "retrieval": args.provenance,
        "processing": args.processing_handoff,
        "analysis": args.analysis_handoff,
        "validation": args.validation_handoff,
        "reporting": args.reporting_handoff,
    }

    upstream_handoffs = {}
    stages_complete = []
    stages_missing = []

    for stage, path_str in stage_args.items():
        data = load_json(path_str)
        if data:
            stages_complete.append(stage)
            ref = {
                "run_id": data.get("run_id", "unknown"),
                "handoff_type": data.get("handoff_type", stage),
            }
            if stage == "validation":
                ref["overall_status"] = data.get("overall_status", "unknown")
            if stage == "reporting":
                ref["output_files"] = data.get("output_files", [])
            upstream_handoffs[stage] = ref
        else:
            stages_missing.append(stage)
            if path_str:
                warnings.append(f"{stage} handoff not found: {path_str}")

    # Determine validation status
    validation_status = None
    if "validation" in upstream_handoffs:
        validation_status = upstream_handoffs["validation"].get("overall_status")

    # Collect all key output files from upstream
    all_outputs = []
    for stage in ["processing", "analysis", "reporting"]:
        if stage in upstream_handoffs:
            data = load_json(stage_args[stage])
            if data:
                all_outputs.extend(data.get("output_files", []))

    # Deduplicate
    seen = set()
    unique_outputs = []
    for o in all_outputs:
        if o not in seen:
            seen.add(o)
            unique_outputs.append(o)

    # Check lead summary exists
    lead_summary_ref = None
    if args.lead_summary:
        p = Path(args.lead_summary).expanduser().resolve()
        if p.exists():
            lead_summary_ref = {
                "path": str(p.relative_to(PROJECT_ROOT)),
                "exists": True,
                "size_bytes": p.stat().st_size,
            }
        else:
            warnings.append(f"lead summary not found: {args.lead_summary}")

    # Determine readiness
    if stages_missing:
        ready_for = "review-incomplete"
    elif validation_status == "REWORK NEEDED":
        ready_for = "rework"
    else:
        ready_for = "human-review"

    handoff = {
        "handoff_type": "lead-analyst",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "run_plan": run_plan_ref,
        "pipeline_status": {
            "stages_complete": stages_complete,
            "stages_missing": stages_missing,
            "total_stages": len(stages_complete) + len(stages_missing),
            "pipeline_complete": len(stages_missing) == 0,
        },
        "validation_status": validation_status,
        "upstream_handoffs": upstream_handoffs,
        "lead_summary": lead_summary_ref,
        "key_outputs": unique_outputs,
        "provenance": build_handoff_provenance(
            args, Path(__file__), output_files=unique_outputs
        ),
        "warnings": warnings,
        "ready_for": ready_for,
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.lead-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))

    print("=== Lead Analyst Handoff ===")
    print(f"  run: {args.run_id}")
    print(f"  stages: {len(stages_complete)} complete, {len(stages_missing)} missing")
    if validation_status:
        print(f"  validation: {validation_status}")
    print(f"  key outputs: {len(unique_outputs)}")
    print(f"  warnings: {len(warnings)}")
    print(f"  ready_for: {ready_for}")
    print(f"wrote lead handoff -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
