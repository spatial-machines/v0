"""Write a structured retrospective for a completed run or milestone chain.

Reads upstream handoff artifacts and produces a markdown retrospective
that captures what happened, what worked, what didn't, and suggested
improvements. Writes to memory/retrospectives/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_DIR = PROJECT_ROOT / "docs" / "memory"
RETRO_DIR = MEMORY_DIR / "retrospectives"


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


def summarize_handoff(data: dict | None, stage: str) -> list[str]:
    """Extract key facts from a handoff dict."""
    if not data:
        return [f"- **{stage}**: *(not provided)*"]
    lines = []
    run_id = data.get("run_id", "unknown")
    summary = data.get("summary", "")
    status = data.get("overall_status") or data.get("validation_status") or ""
    warnings = data.get("warnings", [])
    ready_for = data.get("ready_for", "")
    output_files = data.get("output_files", [])

    header = f"- **{stage}** (run: `{run_id}`)"
    if status:
        header += f" — {status}"
    lines.append(header)
    if summary:
        lines.append(f"  - {summary}")
    if output_files:
        lines.append(f"  - outputs: {len(output_files)} files")
    if warnings:
        for w in warnings[:5]:
            lines.append(f"  - warning: {w}")
    if ready_for:
        lines.append(f"  - ready_for: {ready_for}")
    return lines


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Write a structured run retrospective."
    )
    parser.add_argument("run_id", help="Run or milestone identifier")
    parser.add_argument("title", help="Retrospective title")
    parser.add_argument("--provenance", help="Path to provenance JSON")
    parser.add_argument("--processing-handoff", help="Path to processing handoff JSON")
    parser.add_argument("--analysis-handoff", help="Path to analysis handoff JSON")
    parser.add_argument("--validation-handoff", help="Path to validation handoff JSON")
    parser.add_argument("--reporting-handoff", help="Path to reporting handoff JSON")
    parser.add_argument("--lead-handoff", help="Path to lead analyst handoff JSON")
    parser.add_argument(
        "--what-worked",
        nargs="*",
        default=[],
        help="Things that went well",
    )
    parser.add_argument(
        "--what-didnt",
        nargs="*",
        default=[],
        help="Things that could be improved",
    )
    parser.add_argument(
        "--suggestions",
        nargs="*",
        default=[],
        help="Suggested improvements for future runs",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output path (default: memory/retrospectives/<run_id>.retro.md)",
    )
    args = parser.parse_args()

    RETRO_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()

    # Load handoffs
    provenance = load_json(args.provenance)
    processing = load_json(args.processing_handoff)
    analysis = load_json(args.analysis_handoff)
    validation = load_json(args.validation_handoff)
    reporting = load_json(args.reporting_handoff)
    lead = load_json(args.lead_handoff)

    # Determine overall status
    overall_status = "unknown"
    if lead:
        overall_status = lead.get("ready_for", "unknown")
    elif validation:
        overall_status = validation.get("overall_status", "unknown")

    # Count stages provided
    stages = {
        "retrieval": provenance,
        "processing": processing,
        "analysis": analysis,
        "validation": validation,
        "reporting": reporting,
        "lead-analyst": lead,
    }
    stages_present = [k for k, v in stages.items() if v is not None]

    # --- Build markdown ---
    lines = [
        f"# Retrospective — {args.title}",
        "",
        f"**Run ID**: `{args.run_id}`",
        f"**Date**: {now}",
        f"**Overall outcome**: {overall_status}",
        f"**Stages covered**: {', '.join(stages_present)}",
        "",
        "---",
        "",
        "## Pipeline Summary",
        "",
    ]

    for stage_name, stage_data in stages.items():
        lines.extend(summarize_handoff(stage_data, stage_name))

    lines += ["", "---", "", "## What Worked", ""]
    if args.what_worked:
        for item in args.what_worked:
            lines.append(f"- {item}")
    else:
        lines.append("- Full pipeline ran end-to-end with structured handoffs")
        if provenance:
            lines.append("- Data retrieval with provenance tracking")
        if validation:
            status = validation.get("overall_status", "")
            if status in ("PASS", "PASS WITH WARNINGS"):
                lines.append(f"- Independent validation completed: {status}")
        if reporting:
            lines.append("- Reports generated from upstream artifacts")
        if lead:
            lines.append("- Lead analyst synthesis produced honest summary")

    lines += ["", "## What Could Be Improved", ""]
    if args.what_didnt:
        for item in args.what_didnt:
            lines.append(f"- {item}")
    else:
        # Auto-detect from warnings
        all_warnings = []
        for stage_data in stages.values():
            if stage_data and "warnings" in stage_data:
                all_warnings.extend(stage_data["warnings"])
        if all_warnings:
            for w in all_warnings[:5]:
                lines.append(f"- {w}")
        else:
            lines.append("- *(no specific issues detected from artifacts)*")

    lines += ["", "## Suggested Improvements", ""]
    if args.suggestions:
        for item in args.suggestions:
            lines.append(f"- {item}")
    else:
        lines.append("- Review any PASS WITH WARNINGS items for data quality fixes")
        lines.append("- Consider expanding demographic coverage beyond demo subset")
        lines.append("- Add automated re-run capability after upstream fixes")

    lines += [
        "",
        "---",
        "",
        "*Generated by `scripts/write_retrospective.py`*",
        "",
    ]

    out_path = args.output or str(RETRO_DIR / f"{args.run_id}.retro.md")
    out = Path(out_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))

    print("=== Retrospective Written ===")
    print(f"  run:    {args.run_id}")
    print(f"  title:  {args.title}")
    print(f"  stages: {', '.join(stages_present)}")
    print(f"  status: {overall_status}")
    print(f"wrote retrospective -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
