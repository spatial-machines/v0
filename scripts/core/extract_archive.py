from __future__ import annotations

import json
import zipfile
from datetime import datetime, UTC
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/extract_archive.py <archive-path> [--dest <dir>]")
        return 1

    archive_path = Path(sys.argv[1]).expanduser().resolve()
    if not archive_path.exists():
        print(f"archive not found: {archive_path}")
        return 2

    dest = INTERIM_DIR
    if "--dest" in sys.argv:
        idx = sys.argv.index("--dest")
        if idx + 1 < len(sys.argv):
            dest = Path(sys.argv[idx + 1]).expanduser().resolve()

    if not zipfile.is_zipfile(archive_path):
        print(f"not a valid zip file: {archive_path}")
        return 3

    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zf:
        members = zf.namelist()
        zf.extractall(dest)

    log = {
        "step": "extract_archive",
        "source": str(archive_path),
        "output": str(dest),
        "destination": str(dest),
        "members": members,
        "extracted_at": datetime.now(UTC).isoformat(),
    }

    log_path = dest / f"{archive_path.stem}.extraction.json"
    log_path.write_text(json.dumps(log, indent=2))
    print(f"extracted {len(members)} files from {archive_path.name} -> {dest}")
    print(f"log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
