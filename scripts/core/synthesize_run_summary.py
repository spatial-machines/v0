"""Synthesize a structured run summary from upstream handoff artifacts.

Reads all available stage handoffs, extracts key findings, surfaces
warnings and caveats, and writes a lead summary markdown report.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"


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
        description="Synthesize a structured run summary from upstream handoffs."
    )
    parser.add_argument("run_id", help="Run identifier for the lead analyst run")
    parser.add_argument("task_summary", help="One-line summary of what this run accomplished")
    parser.add_argument("--provenance", help="Path to provenance JSON")
    parser.add_argument("--processing-handoff", help="Path to processing handoff JSON")
    parser.add_argument("--analysis-handoff", help="Path to analysis handoff JSON")
    parser.add_argument("--validation-handoff", help="Path to validation handoff JSON")
    parser.add_argument("--reporting-handoff", help="Path to reporting handoff JSON")
    parser.add_argument("--run-plan", help="Path to run plan JSON")
    parser.add_argument("-o", "--output", help="Output path for lead summary markdown")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all available handoffs
    provenance = load_json(args.provenance)
    processing = load_json(args.processing_handoff)
    analysis = load_json(args.analysis_handoff)
    validation = load_json(args.validation_handoff)
    reporting = load_json(args.reporting_handoff)
    run_plan = load_json(args.run_plan)

    now = datetime.now(UTC).isoformat()

    # --- Gather stage summaries ---
    stages_completed = []
    stages_missing = []
    all_warnings: list[str] = []
    all_caveats: list[str] = []
    key_outputs: list[str] = []

    # Retrieval / provenance
    if provenance:
        stages_completed.append("retrieval")
        sources = provenance.get("sources", [])
        for src in sources:
            ws = src.get("warnings", [])
            all_warnings.extend(f"[retrieval] {w}" for w in ws)
    else:
        stages_missing.append("retrieval")

    # Processing
    if processing:
        stages_completed.append("processing")
        key_outputs.extend(processing.get("output_files", []))
        all_warnings.extend(f"[processing] {w}" for w in processing.get("warnings", []))
    else:
        stages_missing.append("processing")

    # Analysis
    if analysis:
        stages_completed.append("analysis")
        key_outputs.extend(analysis.get("output_files", []))
        all_warnings.extend(f"[analysis] {w}" for w in analysis.get("warnings", []))
        all_caveats.extend(analysis.get("assumptions", []))
    else:
        stages_missing.append("analysis")

    # Validation
    validation_status = None
    validation_recommendation = None
    if validation:
        stages_completed.append("validation")
        validation_status = validation.get("overall_status", "unknown")
        validation_recommendation = validation.get("recommendation", "")
        all_warnings.extend(f"[validation] {w}" for w in validation.get("warnings", []))
    else:
        stages_missing.append("validation")

    # Reporting
    if reporting:
        stages_completed.append("reporting")
        key_outputs.extend(reporting.get("output_files", []))
        all_warnings.extend(f"[reporting] {w}" for w in reporting.get("warnings", []))
    else:
        stages_missing.append("reporting")

    # Deduplicate key outputs
    seen = set()
    unique_outputs = []
    for o in key_outputs:
        if o not in seen:
            seen.add(o)
            unique_outputs.append(o)
    key_outputs = unique_outputs

    # --- Build markdown summary ---
    lines: list[str] = []
    lines.append(f"# Lead Analyst Summary — {args.run_id}")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Task:** {args.task_summary}")
    if validation_status:
        lines.append(f"**QA Status:** {validation_status}")
    lines.append("")

    # Run plan reference
    if run_plan:
        lines.append("## Task Brief")
        lines.append("")
        lines.append(f"- **Task:** {run_plan.get('task', '(not specified)')}")
        lines.append(f"- **Geography:** {run_plan.get('geography', '(not specified)')}")
        sources_list = run_plan.get("sources", [])
        if sources_list:
            lines.append(f"- **Sources:** {', '.join(sources_list)}")
        expected = run_plan.get("expected_outputs", [])
        if expected:
            lines.append(f"- **Expected outputs:** {', '.join(expected)}")
        lines.append("")

    # Pipeline status
    lines.append("## Pipeline Status")
    lines.append("")
    for stage in ["retrieval", "processing", "analysis", "validation", "reporting"]:
        if stage in stages_completed:
            extra = ""
            if stage == "validation" and validation_status:
                extra = f" — {validation_status}"
            lines.append(f"- [x] {stage.capitalize()}{extra}")
        elif stage in stages_missing:
            lines.append(f"- [ ] {stage.capitalize()} — not found")
    lines.append("")
    lines.append(f"**{len(stages_completed)}/{len(stages_completed) + len(stages_missing)} stages complete.**")
    lines.append("")

    # Data sources
    if provenance:
        lines.append("## Data Sources")
        lines.append("")
        for src in provenance.get("sources", []):
            lines.append(f"- **{src.get('source_name', 'unknown')}**: {src.get('dataset_id', '?')} ({src.get('vintage', '?')})")
            lines.append(f"  - Geography: {src.get('geography_level', '?')}")
            lines.append(f"  - Format: {src.get('format', '?')}")
            lines.append(f"  - Retrieved: {src.get('retrieved_at', '?')}")
        lines.append("")

    # Processing summary
    if processing:
        lines.append("## Processing Summary")
        lines.append("")
        for step in processing.get("processing_steps", []):
            lines.append(f"- {step}")
        lines.append("")

    # Analysis outputs
    if analysis:
        lines.append("## Analysis Outputs")
        lines.append("")
        for step in analysis.get("analysis_steps", []):
            lines.append(f"- {step}")
        lines.append("")

    # Key outputs
    if key_outputs:
        lines.append("## Key Outputs")
        lines.append("")
        for o in key_outputs:
            # Check if the file actually exists
            p = (PROJECT_ROOT / o)
            exists = p.exists()
            status = "exists" if exists else "NOT FOUND"
            lines.append(f"- `{o}` — {status}")
        lines.append("")

    # QA status
    if validation:
        lines.append("## QA Status")
        lines.append("")
        lines.append(f"**Overall:** {validation_status}")
        lines.append("")
        if validation_recommendation:
            lines.append(f"**Recommendation:** {validation_recommendation}")
            lines.append("")
        checks = validation.get("check_summaries", [])
        if checks:
            lines.append("| Check | Status | Warnings |")
            lines.append("|---|---|---|")
            for c in checks:
                ws = c.get("warnings", [])
                w_text = "; ".join(ws) if ws else "—"
                lines.append(f"| {c.get('check', '?')} | {c.get('status', '?')} | {w_text} |")
            lines.append("")
        v_counts = {
            "total": validation.get("total_checks", 0),
            "pass": validation.get("checks_pass", 0),
            "warn": validation.get("checks_warn", 0),
            "fail": validation.get("checks_fail", 0),
        }
        lines.append(f"**Checks:** {v_counts['total']} total — {v_counts['pass']} pass, {v_counts['warn']} warn, {v_counts['fail']} fail")
        lines.append("")

    # Caveats and warnings
    if all_warnings or all_caveats:
        lines.append("## Caveats and Warnings")
        lines.append("")
        if all_warnings:
            lines.append("### Warnings")
            lines.append("")
            for w in all_warnings:
                lines.append(f"- {w}")
            lines.append("")
        if all_caveats:
            lines.append("### Assumptions")
            lines.append("")
            for c in all_caveats:
                lines.append(f"- {c}")
            lines.append("")

    # Recommendation
    lines.append("## Recommendation")
    lines.append("")
    if stages_missing:
        lines.append(f"**Pipeline incomplete.** Missing stages: {', '.join(stages_missing)}. "
                      "Resolve missing stages before final delivery.")
    elif validation_status == "REWORK NEEDED":
        lines.append("**Rework needed.** Validation flagged failures that must be addressed "
                      "before this run can be delivered. Review the QA status above for details.")
    elif validation_status == "PASS WITH WARNINGS":
        lines.append("**Ready for human review.** All pipeline stages completed. "
                      "Validation passed with warnings — review the caveats above to determine "
                      "if the outputs are acceptable for the intended use case.")
    elif validation_status == "PASS":
        lines.append("**Ready for delivery.** All pipeline stages completed and validation passed. "
                      "Human review recommended before final delivery.")
    else:
        lines.append("**Review required.** Pipeline completed but validation status is unclear. "
                      "Human review recommended.")
    lines.append("")

    lines.append("---")
    lines.append(f"*This summary was generated by the Lead Analyst orchestration layer. "
                 f"It reflects the state of recorded handoff artifacts, not independent analysis.*")
    lines.append("")

    content = "\n".join(lines)

    # Write output
    if args.output:
        out = Path(args.output).expanduser().resolve()
    else:
        out = REPORTS_DIR / f"{args.run_id.replace('milestone8-', '').replace('-lead-analyst', '')}_lead_summary.md"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content)

    print("=== Run Summary ===")
    print(f"  run: {args.run_id}")
    print(f"  stages: {len(stages_completed)} complete, {len(stages_missing)} missing")
    if validation_status:
        print(f"  validation: {validation_status}")
    print(f"  warnings: {len(all_warnings)}")
    print(f"  key outputs: {len(key_outputs)}")
    print(f"wrote lead summary -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
