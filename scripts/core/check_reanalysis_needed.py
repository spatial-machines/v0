#!/usr/bin/env python3
"""Automated Re-Analysis Trigger — identify completed analyses that need re-running.

When new data vintages are released, reads each analysis's project_brief.json
and all *.log.json files to extract data sources and vintages used, then
compares against data-freshness-schedule.json to detect stale sources.

For each stale source, computes an impact score based on how central the
source is to the analysis (primary vs. supplemental). Outputs a ranked JSON
report and a summary markdown.

Usage:
    # Check one project
    python check_reanalysis_needed.py --project-id mn-poverty-change

    # Check all projects in registry
    python check_reanalysis_needed.py --all

    # Write output files
    python check_reanalysis_needed.py --all --output outputs/reanalysis_report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_FILE = PROJECT_ROOT / "config" / "data-freshness-schedule.json"
REGISTRY_FILE = PROJECT_ROOT / "analyses" / "registry.json"
ANALYSES_DIR = PROJECT_ROOT / "analyses"
TRIGGERS_FILE = PROJECT_ROOT / "config" / "reanalysis-triggers.json"
LOGS_DIR = PROJECT_ROOT / "docs" / "memory"

TODAY = datetime.now(tz=timezone.utc).date()


# ---------------------------------------------------------------------------
# Load configs
# ---------------------------------------------------------------------------

def load_schedule() -> dict:
    if not SCHEDULE_FILE.exists():
        print(f"WARNING: schedule not found: {SCHEDULE_FILE}", file=sys.stderr)
        return {}
    data = json.loads(SCHEDULE_FILE.read_text())
    return data.get("sources", data)


def load_triggers() -> dict:
    if not TRIGGERS_FILE.exists():
        return {}
    try:
        return json.loads(TRIGGERS_FILE.read_text())
    except Exception:
        return {}


def load_registry() -> list[dict]:
    if not REGISTRY_FILE.exists():
        # Try root-level registry
        alt = PROJECT_ROOT / "registry.json"
        if alt.exists():
            try:
                data = json.loads(alt.read_text())
                return data.get("analyses", [])
            except Exception:
                pass
        return []
    try:
        data = json.loads(REGISTRY_FILE.read_text())
        return data.get("analyses", [])
    except Exception:
        return []


def enumerate_analysis_dirs() -> list[Path]:
    """Return sorted list of analysis directories from registry or filesystem."""
    registry = load_registry()
    dirs = []
    if registry:
        for entry in registry:
            pid = entry.get("id") or entry.get("project_id") or entry.get("name")
            if pid:
                candidate = ANALYSES_DIR / pid
                if candidate.is_dir():
                    dirs.append(candidate)
    if not dirs and ANALYSES_DIR.exists():
        dirs = [d for d in ANALYSES_DIR.iterdir()
                if d.is_dir() and not d.name.startswith(".") and d.name != "registry.json"]
    return sorted(dirs)


# ---------------------------------------------------------------------------
# Source / vintage detection from analysis artifacts
# ---------------------------------------------------------------------------

def extract_vintage_from_text(text: str) -> Optional[str]:
    """Try to parse a 4-digit year from text as the vintage."""
    m = re.search(r"\b(20\d{2})\b", text)
    return m.group(1) if m else None


def detect_sources_in_analysis(project_dir: Path, schedule: dict) -> dict[str, dict]:
    """
    Scan project_brief.json + all *.log.json files for data source references.
    Returns: {source_key: {vintage_used, retrieval_date, confidence, is_primary}}
    """
    detected: dict[str, dict] = {}

    # Collect all candidate text blobs
    blobs: list[tuple[str, dict]] = []  # (label, parsed_json)

    project_brief_path = project_dir / "project_brief.json"
    if project_brief_path.exists():
        try:
            data = json.loads(project_brief_path.read_text())
            blobs.append(("project_brief", data))
        except Exception:
            pass

    # Scan runs/ and data/ subdirs for log files
    for pattern in ["**/*.log.json", "**/*handoff.json", "**/*provenance.json", "**/*.analysis-handoff.json"]:
        for lf in project_dir.rglob(pattern.replace("**/", "")):
            try:
                data = json.loads(lf.read_text())
                blobs.append((lf.name, data))
            except Exception:
                pass
    # Also runs at project root level
    runs_dir = project_dir / "runs"
    if runs_dir.exists():
        for lf in runs_dir.glob("*.json"):
            try:
                data = json.loads(lf.read_text())
                blobs.append((lf.name, data))
            except Exception:
                pass

    if not blobs:
        return detected

    # Build combined text for keyword matching
    all_text = " ".join(json.dumps(b[1]).lower() for b in blobs)

    # Extract "primary_data_sources" from project brief if present
    primary_source_labels: set[str] = set()
    for label, data in blobs:
        if "brief" in label:
            for key_path in [
                ["data_sources", "primary"],
                ["data", "primary_sources"],
                ["sources", "primary"],
            ]:
                node = data
                for k in key_path:
                    node = node.get(k, {}) if isinstance(node, dict) else None
                    if node is None:
                        break
                if isinstance(node, list):
                    for s in node:
                        if isinstance(s, str):
                            primary_source_labels.add(s.lower())
                        elif isinstance(s, dict):
                            lbl = s.get("label", s.get("name", s.get("id", "")))
                            if lbl:
                                primary_source_labels.add(lbl.lower())

    for source_key, source_meta in schedule.items():
        keywords = source_meta.get("match_keywords", [])
        if not keywords:
            continue
        matched_keywords = [kw for kw in keywords if kw.lower() in all_text]
        if not matched_keywords:
            continue

        # Try to find the vintage used
        vintage_used = None
        retrieval_date = None
        for _, data in blobs:
            text = json.dumps(data)
            v = extract_vintage_from_text(text)
            if v:
                vintage_used = v
            # Try structured retrieval_date fields
            for k in ["retrieved_at", "retrieval_date", "data_vintage", "vintage"]:
                val = data.get(k)
                if isinstance(val, str) and val:
                    retrieval_date = val
                    break

        # Determine if primary (mentioned in primary sources list OR high keyword density)
        is_primary = (
            source_key in primary_source_labels
            or any(kw.lower() in primary_source_labels for kw in matched_keywords)
            or len(matched_keywords) >= 2
        )

        detected[source_key] = {
            "source_key": source_key,
            "label": source_meta["label"],
            "vintage_used": vintage_used or source_meta.get("current_vintage", "unknown"),
            "retrieval_date": retrieval_date,
            "is_primary": is_primary,
            "matched_keywords": matched_keywords[:3],
            "current_vintage": source_meta.get("current_vintage", "unknown"),
            "next_expected_vintage": source_meta.get("next_expected_vintage", ""),
            "next_release_approx": source_meta.get("next_release_approx", ""),
            "frequency": source_meta.get("frequency", "annual"),
            "url": source_meta.get("url", ""),
        }

    return detected


# ---------------------------------------------------------------------------
# Staleness + impact scoring
# ---------------------------------------------------------------------------

def check_source_staleness(source_info: dict) -> dict:
    """Return staleness status: OK | STALE | UNKNOWN, plus version delta."""
    vintage_used = source_info.get("vintage_used", "unknown")
    current_vintage = source_info.get("current_vintage", "unknown")
    next_expected = source_info.get("next_expected_vintage", "")
    next_release = source_info.get("next_release_approx", "")

    staleness = {
        "status": "OK",
        "vintage_used": vintage_used,
        "latest_available": current_vintage,
        "vintages_behind": 0,
        "message": "",
        "is_major_change": False,
    }

    # Compare as years if both are 4-digit
    def as_year(v: str) -> Optional[int]:
        m = re.match(r"^(\d{4})$", str(v).strip())
        return int(m.group(1)) if m else None

    used_yr = as_year(vintage_used)
    current_yr = as_year(current_vintage)

    if used_yr and current_yr and current_yr > used_yr:
        delta = current_yr - used_yr
        staleness["status"] = "STALE"
        staleness["vintages_behind"] = delta
        staleness["is_major_change"] = delta >= 2
        staleness["message"] = (
            f"Using {vintage_used}, {current_vintage} now available "
            f"({delta} vintage{'s' if delta > 1 else ''} behind)"
        )
        return staleness

    # Check next_release_approx: if release date has passed, flag
    if next_release and next_expected:
        try:
            if re.match(r"^\d{4}$", next_release):
                rel_date = datetime(int(next_release), 7, 1).date()
            elif re.match(r"^\d{4}-\d{2}$", next_release):
                y, m2 = next_release.split("-")
                rel_date = datetime(int(y), int(m2), 1).date()
            else:
                rel_date = None
            if rel_date and TODAY >= rel_date:
                staleness["status"] = "STALE"
                staleness["vintages_behind"] = 1
                staleness["latest_available"] = next_expected
                staleness["message"] = (
                    f"Using {vintage_used}; {next_expected} likely available "
                    f"(estimated release {next_release})"
                )
                return staleness
        except (ValueError, TypeError):
            pass

    staleness["status"] = "OK"
    staleness["message"] = f"Current ({vintage_used} == {current_vintage})"
    return staleness


def compute_impact_score(source_info: dict, staleness: dict, triggers: dict) -> float:
    """
    Compute 0.0–1.0 impact score for a stale source.
    Higher = more central to the analysis → higher urgency to re-run.
    """
    if staleness["status"] != "STALE":
        return 0.0

    score = 0.0
    source_key = source_info.get("source_key", "")

    # Base score from source criticality in triggers config
    source_cfg = triggers.get("source_criticality", {}).get(source_key, {})
    criticality = source_cfg.get("criticality", "informational")
    if criticality == "critical":
        score += 0.5
    elif criticality == "important":
        score += 0.3
    else:
        score += 0.1

    # Primary source detected in this analysis
    if source_info.get("is_primary"):
        score += 0.25

    # Multiple vintages behind
    behind = staleness.get("vintages_behind", 0)
    if behind >= 3:
        score += 0.2
    elif behind == 2:
        score += 0.15
    elif behind == 1:
        score += 0.05

    # Major change flag
    if staleness.get("is_major_change"):
        score += 0.1

    return min(round(score, 3), 1.0)


def compute_staleness_severity(project_result: dict) -> str:
    """Overall severity for a project: CRITICAL | HIGH | MEDIUM | LOW | OK."""
    stale_sources = project_result.get("stale_sources", [])
    if not stale_sources:
        return "OK"
    max_impact = max(s.get("impact_score", 0) for s in stale_sources)
    if max_impact >= 0.7:
        return "CRITICAL"
    elif max_impact >= 0.5:
        return "HIGH"
    elif max_impact >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# Per-analysis check
# ---------------------------------------------------------------------------

def check_analysis(project_dir: Path, schedule: dict, triggers: dict) -> dict:
    """Run re-analysis check for one project directory."""
    project_id = project_dir.name

    # Load project brief metadata
    brief_meta: dict = {}
    brief_path = project_dir / "project_brief.json"
    if brief_path.exists():
        try:
            brief_meta = json.loads(brief_path.read_text())
        except Exception:
            pass

    result = {
        "project_id": project_id,
        "project_title": brief_meta.get("project_title", project_id),
        "created_at": brief_meta.get("created_at", ""),
        "checked_at": TODAY.isoformat(),
        "stale_sources": [],
        "clean_sources": [],
        "unknown_sources": [],
        "reanalysis_recommended": False,
        "severity": "OK",
        "total_sources_detected": 0,
    }

    # Detect sources used
    detected = detect_sources_in_analysis(project_dir, schedule)
    result["total_sources_detected"] = len(detected)

    if not detected:
        result["note"] = "No recognized data sources detected in logs"
        return result

    # Check each source
    for source_key, source_info in detected.items():
        staleness = check_source_staleness(source_info)
        impact = compute_impact_score(source_info, staleness, triggers)

        entry = {
            "source_key": source_key,
            "label": source_info["label"],
            "is_primary": source_info.get("is_primary", False),
            "vintage_used": staleness["vintage_used"],
            "latest_available": staleness["latest_available"],
            "vintages_behind": staleness["vintages_behind"],
            "is_major_change": staleness.get("is_major_change", False),
            "message": staleness["message"],
            "impact_score": impact,
            "url": source_info.get("url", ""),
        }

        if staleness["status"] == "STALE":
            result["stale_sources"].append(entry)
        elif staleness["status"] == "OK":
            result["clean_sources"].append(entry)
        else:
            result["unknown_sources"].append(entry)

    # Sort stale by impact descending
    result["stale_sources"].sort(key=lambda x: x["impact_score"], reverse=True)
    result["reanalysis_recommended"] = len(result["stale_sources"]) > 0
    result["severity"] = compute_staleness_severity(result)

    return result


# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------

def severity_icon(sev: str) -> str:
    return {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🔵",
        "OK": "✅",
    }.get(sev, "❓")


def build_markdown_summary(results: list[dict], checked_at: str) -> str:
    needs_rerun = [r for r in results if r["reanalysis_recommended"]]
    clean = [r for r in results if not r["reanalysis_recommended"]]

    lines = [
        "# Re-Analysis Trigger Report",
        f"\n_Generated: {checked_at}_\n",
        "## Summary\n",
    ]

    if needs_rerun:
        # Build the "N analyses have stale data" lead line
        stale_snippets = []
        for r in needs_rerun[:3]:
            stale_src = r["stale_sources"]
            if stale_src:
                src_msg = stale_src[0]["label"]
                new_v = stale_src[0]["latest_available"]
                stale_snippets.append(f"{r['project_id']} ({src_msg} {new_v} now available)")
        lead = f"**{len(needs_rerun)} {'analysis' if len(needs_rerun) == 1 else 'analyses'} have stale data"
        if stale_snippets:
            lead += f" — {', '.join(stale_snippets)}"
            if len(needs_rerun) > 3:
                lead += f", and {len(needs_rerun) - 3} more"
        lead += "**"
        lines.append(lead)
        lines.append("")
    else:
        lines.append("**All analyses are current. No re-runs needed.**\n")

    lines += [
        f"- Analyses checked: {len(results)}",
        f"- Need re-run: {len(needs_rerun)}",
        f"- Current: {len(clean)}",
        "",
    ]

    if needs_rerun:
        lines.append("## Analyses Requiring Re-Run\n")
        lines.append("_Ranked by staleness severity + impact score_\n")
        for r in needs_rerun:
            icon = severity_icon(r["severity"])
            lines += [
                f"### {icon} {r['project_id']} — {r['project_title']}",
                f"- **Severity:** {r['severity']}",
                f"- **Stale sources:** {len(r['stale_sources'])}",
                "",
            ]
            for src in r["stale_sources"]:
                primary_tag = " *(primary)*" if src["is_primary"] else ""
                lines.append(
                    f"  - **{src['label']}**{primary_tag}: {src['message']}"
                )
                lines.append(f"    - Impact score: {src['impact_score']:.2f}")
                if src.get("url"):
                    lines.append(f"    - Source: {src['url']}")
            lines.append("")
            if r["clean_sources"]:
                lines.append(f"  _(Current sources: {', '.join(s['label'] for s in r['clean_sources'])})_")
                lines.append("")

    if clean:
        lines.append("## ✅ Analyses — Current\n")
        for r in clean:
            lines.append(f"- **{r['project_id']}** — {r.get('project_title', r['project_id'])}")
        lines.append("")

    lines += [
        "---",
        "## How to Re-Run\n",
        "```bash",
        "# Re-run a specific analysis (example: mn-poverty-change)",
        "cd /path/to/gis-agent",
        "# 1. Update source data",
        "python scripts/retrieve_tiger.py --state MN --output analyses/mn-poverty-change/data/raw/",
        "# 2. Re-run full pipeline",
        "python scripts/create_run_plan.py --project-id mn-poverty-change",
        "```",
        "",
        "See project_brief.json in each analysis directory for original pipeline details.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Identify completed analyses that need re-running due to stale data."
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--project-id", help="Check a single analysis by project ID")
    grp.add_argument("--all", action="store_true", help="Check all analyses in registry")
    parser.add_argument("--output", help="Path for JSON output (also writes .md alongside)")
    parser.add_argument(
        "--min-severity",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="LOW",
        help="Only include analyses at or above this severity (default: LOW = all)",
    )
    args = parser.parse_args()

    print("=== Re-Analysis Trigger Check ===")
    print(f"  Date: {TODAY.isoformat()}")

    schedule = load_schedule()
    if not schedule:
        print("ERROR: Could not load data-freshness-schedule.json", file=sys.stderr)
        return 1
    print(f"  Loaded schedule: {len(schedule)} sources")

    triggers = load_triggers()
    print(f"  Loaded triggers config: {len(triggers.get('monitored_analyses', {}))} monitored analyses")

    # Enumerate target analyses
    if args.project_id:
        target_dirs = [ANALYSES_DIR / args.project_id]
        if not target_dirs[0].is_dir():
            print(f"ERROR: Analysis directory not found: {ANALYSES_DIR / args.project_id}", file=sys.stderr)
            return 1
    else:
        target_dirs = enumerate_analysis_dirs()
        # Filter to only auto-monitored if triggers config specifies
        monitored = triggers.get("monitored_analyses", {})
        if monitored:
            target_dirs = [d for d in target_dirs if d.name in monitored]
        if not target_dirs:
            # Fall back: check all
            target_dirs = enumerate_analysis_dirs()

    print(f"  Checking {len(target_dirs)} analysis project(s)...\n")

    results: list[dict] = []
    for adir in target_dirs:
        print(f"  → {adir.name}")
        result = check_analysis(adir, schedule, triggers)
        stale_n = len(result["stale_sources"])
        sev = result["severity"]
        print(f"     {sev} | {stale_n} stale source(s) | {result['total_sources_detected']} detected")
        results.append(result)

    # Filter by min severity
    severity_order = ["OK", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    min_idx = severity_order.index(args.min_severity)
    filtered = [
        r for r in results
        if severity_order.index(r["severity"]) >= min_idx or not r["reanalysis_recommended"]
    ]

    # Sort: needs-rerun first (by severity desc), then clean
    sev_score = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "OK": 0}
    filtered.sort(key=lambda r: sev_score.get(r["severity"], 0), reverse=True)

    checked_at = datetime.now(tz=timezone.utc).isoformat()

    needs_rerun = [r for r in filtered if r["reanalysis_recommended"]]
    print(f"\n  === Results ===")
    print(f"  Analyses checked: {len(results)}")
    print(f"  Need re-run: {len(needs_rerun)}")
    if needs_rerun:
        for r in needs_rerun:
            icon = severity_icon(r["severity"])
            print(f"  {icon} {r['project_id']}: {r['severity']} — {len(r['stale_sources'])} stale source(s)")

    report = {
        "generated_at": checked_at,
        "summary": {
            "analyses_checked": len(results),
            "need_rerun": len(needs_rerun),
            "current": len(results) - len(needs_rerun),
            "severity_counts": {
                sev: sum(1 for r in results if r["severity"] == sev)
                for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "OK"]
            },
        },
        "results": filtered,
    }

    md = build_markdown_summary(filtered, checked_at)

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        md_path = out.with_suffix(".md")
        md_path.write_text(md)
        print(f"\n  JSON: {out}")
        print(f"  Markdown: {md_path}")
    else:
        print("\n--- Summary ---")
        print(md)

    return 1 if needs_rerun else 0


if __name__ == "__main__":
    raise SystemExit(main())
