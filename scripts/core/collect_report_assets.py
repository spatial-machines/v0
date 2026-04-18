"""Collect and normalize upstream artifact references for report generation.

Reads provenance, processing, analysis, and validation handoff JSONs,
resolves artifact paths, checks file existence, and writes a consolidated
asset manifest that the report generators consume.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict | None:
    """Load a JSON file, returning None on failure."""
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def resolve_path(raw: str) -> Path:
    """Resolve a path that may be absolute (container /app/) or relative."""
    p = Path(raw)
    # Container paths start with /app/ — strip to make relative to project root
    if str(p).startswith("/app/"):
        return PROJECT_ROOT / str(p)[5:]
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def check_files(paths: list[str]) -> list[dict]:
    """Check existence and size of a list of file paths."""
    results = []
    for raw in paths:
        rp = resolve_path(raw)
        exists = rp.exists()
        results.append({
            "declared_path": raw,
            "resolved_path": str(rp),
            "exists": exists,
            "size_bytes": rp.stat().st_size if exists else None,
        })
    return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect upstream artifact references into a consolidated asset manifest."
    )
    parser.add_argument(
        "--provenance",
        help="Path to provenance JSON from retrieval stage"
    )
    parser.add_argument(
        "--processing-handoff",
        help="Path to processing handoff JSON"
    )
    parser.add_argument(
        "--analysis-handoff",
        help="Path to analysis handoff JSON"
    )
    parser.add_argument(
        "--validation-handoff", required=True,
        help="Path to validation handoff JSON"
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="Path to write the asset manifest JSON"
    )
    parser.add_argument(
        "--scan-outputs",
        help="Path to outputs/ directory — auto-discover maps, tables, web, and report files"
    )
    args = parser.parse_args()

    warnings: list[str] = []

    # --- Load validation handoff (required) ---
    val_path = Path(args.validation_handoff).expanduser().resolve()
    validation = load_json(val_path)
    if validation is None:
        print(f"ERROR: could not load validation handoff: {val_path}", file=sys.stderr)
        return 1

    # --- Load optional upstream handoffs ---
    provenance = None
    if args.provenance:
        provenance = load_json(Path(args.provenance).expanduser().resolve())
        if provenance is None:
            warnings.append(f"could not load provenance: {args.provenance}")

    processing = None
    if args.processing_handoff:
        processing = load_json(Path(args.processing_handoff).expanduser().resolve())
        if processing is None:
            warnings.append(f"could not load processing handoff: {args.processing_handoff}")

    analysis = None
    if args.analysis_handoff:
        analysis = load_json(Path(args.analysis_handoff).expanduser().resolve())
        if analysis is None:
            warnings.append(f"could not load analysis handoff: {args.analysis_handoff}")
    # Also try to load analysis from validation upstream reference
    if analysis is None and validation.get("upstream_handoff"):
        upstream = validation["upstream_handoff"]
        if upstream.get("handoff_type") == "analysis":
            # Try to find the analysis handoff in runs/
            runs_dir = PROJECT_ROOT / "runs"
            candidate = runs_dir / f"{upstream['run_id']}.analysis-handoff.json"
            if candidate.exists():
                analysis = load_json(candidate)

    # --- Collect all declared output files ---
    all_output_files: list[str] = []
    if analysis:
        all_output_files.extend(analysis.get("output_files", []))
    if processing:
        all_output_files.extend(processing.get("output_files", []))

    # --- Auto-discover outputs if --scan-outputs provided ---
    discovered_maps: list[str] = []
    discovered_tables: list[str] = []
    discovered_web: list[str] = []
    discovered_charts: list[dict] = []
    if args.scan_outputs:
        scan_dir = Path(args.scan_outputs).expanduser().resolve()
        if scan_dir.is_dir():
            charts_dir = scan_dir / "charts"
            for png in sorted(scan_dir.rglob("*.png")):
                is_chart = charts_dir in png.parents
                rel = str(png.relative_to(scan_dir.parent.parent))  # relative to analysis root
                if is_chart:
                    # Charts carry a sidecar with chart_family for grouping in the report.
                    sc_path = png.with_suffix(".style.json")
                    sc_data: dict = {}
                    if sc_path.exists():
                        try:
                            sc_data = json.loads(sc_path.read_text()) or {}
                        except Exception:
                            sc_data = {}
                    discovered_charts.append({
                        "path": rel,
                        "svg": (str(png.with_suffix(".svg").relative_to(scan_dir.parent.parent))
                                if png.with_suffix(".svg").exists() else None),
                        "family": sc_data.get("chart_family"),
                        "kind": sc_data.get("chart_kind"),
                        "field": sc_data.get("field"),
                        "title": sc_data.get("title"),
                        "pairs_with": sc_data.get("pairs_with"),
                    })
                else:
                    discovered_maps.append(rel)
                if rel not in all_output_files:
                    all_output_files.append(str(png))
            for csv in sorted(scan_dir.rglob("*.csv")):
                rel = str(csv.relative_to(scan_dir.parent.parent))
                discovered_tables.append(rel)
                if rel not in all_output_files:
                    all_output_files.append(str(csv))
            for html in sorted(scan_dir.rglob("*.html")):
                rel = str(html.relative_to(scan_dir.parent.parent))
                discovered_web.append(rel)
                if rel not in all_output_files:
                    all_output_files.append(str(html))

    file_checks = check_files(all_output_files)
    missing = [fc for fc in file_checks if not fc["exists"]]
    if missing:
        for m in missing:
            warnings.append(f"declared output file not found: {m['declared_path']}")

    # --- Collect sources from provenance ---
    sources = []
    if provenance:
        sources = provenance.get("sources", [])

    # --- Collect processing steps ---
    processing_steps = []
    if processing:
        processing_steps = processing.get("processing_steps", [])

    # --- Collect analysis info ---
    analysis_steps = []
    analysis_assumptions = []
    analysis_warnings = []
    if analysis:
        analysis_steps = analysis.get("analysis_steps", [])
        analysis_assumptions = analysis.get("assumptions", [])
        analysis_warnings = analysis.get("warnings", [])

    # --- Collect validation info ---
    validation_status = validation.get("overall_status", "UNKNOWN")
    validation_recommendation = validation.get("recommendation", "")
    check_summaries = validation.get("check_summaries", [])
    validation_warnings = validation.get("warnings", [])
    checks_total = validation.get("total_checks", 0)
    checks_pass = validation.get("checks_pass", 0)
    checks_warn = validation.get("checks_warn", 0)
    checks_fail = validation.get("checks_fail", 0)

    # --- Build asset manifest ---
    manifest = {
        "manifest_type": "report-assets",
        "created_at": datetime.now(UTC).isoformat(),
        "run_ids": {
            "provenance": provenance.get("run_id") if provenance else None,
            "processing": processing.get("run_id") if processing else None,
            "analysis": analysis.get("run_id") if analysis else None,
            "validation": validation.get("run_id"),
        },
        "sources": sources,
        "processing_steps": processing_steps,
        "analysis": {
            "steps": analysis_steps,
            "assumptions": analysis_assumptions,
            "warnings": analysis_warnings,
            "output_files": analysis.get("output_files", []) if analysis else [],
        },
        "validation": {
            "overall_status": validation_status,
            "recommendation": validation_recommendation,
            "check_summaries": check_summaries,
            "total_checks": checks_total,
            "checks_pass": checks_pass,
            "checks_warn": checks_warn,
            "checks_fail": checks_fail,
            "warnings": validation_warnings,
        },
        "output_file_checks": file_checks,
        "discovered_outputs": {
            "maps": discovered_maps,
            "charts": discovered_charts,
            "tables": discovered_tables,
            "web": discovered_web,
        },
        "key_findings": [],
        "interpretation": "",
        "warnings": warnings,
    }

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))

    print(f"wrote asset manifest -> {out}")
    print(f"  sources: {len(sources)}")
    print(f"  processing steps: {len(processing_steps)}")
    print(f"  analysis outputs: {len(analysis.get('output_files', [])) if analysis else 0}")
    print(f"  validation status: {validation_status}")
    print(f"  file checks: {len(file_checks)} ({len(missing)} missing)")
    print(f"  warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
