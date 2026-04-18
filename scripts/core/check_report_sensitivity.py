#!/usr/bin/env python3
"""Sensitivity and Conflict Detector — scan a report for political/editorial risks.

Before publishing, compare a markdown report against the project brief's
political context and flag findings that need careful framing.

Severity levels:
  FAIL  — must be addressed before publishing
  WARN  — review with judgment; may be fine in context
  INFO  — suggestion for stronger writing

Usage:
    python check_report_sensitivity.py \\
        --report outputs/reports/analysis_report.md \\
        --brief analyses/ne-tracts-poverty/project_brief.json \\
        --output outputs/qa/sensitivity_report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import shorten
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def load_report(path: Path) -> tuple[list[str], str]:
    """Return (lines, full_text)."""
    text = path.read_text(encoding="utf-8")
    return text.splitlines(), text


def load_brief(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Could not load brief: {e}", file=sys.stderr)
        return {}


def paragraph_at_line(lines: list[str], line_no: int, window: int = 3) -> str:
    """Extract context around a line."""
    start = max(0, line_no - window)
    end = min(len(lines), line_no + window + 1)
    return "\n".join(lines[start:end])


def excerpt(text: str, max_len: int = 200) -> str:
    return shorten(text.strip(), max_len, placeholder="…")


# ---------------------------------------------------------------------------
# Detection rules
# ---------------------------------------------------------------------------

def rule_sensitive_topics(
    lines: list[str], brief: dict
) -> list[dict]:
    """Rule 1: sensitive_findings_to_handle_carefully → flag paragraphs that mention them."""
    findings = []
    sensitive_topics: list[str] = brief.get("sensitive_findings_to_handle_carefully", [])
    if not sensitive_topics:
        return []

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        for topic in sensitive_topics:
            if isinstance(topic, str) and topic.lower() in line_lower:
                findings.append({
                    "rule": "sensitive_topic",
                    "severity": "WARN",
                    "line_number": i,
                    "line": line.strip(),
                    "context": paragraph_at_line(lines, i - 1),
                    "matched_topic": topic,
                    "message": (
                        f"Report mentions a sensitive topic identified in brief: '{topic}'. "
                        "Ensure framing is careful, evidence-based, and non-inflammatory."
                    ),
                    "suggested_rephrasing": (
                        f"Verify this passage uses neutral, descriptive language for '{topic}'. "
                        "Add a caveat or methodological note if the finding is likely to be contested."
                    ),
                })
                break  # One flag per line is enough

    return findings


def rule_hero_contradicts_belief(
    lines: list[str], brief: dict, full_text: str
) -> list[dict]:
    """Rule 2: hero finding contradicts what_they_already_believe."""
    findings = []
    existing_beliefs: list[str] = brief.get("what_they_already_believe", [])
    hero_finding: str = brief.get("hero_finding", brief.get("key_finding", ""))

    if not hero_finding or not existing_beliefs:
        return []

    hero_lower = hero_finding.lower()

    # Simple contradiction check: look for negation patterns near belief keywords
    negations = re.compile(
        r"\b(not|no|contrary|contrary to|opposite|contradicts?|disproves?|"
        r"challenges?|unexpected|surprising|counter|lower than expected|"
        r"higher than expected|less than expected|more than expected)\b",
        re.IGNORECASE,
    )

    for i, line in enumerate(lines, 1):
        # Check if the hero finding or its key terms appear near a negation
        line_lower = line.lower()
        hero_words = set(w for w in hero_lower.split() if len(w) > 4)
        line_words = set(line_lower.split())
        overlap = hero_words & line_words
        if overlap and negations.search(line):
            findings.append({
                "rule": "hero_contradicts_belief",
                "severity": "WARN",
                "line_number": i,
                "line": line.strip(),
                "context": paragraph_at_line(lines, i - 1),
                "message": (
                    "This line appears to contradict the hero finding or a prior belief held by the client. "
                    "Flag: 'Challenges prior belief — ensure evidence is airtight.'"
                ),
                "hero_finding": hero_finding,
                "existing_beliefs": existing_beliefs,
                "suggested_rephrasing": (
                    "If this challenges what the client already believes, lead with the strongest evidence "
                    "first. Acknowledge the prior assumption explicitly before presenting the finding. "
                    "E.g.: 'Although [prior belief], the data shows…'"
                ),
            })

    return findings


# Causal language patterns for race/ethnicity
CAUSAL_RACE_PATTERNS = [
    # Subject + race/ethnicity + causal verb
    re.compile(
        r"\b(because|due to|caused by|driven by|attributable to|explained by|"
        r"result of|owing to|leads? to|results? in|causes?)\b"
        r"[^.]{0,60}"
        r"\b(race|racial|ethnicity|ethnic|hispanic|latino|latina|latinx|"
        r"black|white|asian|indigenous|native american|african american|"
        r"minority|minorities|people of color|poc)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(race|racial|ethnicity|ethnic|hispanic|latino|latina|latinx|"
        r"black|white|asian|indigenous|native american|african american|"
        r"minority|minorities|people of color|poc)\b"
        r"[^.]{0,60}"
        r"\b(causes?|drives?|leads? to|results? in|explains?|determines?|"
        r"predicts?|accounts? for)\b",
        re.IGNORECASE,
    ),
]

# Descriptive / correlational patterns that are OK (to reduce false positives)
DESCRIPTIVE_RACE_PATTERNS = re.compile(
    r"\b(disproportionately affect|disproportionate|more likely|less likely|"
    r"higher rates? among|lower rates? among|concentrated among|predominantly|"
    r"largely|mostly|majority|correlated with|associated with|compared to)\b",
    re.IGNORECASE,
)


def rule_race_causal(lines: list[str]) -> list[dict]:
    """Rule 3: Race/ethnicity mentioned as causal (not just descriptive) → FAIL."""
    findings = []
    for i, line in enumerate(lines, 1):
        for pattern in CAUSAL_RACE_PATTERNS:
            m = pattern.search(line)
            if m:
                # Skip if it's clearly descriptive/correlational
                if DESCRIPTIVE_RACE_PATTERNS.search(line):
                    continue
                findings.append({
                    "rule": "race_causal_language",
                    "severity": "FAIL",
                    "line_number": i,
                    "line": line.strip(),
                    "context": paragraph_at_line(lines, i - 1),
                    "matched_text": m.group(0),
                    "message": (
                        "Race or ethnicity appears to be used as a causal explanation rather than a "
                        "descriptive correlation. This framing can be misleading and harmful. "
                        "MUST be revised before publishing."
                    ),
                    "suggested_rephrasing": (
                        "Replace causal language with correlational/descriptive framing. "
                        "E.g.: instead of 'poverty is caused by race,' write "
                        "'poverty rates are higher among [group], likely reflecting structural "
                        "barriers including [specific barrier].' Always attribute to systems, "
                        "not identity."
                    ),
                })
                break  # One flag per line

    return findings


POLICY_VERBS = re.compile(
    r"\b(should|must|recommend|recommends?|ought to|urge|urges?|call for|"
    r"calls? for|propose|proposes?|advocate|advocates?|suggest|suggests? that "
    r"(?:the county|the city|the state|officials?|policymakers?))\b",
    re.IGNORECASE,
)

DISCLAIMER_PATTERNS = re.compile(
    r"\b(note|disclaimer|caveat|caution|limitation|based on|subject to|"
    r"contingent|pending|further analysis|additional research|not a substitute|"
    r"for informational|not policy advice|consult)\b",
    re.IGNORECASE,
)


def rule_policy_without_disclaimer(lines: list[str]) -> list[dict]:
    """Rule 4: Policy recommendation without explicit disclaimer → WARN."""
    findings = []
    for i, line in enumerate(lines, 1):
        if POLICY_VERBS.search(line):
            # Check surrounding context (±3 lines) for a disclaimer
            start = max(0, i - 4)
            end = min(len(lines), i + 3)
            context_block = " ".join(lines[start:end])
            if not DISCLAIMER_PATTERNS.search(context_block):
                findings.append({
                    "rule": "policy_without_disclaimer",
                    "severity": "WARN",
                    "line_number": i,
                    "line": line.strip(),
                    "context": paragraph_at_line(lines, i - 1),
                    "message": (
                        "Policy recommendation detected without an explicit disclaimer "
                        "that findings are data-driven and not prescriptive policy advice."
                    ),
                    "suggested_rephrasing": (
                        "Add a disclaimer near policy-adjacent language. E.g.: "
                        "'Based on this data, the analysis supports further investigation into X. "
                        "Final policy decisions should incorporate stakeholder input and "
                        "community context beyond the scope of this analysis.'"
                    ),
                })

    return findings


SUPERLATIVES = re.compile(
    r"\b(worst|best|most|highest|lowest|greatest|least|largest|smallest|"
    r"most severe|most concentrated|most affected|most underserved|"
    r"number one|#1|top-ranked|bottom-ranked)\b",
    re.IGNORECASE,
)

CITATION_NEARBY = re.compile(
    r"(\([^)]{3,}\)|\[\d+\]|according to|per the|data show|data shows|"
    r"figure \d|table \d|see appendix|as shown|source:|\d{4} [A-Z])",
    re.IGNORECASE,
)


def rule_superlative_without_citation(lines: list[str]) -> list[dict]:
    """Rule 5: Superlatives without citation → WARN."""
    findings = []
    for i, line in enumerate(lines, 1):
        m = SUPERLATIVES.search(line)
        if m:
            # Check line + next line for a citation signal
            context_block = line
            if i < len(lines):
                context_block += " " + lines[i]
            if not CITATION_NEARBY.search(context_block):
                findings.append({
                    "rule": "superlative_without_citation",
                    "severity": "WARN",
                    "line_number": i,
                    "line": line.strip(),
                    "context": paragraph_at_line(lines, i - 1),
                    "matched_superlative": m.group(0),
                    "message": (
                        f"Superlative '{m.group(0)}' used without an obvious citation or "
                        "data reference nearby. Strong claims require strong evidence."
                    ),
                    "suggested_rephrasing": (
                        f"Follow '{m.group(0)}' with a specific data reference. "
                        "E.g.: '…the highest poverty rate in the state (24%, ACS 2022 5-year)' "
                        "or add a parenthetical: '(see Table 2).'"
                    ),
                })

    return findings


PASSIVE_UNCERTAINTY = re.compile(
    r"\b(may suggest|seem(s)? to (indicate|suggest|imply|show)|"
    r"might suggest|could suggest|appears? to (indicate|suggest)|"
    r"tends? to suggest|would seem to|seems? like|seems? as though|"
    r"might indicate|may indicate|could indicate|could imply|may imply)\b",
    re.IGNORECASE,
)

KEY_FINDING_MARKERS = re.compile(
    r"^#+\s*(key finding|finding|conclusion|summary|result|hero|executive)",
    re.IGNORECASE,
)


def rule_passive_uncertainty(lines: list[str]) -> list[dict]:
    """Rule 6: Passive uncertainty phrases in key findings → INFO."""
    findings = []
    in_key_section = False

    for i, line in enumerate(lines, 1):
        if KEY_FINDING_MARKERS.match(line):
            in_key_section = True

        m = PASSIVE_UNCERTAINTY.search(line)
        if m:
            findings.append({
                "rule": "passive_uncertainty",
                "severity": "INFO",
                "line_number": i,
                "line": line.strip(),
                "context": paragraph_at_line(lines, i - 1),
                "matched_phrase": m.group(0),
                "in_key_section": in_key_section,
                "message": (
                    f"Passive uncertainty phrase '{m.group(0)}' detected. "
                    "Prefer active, assertive language in findings. "
                    "If the evidence is genuinely uncertain, be specific about why."
                ),
                "suggested_rephrasing": (
                    f"Replace '{m.group(0)}' with direct language. "
                    "E.g.: 'This suggests' → 'The data shows'; "
                    "'may indicate' → 'indicates' (if confident) or "
                    "'is consistent with' (if uncertain). "
                    "If genuinely unsure, say: 'Further analysis is needed to confirm X.'"
                ),
            })

    return findings


# ---------------------------------------------------------------------------
# Aggregate and run
# ---------------------------------------------------------------------------

def run_all_rules(lines: list[str], full_text: str, brief: dict) -> list[dict]:
    all_findings = []
    all_findings += rule_sensitive_topics(lines, brief)
    all_findings += rule_hero_contradicts_belief(lines, brief, full_text)
    all_findings += rule_race_causal(lines)
    all_findings += rule_policy_without_disclaimer(lines)
    all_findings += rule_superlative_without_citation(lines)
    all_findings += rule_passive_uncertainty(lines)
    return sorted(all_findings, key=lambda f: (
        {"FAIL": 0, "WARN": 1, "INFO": 2}.get(f["severity"], 9),
        f["line_number"],
    ))


def build_summary(findings: list[dict]) -> dict:
    fail = [f for f in findings if f["severity"] == "FAIL"]
    warn = [f for f in findings if f["severity"] == "WARN"]
    info = [f for f in findings if f["severity"] == "INFO"]

    rules_hit: dict[str, int] = {}
    for f in findings:
        rules_hit[f["rule"]] = rules_hit.get(f["rule"], 0) + 1

    verdict = "PASS"
    if fail:
        verdict = "FAIL"
    elif warn:
        verdict = "WARN"

    return {
        "verdict": verdict,
        "total_findings": len(findings),
        "fail_count": len(fail),
        "warn_count": len(warn),
        "info_count": len(info),
        "rules_triggered": rules_hit,
    }


def format_markdown_report(
    findings: list[dict],
    summary: dict,
    report_path: str,
    brief_path: str,
    checked_at: str,
) -> str:
    lines_out = [
        "# Sensitivity & Conflict Detection Report",
        f"\n_Report: `{report_path}`_",
        f"_Brief: `{brief_path}`_",
        f"_Checked: {checked_at}_\n",
        "## Verdict\n",
    ]

    verdict = summary["verdict"]
    verdict_icons = {"PASS": "✅", "WARN": "⚠️", "FAIL": "🚨"}
    lines_out.append(
        f"{verdict_icons.get(verdict, '❔')} **{verdict}** — "
        f"{summary['fail_count']} FAIL · {summary['warn_count']} WARN · {summary['info_count']} INFO\n"
    )

    if verdict == "PASS":
        lines_out.append("_No blocking issues found. Review WARN and INFO items before publishing._\n")

    for severity, label, icon in [("FAIL", "Must Fix", "🚨"), ("WARN", "Review", "⚠️"), ("INFO", "Suggestions", "💡")]:
        sev_findings = [f for f in findings if f["severity"] == severity]
        if not sev_findings:
            continue
        lines_out += [f"\n## {icon} {label} ({severity}) — {len(sev_findings)} findings\n"]
        for i, f in enumerate(sev_findings, 1):
            lines_out += [
                f"### {i}. Line {f['line_number']}: `{f['rule']}`",
                f"\n**Message:** {f['message']}\n",
                f"**Line {f['line_number']}:**",
                f"```",
                f"{f['line'][:300]}",
                f"```",
            ]
            if f.get("context"):
                lines_out += [
                    f"\n**Context:**",
                    f"```",
                    f"{f['context'][:400]}",
                    f"```",
                ]
            if f.get("suggested_rephrasing"):
                lines_out.append(f"\n💬 **Suggestion:** {f['suggested_rephrasing']}\n")
            lines_out.append("---")

    return "\n".join(lines_out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan a report for sensitivity and political conflict issues before publishing."
    )
    parser.add_argument("--report", required=True, help="Path to the markdown report to scan")
    parser.add_argument("--brief", required=True, help="Path to project_brief.json")
    parser.add_argument("--output", help="Path to write JSON sensitivity report")
    parser.add_argument("--quiet", action="store_true", help="Only print summary, not all findings")
    args = parser.parse_args()

    report_path = Path(args.report).expanduser().resolve()
    brief_path = Path(args.brief).expanduser().resolve()

    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}", file=sys.stderr)
        return 1
    if not brief_path.exists():
        print(f"ERROR: Brief not found: {brief_path}", file=sys.stderr)
        return 1

    print("=== Sensitivity / Conflict Detector ===")
    print(f"  Report: {report_path.name}")
    print(f"  Brief:  {brief_path.name}")

    lines, full_text = load_report(report_path)
    brief = load_brief(brief_path)

    print(f"  Lines: {len(lines)} | Brief keys: {list(brief.keys())[:8]}")
    print("  Running checks...")

    findings = run_all_rules(lines, full_text, brief)
    summary = build_summary(findings)
    checked_at = datetime.now(tz=timezone.utc).isoformat()

    # Print summary
    verdict = summary["verdict"]
    icons = {"PASS": "✅", "WARN": "⚠️", "FAIL": "🚨"}
    print(f"\n  Verdict: {icons.get(verdict, '?')} {verdict}")
    print(f"  FAIL: {summary['fail_count']} | WARN: {summary['warn_count']} | INFO: {summary['info_count']}")

    if not args.quiet:
        for f in findings:
            sev = f["severity"]
            icon = {"FAIL": "🚨", "WARN": "⚠️", "INFO": "💡"}.get(sev, "?")
            print(f"\n  {icon} [{sev}] Line {f['line_number']} — {f['rule']}")
            print(f"     {excerpt(f['message'], 120)}")
            if f.get("suggested_rephrasing"):
                print(f"     → {excerpt(f['suggested_rephrasing'], 100)}")

    # Build output
    md_report = format_markdown_report(
        findings, summary,
        str(report_path), str(brief_path),
        checked_at,
    )

    output_payload = {
        "generated_at": checked_at,
        "report": str(report_path),
        "brief": str(brief_path),
        "summary": summary,
        "findings": findings,
    }

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
        md_path = out_path.with_suffix(".md")
        md_path.write_text(md_report, encoding="utf-8")
        print(f"\n  JSON: {out_path}")
        print(f"  Markdown: {md_path}")
    else:
        print("\n--- Sensitivity Report ---")
        print(md_report)

    # Exit code: 0 = pass/info only, 1 = warn, 2 = fail
    if summary["fail_count"] > 0:
        return 2
    if summary["warn_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
