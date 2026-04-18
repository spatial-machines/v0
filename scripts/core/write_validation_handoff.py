from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

from handoff_utils import add_common_handoff_args, build_handoff_provenance

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Aggregate validation check results into a structured validation handoff."
    )
    parser.add_argument("run_id", help="Run identifier")
    parser.add_argument("summary", help="One-line summary of what was validated")
    parser.add_argument(
        "--check-files", nargs="*", default=[],
        help="Paths to individual validation check JSON files to aggregate"
    )
    parser.add_argument(
        "--source-handoff",
        help="Path to upstream analysis handoff JSON to reference"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for handoff (default: runs/)"
    )
    add_common_handoff_args(parser)
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Load individual check results
    all_checks = []
    all_warnings = []
    check_summaries = []

    for cf in args.check_files:
        p = Path(cf).expanduser().resolve()
        if not p.exists():
            all_warnings.append(f"check file not found: {cf}")
            continue
        try:
            data = json.loads(p.read_text())
        except Exception as e:
            all_warnings.append(f"could not parse check file {cf}: {e}")
            continue

        check_name = data.get("check", p.stem)
        check_status = data.get("overall_status", "UNKNOWN")
        check_summaries.append({
            "check": check_name,
            "status": check_status,
            "source_file": cf,
            "warnings": data.get("warnings", []),
        })

        for w in data.get("warnings", []):
            all_warnings.append(f"[{check_name}] {w}")

        for c in data.get("checks", data.get("results", [])):
            all_checks.append({
                "group": check_name,
                "check": c.get("check", "?"),
                "status": c.get("status", "?"),
                "message": c.get("message", ""),
            })

    # Determine overall outcome
    statuses = [cs["status"] for cs in check_summaries]
    if "FAIL" in statuses:
        overall = "REWORK NEEDED"
        recommendation = (
            "One or more checks failed. Review the failing checks and fix upstream "
            "data or processing before proceeding to reporting."
        )
    elif "WARN" in statuses:
        overall = "PASS WITH WARNINGS"
        recommendation = (
            "All checks passed but warnings were raised. Review warnings to determine "
            "if they are acceptable for the intended use case before proceeding."
        )
    elif statuses:
        overall = "PASS"
        recommendation = "All checks passed. Output is ready for reporting."
    else:
        overall = "NO CHECKS RUN"
        recommendation = "No validation checks were loaded. Verify check file paths."

    # Reference upstream handoff
    upstream = None
    if args.source_handoff:
        hp = Path(args.source_handoff).expanduser().resolve()
        if hp.exists():
            try:
                upstream_data = json.loads(hp.read_text())
                upstream = {
                    "run_id": upstream_data.get("run_id", "unknown"),
                    "handoff_type": upstream_data.get("handoff_type", "unknown"),
                    "output_files": upstream_data.get("output_files", []),
                }
            except Exception:
                all_warnings.append(f"could not parse upstream handoff: {hp}")

    handoff = {
        "handoff_type": "validation",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "overall_status": overall,
        "recommendation": recommendation,
        "check_summaries": check_summaries,
        "total_checks": len(all_checks),
        "checks_pass": sum(1 for c in all_checks if c["status"] == "PASS"),
        "checks_warn": sum(1 for c in all_checks if c["status"] == "WARN"),
        "checks_fail": sum(1 for c in all_checks if c["status"] == "FAIL"),
        "all_checks": all_checks,
        "provenance": build_handoff_provenance(
            args, Path(__file__), output_files=args.check_files
        ),
        "warnings": all_warnings,
        "upstream_handoff": upstream,
        "ready_for": "reporting" if overall == "PASS" else "review",
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.validation-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))

    print(f"=== Validation Handoff: {overall} ===")
    print(f"  run: {args.run_id}")
    print(f"  checks: {handoff['total_checks']} total "
          f"({handoff['checks_pass']} pass, {handoff['checks_warn']} warn, {handoff['checks_fail']} fail)")
    print(f"  warnings: {len(all_warnings)}")
    print(f"  recommendation: {recommendation}")
    print(f"  ready_for: {handoff['ready_for']}")
    print(f"wrote validation handoff -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
