from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Write a provenance artifact.")
    parser.add_argument("run_id", help="Run identifier")
    parser.add_argument("task_summary", help="One-line summary")
    parser.add_argument("--manifest-dir", default=None, help="Directory to scan for manifests (default: data/raw/)")
    parser.add_argument("--interim-dir", default=None, help="Interim data directory (unused, reserved)")
    parser.add_argument("--output-dir", default=None, help="Override output directory for handoff (default: runs/)")
    args = parser.parse_args()

    run_id = args.run_id
    task_summary = args.task_summary

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)

    manifest_dir = Path(args.manifest_dir).expanduser().resolve() if args.manifest_dir else RAW_DIR
    manifests = []
    for path in sorted(manifest_dir.glob("*.manifest.json")):
        try:
            manifests.append(json.loads(path.read_text()))
        except Exception:
            pass

    provenance = {
        "run_id": run_id,
        "task_summary": task_summary,
        "created_at": datetime.now(UTC).isoformat(),
        "sources": manifests,
        "artifacts": [m.get("stored_path") for m in manifests],
        "processing_steps": [],
        "analysis_steps": [],
        "validation_summary": None,
        "notes": ["Initial provenance generated from retrieval manifests."],
    }

    out = runs_dir / f"{run_id}.provenance.json"
    out.write_text(json.dumps(provenance, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
