"""Create a structured run plan / task brief for a GIS analysis run.

Records the task scope, geography, expected data sources, pipeline stages,
and desired outputs so downstream agents and reviewers have a clear contract.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a structured run plan / task brief."
    )
    parser.add_argument("run_id", help="Run identifier (e.g. milestone8-ne-tracts-lead-analyst)")
    parser.add_argument("task", help="One-line description of the analysis task")
    parser.add_argument(
        "--geography", default="",
        help="Geographic scope (e.g. 'Nebraska census tracts')"
    )
    parser.add_argument(
        "--sources", nargs="*", default=[],
        help="Expected data sources (e.g. 'Census TIGER 2024' 'ACS demographics')"
    )
    parser.add_argument(
        "--stages", nargs="*",
        default=["retrieval", "processing", "analysis", "validation", "reporting"],
        help="Expected pipeline stages (default: all five)"
    )
    parser.add_argument(
        "--expected-outputs", nargs="*", default=[],
        help="Expected output types or files (e.g. 'choropleth map' 'summary table' 'HTML report')"
    )
    parser.add_argument(
        "--notes", nargs="*", default=[],
        help="Additional notes for the run plan"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for run plan (default: runs/)"
    )
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "plan_type": "run-plan",
        "run_id": args.run_id,
        "task": args.task,
        "geography": args.geography,
        "sources": args.sources,
        "expected_stages": args.stages,
        "expected_outputs": args.expected_outputs,
        "created_at": datetime.now(UTC).isoformat(),
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.run-plan.json"
    out.write_text(json.dumps(plan, indent=2))

    print("=== Run Plan ===")
    print(f"  run: {args.run_id}")
    print(f"  task: {args.task}")
    print(f"  geography: {args.geography or '(not specified)'}")
    print(f"  sources: {len(args.sources)}")
    print(f"  stages: {', '.join(args.stages)}")
    print(f"  expected outputs: {len(args.expected_outputs)}")
    print(f"wrote run plan -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
