#!/usr/bin/env python3
"""Validate a benchmark batch closeout against question-level artifacts.

Purpose:
- catch stale or contradictory benchmark scoring before a batch is closed
- verify that question-level score notes and summary CSV stay in sync
- flag suspicious zero-score questions that actually have substantive outputs

Usage:
    python scripts/core/validate_benchmark_batch.py \
        --benchmark-root analyses/benchmark-day1-easy-2026-04-10 \
        --summary-csv analyses/benchmark-day1-easy-2026-04-10/summary/day1_easy_E01_E20_scores.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_NOTE_FILES = [
    Path("notes/wiki_pages.txt"),
    Path("notes/delegation.md"),
    Path("notes/score.md"),
]

NON_SUBSTANTIVE_SUFFIXES = {
    ".manifest.json",
    ".fetch_poi_postgis.json",
}

IGNORE_PARTS = {"notes", "runs", "__pycache__"}


@dataclass
class QuestionAudit:
    question: str
    score_note: int | None
    summary_score: int | None
    data_files: int
    output_files: int
    missing_notes: list[str]
    issues: list[str]


def parse_score(score_path: Path) -> int | None:
    if not score_path.exists():
        return None
    text = score_path.read_text()
    match = re.search(r"Score:\s*(\d+)\s*/\s*5", text)
    return int(match.group(1)) if match else None


def is_substantive(path: Path) -> bool:
    name = path.name
    suffix_combo = "".join(path.suffixes[-2:]) if len(path.suffixes) >= 2 else path.suffix
    if suffix_combo in NON_SUBSTANTIVE_SUFFIXES or path.suffix in {".json", ".md", ".txt", ".py"}:
        return False
    if name.startswith("."):
        return False
    return True


def count_substantive_files(question_dir: Path, bucket: str) -> int:
    root = question_dir / bucket
    if not root.exists():
        return 0
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        if is_substantive(path):
            count += 1
    return count


def load_summary_scores(summary_csv: Path) -> tuple[dict[str, int], int | None]:
    if not summary_csv.exists():
        return {}, None
    scores: dict[str, int] = {}
    total = 0
    with summary_csv.open() as f:
        for row in csv.DictReader(f):
            question = row["question"].strip()
            score = int(row["score"])
            scores[question] = score
            total += score
    return scores, total


def audit_question(question_dir: Path, summary_scores: dict[str, int]) -> QuestionAudit:
    missing_notes = [str(rel) for rel in REQUIRED_NOTE_FILES if not (question_dir / rel).exists()]
    score_note = parse_score(question_dir / "notes/score.md")
    summary_score = summary_scores.get(question_dir.name)
    data_files = count_substantive_files(question_dir, "data")
    output_files = count_substantive_files(question_dir, "outputs")

    issues: list[str] = []
    if missing_notes:
        issues.append("missing_required_notes")
    if score_note is None:
        issues.append("unparseable_or_missing_score_note")
    if summary_score is None:
        issues.append("missing_summary_row")
    if score_note is not None and summary_score is not None and score_note != summary_score:
        issues.append("score_note_summary_mismatch")
    if score_note == 0 and (data_files > 0 or output_files > 0):
        issues.append("zero_score_with_substantive_artifacts")
    if summary_score == 0 and (data_files > 0 or output_files > 0):
        issues.append("summary_zero_with_substantive_artifacts")

    return QuestionAudit(
        question=question_dir.name,
        score_note=score_note,
        summary_score=summary_score,
        data_files=data_files,
        output_files=output_files,
        missing_notes=missing_notes,
        issues=issues,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate benchmark batch closeout consistency")
    parser.add_argument("--benchmark-root", required=True, help="Benchmark batch root directory")
    parser.add_argument("--summary-csv", required=True, help="Batch summary CSV path")
    parser.add_argument("--output-json", help="Optional JSON audit output path")
    parser.add_argument("--output-md", help="Optional markdown audit output path")
    args = parser.parse_args()

    benchmark_root = Path(args.benchmark_root)
    summary_csv = Path(args.summary_csv)

    questions_root = benchmark_root / "questions"
    if not questions_root.exists():
        print(f"ERROR: questions dir not found: {questions_root}")
        return 2

    summary_scores, csv_total = load_summary_scores(summary_csv)
    audits = [audit_question(qdir, summary_scores) for qdir in sorted(questions_root.glob("E*")) if qdir.is_dir()]
    issue_count = sum(len(a.issues) for a in audits)
    note_total = sum(a.score_note for a in audits if a.score_note is not None)
    note_total = note_total if all(a.score_note is not None for a in audits) else None

    global_issues: list[str] = []
    if csv_total is None:
        global_issues.append("missing_summary_csv")
    elif note_total is not None and csv_total != note_total:
        global_issues.append("summary_total_mismatch")

    report = {
        "benchmark_root": str(benchmark_root),
        "summary_csv": str(summary_csv),
        "question_count": len(audits),
        "csv_total": csv_total,
        "score_note_total": note_total,
        "global_issues": global_issues,
        "questions": [asdict(a) for a in audits],
        "ok": issue_count == 0 and not global_issues,
    }

    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))

    if args.output_md:
        out = Path(args.output_md)
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Benchmark Batch Validation Report",
            "",
            f"- Benchmark root: `{benchmark_root}`",
            f"- Summary CSV: `{summary_csv}`",
            f"- CSV total: `{csv_total}`",
            f"- Score-note total: `{note_total}`",
            f"- Global issues: {', '.join(global_issues) if global_issues else 'none'}",
            "",
            "| Question | Score note | Summary score | Data files | Output files | Issues |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for audit in audits:
            lines.append(
                f"| {audit.question} | {audit.score_note if audit.score_note is not None else '—'} | {audit.summary_score if audit.summary_score is not None else '—'} | {audit.data_files} | {audit.output_files} | {', '.join(audit.issues) if audit.issues else 'none'} |"
            )
        out.write_text("\n".join(lines) + "\n")

    print(f"Validated {len(audits)} questions")
    if global_issues:
        print(f"Global issues: {', '.join(global_issues)}")
    for audit in audits:
        status = "OK" if not audit.issues else f"ISSUES: {', '.join(audit.issues)}"
        print(
            f"{audit.question}: note={audit.score_note} summary={audit.summary_score} "
            f"data={audit.data_files} outputs={audit.output_files} -> {status}"
        )

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
