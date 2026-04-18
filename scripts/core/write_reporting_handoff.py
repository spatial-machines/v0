"""Write a structured reporting handoff artifact.

Records what reports were generated, references upstream handoffs,
and declares the pipeline ready for Lead Analyst synthesis or archival.
"""
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
        description="Write a structured reporting handoff artifact."
    )
    parser.add_argument("run_id", help="Run identifier for this reporting run")
    parser.add_argument("summary", help="One-line summary of what was reported")
    parser.add_argument(
        "--report-files", nargs="*", default=[],
        help="Paths to generated report files (markdown, HTML)"
    )
    parser.add_argument(
        "--asset-manifest",
        help="Path to the report asset manifest JSON"
    )
    parser.add_argument(
        "--source-handoff",
        help="Path to upstream validation handoff JSON to reference"
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

    # Check report files exist
    report_file_checks = []
    for rf in args.report_files:
        p = Path(rf).expanduser().resolve()
        exists = p.exists()
        report_file_checks.append({
            "path": rf,
            "exists": exists,
            "size_bytes": p.stat().st_size if exists else None,
        })
        if not exists:
            warnings.append(f"report file not found: {rf}")

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
                    "overall_status": upstream_data.get("overall_status"),
                }
            except Exception:
                warnings.append(f"could not parse upstream handoff: {hp}")
        else:
            warnings.append(f"upstream handoff not found: {args.source_handoff}")

    # Load asset manifest for context
    asset_summary = None
    if args.asset_manifest:
        mp = Path(args.asset_manifest).expanduser().resolve()
        if mp.exists():
            try:
                manifest = json.loads(mp.read_text())
                asset_summary = {
                    "sources": len(manifest.get("sources", [])),
                    "processing_steps": len(manifest.get("processing_steps", [])),
                    "analysis_outputs": len(manifest.get("analysis", {}).get("output_files", [])),
                    "validation_status": manifest.get("validation", {}).get("overall_status"),
                }
            except Exception:
                warnings.append(f"could not parse asset manifest: {args.asset_manifest}")

    output_files = [item["path"] for item in report_file_checks if item["exists"]]

    handoff = {
        "handoff_type": "reporting",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "output_files": output_files,
        "report_files": report_file_checks,
        "asset_summary": asset_summary,
        "upstream_handoff": upstream,
        "provenance": build_handoff_provenance(
            args, Path(__file__), output_files=output_files
        ),
        "warnings": warnings,
        "ready_for": "synthesis",
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.reporting-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))

    print(f"=== Reporting Handoff ===")
    print(f"  run: {args.run_id}")
    print(f"  reports: {len(report_file_checks)}")
    print(f"  warnings: {len(warnings)}")
    print(f"  ready_for: {handoff['ready_for']}")
    print(f"wrote reporting handoff -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
