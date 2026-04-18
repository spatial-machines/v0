"""Log a lesson learned to the structured lessons log.

Appends a single JSONL entry to docs/memory/lessons-learned.jsonl with
category, tags, and a human-readable description. Designed for
incremental use — call it after any run, review, or incident.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "docs" / "memory"
DEFAULT_LOG = MEMORY_DIR / "lessons-learned.jsonl"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Log a lesson learned to the structured lessons log."
    )
    parser.add_argument("lesson", help="One-line description of the lesson")
    parser.add_argument(
        "--category",
        default="general",
        help="Category (e.g. data-quality, pipeline, tooling, process, qa)",
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        default=[],
        help="Optional tags for filtering (e.g. retrieval, census, joins)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run ID this lesson relates to (optional)",
    )
    parser.add_argument(
        "--detail",
        default=None,
        help="Longer explanation or context (optional)",
    )
    parser.add_argument(
        "-o", "--output",
        default=str(DEFAULT_LOG),
        help="Path to the lessons log file (default: memory/lessons-learned.jsonl)",
    )
    args = parser.parse_args()

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "category": args.category,
        "tags": args.tags,
        "lesson": args.lesson,
    }
    if args.run_id:
        entry["run_id"] = args.run_id
    if args.detail:
        entry["detail"] = args.detail

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Count total lessons
    total = sum(1 for line in out.read_text().splitlines() if line.strip())

    print("=== Lesson Logged ===")
    print(f"  category: {args.category}")
    print(f"  tags:     {', '.join(args.tags) if args.tags else '(none)'}")
    print(f"  lesson:   {args.lesson}")
    if args.run_id:
        print(f"  run_id:   {args.run_id}")
    print(f"  total lessons: {total}")
    print(f"wrote lesson -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
