#!/usr/bin/env python3
"""Peer Review Agent Runner — assembles a review brief and invokes the Skeptic.

Finds a completed analysis by project ID, reads its outputs (maps, reports,
validation JSON), assembles a structured peer review brief, and writes the
critique to outputs/qa/<project_id>_peer_review.json.

The review is performed by this script acting as the Skeptic persona defined
in workspace-peer-reviewer/SOUL.md. It reads ONLY the output artifacts —
never scripts, raw data, or handoff logs — to simulate an independent reviewer
who sees only what would be delivered to a client.

Usage:
    python run_peer_review.py --project-id chicago-food-access
    python run_peer_review.py --project-id ks-healthcare-access --verbose
    python run_peer_review.py --project-id chicago-food-access --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYSES_DIR = PROJECT_ROOT / "analyses"

# ---------------------------------------------------------------------------
# Output readers — only touches outputs/
# ---------------------------------------------------------------------------

def collect_output_files(project_dir: Path) -> dict[str, list[Path]]:
    """Index all output files by category. Never touches scripts/ or data/."""
    outputs_dir = project_dir / "outputs"
    if not outputs_dir.exists():
        return {}

    categories: dict[str, list[Path]] = {
        "maps": [],
        "reports": [],
        "qa": [],
        "web": [],
        "qgis": [],
    }

    for subdir, cat in [
        ("maps", "maps"),
        ("reports", "reports"),
        ("qa", "qa"),
        ("web", "web"),
        ("qgis", "qgis"),
    ]:
        d = outputs_dir / subdir
        if d.exists():
            categories[cat] = sorted(d.rglob("*") if cat == "qgis" else d.glob("*"))
            categories[cat] = [f for f in categories[cat] if f.is_file()]

    return categories


def read_report_excerpt(project_dir: Path, max_chars: int = 3000) -> str:
    """Read the executive brief or technical report for critique context."""
    reports_dir = project_dir / "outputs" / "reports"
    if not reports_dir.exists():
        return "(no report found)"

    # Preference order
    for candidate in ["executive_brief.md", "analysis_report.md", "technical_report.md"]:
        p = reports_dir / candidate
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[...truncated for peer review...]"
            return text

    # Fall back to any markdown file
    md_files = sorted(reports_dir.glob("*.md"))
    if md_files:
        text = md_files[0].read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...truncated for peer review...]"
        return text

    return "(no readable report found)"


def read_validation_json(project_dir: Path) -> dict[str, Any] | None:
    """Read validation/QA JSON if available."""
    candidates = [
        project_dir / "outputs" / "qa" / "validation_report.json",
        project_dir / "runs" / "validation_report.json",
        project_dir / "outputs" / "reports" / "benchmark_scorecard.md",
    ]
    for p in candidates:
        if p.exists() and p.suffix == ".json":
            try:
                return json.loads(p.read_text())
            except json.JSONDecodeError:
                pass
    return None


def read_project_brief(project_dir: Path) -> dict[str, Any] | None:
    """Read the project brief for context (hero question, audience, etc.)."""
    p = project_dir / "project_brief.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return None


def read_benchmark_score(project_dir: Path) -> str | None:
    """Extract benchmark score from scorecard markdown if present."""
    scorecard = project_dir / "outputs" / "reports" / "benchmark_scorecard.md"
    if not scorecard.exists():
        return None
    text = scorecard.read_text(encoding="utf-8", errors="replace")
    # Look for score pattern like "Score: 87/100" or "**87/100**"
    match = re.search(r'(?:score|total)[:\s*]+(\d{1,3})\s*/\s*100', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}/100"
    match = re.search(r'\*\*(\d{1,3}/100)\*\*', text)
    if match:
        return match.group(1)
    return None

# ---------------------------------------------------------------------------
# Map critique helpers
# ---------------------------------------------------------------------------

MAP_TYPE_RULES: dict[str, dict[str, Any]] = {
    "choropleth": {
        "good_for": ["rates", "percentages", "continuous values", "normalized data"],
        "bad_for": ["raw counts", "binary yes/no", "point data"],
        "check": "Is the variable normalized (rate/pct)? Raw counts on a choropleth are misleading.",
    },
    "dot_density": {
        "good_for": ["raw counts", "population totals", "absolute quantities"],
        "bad_for": ["rates", "percentages"],
        "check": "Is this showing a count (good) or a rate (misleading)?",
    },
    "hotspot": {
        "good_for": ["spatially autocorrelated continuous values"],
        "bad_for": ["non-significant global Moran's I", "binary flags"],
        "check": "Was Global Moran's I run first? A non-significant result means hotspot maps show noise.",
    },
    "bivariate": {
        "good_for": ["two correlated continuous variables", "joint distribution exploration"],
        "bad_for": ["more than 2 variables", "non-comparable scales"],
        "check": "Are both variables normalized to the same geographic unit? Are scales comparable?",
    },
    "service_area": {
        "good_for": ["facility access", "drive time", "coverage"],
        "bad_for": ["population-level rates", "continuous outcomes"],
        "check": "Do the service area buffers account for road network or just straight-line distance?",
    },
}


def critique_map_choices(output_files: dict[str, list[Path]], brief: dict | None) -> list[dict]:
    """
    Critique map type appropriateness for detected variable types.
    Returns list of findings.
    """
    findings = []
    map_files = output_files.get("maps", [])
    if not map_files:
        findings.append({
            "severity": "BLOCKING",
            "dimension": "map_choices",
            "finding": "No map outputs found in outputs/maps/.",
            "suggested_fix": "Run cartography agent before peer review.",
        })
        return findings

    map_names = [f.stem.lower() for f in map_files if f.suffix in (".png", ".jpg", ".html")]

    # Check for raw-count choropleths
    choropleth_names = [n for n in map_names if "choropleth" in n]
    for name in choropleth_names:
        if re.search(r'\btotal\b|\bcount\b|\bnum\b|\bpopulation\b', name):
            findings.append({
                "severity": "MODERATE",
                "dimension": "map_choices",
                "map": name,
                "finding": f"'{name}' appears to show raw counts on a choropleth. "
                           "Choropleths of raw counts are misleading because larger-area "
                           "polygons visually dominate regardless of density.",
                "suggested_fix": "Normalize to rate or density per unit area/population, "
                                 "or switch to a dot density or proportional symbol map.",
            })

    # Check for hotspot maps — confirm Moran's I evidence
    hotspot_names = [n for n in map_names if "hotspot" in n or "gi_star" in n or "lisa" in n]
    for name in hotspot_names:
        findings.append({
            "severity": "INFO",
            "dimension": "map_choices",
            "map": name,
            "finding": f"'{name}' shows local clustering. Verify Global Moran's I was significant "
                       "(p ≤ 0.05) before this map was generated.",
            "suggested_fix": "Check runs/morans_i_*.json for the I statistic and p-value. "
                             "If p > 0.05, replace with choropleth + top-N ranking.",
        })

    # Check for binary choropleths
    for name in choropleth_names:
        if re.search(r'\bflag\b|\bbinary\b|\byes_no\b|\bdesert\b', name):
            findings.append({
                "severity": "LOW",
                "dimension": "map_choices",
                "map": name,
                "finding": f"'{name}' uses choropleth for a binary/flag variable. "
                           "Binary data on 5-class choropleth wastes the color scale.",
                "suggested_fix": "Consider a simple two-color fill (yes/no) or overlay with "
                                 "a continuous variable to add analytical depth.",
            })

    if not findings:
        findings.append({
            "severity": "INFO",
            "dimension": "map_choices",
            "finding": f"Reviewed {len(map_names)} map(s). No obvious map-type mismatches detected "
                       "from filenames. Manual visual inspection recommended.",
            "suggested_fix": "None required at this stage.",
        })

    return findings


# ---------------------------------------------------------------------------
# Report critique helpers
# ---------------------------------------------------------------------------

def critique_hero_finding(report_text: str, brief: dict | None) -> dict:
    """Check whether the hero finding is supported by the evidence in the report."""
    hero_q = ""
    pyramid_lead = ""
    if brief:
        hero_q = brief.get("engagement", {}).get("hero_question", "")
        pyramid_lead = brief.get("report", {}).get("pyramid_lead", "")

    # Look for quantified findings in the report
    has_numbers = bool(re.search(r'\d+\.?\d*\s*(%|percent|tracts?|counties|people|residents)', report_text, re.IGNORECASE))
    has_specific_place = bool(re.search(r'\b(tract|county|zip|neighborhood|ward)\b', report_text, re.IGNORECASE))
    has_comparison = bool(re.search(r'(compared to|vs\.?|higher than|lower than|above|below) (the |state |national )?average', report_text, re.IGNORECASE))
    has_statistical_support = bool(re.search(r"(significant|p[- ]=|moran|hotspot|cluster|regression|r-squared|coefficient)", report_text, re.IGNORECASE))

    issues = []
    if not has_numbers:
        issues.append("Report lacks quantified findings (specific numbers, percentages, or counts).")
    if not has_specific_place:
        issues.append("Report does not name specific places — findings are too generic.")
    if not has_comparison:
        issues.append("No comparison to baseline (state/national average) — hard to assess magnitude.")
    if not has_statistical_support:
        issues.append("No reference to statistical evidence (Moran's I, hotspot significance, regression).")

    if issues:
        return {
            "severity": "MODERATE" if len(issues) >= 3 else "LOW",
            "dimension": "hero_finding_evidence",
            "finding": "Hero finding may not be fully supported by quantified evidence. Issues: " + "; ".join(issues),
            "hero_question": hero_q,
            "suggested_fix": "Ensure the executive brief leads with a specific number (e.g., '12 tracts'), "
                             "a named geography, a comparison to baseline, and a reference to the "
                             "statistical method that supports the claim.",
        }
    return {
        "severity": "PASS",
        "dimension": "hero_finding_evidence",
        "finding": "Report contains quantified findings, specific geographies, comparisons, and statistical support.",
        "suggested_fix": "None required.",
    }


def critique_caveats(report_text: str, validation: dict | None) -> dict:
    """Check whether caveats are adequately disclosed."""
    caveat_signals = [
        (r'\bvintage\b|\bdata\s+age\b|\bold\s+data\b', "data vintage"),
        (r'\bmargin\s+of\s+error\b|\bmoe\b', "MOE disclosure"),
        (r'\bproxy\b|\bsurrogate\b|\bapproximat\b', "proxy variable caveat"),
        (r'\bcausal\b|\bcorrelation\b|\bnot\s+causal\b|\bassociation\b', "causation vs correlation"),
        (r'\binstitutional\b|\buniversity\b|\bprison\b|\bgroup\s+quarter\b', "institutional tract flagging"),
    ]

    missing = []
    for pattern, label in caveat_signals:
        if not re.search(pattern, report_text, re.IGNORECASE):
            missing.append(label)

    # Check if validation JSON has warnings that weren't reflected
    qa_warnings = []
    if validation:
        qa_warnings = validation.get("warnings", []) + validation.get("non_blocking", [])

    if missing or qa_warnings:
        issues = missing + ([f"QA warning not disclosed: {w}" for w in qa_warnings[:3]] if qa_warnings else [])
        return {
            "severity": "MODERATE" if len(issues) >= 3 else "LOW",
            "dimension": "caveat_strength",
            "finding": "Caveats may be insufficient. Missing disclosures: " + "; ".join(issues) + ".",
            "suggested_fix": "Add a Limitations section that explicitly addresses: "
                             + ", ".join(missing or ["review QA warnings"])
                             + ". Each caveat should explain the directional risk to the finding.",
        }

    return {
        "severity": "PASS",
        "dimension": "caveat_strength",
        "finding": "Report covers key caveat categories: data vintage, MOE, proxy variables, "
                   "causation framing, and institutional tracts.",
        "suggested_fix": "None required.",
    }


def critique_alternative_explanations(report_text: str, question_type: str) -> dict:
    """Flag if the report ignores plausible alternative explanations."""
    alt_signals = {
        "healthcare_access_gap": [
            (r'\bimmigrant\b|\bundocumented\b|\blanguage\b|\bcultural\b', "cultural/language access barriers"),
            (r'\binsurance\b|\bmedic(aid|are)\b', "insurance coverage as a confounder"),
            (r'\bprovider\s+shortage\b|\bworkforce\b', "provider supply constraints"),
        ],
        "food_access_gap": [
            (r'\bcar\b|\bvehicle\b|\btransit\b|\bwalk\b', "transportation access"),
            (r'\baffordabilit\b|\bprice\b|\bcost\b', "affordability vs physical distance"),
            (r'\bcultural\b|\bprefer\b|\bshopping\b', "cultural food preferences / informal markets"),
        ],
        "poverty_socioeconomic": [
            (r'\bhistorical\b|\bsegregat\b|\bredlin\b', "historical segregation / redlining context"),
            (r'\btax\b|\binvestment\b|\bdisinvest\b', "public disinvestment as driver"),
            (r'\bwages?\b|\bemployer\b|\bindustry\b', "local labor market conditions"),
        ],
        "environmental_justice": [
            (r'\bhistorical\b|\bindust(ry|rial)\b|\bzoning\b', "historical zoning / industrial legacy"),
            (r'\bproperty\s+value\b|\bhome\b|\brent\b', "housing market sorting"),
        ],
    }

    signals = alt_signals.get(question_type, [])
    missing_alts = []
    for pattern, label in signals:
        if not re.search(pattern, report_text, re.IGNORECASE):
            missing_alts.append(label)

    if missing_alts:
        return {
            "severity": "LOW",
            "dimension": "alternative_explanations",
            "finding": f"Report may not address these plausible alternative explanations for the {question_type.replace('_', ' ')} pattern: "
                       + "; ".join(missing_alts) + ".",
            "suggested_fix": "Add a brief 'Alternative Explanations' or 'Interpretation Limits' paragraph "
                             "acknowledging these factors. This pre-empts a hostile reviewer's objections.",
        }

    return {
        "severity": "PASS",
        "dimension": "alternative_explanations",
        "finding": "Report addresses plausible alternative explanations for the detected pattern.",
        "suggested_fix": "None required.",
    }


def detect_fatal_flaws(
    output_files: dict[str, list[Path]],
    validation: dict | None,
    brief: dict | None,
) -> dict:
    """Run the hostile-reviewer check: would a fatal flaw block publication?"""
    blockers = []

    # No QGIS package
    qgis_files = output_files.get("qgis", [])
    if not qgis_files:
        blockers.append("No QGIS package found — required for every deliverable (per SOUL.md).")

    # QA validation failed
    if validation:
        blocked = validation.get("blocked", False)
        blocking_failures = validation.get("blocking_failures", [])
        if blocked or blocking_failures:
            blockers.append(
                f"Validation QA reported blocking failures: {'; '.join(str(f) for f in blocking_failures[:3])}"
            )
        join_rate = validation.get("join_rate", None)
        if join_rate is not None and join_rate < 0.85:
            blockers.append(f"Join match rate {join_rate:.1%} is below the 85% threshold.")

    # Brief missing hero question
    if brief:
        hero_q = brief.get("engagement", {}).get("hero_question", "")
        if not hero_q or hero_q.startswith("TBD"):
            blockers.append("Hero question in project brief is blank or placeholder — report has no defined thesis.")

    # No maps at all
    if not output_files.get("maps"):
        blockers.append("No map outputs found — deliverable is incomplete.")

    # No report
    if not output_files.get("reports"):
        blockers.append("No written report found in outputs/reports/.")

    if blockers:
        return {
            "severity": "BLOCKING",
            "dimension": "fatal_flaw_check",
            "finding": f"{len(blockers)} potential fatal flaw(s) found: " + " | ".join(blockers),
            "suggested_fix": "Resolve all blocking issues before delivery. "
                             "Do not send to client until these are cleared.",
        }

    return {
        "severity": "PASS",
        "dimension": "fatal_flaw_check",
        "finding": "No blocking fatal flaws detected. QGIS package present, validation passed, "
                   "hero question defined, maps and report present.",
        "suggested_fix": "None required.",
    }


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

SEVERITY_WEIGHT = {"BLOCKING": 10, "MODERATE": 3, "LOW": 1, "INFO": 0, "PASS": 0}

# ---------------------------------------------------------------------------
# Finding → Agent routing table
# ---------------------------------------------------------------------------

FINDING_TO_AGENT: dict[str, str | dict[str, str]] = {
    "map_choices":              "cartography",
    "hero_finding_evidence":    "report-writer",
    "caveat_strength":          "report-writer",
    "alternative_explanations": "report-writer",
    "fatal_flaw_check": {
        "no qgis":              "cartography",
        "validation":           "validation-qa",
        "join_rate":            "data-processing",
        "no maps":              "cartography",
        "no report":            "report-writer",
    },
}

# Priority: lower number = fix first.  Agents that affect correctness before visual/narrative.
AGENT_PRIORITY: dict[str, int] = {
    "validation-qa":    1,
    "data-processing":  2,
    "cartography":      3,
    "report-writer":    4,
}

# Keywords used to sub-route fatal_flaw_check findings to the right agent.
_FATAL_FLAW_KEYWORDS: list[tuple[str, str]] = [
    ("qgis",        "no qgis"),
    ("validation",  "validation"),
    ("blocking",    "validation"),
    ("join",        "join_rate"),
    ("match rate",  "join_rate"),
    ("no map",      "no maps"),
    ("no report",   "no report"),
]


def _resolve_agent_for_finding(finding: dict) -> str | None:
    """Return the target agent name for a single finding, or None if PASS/INFO."""
    severity = finding.get("severity", "INFO")
    if severity in ("PASS", "INFO"):
        return None

    dimension = finding.get("dimension", "")
    mapping = FINDING_TO_AGENT.get(dimension)
    if mapping is None:
        return None

    if isinstance(mapping, str):
        return mapping

    # fatal_flaw_check — inspect the finding text for keyword matches
    text = finding.get("finding", "").lower()
    for keyword, key in _FATAL_FLAW_KEYWORDS:
        if keyword in text:
            return mapping.get(key)

    # Fallback for fatal_flaw_check: most conservative choice
    return "validation-qa"


def _build_instruction(findings_for_agent: list[dict]) -> str:
    """Combine finding + suggested_fix into an actionable instruction string."""
    parts: list[str] = []
    for i, f in enumerate(findings_for_agent, 1):
        desc = f.get("finding", "")
        fix = f.get("suggested_fix", "")
        if fix and fix != "None required.":
            parts.append(f"({i}) {desc} — Fix: {fix}")
        else:
            parts.append(f"({i}) {desc}")
    return " ".join(parts)


def build_routing_action(
    verdict: str,
    findings: list[dict],
    revision_number: int = 1,
    max_revisions: int = 2,
) -> dict | None:
    """Build the routing_action structure for REVISE or REJECT verdicts.

    Returns None for PASS.
    """
    if verdict == "PASS":
        return None

    # Group non-PASS/INFO findings by target agent
    agent_findings: dict[str, list[dict]] = {}
    for f in findings:
        agent = _resolve_agent_for_finding(f)
        if agent is not None:
            agent_findings.setdefault(agent, []).append(f)

    # Build re_route list sorted by priority
    re_route: list[dict] = []
    for agent in sorted(agent_findings, key=lambda a: AGENT_PRIORITY.get(a, 99)):
        afindings = agent_findings[agent]
        entry: dict[str, Any] = {
            "agent": agent,
            "priority": AGENT_PRIORITY.get(agent, 99),
            "findings": list({f.get("dimension", "") for f in afindings}),
            "instruction": _build_instruction(afindings),
        }
        re_route.append(entry)

    routing: dict[str, Any] = {
        "verdict": verdict,
        "revision_number": revision_number,
        "re_route": re_route,
        "max_revisions": max_revisions,
        "escalate_to_human_if": "revision_number > max_revisions",
    }

    if verdict == "REJECT":
        routing["requires_human_review"] = True

    return routing


def compute_verdict(findings: list[dict]) -> str:
    total_weight = sum(SEVERITY_WEIGHT.get(f.get("severity", "INFO"), 0) for f in findings)
    if any(f.get("severity") == "BLOCKING" for f in findings):
        return "REJECT"
    if total_weight >= 6:
        return "REVISE"
    return "PASS"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run peer review on a completed GIS analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--project-id", required=True, help="Project ID (must match analyses/ directory name)")
    parser.add_argument("--verbose", action="store_true", help="Print full report text during review")
    parser.add_argument("--dry-run", action="store_true", help="Print critique but do not write JSON")
    args = parser.parse_args()

    project_id = args.project_id
    project_dir = ANALYSES_DIR / project_id

    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        print(f"  Available projects: {[d.name for d in ANALYSES_DIR.iterdir() if d.is_dir()]}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("The Skeptic — Peer Review Agent")
    print("=" * 60)
    print(f"\nReviewing: {project_id}")
    print(f"Directory: {project_dir}\n")

    # ── Collect outputs (outputs/ only — never scripts/ or data/) ──────────
    output_files = collect_output_files(project_dir)
    map_count = len(output_files.get("maps", []))
    report_count = len(output_files.get("reports", []))
    qa_count = len(output_files.get("qa", []))

    print(f"Found: {map_count} map file(s), {report_count} report file(s), {qa_count} QA file(s)")

    # ── Read artifacts ──────────────────────────────────────────────────────
    report_text = read_report_excerpt(project_dir)
    validation = read_validation_json(project_dir)
    brief = read_project_brief(project_dir)
    benchmark_score = read_benchmark_score(project_dir)

    question_type = "unknown"
    if brief:
        question_type = brief.get("_question_type_detected", "unknown")
        if question_type == "unknown":
            # Infer from hero question
            hero_q = brief.get("engagement", {}).get("hero_question", "").lower()
            if "health" in hero_q or "hospital" in hero_q:
                question_type = "healthcare_access_gap"
            elif "food" in hero_q or "grocery" in hero_q:
                question_type = "food_access_gap"
            elif "poverty" in hero_q or "income" in hero_q:
                question_type = "poverty_socioeconomic"
            elif "environment" in hero_q or "pollution" in hero_q:
                question_type = "environmental_justice"

    if args.verbose:
        print("\n── REPORT EXCERPT ──────────────────────────────────────")
        print(report_text[:1500])
        print("────────────────────────────────────────────────────────\n")

    # ── Run the five critique dimensions ───────────────────────────────────
    print("Running critique dimensions...")

    findings: list[dict] = []

    # 1. Hero finding evidence
    hero_critique = critique_hero_finding(report_text, brief)
    findings.append(hero_critique)

    # 2. Map choices
    map_critiques = critique_map_choices(output_files, brief)
    findings.extend(map_critiques)

    # 3. Alternative explanations
    alt_critique = critique_alternative_explanations(report_text, question_type)
    findings.append(alt_critique)

    # 4. Caveat strength
    caveat_critique = critique_caveats(report_text, validation)
    findings.append(caveat_critique)

    # 5. Fatal flaw check
    fatal_critique = detect_fatal_flaws(output_files, validation, brief)
    findings.append(fatal_critique)

    # ── Compute verdict ────────────────────────────────────────────────────
    verdict = compute_verdict(findings)

    # ── Build routing action for REVISE / REJECT ──────────────────────────
    routing_action = build_routing_action(verdict, findings)

    # ── Build output JSON ──────────────────────────────────────────────────
    critique_json: dict[str, Any] = {
        "review_schema": "peer-review-v1",
        "project_id": project_id,
        "reviewed_at": datetime.now(UTC).isoformat(),
        "reviewed_by": "peer-reviewer (The Skeptic)",
        "reviewer_workspace": str(Path(__file__).resolve().parents[2] / "agents" / "peer-reviewer"),
        "scope": "outputs only — maps, reports, QA. Scripts, raw data, and handoff logs not read.",
        "benchmark_score": benchmark_score,
        "verdict": verdict,
        "verdict_rationale": {
            "PASS": "No blocking issues. Minor findings only. Safe to deliver.",
            "REVISE": "Moderate issues found. Revisions required before delivery.",
            "REJECT": "Blocking flaw(s) found. Do not deliver. Fix and resubmit.",
        }.get(verdict, ""),
        "artifacts_reviewed": {
            "maps": [str(f.name) for f in output_files.get("maps", [])],
            "reports": [str(f.name) for f in output_files.get("reports", [])],
            "qa": [str(f.name) for f in output_files.get("qa", [])],
        },
        "routing_action": routing_action,
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
            "blocking": sum(1 for f in findings if f.get("severity") == "BLOCKING"),
            "moderate": sum(1 for f in findings if f.get("severity") == "MODERATE"),
            "low": sum(1 for f in findings if f.get("severity") == "LOW"),
            "pass": sum(1 for f in findings if f.get("severity") == "PASS"),
        },
        "_critique_dimensions": [
            "1. Does the hero finding follow from the evidence?",
            "2. Are map choices appropriate for the data type?",
            "3. Are there alternative explanations the report ignores?",
            "4. Are the caveats strong enough?",
            "5. Would a hostile reviewer find a fatal flaw?",
        ],
    }

    # ── Print critique summary ─────────────────────────────────────────────
    print()
    print("─" * 60)
    verdict_emoji = {"PASS": "✅", "REVISE": "⚠️ ", "REJECT": "❌"}.get(verdict, "?")
    print(f"VERDICT: {verdict_emoji} {verdict}")
    if benchmark_score:
        print(f"BENCHMARK SCORE: {benchmark_score}")
    print()
    print("FINDINGS:")
    for i, f in enumerate(findings, 1):
        sev = f.get("severity", "INFO")
        dim = f.get("dimension", "").replace("_", " ").upper()
        finding_text = f.get("finding", "")[:120]
        print(f"  [{i}] [{sev:8s}] {dim}")
        print(f"       {finding_text}")
        if f.get("suggested_fix") and f.get("suggested_fix") != "None required.":
            fix = f.get("suggested_fix", "")[:100]
            print(f"       FIX: {fix}")
        print()

    summary = critique_json["summary"]
    print(f"Summary: {summary['blocking']} blocking · {summary['moderate']} moderate · "
          f"{summary['low']} low · {summary['pass']} pass")

    # ── Write output ───────────────────────────────────────────────────────
    if not args.dry_run:
        qa_dir = project_dir / "outputs" / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        out_path = qa_dir / f"{project_id}_peer_review.json"
        out_path.write_text(json.dumps(critique_json, indent=2))
        print(f"\nOUTPUT → {out_path}")
    else:
        print("\n[dry-run] No file written.")

    return 0 if verdict in ("PASS", "REVISE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
