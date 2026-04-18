"""Check pipeline status by inspecting available upstream handoff artifacts.

Looks for expected stage handoffs in the runs/ directory and reports
which stages are complete, which are missing, and the overall pipeline state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"

# Map of stage name -> (handoff_type field, filename suffix pattern)
STAGE_SPECS = {
    "retrieval": ("provenance", ".provenance.json"),
    "processing": ("processing", ".processing-handoff.json"),
    "analysis": ("analysis", ".analysis-handoff.json"),
    "validation": ("validation", ".validation-handoff.json"),
    "reporting": ("reporting", ".reporting-handoff.json"),
}


def find_handoff(stage: str, suffix: str, run_prefix: str | None, runs_dir: Path = RUNS_DIR) -> Path | None:
    """Find a handoff file for a stage, optionally scoped to a run prefix."""
    candidates = sorted(runs_dir.glob(f"*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
    if run_prefix:
        for c in candidates:
            if run_prefix in c.name:
                return c
    return candidates[0] if candidates else None


def load_handoff(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Check pipeline status by inspecting handoff artifacts."
    )
    parser.add_argument(
        "--run-prefix", default=None,
        help="Filter handoffs to those matching this prefix (e.g. 'milestone' or 'ne-tracts')"
    )
    parser.add_argument(
        "--stages", nargs="*",
        default=["retrieval", "processing", "analysis", "validation", "reporting"],
        help="Pipeline stages to check (default: all five)"
    )
    parser.add_argument(
        "--run-plan",
        help="Path to a run plan JSON — stages will be read from the plan"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output status as JSON instead of human-readable text"
    )
    parser.add_argument(
        "--runs-dir", default=None,
        help="Override runs directory to scan (default: runs/)"
    )
    args = parser.parse_args()

    # If a run plan is provided, use its expected stages
    if args.run_plan:
        plan_path = Path(args.run_plan).expanduser().resolve()
        if plan_path.exists():
            try:
                plan = json.loads(plan_path.read_text())
                args.stages = plan.get("expected_stages", args.stages)
                if not args.run_prefix:
                    args.run_prefix = plan.get("run_id")
            except Exception:
                print(f"WARNING: could not parse run plan: {args.run_plan}", file=sys.stderr)

    active_runs_dir = Path(args.runs_dir).expanduser().resolve() if args.runs_dir else RUNS_DIR

    stages_status = []
    for stage in args.stages:
        if stage not in STAGE_SPECS:
            stages_status.append({
                "stage": stage,
                "status": "unknown",
                "message": f"unknown stage type: {stage}",
                "handoff_file": None,
            })
            continue

        handoff_type, suffix = STAGE_SPECS[stage]
        path = find_handoff(stage, suffix, args.run_prefix, active_runs_dir)

        if path is None:
            stages_status.append({
                "stage": stage,
                "status": "missing",
                "message": "no handoff artifact found",
                "handoff_file": None,
            })
            continue

        data = load_handoff(path)
        if data is None:
            stages_status.append({
                "stage": stage,
                "status": "error",
                "message": f"could not parse {path.name}",
                "handoff_file": str(path.relative_to(PROJECT_ROOT)),
            })
            continue

        info = {
            "stage": stage,
            "status": "complete",
            "handoff_file": str(path.relative_to(PROJECT_ROOT)),
            "run_id": data.get("run_id", "unknown"),
            "created_at": data.get("created_at", "unknown"),
        }

        # Add stage-specific details
        if stage == "validation":
            info["overall_status"] = data.get("overall_status", "unknown")
            info["recommendation"] = data.get("recommendation", "")
            warnings = data.get("warnings", [])
            info["warning_count"] = len(warnings)
        elif stage == "reporting":
            info["ready_for"] = data.get("ready_for", "unknown")
            info["output_files"] = data.get("output_files", [])

        stages_status.append(info)

    complete = [s for s in stages_status if s["status"] == "complete"]
    missing = [s for s in stages_status if s["status"] == "missing"]

    summary = {
        "checked_stages": len(stages_status),
        "complete": len(complete),
        "missing": len(missing),
        "stages": stages_status,
        "pipeline_ready": len(missing) == 0,
    }

    # Add validation status if available
    for s in stages_status:
        if s["stage"] == "validation" and s["status"] == "complete":
            summary["validation_status"] = s.get("overall_status", "unknown")
            break

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("=== Pipeline Status ===")
        for s in stages_status:
            icon = "OK" if s["status"] == "complete" else "MISSING" if s["status"] == "missing" else "ERROR"
            line = f"  [{icon}] {s['stage']}"
            if s.get("handoff_file"):
                line += f"  ({s['handoff_file']})"
            if s.get("overall_status"):
                line += f"  -> {s['overall_status']}"
            print(line)

        print(f"\n  {len(complete)}/{len(stages_status)} stages complete")
        if missing:
            print(f"  missing: {', '.join(s['stage'] for s in missing)}")
        if summary.get("validation_status"):
            print(f"  validation: {summary['validation_status']}")
        print(f"  pipeline ready: {'yes' if summary['pipeline_ready'] else 'no'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
