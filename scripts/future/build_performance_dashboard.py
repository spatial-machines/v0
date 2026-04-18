#!/usr/bin/env python3
"""Build an HTML performance dashboard tracking QA benchmark scores and pipeline health.

Reads all outputs/qa/*_validation.json files across analyses, reads the
lessons-learned.jsonl log, and produces a self-contained HTML dashboard
with Chart.js charts, a QA summary table, and failure analysis.

Usage:
    python build_performance_dashboard.py
    python build_performance_dashboard.py --output site/build/performance/index.html
    python build_performance_dashboard.py --registry-path analyses/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"
REGISTRY_FILE = PROJECT_ROOT / "registry.json"
LESSONS_LOG = PROJECT_ROOT / "docs" / "memory" / "lessons-learned.jsonl"

DEFAULT_OUTPUT = PROJECT_ROOT / "site" / "build" / "performance" / "index.html"

# QA dimensions we track across validation files
QA_DIMENSIONS = [
    "geometry",
    "join_coverage",
    "null_rate",
    "crs",
    "spatial_autocorr",
    "feature_count",
    "quantile_spread",
    "output_existence",
    "schema",
    "value_range",
]


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {}
    try:
        return json.loads(REGISTRY_FILE.read_text())
    except Exception:
        return {}


def enumerate_analyses() -> list[Path]:
    registry = load_registry()
    dirs = []
    analyses = registry.get("analyses", [])
    if isinstance(analyses, list):
        for entry in analyses:
            project_id = entry.get("project_id") or entry.get("id") or entry.get("name") if isinstance(entry, dict) else str(entry)
            if project_id:
                candidate = ANALYSES_DIR / project_id
                if candidate.is_dir():
                    dirs.append(candidate)
    elif isinstance(analyses, dict):
        for project_id in analyses:
            candidate = ANALYSES_DIR / project_id
            if candidate.is_dir():
                dirs.append(candidate)

    if not dirs and ANALYSES_DIR.exists():
        dirs = [d for d in ANALYSES_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]

    return sorted(dirs)


def collect_qa_results(analyses: list[Path]) -> list[dict]:
    """Collect all QA validation JSON files from all analyses."""
    records = []

    for adir in analyses:
        qa_dir = adir / "outputs" / "qa"
        if not qa_dir.exists():
            # Also check runs/ directory at project root
            qa_dir = PROJECT_ROOT / "runs"

        # Scan both locations
        search_dirs = [adir / "outputs" / "qa", PROJECT_ROOT / "runs"]
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for vf in sdir.glob("*validation*.json"):
                try:
                    data = json.loads(vf.read_text())
                    records.append({
                        "analysis": adir.name,
                        "file": str(vf.relative_to(PROJECT_ROOT)),
                        "run_id": data.get("run_id", vf.stem),
                        "overall_status": data.get("overall_status", "UNKNOWN"),
                        "checks": data.get("checks", []),
                        "warnings": data.get("warnings", []),
                        "created_at": data.get("created_at", ""),
                        "recommendation": data.get("recommendation", ""),
                        "_raw": data,
                    })
                except Exception:
                    pass

    return records


def extract_dimension_results(record: dict) -> dict[str, str]:
    """Extract pass/fail/warn per QA dimension from a validation record."""
    results: dict[str, str] = {}
    checks = record.get("checks", [])

    for check in checks:
        name = check.get("check", check.get("name", "")).lower()
        status = check.get("status", check.get("result", "UNKNOWN")).upper()

        # Map check names to dimensions
        for dim in QA_DIMENSIONS:
            if dim in name or name in dim:
                # Take worst status if multiple checks map to same dimension
                existing = results.get(dim, "PASS")
                if status == "FAIL" or existing == "FAIL":
                    results[dim] = "FAIL"
                elif status == "WARN" or existing == "WARN":
                    results[dim] = "WARN"
                else:
                    results[dim] = status
                break

    return results


def collect_lessons(limit: int = 200) -> list[dict]:
    """Load lessons-learned.jsonl entries."""
    if not LESSONS_LOG.exists():
        return []
    lessons = []
    try:
        for line in LESSONS_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                lessons.append(json.loads(line))
            except Exception:
                pass
    except Exception:
        pass
    return lessons[-limit:]  # most recent entries


def top_failure_reasons(lessons: list[dict], n: int = 5) -> list[dict]:
    """Extract top N failure reasons from lessons log."""
    reasons: Counter = Counter()
    for entry in lessons:
        # Support multiple possible field names
        reason = (
            entry.get("issue")
            or entry.get("problem")
            or entry.get("lesson")
            or entry.get("message")
            or entry.get("summary")
            or ""
        )
        category = entry.get("category", entry.get("type", "general"))
        if reason:
            reasons[(category, reason[:120])] += 1

    top = []
    for (cat, reason), count in reasons.most_common(n):
        top.append({"category": cat, "reason": reason, "count": count})
    return top


def collect_script_coverage(analyses: list[Path]) -> dict[str, list[str]]:
    """Detect which scripts have been used based on handoff/log file references."""
    coverage: dict[str, set] = {}  # script_name -> set of analyses that used it

    all_scripts = sorted([
        p.stem for p in (PROJECT_ROOT / "scripts").glob("*.py")
        if not p.stem.startswith("_")
    ])

    # Initialize
    for s in all_scripts:
        coverage[s] = set()

    # Scan all JSON files in analyses and runs
    scan_dirs = list(analyses) + [PROJECT_ROOT / "runs"]
    for sdir in scan_dirs:
        if not sdir.exists():
            continue
        analysis_name = sdir.name if sdir != PROJECT_ROOT / "runs" else "_runs"
        for jf in sdir.rglob("*.json"):
            try:
                text = jf.read_text()
                for script in all_scripts:
                    if script in text:
                        coverage[script].add(analysis_name)
            except Exception:
                pass

    return {k: sorted(v) for k, v in coverage.items()}


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    "PASS": "#22c55e",
    "WARN": "#f59e0b",
    "FAIL": "#ef4444",
    "UNKNOWN": "#9ca3af",
}

STATUS_BG = {
    "PASS": "#f0fdf4",
    "WARN": "#fffbeb",
    "FAIL": "#fef2f2",
    "UNKNOWN": "#f9fafb",
}


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#9ca3af")
    bg = STATUS_BG.get(status, "#f9fafb")
    return (
        f'<span style="background:{bg};color:{color};padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em;font-weight:600;border:1px solid {color}">'
        f"{status}</span>"
    )


def build_qa_table_html(qa_records: list[dict]) -> str:
    if not qa_records:
        return "<p style='color:#6b7280'>No QA validation files found across analyses.</p>"

    rows = []
    for rec in qa_records:
        dim_results = extract_dimension_results(rec)
        overall = rec["overall_status"]
        row_bg = STATUS_BG.get(overall, "#f9fafb")
        cells = [
            f'<td style="padding:8px 12px;white-space:nowrap"><strong>{rec["analysis"]}</strong></td>',
            f'<td style="padding:8px 12px;white-space:nowrap;font-size:0.8em;color:#6b7280">{rec.get("run_id","")[:32]}</td>',
            f'<td style="padding:8px 12px;text-align:center">{status_badge(overall)}</td>',
        ]
        for dim in QA_DIMENSIONS:
            st = dim_results.get(dim, "—")
            if st == "—":
                cells.append('<td style="padding:8px 12px;text-align:center;color:#d1d5db">—</td>')
            else:
                cells.append(f'<td style="padding:8px 12px;text-align:center">{status_badge(st)}</td>')

        rows.append(
            f'<tr style="background:{row_bg};border-bottom:1px solid #e5e7eb">'
            + "".join(cells)
            + "</tr>"
        )

    dim_headers = "".join(
        f'<th style="padding:8px 12px;text-align:center;font-size:0.75em;'
        f'text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">'
        f'{dim.replace("_", " ")}</th>'
        for dim in QA_DIMENSIONS
    )

    return f"""
