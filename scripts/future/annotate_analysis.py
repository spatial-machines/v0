#!/usr/bin/env python3
"""Collaborative Annotation Layer — let reviewers annotate maps and findings.

Annotations are stored per-analysis in analyses/<project-id>/annotations.json.
Important annotations (institutional, correction) feed back into lessons-learned.jsonl.
Correction-type annotations apply exclusions to data/processed/exclusions.json.

Usage:
    # Add an annotation
    python annotate_analysis.py --project-id ks-poverty-health --action add \\
        --feature-id 20161009800 --type institutional \\
        --note "Lansing Correctional Facility — artificially high poverty rate, exclude from hotspot interpretation"

    # List all annotations for a project
    python annotate_analysis.py --project-id ks-poverty-health --action list

    # Export annotation sheet (Markdown)
    python annotate_analysis.py --project-id ks-poverty-health --action export \\
        --output outputs/ks-poverty-health-annotations.md

    # Apply correction-type annotations to exclusions.json
    python annotate_analysis.py --project-id ks-poverty-health --action apply

Annotation types:
    institutional  — group quarters, prisons, universities, military bases
    data-quality   — known data issues (suppressed values, MOE concerns)
    context        — local context that explains an anomaly
    correction     — error or misclassification; triggers exclusion

Reviewer field:
    Set via --reviewer, or falls back to GIS_REVIEWER env var, or 'unknown'.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import fill, indent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"
LOGS_DIR = PROJECT_ROOT / "docs" / "memory"
LESSONS_FILE = LOGS_DIR / "lessons-learned.jsonl"

# Annotation types that feed back into lessons-learned
LESSONS_TYPES = {"institutional", "correction"}

# Annotation types that show a header warning in exports
WARNING_TYPES = {"correction", "data-quality"}

TYPE_ICONS = {
    "institutional": "🏛️",
    "data-quality": "⚠️",
    "context": "💬",
    "correction": "🔴",
}

TYPE_DESCRIPTIONS = {
    "institutional": "Group quarters, prisons, universities, military installations",
    "data-quality": "Known data issues — suppression, high MOE, misreported values",
    "context": "Local context that explains an anomaly without invalidating the data",
    "correction": "Error or confirmed misclassification — triggers feature exclusion",
}


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def get_annotations_path(project_id: str) -> Path:
    return ANALYSES_DIR / project_id / "annotations.json"


def get_exclusions_path(project_id: str) -> Path:
    """Global exclusions file that pipeline scripts consult."""
    return PROJECT_ROOT / "data" / "processed" / "exclusions.json"


def load_annotations(project_id: str) -> dict:
    path = get_annotations_path(project_id)
    if not path.exists():
        return {
            "_meta": {
                "project_id": project_id,
                "schema_version": "1.0",
                "description": "Human reviewer annotations for GIS analysis features and findings.",
            },
            "annotations": [],
        }
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse annotations.json: {e}", file=sys.stderr)
        sys.exit(1)


def save_annotations(project_id: str, data: dict) -> None:
    path = get_annotations_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_exclusions(project_id: str) -> dict:
    path = get_exclusions_path(project_id)
    if not path.exists():
        return {
            "_meta": {
                "description": "Feature IDs excluded from pipeline analysis runs. Auto-updated by annotation apply.",
                "schema_version": "1.0",
            },
            "exclusions": {},
        }
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"_meta": {}, "exclusions": {}}


def save_exclusions(project_id: str, data: dict) -> None:
    path = get_exclusions_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def append_lessons_learned(entry: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with LESSONS_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def action_add(project_id: str, feature_id: str, ann_type: str, note: str, reviewer: str) -> int:
    """Append a new annotation."""
    if not feature_id:
        print("ERROR: --feature-id is required for 'add'", file=sys.stderr)
        return 1
    if not note:
        print("ERROR: --note is required for 'add'", file=sys.stderr)
        return 1

    data = load_annotations(project_id)
    now = datetime.now(tz=timezone.utc).isoformat()

    annotation = {
        "id": f"ann-{len(data['annotations']) + 1:04d}",
        "feature_id": str(feature_id),
        "type": ann_type,
        "note": note,
        "reviewer": reviewer,
        "created_at": now,
        "applied": False,
    }

    data["annotations"].append(annotation)
    save_annotations(project_id, data)

    icon = TYPE_ICONS.get(ann_type, "📝")
    print(f"{icon} Annotation added [{annotation['id']}]")
    print(f"  Project:    {project_id}")
    print(f"  Feature ID: {feature_id}")
    print(f"  Type:       {ann_type} — {TYPE_DESCRIPTIONS.get(ann_type, '')}")
    print(f"  Note:       {note}")
    print(f"  Reviewer:   {reviewer}")
    print(f"  Saved to:   {get_annotations_path(project_id)}")

    # Log to lessons-learned for institutional + correction
    if ann_type in LESSONS_TYPES:
        lesson = {
            "timestamp": now,
            "project_id": project_id,
            "annotation_id": annotation["id"],
            "feature_id": str(feature_id),
            "type": ann_type,
            "note": note,
            "reviewer": reviewer,
            "source": "annotate_analysis.py",
        }
        append_lessons_learned(lesson)
        print(f"\n  📚 Logged to lessons-learned: {LESSONS_FILE}")

    if ann_type == "correction":
        print(
            f"\n  ⚠️  Correction annotation added. Run with --action apply to write "
            f"feature {feature_id} to exclusions.json."
        )

    return 0


def action_list(project_id: str, ann_type: str | None = None) -> int:
    """Print all annotations for a project."""
    data = load_annotations(project_id)
    annotations = data.get("annotations", [])

    if ann_type:
        annotations = [a for a in annotations if a.get("type") == ann_type]

    if not annotations:
        print(f"No annotations found for project '{project_id}'" +
              (f" (type={ann_type})" if ann_type else "") + ".")
        return 0

    print(f"=== Annotations: {project_id} ({len(annotations)} total) ===\n")

    for a in annotations:
        icon = TYPE_ICONS.get(a.get("type", ""), "📝")
        applied_tag = " [APPLIED]" if a.get("applied") else ""
        print(f"{icon} [{a['id']}] {a['type'].upper()}{applied_tag}")
        print(f"   Feature:  {a['feature_id']}")
        print(f"   Note:     {a['note']}")
        print(f"   Reviewer: {a.get('reviewer', 'unknown')}")
        print(f"   Date:     {a.get('created_at', '')[:10]}")
        print()

    return 0


def action_export(project_id: str, output_path: str | None) -> int:
    """Generate a Markdown annotation sheet for human review."""
    data = load_annotations(project_id)
    annotations = data.get("annotations", [])

    if not annotations:
        print(f"No annotations found for project '{project_id}'. Nothing to export.")
        return 0

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for a in annotations:
        t = a.get("type", "unknown")
        by_type.setdefault(t, []).append(a)

    lines = [
        f"# Annotation Sheet: {project_id}",
        f"\n_Exported: {datetime.now(tz=timezone.utc).isoformat()[:10]}_",
        f"_Total annotations: {len(annotations)}_\n",
        "---\n",
    ]

    # Summary table
    lines += [
        "## Summary\n",
        "| Type | Count | Description |",
        "|------|-------|-------------|",
    ]
    for t in ["correction", "institutional", "data-quality", "context"]:
        count = len(by_type.get(t, []))
        if count:
            desc = TYPE_DESCRIPTIONS.get(t, "")
            icon = TYPE_ICONS.get(t, "")
            lines.append(f"| {icon} {t} | {count} | {desc} |")
    lines.append("")

    # Corrections first (highest priority)
    if "correction" in by_type:
        lines += [
            "## 🔴 Corrections\n",
            "> These features have confirmed errors or misclassifications.",
            "> Run `python annotate_analysis.py --project-id {project_id} --action apply`",
            "> to write these to `exclusions.json` for future pipeline runs.\n",
        ]
        for a in by_type["correction"]:
            applied_tag = " ✅ *applied*" if a.get("applied") else " ⏳ *pending apply*"
            lines += [
                f"### Feature `{a['feature_id']}`{applied_tag}",
                f"- **Annotation ID:** {a['id']}",
                f"- **Note:** {a['note']}",
                f"- **Reviewer:** {a.get('reviewer', 'unknown')}",
                f"- **Date:** {a.get('created_at', '')[:10]}",
                "",
            ]

    # Institutional
    if "institutional" in by_type:
        lines += [
            "## 🏛️ Institutional Features\n",
            "> These features have group quarters (prisons, universities, military bases, etc.)",
            "> that cause artificially skewed demographic rates. Exclude from hotspot interpretation.\n",
        ]
        for a in by_type["institutional"]:
            lines += [
                f"### Feature `{a['feature_id']}`",
                f"- **Note:** {a['note']}",
                f"- **Reviewer:** {a.get('reviewer', 'unknown')}",
                f"- **Date:** {a.get('created_at', '')[:10]}",
                "",
            ]

    # Data quality
    if "data-quality" in by_type:
        lines += [
            "## ⚠️ Data Quality Issues\n",
        ]
        for a in by_type["data-quality"]:
            lines += [
                f"### Feature `{a['feature_id']}`",
                f"- **Note:** {a['note']}",
                f"- **Reviewer:** {a.get('reviewer', 'unknown')}",
                f"- **Date:** {a.get('created_at', '')[:10]}",
                "",
            ]

    # Context
    if "context" in by_type:
        lines += [
            "## 💬 Contextual Notes\n",
        ]
        for a in by_type["context"]:
            lines += [
                f"### Feature `{a['feature_id']}`",
                f"- **Note:** {a['note']}",
                f"- **Reviewer:** {a.get('reviewer', 'unknown')}",
                f"- **Date:** {a.get('created_at', '')[:10]}",
                "",
            ]

    # Any other types
    for t, items in by_type.items():
        if t not in {"correction", "institutional", "data-quality", "context"}:
            lines += [f"## {t.title()}\n"]
            for a in items:
                lines += [
                    f"### Feature `{a['feature_id']}`",
                    f"- **Note:** {a['note']}",
                    f"- **Reviewer:** {a.get('reviewer', 'unknown')}",
                    "",
                ]

    md = "\n".join(lines)

    if output_path:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        print(f"✅ Annotation sheet exported: {out}")
    else:
        print(md)

    return 0


def action_apply(project_id: str) -> int:
    """Apply correction-type annotations to exclusions.json."""
    data = load_annotations(project_id)
    annotations = data.get("annotations", [])

    corrections = [a for a in annotations if a.get("type") == "correction" and not a.get("applied")]

    if not corrections:
        print(f"No pending correction annotations for '{project_id}'.")
        return 0

    print(f"Applying {len(corrections)} correction(s) to exclusions.json...")

    exclusions_data = load_exclusions(project_id)
    project_exclusions = exclusions_data["exclusions"].get(project_id, {})

    applied_ids = []
    for a in corrections:
        fid = a["feature_id"]
        project_exclusions[fid] = {
            "feature_id": fid,
            "excluded_at": datetime.now(tz=timezone.utc).isoformat(),
            "reason": a["note"],
            "annotation_id": a["id"],
            "annotation_type": a["type"],
            "reviewer": a.get("reviewer", "unknown"),
        }
        a["applied"] = True
        a["applied_at"] = datetime.now(tz=timezone.utc).isoformat()
        applied_ids.append(a["id"])
        print(f"  🔴 Excluded: {fid} — {a['note'][:80]}")

    exclusions_data["exclusions"][project_id] = project_exclusions
    save_exclusions(project_id, exclusions_data)
    save_annotations(project_id, data)

    excl_path = get_exclusions_path(project_id)
    print(f"\n✅ {len(applied_ids)} correction(s) written to: {excl_path}")
    print(f"   Annotation IDs applied: {', '.join(applied_ids)}")
    print(f"\n   Future pipeline runs will skip excluded features.")
    print(f"   Pipeline scripts should load exclusions.json and filter before analysis.")

    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collaborative annotation layer for GIS analysis review."
    )
    parser.add_argument("--project-id", required=True, help="Analysis project ID")
    parser.add_argument(
        "--action",
        required=True,
        choices=["add", "list", "export", "apply"],
        help="Action to perform",
    )
    parser.add_argument(
        "--feature-id",
        help="GEOID or feature index to annotate (required for 'add')",
    )
    parser.add_argument(
        "--note",
        help="Annotation text (required for 'add')",
    )
    parser.add_argument(
        "--type",
        dest="ann_type",
        choices=["institutional", "data-quality", "context", "correction"],
        default="context",
        help="Annotation type (default: context)",
    )
    parser.add_argument(
        "--reviewer",
        default=None,
        help="Reviewer name/ID (falls back to GIS_REVIEWER env var)",
    )
    parser.add_argument(
        "--output",
        help="Output path for 'export' action",
    )
    parser.add_argument(
        "--filter-type",
        dest="filter_type",
        choices=["institutional", "data-quality", "context", "correction"],
        help="Filter 'list' output to this annotation type only",
    )
    args = parser.parse_args()

    # Resolve reviewer
    reviewer = args.reviewer or os.environ.get("GIS_REVIEWER", "unknown")

    # Verify project exists
    project_dir = ANALYSES_DIR / args.project_id
    if not project_dir.is_dir():
        print(f"ERROR: Analysis directory not found: {project_dir}", file=sys.stderr)
        print(f"       Available analyses: {[d.name for d in ANALYSES_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]}", file=sys.stderr)
        return 1

    if args.action == "add":
        return action_add(
            project_id=args.project_id,
            feature_id=args.feature_id or "",
            ann_type=args.ann_type,
            note=args.note or "",
            reviewer=reviewer,
        )

    elif args.action == "list":
        return action_list(args.project_id, ann_type=args.filter_type)

    elif args.action == "export":
        return action_export(args.project_id, output_path=args.output)

    elif args.action == "apply":
        return action_apply(args.project_id)

    else:
        print(f"ERROR: Unknown action '{args.action}'", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
