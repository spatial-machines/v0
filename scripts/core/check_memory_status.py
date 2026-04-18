"""Check and report the current state of the project memory layer.

Scans docs/memory/, runs/, docs/handbooks/, and docs to report coverage gaps
and staleness. Useful for verifying that the memory layer is in sync
with the actual project state.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "docs" / "memory"


def file_age_label(path: Path) -> str:
    """Return a human-readable age string for a file."""
    if not path.exists():
        return "missing"
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        delta = datetime.now(UTC) - mtime
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    except Exception:
        return "unknown"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Check and report project memory status."
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Optional: write status report as JSON to this path",
    )
    args = parser.parse_args()

    issues: list[str] = []
    status: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {},
    }

    # --- Check PROJECT_MEMORY.md ---
    pm = MEMORY_DIR / "PROJECT_MEMORY.md"
    pm_exists = pm.exists()
    status["checks"]["project_memory"] = {
        "path": "memory/PROJECT_MEMORY.md",
        "exists": pm_exists,
        "age": file_age_label(pm) if pm_exists else None,
    }
    if not pm_exists:
        issues.append("memory/PROJECT_MEMORY.md does not exist — run update_project_memory.py")

    # --- Check lessons log ---
    ll = MEMORY_DIR / "lessons-learned.jsonl"
    ll_exists = ll.exists()
    lesson_count = 0
    if ll_exists:
        lesson_count = sum(1 for l in ll.read_text().splitlines() if l.strip())
    status["checks"]["lessons_learned"] = {
        "path": "memory/lessons-learned.jsonl",
        "exists": ll_exists,
        "entry_count": lesson_count,
    }
    if not ll_exists:
        issues.append("memory/lessons-learned.jsonl does not exist — no lessons logged yet")
    elif lesson_count == 0:
        issues.append("memory/lessons-learned.jsonl is empty")

    # --- Check retrospectives ---
    retro_dir = MEMORY_DIR / "retrospectives"
    retros = sorted(retro_dir.glob("*.md")) if retro_dir.exists() else []
    status["checks"]["retrospectives"] = {
        "path": "memory/retrospectives/",
        "exists": retro_dir.exists(),
        "count": len(retros),
        "files": [str(r.relative_to(PROJECT_ROOT)) for r in retros],
    }
    if not retros:
        issues.append("No retrospectives found in memory/retrospectives/")

    # --- Check handoff coverage ---
    runs_dir = PROJECT_ROOT / "runs"
    handoff_files = sorted(runs_dir.glob("*.json")) if runs_dir.exists() else []
    handoff_types = set()
    for hf in handoff_files:
        try:
            data = json.loads(hf.read_text())
            handoff_types.add(data.get("handoff_type", "unknown"))
        except Exception:
            pass
    status["checks"]["handoffs"] = {
        "path": "runs/",
        "count": len(handoff_files),
        "types": sorted(handoff_types),
    }

    # --- Check handbooks vs roles ---
    role_handbooks = sorted(
        (PROJECT_ROOT / "docs" / "handbooks" / "roles").glob("*.md")
    ) if (PROJECT_ROOT / "docs" / "handbooks" / "roles").exists() else []
    workflow_handbooks = sorted(
        (PROJECT_ROOT / "docs" / "handbooks" / "workflows").glob("*.md")
    ) if (PROJECT_ROOT / "docs" / "handbooks" / "workflows").exists() else []
    status["checks"]["handbooks"] = {
        "roles": len(role_handbooks),
        "workflows": len(workflow_handbooks),
    }

    # --- Check key docs exist ---
    key_docs = ["README.md", "ROADMAP.md", "ARCHITECTURE.md", "TEAM.md", "QA_CHECKLIST.md"]
    docs_status = {}
    for doc in key_docs:
        p = PROJECT_ROOT / doc
        docs_status[doc] = {
            "exists": p.exists(),
            "age": file_age_label(p) if p.exists() else None,
        }
    status["checks"]["docs"] = docs_status

    # --- Overall assessment ---
    if not issues:
        overall = "OK"
    elif len(issues) <= 2:
        overall = "PARTIAL"
    else:
        overall = "GAPS"

    status["overall"] = overall
    status["issues"] = issues

    # Print report
    print("=== Memory Status Report ===")
    print(f"  overall:          {overall}")
    print(f"  project memory:   {'exists' if pm_exists else 'MISSING'} ({file_age_label(pm)})")
    print(f"  lessons logged:   {lesson_count}")
    print(f"  retrospectives:   {len(retros)}")
    print(f"  handoff artifacts:{len(handoff_files)}")
    print(f"  role handbooks:   {len(role_handbooks)}")
    print(f"  workflow handbooks:{len(workflow_handbooks)}")
    if issues:
        print("")
        print("  Issues:")
        for issue in issues:
            print(f"    - {issue}")

    # Optionally write JSON
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(status, indent=2))
        print(f"\nwrote status report -> {out}")

    return 0 if overall == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
