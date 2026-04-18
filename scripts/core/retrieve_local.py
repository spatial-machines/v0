from __future__ import annotations

import argparse
import json
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy a local file into data/raw and write a manifest."
    )
    parser.add_argument("--source", required=True, help="Path to the local file to ingest")
    parser.add_argument("--label", default=None, help="Optional label (used as output filename stem)")
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory (default: data/raw/)"
    )
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"source file does not exist: {source}")
        return 2

    raw_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    if args.label:
        dest = raw_dir / (args.label + source.suffix)
    else:
        dest = raw_dir / source.name
    if source != dest:
        dest.write_bytes(source.read_bytes())

    manifest = {
        "dataset_id": dest.stem,
        "retrieval_method": "local-copy",
        "source_name": source.name,
        "source_type": "local-file",
        "source_url": None,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(dest.resolve().relative_to(PROJECT_ROOT)),
        "format": dest.suffix.lower().lstrip("."),
        "geography_level": None,
        "vintage": None,
        "notes": ["Copied local file into data/raw for reproducibility."],
        "warnings": [],
    }

    out = raw_dir / f"{dest.stem}.manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"stored {dest}")
    print(f"manifest {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
