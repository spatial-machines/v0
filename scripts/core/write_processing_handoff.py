from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

from handoff_utils import add_common_handoff_args, build_handoff_provenance

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"


def collect_logs(search_dirs: list[Path], patterns: list[str]) -> list[dict]:
    """Collect all processing log JSONs from the given directories."""
    logs = []
    for d in search_dirs:
        if not d.is_dir():
            continue
        for pattern in patterns:
            for path in sorted(d.glob(pattern)):
                try:
                    logs.append(json.loads(path.read_text()))
                except Exception:
                    pass
    return logs


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Write a processing handoff artifact.")
    parser.add_argument("run_id", help="Run identifier")
    parser.add_argument("summary", help="One-line summary of what was processed")
    parser.add_argument(
        "--output-files", nargs="*", default=[],
        help="Paths to final output files to list in handoff"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for handoff (default: runs/)"
    )
    add_common_handoff_args(parser)
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)

    interim_dir = PROJECT_ROOT / "data" / "interim"
    processed_dir = PROJECT_ROOT / "data" / "processed"

    log_patterns = [
        "*.extraction.json",
        "*.processing.json",
        "*.join.json",
        "*.derivation.json",
    ]

    processing_logs = collect_logs([interim_dir, processed_dir], log_patterns)

    # Summarize steps and warnings
    all_steps = []
    all_warnings = []
    for log in processing_logs:
        step_name = log.get("step", "unknown")
        for s in log.get("processing_steps", []):
            all_steps.append(f"[{step_name}] {s}")
        for w in log.get("warnings", []):
            all_warnings.append(f"[{step_name}] {w}")
        # join diagnostics
        if "diagnostics" in log:
            all_steps.append(f"[{step_name}] diagnostics: {json.dumps(log['diagnostics'])}")

    handoff = {
        "handoff_type": "processing",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "output_files": args.output_files,
        "processing_steps": all_steps,
        "warnings": all_warnings,
        "processing_logs": [
            log.get("step", "unknown") + ": " + log.get("output", "?")
            for log in processing_logs
        ],
        "provenance": build_handoff_provenance(
            args, Path(__file__), output_files=args.output_files
        ),
        "ready_for": "analysis",
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.processing-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))
    print(f"wrote processing handoff -> {out}")
    print(f"  steps: {len(all_steps)}")
    print(f"  warnings: {len(all_warnings)}")
    print(f"  output files: {len(args.output_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