<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
  <thead>
    <tr style="background:#f3f4f6;border-bottom:2px solid #e5e7eb">
      <th style="padding:8px 12px;text-align:left">Analysis</th>
      <th style="padding:8px 12px;text-align:left">Run ID</th>
      <th style="padding:8px 12px;text-align:center">Overall</th>
      {dim_headers}
    </tr>
  </thead>
  <tbody>
    {"".join(rows)}
  </tbody>
</table>
</div>
"""


def build_failures_html(top_failures: list[dict]) -> str:
    if not top_failures:
        return "<p style='color:#6b7280'>No lessons-learned entries found.</p>"

    items = []
    for i, f in enumerate(top_failures, 1):
        items.append(f"""
<div style="display:flex;align-items:flex-start;gap:12px;padding:12px;
  background:#fff;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px">
  <div style="background:#3b82f6;color:#fff;border-radius:50%;width:28px;height:28px;
    display:flex;align-items:center;justify-content:center;font-weight:700;
    flex-shrink:0;font-size:0.85em">{i}</div>
  <div style="flex:1">
    <div style="font-weight:600;color:#111827">{f['reason']}</div>
    <div style="font-size:0.8em;color:#6b7280;margin-top:2px">
      Category: <code>{f['category']}</code> &nbsp;·&nbsp; Seen {f['count']}×
    </div>
  </div>
