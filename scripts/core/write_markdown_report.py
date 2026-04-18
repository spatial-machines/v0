"""Generate a structured markdown report from a report asset manifest.

Reads the consolidated asset manifest produced by collect_report_assets.py
and writes a markdown report with title, scope, methods, outputs, QA status,
caveats, and sources sections.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def build_report(manifest: dict, title: str, run_id: str) -> str:
    """Build the markdown report string from the asset manifest."""
    lines: list[str] = []

    validation = manifest.get("validation", {})
    overall_status = validation.get("overall_status", "UNKNOWN")

    # --- Title / Summary ---
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Run ID:** {run_id}  ")
    lines.append(f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}  ")
    lines.append(f"**QA Status:** {overall_status}")
    lines.append("")

    # --- Scope / Inputs ---
    lines.append("## Scope and Inputs")
    lines.append("")

    sources = manifest.get("sources", [])
    if sources:
        for src in sources:
            name = src.get("source_name", "Unknown")
            dataset = src.get("dataset_id", "unknown")
            vintage = src.get("vintage", "unknown")
            geo = src.get("geography_level", "unknown")
            lines.append(f"- **{name}**: `{dataset}` — {geo} level, vintage {vintage}")
    else:
        lines.append("- No provenance sources recorded.")
    lines.append("")

    run_ids = manifest.get("run_ids", {})
    upstream_refs = []
    for stage, rid in run_ids.items():
        if rid:
            upstream_refs.append(f"- {stage}: `{rid}`")
    if upstream_refs:
        lines.append("**Upstream run IDs:**")
        lines.extend(upstream_refs)
        lines.append("")

    # --- Key Findings (auto-extracted) ---
    key_findings = manifest.get("key_findings", [])
    if key_findings:
        lines.append("## Key Findings")
        lines.append("")
        for i, finding in enumerate(key_findings, 1):
            lines.append(f"{i}. {finding}")
        lines.append("")

    # --- Methods ---
    lines.append("## Methods")
    lines.append("")

    processing_steps = manifest.get("processing_steps", [])
    if processing_steps:
        lines.append("### Processing")
        lines.append("")
        for step in processing_steps:
            lines.append(f"- {step}")
        lines.append("")

    analysis = manifest.get("analysis", {})
    analysis_steps = analysis.get("steps", [])
    if analysis_steps:
        lines.append("### Analysis")
        lines.append("")
        for step in analysis_steps:
            lines.append(f"- {step}")
        lines.append("")

    assumptions = analysis.get("assumptions", [])
    if assumptions:
        lines.append("### Assumptions")
        lines.append("")
        for a in assumptions:
            lines.append(f"- {a}")
        lines.append("")

    # --- Outputs Created ---
    lines.append("## Outputs Created")
    lines.append("")

    output_files = analysis.get("output_files", [])
    file_checks = manifest.get("output_file_checks", [])
    check_map = {fc["declared_path"]: fc for fc in file_checks}

    if output_files:
        lines.append("| File | Status | Size |")
        lines.append("|---|---|---|")
        for f in output_files:
            fc = check_map.get(f, {})
            exists = fc.get("exists", False)
            status = "OK" if exists else "MISSING"
            size = fc.get("size_bytes")
            size_str = _format_size(size) if size else "—"
            lines.append(f"| `{f}` | {status} | {size_str} |")
        lines.append("")
    else:
        lines.append("No output files recorded in upstream handoffs.")
        lines.append("")

    # --- QA Status ---
    lines.append("## QA Status")
    lines.append("")
    lines.append(f"**Overall:** {overall_status}")
    lines.append("")

    checks_total = validation.get("total_checks", 0)
    checks_pass = validation.get("checks_pass", 0)
    checks_warn = validation.get("checks_warn", 0)
    checks_fail = validation.get("checks_fail", 0)
    lines.append(f"- Total checks: {checks_total}")
    lines.append(f"- Passed: {checks_pass}")
    lines.append(f"- Warnings: {checks_warn}")
    lines.append(f"- Failed: {checks_fail}")
    lines.append("")

    recommendation = validation.get("recommendation", "")
    if recommendation:
        lines.append(f"**Recommendation:** {recommendation}")
        lines.append("")

    check_summaries = validation.get("check_summaries", [])
    if check_summaries:
        lines.append("### Check Details")
        lines.append("")
        lines.append("| Check | Status | Warnings |")
        lines.append("|---|---|---|")
        for cs in check_summaries:
            name = cs.get("check", "?")
            status = cs.get("status", "?")
            warns = cs.get("warnings", [])
            warn_text = "; ".join(warns) if warns else "—"
            lines.append(f"| {name} | {status} | {warn_text} |")
        lines.append("")

    # --- Interpretation ---
    interpretation = manifest.get("interpretation", "")
    if interpretation:
        lines.append("## Interpretation")
        lines.append("")
        lines.append(interpretation)
        lines.append("")

    # --- Caveats ---
    lines.append("## Caveats")
    lines.append("")

    all_warnings = []
    all_warnings.extend(analysis.get("warnings", []))
    all_warnings.extend(validation.get("warnings", []))
    all_warnings.extend(manifest.get("warnings", []))

    if all_warnings:
        for w in all_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- No warnings or caveats recorded.")
    lines.append("")

    # --- Sources / Provenance ---
    lines.append("## Sources and Provenance")
    lines.append("")

    if sources:
        for src in sources:
            name = src.get("source_name", "Unknown")
            url = src.get("source_url", "")
            method = src.get("retrieval_method", "unknown")
            retrieved = src.get("retrieved_at", "unknown")
            stored = src.get("stored_path", "unknown")
            lines.append(f"### {name}")
            lines.append("")
            if url:
                lines.append(f"- **URL:** `{url}`")
            lines.append(f"- **Method:** {method}")
            lines.append(f"- **Retrieved:** {retrieved}")
            lines.append(f"- **Stored:** `{stored}`")
            notes = src.get("notes", [])
            if notes:
                for n in notes:
                    lines.append(f"- {n}")
            lines.append("")
    else:
        lines.append("No provenance information available.")
        lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by GIS Analyst Agent Team — Reporting Agent v1*")
    lines.append("")

    return "\n".join(lines)


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "—"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a markdown report from asset manifest.")
    parser.add_argument("manifest", help="Path to report asset manifest JSON")
    parser.add_argument("--title", default="GIS Analysis Report",
                        help="Report title")
    parser.add_argument("--run-id", default="unknown",
                        help="Run ID for this reporting run")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to write the markdown report")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = load_json(manifest_path)
    report = build_report(manifest, args.title, args.run_id)

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)

    print(f"wrote markdown report -> {out}")
    print(f"  sections: 7")
    print(f"  length: {len(report)} chars, {report.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
