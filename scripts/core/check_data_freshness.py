#!/usr/bin/env python3
"""Data Freshness Monitor — check how current each data source is.

Compares known data source vintages and update schedules against today's
date and flags sources where a newer vintage is likely available. Also
scans analysis log.json files to detect which sources were used and
whether any need refreshing.

Usage:
    # Check all data sources against schedule
    python check_data_freshness.py --all

    # Check a specific analysis project
    python check_data_freshness.py --project-dir analyses/ne-tracts-poverty

    # Check all analyses in registry
    python check_data_freshness.py --all --output outputs/freshness_report.json

    # Check a single analysis and write output
    python check_data_freshness.py --project-dir analyses/ne-tracts-poverty \\
        --output outputs/ne-tracts-freshness.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_FILE = PROJECT_ROOT / "config" / "data-freshness-schedule.json"
REGISTRY_FILE = PROJECT_ROOT / "registry.json"
ANALYSES_DIR = PROJECT_ROOT / "analyses"

TODAY = datetime.now(tz=timezone.utc).date()


# ---------------------------------------------------------------------------
# Load schedule
# ---------------------------------------------------------------------------

def load_schedule() -> dict:
    if not SCHEDULE_FILE.exists():
        print(f"WARNING: schedule file not found: {SCHEDULE_FILE}", file=sys.stderr)
        return {}
    return json.loads(SCHEDULE_FILE.read_text())["sources"]


# ---------------------------------------------------------------------------
# Source-level freshness check
# ---------------------------------------------------------------------------

def check_source_freshness(key: str, source: dict, reference_date: Optional[str] = None) -> dict:
    """Check a single data source for staleness.

    Args:
        key: source identifier
        source: source metadata dict from schedule
        reference_date: ISO date string override (e.g. '2023-06-01') for
                        when the data was retrieved; None = use today

    Returns:
        dict with keys: source_key, label, status, message, current_vintage,
                         next_vintage, days_since_threshold, recommendation
    """
    result = {
        "source_key": key,
        "label": source["label"],
        "frequency": source["frequency"],
        "current_vintage": source.get("current_vintage", "unknown"),
        "current_coverage": source.get("current_coverage", ""),
        "next_expected_vintage": source.get("next_expected_vintage", ""),
        "next_release_approx": source.get("next_release_approx", ""),
        "staleness_threshold_days": source.get("staleness_threshold_days", 365),
        "status": "OK",
        "message": "",
        "recommendation": "",
        "checked_at": TODAY.isoformat(),
    }

    freq = source.get("frequency", "annual")
    threshold_days = source.get("staleness_threshold_days", 365)

    # For sources with a fixed annual/quadrennial vintage, check if a
    # newer vintage is likely available by examining next_release_approx
    next_release = source.get("next_release_approx")
    if next_release:
        # Parse approximate release date (may be just YYYY or YYYY-MM)
        try:
            if re.match(r"^\d{4}$", next_release):
                release_date = datetime(int(next_release), 7, 1).date()
            elif re.match(r"^\d{4}-\d{2}$", next_release):
                y, m = next_release.split("-")
                release_date = datetime(int(y), int(m), 1).date()
            else:
                release_date = None
        except ValueError:
            release_date = None

        if release_date and TODAY >= release_date:
            next_vintage = source.get("next_expected_vintage", "")
            result["status"] = "STALE"
            result["message"] = (
                f"Newer vintage likely available: {next_vintage} "
                f"(estimated release {next_release})"
            )
            result["recommendation"] = (
                f"Update to {next_vintage} vintage. "
                f"Check {source.get('url', 'source URL')} for current release."
            )
            return result

    # For continuous/monthly/quarterly sources, check threshold days
    if freq in ("continuous", "monthly", "quarterly") and reference_date:
        try:
            ref = datetime.fromisoformat(reference_date).date()
            age_days = (TODAY - ref).days
            if age_days > threshold_days:
                result["status"] = "STALE"
                result["days_since_retrieval"] = age_days
                result["message"] = (
                    f"Source data is {age_days} days old "
                    f"(threshold: {threshold_days} days for {freq} source)"
                )
                result["recommendation"] = (
                    f"Re-retrieve {source['label']} — "
                    f"new data likely available. Threshold for {freq} updates is {threshold_days} days."
                )
            else:
                result["status"] = "OK"
                result["days_since_retrieval"] = age_days
                result["message"] = f"Source is current ({age_days} days old, threshold {threshold_days})"
        except (ValueError, TypeError):
            result["status"] = "UNKNOWN"
            result["message"] = "Could not determine retrieval date"
    elif freq in ("continuous", "monthly", "quarterly") and not reference_date:
        result["status"] = "UNKNOWN"
        result["message"] = (
            f"No retrieval date found for {freq} source. "
            f"Verify data is recent (threshold: {threshold_days} days)."
        )
        result["recommendation"] = "Record retrieval date in provenance to enable automatic staleness checks."
    else:
        result["status"] = "OK"
        result["message"] = f"No newer vintage detected. Current: {source.get('current_vintage', 'unknown')}"

    return result


# ---------------------------------------------------------------------------
# Scan analysis log.json files for source references
# ---------------------------------------------------------------------------

def detect_sources_in_logs(project_dir: Path, schedule: dict) -> list[dict]:
    """Scan *.log.json and provenance.json files for data source references."""
    detected = []
    seen_keys = set()

    # Gather all JSON log files
    log_files = list(project_dir.rglob("*.log.json"))
    log_files += list(project_dir.rglob("*.provenance.json"))
    log_files += list(project_dir.rglob("*.analysis-handoff.json"))
    log_files += list(project_dir.rglob("*.processing-handoff.json"))

    # Also check runs/ directory at project root
    runs_dir = PROJECT_ROOT / "runs"
    if runs_dir.exists():
        log_files += list(runs_dir.glob("*.json"))

    if not log_files:
        print(f"  No log files found in {project_dir}")
        return []

    # Collect all text to search through
    all_text_lower = ""
    retrieval_dates: dict[str, str] = {}  # source_key -> ISO date string

    for lf in log_files:
        try:
            data = json.loads(lf.read_text())
            text = json.dumps(data).lower()
            all_text_lower += " " + text

            # Try to extract retrieval dates from provenance
            if "provenance" in lf.name or "retrieval" in lf.name:
                created_at = data.get("created_at", data.get("retrieved_at", ""))
                sources_used = data.get("sources", data.get("data_sources", []))
                for src in (sources_used if isinstance(sources_used, list) else []):
                    src_id = src.get("id", src.get("source", ""))
                    src_date = src.get("retrieved_at", src.get("date", created_at))
                    if src_id and src_date:
                        retrieval_dates[src_id.lower()] = src_date
        except Exception:
            pass

    # Match keywords to known sources
    for key, source in schedule.items():
        keywords = source.get("match_keywords", [])
        matched = any(kw.lower() in all_text_lower for kw in keywords)
        if matched and key not in seen_keys:
            seen_keys.add(key)
            # Look for a retrieval date
            ref_date = retrieval_dates.get(key)
            check = check_source_freshness(key, source, reference_date=ref_date)
            check["detected_in_logs"] = True
            check["log_files_scanned"] = len(log_files)
            detected.append(check)

    return detected


# ---------------------------------------------------------------------------
# Load registry and enumerate analyses
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {}
    try:
        return json.loads(REGISTRY_FILE.read_text())
    except Exception:
        return {}


def enumerate_analyses() -> list[Path]:
    """Return all analysis directories either from registry or filesystem scan."""
    registry = load_registry()
    dirs = []

    # Registry may list analyses as a list or dict
    analyses = registry.get("analyses", [])
    if isinstance(analyses, list):
        for entry in analyses:
            if isinstance(entry, dict):
                project_id = entry.get("project_id") or entry.get("id") or entry.get("name")
            else:
                project_id = str(entry)
            if project_id:
                candidate = ANALYSES_DIR / project_id
                if candidate.is_dir():
                    dirs.append(candidate)
    elif isinstance(analyses, dict):
        for project_id in analyses:
            candidate = ANALYSES_DIR / project_id
            if candidate.is_dir():
                dirs.append(candidate)

    # Fallback: scan analyses/ directory directly
    if not dirs and ANALYSES_DIR.exists():
        dirs = [d for d in ANALYSES_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]

    return sorted(dirs)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def status_icon(status: str) -> str:
    return {"OK": "✅", "STALE": "⚠️", "UNKNOWN": "❓"}.get(status, "❔")


def build_markdown_report(
    source_results: list[dict],
    analysis_results: dict[str, list[dict]],
    checked_at: str,
) -> str:
    stale_sources = [r for r in source_results if r["status"] == "STALE"]
    ok_sources = [r for r in source_results if r["status"] == "OK"]
    unknown_sources = [r for r in source_results if r["status"] == "UNKNOWN"]

    lines = [
        "# Data Freshness Report",
        f"\n_Generated: {checked_at}_\n",
        "## Source Schedule Overview\n",
        f"- **Total sources tracked:** {len(source_results)}",
        f"- **Current (OK):** {len(ok_sources)}",
        f"- **Stale (newer vintage likely):** {len(stale_sources)}",
        f"- **Unknown / needs review:** {len(unknown_sources)}",
        "",
    ]

    if stale_sources:
        lines += [
            "## ⚠️ Stale Sources — Action Required\n",
        ]
        for r in stale_sources:
            lines += [
                f"### {r['label']}",
                f"- **Status:** {r['status']}",
                f"- **Current vintage:** {r['current_vintage']}",
                f"- **Message:** {r['message']}",
                f"- **Recommendation:** {r['recommendation']}",
                f"- **Source:** {r.get('source_key', '')}",
                "",
            ]

    if unknown_sources:
        lines += ["## ❓ Unknown / Needs Verification\n"]
        for r in unknown_sources:
            lines += [
                f"### {r['label']}",
                f"- **Message:** {r['message']}",
                f"- **Recommendation:** {r.get('recommendation', 'Verify manually.')}",
                "",
            ]

    lines += ["## ✅ Sources — Current\n"]
    for r in ok_sources:
        lines.append(
            f"- **{r['label']}** — {r['current_vintage']} ({r.get('message', '')})"
        )

    if analysis_results:
        lines += [
            "",
            "---",
            "## Analysis-Level Freshness\n",
        ]
        for proj_id, results in analysis_results.items():
            stale = [r for r in results if r["status"] == "STALE"]
            unk = [r for r in results if r["status"] == "UNKNOWN"]
            icon = "⚠️" if stale else ("❓" if unk else "✅")
            lines.append(f"### {icon} {proj_id}\n")
            if not results:
                lines.append("_No recognized data sources detected in logs._\n")
                continue
            for r in results:
                lines.append(
                    f"- {status_icon(r['status'])} **{r['label']}** "
                    f"(vintage: {r['current_vintage']}) — {r['message']}"
                )
                if r.get("recommendation"):
                    lines.append(f"  - 🔧 {r['recommendation']}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check data source freshness against known update schedules."
    )
    parser.add_argument(
        "--project-dir",
        help="Path to a specific analysis directory to check (e.g. analyses/ne-tracts-poverty)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all analyses found in registry.json (or analyses/ directory)"
    )
    parser.add_argument(
        "--output",
        help="Path to write JSON output (also writes .md alongside it)"
    )
    parser.add_argument(
        "--sources-only",
        action="store_true",
        help="Only check source schedule, skip analysis log scanning"
    )
    args = parser.parse_args()

    print("=== Data Freshness Monitor ===")
    print(f"  Date: {TODAY.isoformat()}")

    schedule = load_schedule()
    if not schedule:
        print("ERROR: Could not load freshness schedule.", file=sys.stderr)
        return 1

    print(f"  Loaded schedule with {len(schedule)} sources")

    # --- Source-level checks (always run) ---
    print("\n[1/3] Checking source schedules...")
    source_results = []
    for key, source in schedule.items():
        result = check_source_freshness(key, source)
        source_results.append(result)
        icon = status_icon(result["status"])
        print(f"  {icon} {result['label']}: {result['status']}")
        if result["message"]:
            print(f"       {result['message']}")

    # --- Analysis-level checks ---
    analysis_results: dict[str, list[dict]] = {}

    if not args.sources_only:
        if args.project_dir:
            project_dir = Path(args.project_dir).expanduser().resolve()
            if not project_dir.is_dir():
                # Try relative to analyses/
                project_dir = ANALYSES_DIR / args.project_dir
            if not project_dir.is_dir():
                print(f"ERROR: Project directory not found: {args.project_dir}", file=sys.stderr)
                return 1
            print(f"\n[2/3] Scanning analysis: {project_dir.name}")
            results = detect_sources_in_logs(project_dir, schedule)
            analysis_results[project_dir.name] = results
            print(f"  Detected {len(results)} recognized data sources in logs")

        elif args.all:
            analyses = enumerate_analyses()
            print(f"\n[2/3] Scanning {len(analyses)} analysis projects...")
            for adir in analyses:
                print(f"  → {adir.name}")
                results = detect_sources_in_logs(adir, schedule)
                analysis_results[adir.name] = results
                stale = sum(1 for r in results if r["status"] == "STALE")
                print(f"     {len(results)} sources detected, {stale} stale")
        else:
            print("\n[2/3] No --project-dir or --all specified; skipping analysis log scan.")

    # --- Build report ---
    print("\n[3/3] Building report...")
    checked_at = datetime.now(tz=timezone.utc).isoformat()

    # Summary counts
    stale_count = sum(1 for r in source_results if r["status"] == "STALE")
    ok_count = sum(1 for r in source_results if r["status"] == "OK")
    unknown_count = sum(1 for r in source_results if r["status"] == "UNKNOWN")

    report = {
        "generated_at": checked_at,
        "summary": {
            "sources_checked": len(source_results),
            "stale": stale_count,
            "ok": ok_count,
            "unknown": unknown_count,
            "analyses_checked": len(analysis_results),
        },
        "source_freshness": source_results,
        "analysis_freshness": analysis_results,
    }

    md = build_markdown_report(source_results, analysis_results, checked_at)

    print(f"\n  Sources checked: {len(source_results)}")
    print(f"  Stale: {stale_count} | OK: {ok_count} | Unknown: {unknown_count}")
    if analysis_results:
        total_analysis_stale = sum(
            sum(1 for r in results if r["status"] == "STALE")
            for results in analysis_results.values()
        )
        print(f"  Analyses checked: {len(analysis_results)} | Stale sources in analyses: {total_analysis_stale}")

    # --- Output ---
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        md_path = out_path.with_suffix(".md")
        md_path.write_text(md)
        print(f"\n  JSON: {out_path}")
        print(f"  Markdown: {md_path}")
    else:
        print("\n--- Markdown Summary ---")
        print(md)

    return 1 if stale_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