</div>""")
    return "".join(items)


def build_coverage_html(coverage: dict[str, list[str]]) -> str:
    exercised = [(s, a) for s, a in coverage.items() if a]
    unexercised = [s for s, a in coverage.items() if not a]

    ex_html = ""
    if exercised:
        rows = []
        for script, analyses in sorted(exercised):
            rows.append(
                f'<tr style="border-bottom:1px solid #f3f4f6">'
                f'<td style="padding:6px 12px;font-family:monospace;font-size:0.85em">{script}</td>'
                f'<td style="padding:6px 12px;font-size:0.8em;color:#6b7280">{", ".join(analyses[:5])}'
                f'{"..." if len(analyses) > 5 else ""}</td>'
                f'</tr>'
            )
        ex_html = f"""
<h4 style="color:#374151;margin:16px 0 8px">Exercised ({len(exercised)} scripts)</h4>
<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:0.9em">
<thead><tr style="background:#f3f4f6">
  <th style="padding:6px 12px;text-align:left">Script</th>
  <th style="padding:6px 12px;text-align:left">Used in</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table></div>"""

    unex_html = ""
    if unexercised:
        tags = "".join(
            f'<code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;'
            f'font-size:0.8em;margin:2px;display:inline-block">{s}</code>'
            for s in unexercised
        )
        unex_html = f'<h4 style="color:#374151;margin:16px 0 8px">Not yet exercised ({len(unexercised)} scripts)</h4><div style="line-height:2">{tags}</div>'

    return ex_html + unex_html


def build_summary_stats_html(qa_records: list[dict]) -> tuple[str, dict]:
    """Build summary stats cards and return chart data."""
    total = len(qa_records)
    pass_count = sum(1 for r in qa_records if r["overall_status"] == "PASS")
    warn_count = sum(1 for r in qa_records if r["overall_status"] == "WARN")
    fail_count = sum(1 for r in qa_records if r["overall_status"] == "FAIL")

    # Dimension-level counts
    dim_stats: dict[str, Counter] = {d: Counter() for d in QA_DIMENSIONS}
    for rec in qa_records:
        dims = extract_dimension_results(rec)
        for d, st in dims.items():
            dim_stats[d][st] += 1

    chart_data = {
        "overall": {
            "labels": ["PASS", "WARN", "FAIL"],
            "data": [pass_count, warn_count, fail_count],
            "colors": [STATUS_COLORS["PASS"], STATUS_COLORS["WARN"], STATUS_COLORS["FAIL"]],
        },
        "by_dimension": {
            "labels": [d.replace("_", " ") for d in QA_DIMENSIONS],
            "pass": [dim_stats[d]["PASS"] for d in QA_DIMENSIONS],
            "warn": [dim_stats[d]["WARN"] for d in QA_DIMENSIONS],
            "fail": [dim_stats[d]["FAIL"] for d in QA_DIMENSIONS],
        },
    }

    def card(label: str, value: int, color: str) -> str:
        return (
            f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;'
            f'padding:20px;text-align:center;border-top:4px solid {color}">'
            f'<div style="font-size:2em;font-weight:700;color:{color}">{value}</div>'
            f'<div style="color:#6b7280;font-size:0.85em;margin-top:4px">{label}</div>'
            f'</div>'
        )

    html = (
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px">'
        + card("Total Analyses", total, "#3b82f6")
        + card("Pass", pass_count, STATUS_COLORS["PASS"])
        + card("Warn", warn_count, STATUS_COLORS["WARN"])
        + card("Fail", fail_count, STATUS_COLORS["FAIL"])
        + "</div>"
    )
    return html, chart_data


def render_html(
    qa_records: list[dict],
    top_failures: list[dict],
    coverage: dict[str, list[str]],
    generated_at: str,
) -> str:
    stats_html, chart_data = build_summary_stats_html(qa_records)
    qa_table = build_qa_table_html(qa_records)
    failures_html = build_failures_html(top_failures)
    coverage_html = build_coverage_html(coverage)

    chart_data_json = json.dumps(chart_data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GIS Agent — Performance Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f9fafb; color: #111827; line-height: 1.5; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
  h1 {{ font-size: 1.75em; font-weight: 700; color: #111827; }}
  h2 {{ font-size: 1.2em; font-weight: 600; color: #374151; margin: 0 0 16px; }}
  .section {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
    padding: 24px; margin-bottom: 24px; }}
  .header {{ display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }}
  .timestamp {{ font-size: 0.8em; color: #9ca3af; }}
  .charts-row {{ display: grid; grid-template-columns: 1fr 2fr; gap: 24px; margin-bottom: 24px; }}
  @media (max-width: 900px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
  .chart-wrap {{ position: relative; height: 300px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>📊 GIS Agent — Performance Dashboard</h1>
      <div class="timestamp">Generated: {generated_at}</div>
    </div>
  </div>

  <div class="section">
    <h2>Summary</h2>
    {stats_html}
  </div>

  <div class="charts-row">
    <div class="section">
      <h2>Overall QA Results</h2>
      <div class="chart-wrap">
        <canvas id="overallChart"></canvas>
      </div>
    </div>
    <div class="section">
      <h2>Results by QA Dimension</h2>
      <div class="chart-wrap">
        <canvas id="dimChart"></canvas>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>QA Results — All Analyses</h2>
    {qa_table}
  </div>

  <div class="section">
    <h2>Top 5 Most Common Failure Reasons</h2>
    <p style="font-size:0.85em;color:#6b7280;margin-bottom:16px">
      From <code>logs/lessons-learned.jsonl</code>
    </p>
    {failures_html}
  </div>

  <div class="section">
    <h2>Script Coverage</h2>
    <p style="font-size:0.85em;color:#6b7280;margin-bottom:16px">
      Scripts detected in analysis logs and handoff artifacts.
    </p>
    {coverage_html}
  </div>
</div>

<script>
const DATA = {chart_data_json};

// Overall donut
new Chart(document.getElementById('overallChart'), {{
  type: 'doughnut',
  data: {{
    labels: DATA.overall.labels,
    datasets: [{{
      data: DATA.overall.data,
      backgroundColor: DATA.overall.colors,
      borderWidth: 2,
      borderColor: '#fff',
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'bottom' }},
      tooltip: {{ callbacks: {{
        label: ctx => ` ${{ctx.label}}: ${{ctx.parsed}}`
      }}}}
    }}
  }}
}});

// Dimension stacked bar
new Chart(document.getElementById('dimChart'), {{
  type: 'bar',
  data: {{
    labels: DATA.by_dimension.labels,
    datasets: [
      {{ label: 'PASS', data: DATA.by_dimension.pass, backgroundColor: '{STATUS_COLORS["PASS"]}' }},
      {{ label: 'WARN', data: DATA.by_dimension.warn, backgroundColor: '{STATUS_COLORS["WARN"]}' }},
      {{ label: 'FAIL', data: DATA.by_dimension.fail, backgroundColor: '{STATUS_COLORS["FAIL"]}' }},
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    scales: {{
      x: {{ stacked: true, ticks: {{ font: {{ size: 11 }} }} }},
      y: {{ stacked: true, beginAtZero: true, ticks: {{ stepSize: 1 }} }}
    }},
    plugins: {{ legend: {{ position: 'bottom' }} }}
  }}
}});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an HTML performance dashboard for GIS agent QA results."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output HTML path (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--data-output",
        default=None,
        help="Optional JSON data file output path (default: <output>.json)"
    )
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    data_out = Path(args.data_output).expanduser().resolve() if args.data_output else out_path.with_suffix(".json")

    print("=== Performance Dashboard Builder ===")

    # Collect data
    analyses = enumerate_analyses()
    print(f"  Analyses found: {len(analyses)}")

    print("  Collecting QA results...")
    qa_records = collect_qa_results(analyses)
    print(f"  QA records: {len(qa_records)}")

    print("  Loading lessons log...")
    lessons = collect_lessons()
    top_failures = top_failure_reasons(lessons)
    print(f"  Lessons loaded: {len(lessons)} | Top failures extracted: {len(top_failures)}")

    print("  Analyzing script coverage...")
    coverage = collect_script_coverage(analyses)
    exercised = sum(1 for v in coverage.values() if v)
    print(f"  Scripts tracked: {len(coverage)} | Exercised: {exercised}")

    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Render
    html = render_html(qa_records, top_failures, coverage, generated_at)

    # Data JSON for downstream consumption
    data_payload = {
        "generated_at": generated_at,
        "analyses_count": len(analyses),
        "qa_records_count": len(qa_records),
        "qa_records": [
            {
                "analysis": r["analysis"],
                "run_id": r["run_id"],
                "overall_status": r["overall_status"],
                "created_at": r["created_at"],
                "dimensions": extract_dimension_results(r),
            }
            for r in qa_records
        ],
        "top_failures": top_failures,
        "script_coverage": {
            "total": len(coverage),
            "exercised": exercised,
            "unexercised_count": len(coverage) - exercised,
            "scripts": coverage,
        },
    }

    # Write outputs
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    data_out.parent.mkdir(parents=True, exist_ok=True)
    data_out.write_text(json.dumps(data_payload, indent=2), encoding="utf-8")

    print(f"\n  HTML: {out_path}")
    print(f"  JSON: {data_out}")
    print("  Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
