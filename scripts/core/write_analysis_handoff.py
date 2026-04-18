from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

from handoff_utils import add_common_handoff_args, build_handoff_provenance

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def collect_logs(search_dirs: list[Path], patterns: list[str]) -> list[dict]:
    """Collect analysis log JSONs from the given directories."""
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

    parser = argparse.ArgumentParser(description="Write an analysis handoff artifact.")
    parser.add_argument("run_id", help="Run identifier")
    parser.add_argument("summary", help="One-line summary of analysis performed")
    parser.add_argument(
        "--output-files", nargs="*", default=[],
        help="Paths to analysis output files (maps, tables, etc.)"
    )
    parser.add_argument(
        "--source-handoff",
        help="Path to upstream processing handoff JSON to reference"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for handoff (default: runs/)"
    )
    parser.add_argument(
        "--recommended-charts", default=None,
        help=(
            "Path to a JSON file describing charts cartography should produce "
            "from this analysis's outputs. Shape: "
            '[{"family":"distribution","kind":"histogram","field":"poverty_rate"}, '
            '{"family":"comparison","kind":"lollipop","field":"poverty_rate","top_n":15}]. '
            "See docs/wiki/standards/CHART_DESIGN_STANDARD.md for the pairing rule."
        ),
    )
    add_common_handoff_args(parser)
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Collect analysis logs from outputs/
    maps_dir = OUTPUTS_DIR / "maps"
    tables_dir = OUTPUTS_DIR / "tables"

    log_patterns = [
        "*.summary-stats.json",
        "*.choropleth.json",
        "*.top-n.json",
    ]

    analysis_logs = collect_logs([maps_dir, tables_dir], log_patterns)

    # Summarize steps, warnings, and assumptions
    all_steps = []
    all_warnings = []
    all_assumptions = []
    for log in analysis_logs:
        step_name = log.get("step", "unknown")
        output = log.get("output", "?")
        all_steps.append(f"[{step_name}] -> {output}")
        for w in log.get("warnings", []):
            all_warnings.append(f"[{step_name}] {w}")
        for a in log.get("assumptions", []):
            all_assumptions.append(f"[{step_name}] {a}")

    # Load recommended charts if provided (spatial-stats → cartography
    # contract per docs/wiki/standards/CHART_DESIGN_STANDARD.md pairing rule).
    recommended_charts: list[dict] = []
    if args.recommended_charts:
        rc_path = Path(args.recommended_charts).expanduser().resolve()
        if rc_path.exists():
            try:
                rc_data = json.loads(rc_path.read_text())
                if isinstance(rc_data, list):
                    recommended_charts = rc_data
            except Exception as exc:
                all_warnings.append(
                    f"could not parse recommended-charts file {rc_path}: {exc}"
                )
        else:
            all_warnings.append(f"recommended-charts file not found: {rc_path}")

    # Reference upstream handoff if provided
    upstream = None
    if args.source_handoff:
        hp = Path(args.source_handoff).expanduser().resolve()
        if hp.exists():
            try:
                upstream = json.loads(hp.read_text())
            except Exception:
                all_warnings.append(f"could not parse upstream handoff: {hp}")

    handoff = {
        "handoff_type": "analysis",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "output_files": args.output_files,
        "analysis_steps": all_steps,
        "assumptions": all_assumptions,
        "warnings": all_warnings,
        "analysis_logs": [
            log.get("step", "unknown") + ": " + log.get("output", "?")
            for log in analysis_logs
        ],
        "recommended_charts": recommended_charts,
        "provenance": build_handoff_provenance(
            args, Path(__file__), output_files=args.output_files
        ),
        "upstream_handoff": {
            "run_id": upstream.get("run_id", "unknown"),
            "handoff_type": upstream.get("handoff_type", "unknown"),
            "output_files": upstream.get("output_files", []),
        } if upstream else None,
        "ready_for": "validation",
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.analysis-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))
    print(f"wrote analysis handoff -> {out}")
    print(f"  steps: {len(all_steps)}")
    print(f"  warnings: {len(all_warnings)}")
    print(f"  assumptions: {len(all_assumptions)}")
    print(f"  output files: {len(args.output_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
