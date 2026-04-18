"""Write a structured QGIS bridge handoff artifact to runs/.

Records what was packaged, the validation status carried forward, and
the location of the review package.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Write a QGIS bridge handoff artifact."
    )
    parser.add_argument("run_id", help="Run identifier")
    parser.add_argument("summary", help="Human-readable summary of the QGIS package")
    parser.add_argument("--package-dir", required=True, help="Path to the QGIS review package directory")
    parser.add_argument("--validation-status", default="PASS WITH WARNINGS", help="Upstream validation status")
    parser.add_argument("--source-handoff", default=None, help="Path to the upstream lead/validation handoff")
    parser.add_argument("--package-files", nargs="+", default=[], help="Key files in the package")
    parser.add_argument("--warnings", nargs="+", default=[], help="Warnings to carry forward")
    parser.add_argument("--notes", nargs="+", default=[], help="Additional notes")
    parser.add_argument("--output-dir", default=None, help="Override output directory for handoff (default: runs/)")
    args = parser.parse_args()

    pkg_dir = Path(args.package_dir)
    if not pkg_dir.is_absolute():
        pkg_dir = PROJECT_ROOT / pkg_dir

    # Read manifest if it exists
    manifest_path = pkg_dir / "manifest.json"
    manifest = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())

    # Build upstream reference
    upstream = None
    if args.source_handoff:
        sp = Path(args.source_handoff)
        if not sp.is_absolute():
            sp = PROJECT_ROOT / sp
        if sp.exists():
            upstream_data = json.loads(sp.read_text())
            upstream = {
                "run_id": upstream_data.get("run_id"),
                "handoff_type": upstream_data.get("handoff_type"),
            }

    handoff = {
        "handoff_type": "qgis-bridge",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "package_dir": str(pkg_dir.relative_to(PROJECT_ROOT)),
        "validation_status": args.validation_status,
        "package_files": args.package_files,
        "manifest": {
            "total_files": manifest["total_files"] if manifest else 0,
            "total_size_bytes": manifest["total_size_bytes"] if manifest else 0,
        },
        "upstream_handoff": upstream,
        "warnings": args.warnings,
        "ready_for": "qgis-review",
        "notes": args.notes,
    }

    # Write handoff
    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else PROJECT_ROOT / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    out_path = runs_dir / f"{args.run_id}.qgis-handoff.json"
    out_path.write_text(json.dumps(handoff, indent=2))

    print(f"wrote QGIS handoff -> {out_path.relative_to(PROJECT_ROOT)}")
    print(f"  run:              {args.run_id}")
    print(f"  package:          {handoff['package_dir']}")
    print(f"  validation:       {args.validation_status}")
    print(f"  files in package: {handoff['manifest']['total_files']}")
    print(f"  ready_for:        qgis-review")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
