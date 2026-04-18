"""Generate a modern, self-contained HTML report from a report asset manifest.

Reads the consolidated asset manifest produced by collect_report_assets.py
plus the project brief and summary stats, then writes a single-file HTML
page:

  - Executive summary from the project brief's pyramid lead
  - KPI hero cards auto-derived from summary_stats and domain tables
  - Base64-embedded maps with captions pulled from their .style.json sidecars
  - Paired charts laid out in a 2-column grid
  - Embedded interactive web-map iframe + open-in-tab button
  - Methods, QA, Caveats (auto-injected standard disclosures), Sources

The output is a single HTML file the client can email or commit. No
external assets; no JavaScript frameworks.
"""
from __future__ import annotations

import base64
import csv
import json
import sys
from datetime import datetime, UTC
from html import escape
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ═════════════════════════════════════════════════════════════════════════
# IO helpers
# ═════════════════════════════════════════════════════════════════════════

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve(path: str | Path, analysis_dir: Path | None) -> Path | None:
    """Resolve a manifest-relative path to an absolute file on disk.

    Manifests record paths a few different ways — absolute, relative to
    the project root, relative to the analyses/ sibling, relative to the
    analysis itself. Try each. Windows paths use backslashes, POSIX uses
    forward — normalize.
    """
    raw = str(path).replace("\\", "/")
    p = Path(raw)
    if p.is_absolute() and p.exists():
        return p

    bases: list[Path] = []
    if analysis_dir is not None:
        bases.append(analysis_dir)           # analysis-relative
        bases.append(analysis_dir.parent)    # analyses/-relative (common)
    bases.append(PROJECT_ROOT)               # repo-root-relative
    bases.append(PROJECT_ROOT / "analyses")  # legacy

    for base in bases:
        candidate = (base / p).resolve()
        if candidate.exists():
            return candidate
    return None


def _b64_png(path: Path) -> str | None:
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except (OSError, ValueError):
        return None


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "&mdash;"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _status_class(status: str) -> str:
    s = (status or "").upper()
    if s == "PASS":
        return "status-pass"
    if s in ("WARN", "PASS WITH WARNINGS"):
        return "status-warn"
    if s in ("FAIL", "REWORK NEEDED"):
        return "status-fail"
    return ""


# ═════════════════════════════════════════════════════════════════════════
# Stats / KPI derivation
# ═════════════════════════════════════════════════════════════════════════

def _read_csv(path: Path) -> list[dict]:
    try:
        with path.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except (OSError, csv.Error):
        return []


def _derive_kpis(
    manifest: dict,
    project_brief: dict,
    analysis_dir: Path | None,
) -> list[dict]:
    """Auto-derive 4 KPI hero cards from available stats.

    Tries, in order:
      1. Food-access KPIs (tracts / food_desert_count / food_desert_pop / gap)
         when food_desert_demographics.csv is present
      2. Generic descriptive KPIs from summary_stats.csv (field count, mean,
         median, spread of the first numeric field)
      3. Fallback counts from the manifest (maps / charts / tables / sources)

    Returns up to 4 ``{"value": str, "label": str}`` dicts.
    """
    if analysis_dir is None:
        return _fallback_kpis(manifest)

    stats_dir = analysis_dir / "outputs" / "spatial_stats"
    fd_csv = stats_dir / "food_desert_demographics.csv"
    summary_csv = stats_dir / "summary_stats.csv"

    # ── 1. Food-access domain KPIs ──
    if fd_csv.exists():
        rows = _read_csv(fd_csv)
        fd_row = next(
            (r for r in rows if "food desert" in r.get(
                "food_desert_vehicle", "").lower() and
                "not" not in r.get("food_desert_vehicle", "").lower()),
            None,
        )
        not_fd_row = next(
            (r for r in rows if "not" in r.get(
                "food_desert_vehicle", "").lower()),
            None,
        )
        if fd_row and not_fd_row:
            try:
                fd_tracts = int(fd_row["tracts"])
                fd_pop = int(fd_row["total_pop"])
                total_pop = fd_pop + int(not_fd_row["total_pop"])
                fd_poverty = float(fd_row["mean_poverty_rate"])
                city_poverty = float(not_fd_row["mean_poverty_rate"])
                gap_pp = fd_poverty - city_poverty
                return [
                    {"value": f"{fd_tracts}",
                     "label": "Food-desert tracts"},
                    {"value": f"{fd_pop:,}",
                     "label": "Residents in food deserts"},
                    {"value": f"{100 * fd_pop / total_pop:.1f}%",
                     "label": "Share of population"},
                    {"value": f"+{gap_pp:.1f} pp",
                     "label": "Poverty gap vs rest of city"},
                ]
            except (KeyError, ValueError, ZeroDivisionError):
                pass

    # ── 2. Generic descriptive KPIs from summary_stats.csv ──
    if summary_csv.exists():
        rows = _read_csv(summary_csv)
        # Pick the first numeric field (skip any field rows that are entirely null)
        row = next((r for r in rows if r.get("non_null_count", "0") != "0"), None)
        if row:
            try:
                field = row["field"].replace("_", " ")
                n = int(row["non_null_count"])
                mean_v = float(row["mean"])
                median_v = float(row["median"])
                max_v = float(row["max"])
                return [
                    {"value": f"{n:,}", "label": f"Features with {field}"},
                    {"value": f"{mean_v:.1f}", "label": f"Mean {field}"},
                    {"value": f"{median_v:.1f}", "label": f"Median {field}"},
                    {"value": f"{max_v:.1f}", "label": f"Highest {field}"},
                ]
            except (KeyError, ValueError):
                pass

    # ── 3. Fallback: manifest counts ──
    return _fallback_kpis(manifest)


def _fallback_kpis(manifest: dict) -> list[dict]:
    discovered = manifest.get("discovered_outputs", {})
    return [
        {"value": str(len(discovered.get("maps", []))), "label": "Maps"},
        {"value": str(len(discovered.get("charts", []))), "label": "Charts"},
        {"value": str(len(discovered.get("tables", []))), "label": "Tables"},
        {"value": str(len(manifest.get("sources", []))), "label": "Data sources"},
    ]


# ═════════════════════════════════════════════════════════════════════════
# Standard caveats — peer-reviewer-flagged disclosures every analysis needs
# ═════════════════════════════════════════════════════════════════════════

STANDARD_CAVEATS = [
    {
        "topic": "Margins of error",
        "body": (
            "ACS 5-year estimates carry sampling margins of error. Tracts "
            "with high coefficients of variation (CV &gt; 30%) are flagged "
            "in the processed data; interpret extreme values for small "
            "populations with particular caution."
        ),
    },
    {
        "topic": "Proxy variables",
        "body": (
            "Measures like no-vehicle household share or distance to "
            "supermarket are <em>proxies</em> for access, not direct "
            "measurements of the lived experience of food shopping. They "
            "do not capture corner-store availability, transit service "
            "frequency, or cultural food preferences."
        ),
    },
    {
        "topic": "Correlation vs causation",
        "body": (
            "Spatial concentration of poverty, vehicle access, and "
            "supermarket density is documented here; this analysis does "
            "not demonstrate a causal relationship between any of them "
            "and health or economic outcomes."
        ),
    },
    {
        "topic": "Institutional tracts",
        "body": (
            "Tracts that are predominantly parks, airports, military "
            "installations, or university campuses have extreme per-capita "
            "statistics by construction. Where present in this study area "
            "they are flagged in the processed data; readers should "
            "discount findings that ride on a single institutional tract."
        ),
    },
]

ALTERNATIVE_EXPLANATIONS = [
    {
        "label": "Affordability vs physical distance",
        "body": (
            "A supermarket may be geographically nearby yet out of reach "
            "for a household that can't afford a full grocery basket. "
            "Pair findings with SNAP redemption rates or food-price data "
            "before recommending access-only interventions."
        ),
    },
    {
        "label": "Informal and cultural food channels",
        "body": (
            "Corner stores, bodegas, ethnic grocery markets, food "
            "cooperatives, and mutual-aid distributions are inconsistently "
            "captured in OSM and SNAP retailer data. Neighborhoods with "
            "strong informal channels may look like food deserts in the "
            "data while functioning otherwise for their residents."
        ),
    },
]


# ═════════════════════════════════════════════════════════════════════════
# CSS (sedgwick-parity template)
# ═════════════════════════════════════════════════════════════════════════

CSS = """\
:root {
  --fg: #1c1c1c; --muted: #666; --line: #e0e0e0; --accent: #c04040;
  --bg: #fafafa; --card: #ffffff;
  --pass: #2f7a3a; --warn: #a16207; --fail: #b91c1c;
  --chip-pass-bg: #e6f4ea; --chip-warn-bg: #fef6e0; --chip-fail-bg: #fdecec;
}
* { box-sizing: border-box }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
       background: var(--bg); color: var(--fg); margin: 0;
       line-height: 1.55; -webkit-font-smoothing: antialiased; }
.wrap { max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
header.title { border-bottom: 1px solid var(--line); padding-bottom: 1rem; margin-bottom: 1.5rem; }
h1 { margin: 0 0 .35rem; font-size: 1.9rem; line-height: 1.2; }
h2 { font-size: 1.15rem; margin: 2.25rem 0 .85rem; color: #222;
     border-bottom: 1px solid var(--line); padding-bottom: .3rem;
     text-transform: uppercase; letter-spacing: .04em; font-weight: 600; }
h3 { font-size: 1rem; margin: 1.25rem 0 .4rem; color: #333; }
p, li { font-size: .95rem; }
ul, ol { margin: .25rem 0 .5rem 1.5rem; }
.sub { color: var(--muted); font-size: .92rem; }
.lead { font-size: 1.05rem; line-height: 1.6; color: #222; margin: .75rem 0 0; }
code { background: #eee; padding: .1rem .3rem; border-radius: 3px; font-size: .85rem; }
.meta { color: var(--muted); font-size: .9rem; margin-top: .25rem; }
.chip { display: inline-block; padding: .15rem .55rem; border-radius: 999px;
        font-size: .78rem; font-weight: 600; letter-spacing: .02em; }
.status-pass { background: var(--chip-pass-bg); color: var(--pass); }
.status-warn { background: var(--chip-warn-bg); color: var(--warn); }
.status-fail { background: var(--chip-fail-bg); color: var(--fail); }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
        margin: 1.5rem 0; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 6px;
       padding: 1rem 1.1rem; }
.kpi .v { font-size: 1.65rem; font-weight: 700; color: var(--accent);
          line-height: 1.1; }
.kpi .l { color: var(--muted); font-size: .78rem; text-transform: uppercase;
          letter-spacing: .05em; margin-top: .25rem; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 6px;
        padding: .6rem; margin: 0; }
.card img { width: 100%; height: auto; display: block; border-radius: 4px; }
.card figcaption { padding: .55rem .3rem 0; color: var(--muted); font-size: .85rem; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.full { width: 100%; border: 1px solid var(--line); border-radius: 6px;
        background: var(--card); padding: .6rem; }
.full img { width: 100%; height: auto; display: block; border-radius: 4px; }
.embed { width: 100%; height: 560px; border: 1px solid var(--line);
         border-radius: 6px; background: var(--card); }
.btn { display: inline-block; padding: .55rem 1rem; margin: .5rem 0;
       background: #1f4e79; color: #fff; text-decoration: none; border-radius: 4px;
       font-size: .9rem; font-weight: 500; }
.btn:hover { background: #163a5b; }
.caveat { background: #fff8e1; border-left: 4px solid #e9b02f;
          padding: .75rem 1rem; margin: .75rem 0; font-size: .9rem;
          border-radius: 0 4px 4px 0; }
.caveat .topic { font-weight: 700; color: #5a4100; }
.caveat p { margin-top: .2rem; }
table { width: 100%; border-collapse: collapse; margin: .75rem 0; font-size: .9rem; }
th, td { text-align: left; padding: .45rem .65rem;
         border-bottom: 1px solid var(--line); }
th { background: #f3f3f3; font-weight: 600; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line);
         color: var(--muted); font-size: .85rem; }
@media (max-width: 900px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .grid2 { grid-template-columns: 1fr; }
  .embed { height: 400px; }
}
@media (max-width: 540px) {
  .kpis { grid-template-columns: 1fr; }
}
"""


# ═════════════════════════════════════════════════════════════════════════
# Section builders
# ═════════════════════════════════════════════════════════════════════════

def _build_header(title: str, run_id: str, brief: dict, overall_status: str) -> list[str]:
    status_cls = _status_class(overall_status)
    audience = brief.get("audience", {})
    reader = audience.get("primary_reader", "")
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    parts = [
        '<header class="title">',
        f'  <h1>{escape(title)}</h1>',
    ]
    if reader:
        parts.append(f'  <p class="sub">Prepared for {escape(reader)}</p>')
    parts.append(
        f'  <p class="meta">Run <code>{escape(run_id)}</code> &middot; '
        f'{now} &middot; '
        f'QA <span class="chip {status_cls}">{escape(overall_status)}</span></p>'
    )
    parts.append('</header>')
    return parts


def _build_executive_summary(brief: dict, manifest: dict) -> list[str]:
    report_block = brief.get("report", {})
    lead = report_block.get("pyramid_lead")
    scqa = report_block.get("scqa", {})
    engagement = brief.get("engagement", {})
    hero_q = engagement.get("hero_question")

    parts: list[str] = []
    # Always include the section header so the reader knows where the answer is.
    parts.append('<h2>Executive summary</h2>')

    # Hero question
    if hero_q:
        parts.append(f'<p class="sub"><em>{escape(hero_q)}</em></p>')

    # Lead answer — the Pyramid "answer first" bit
    if lead:
        parts.append(f'<p class="lead">{escape(lead)}</p>')
    else:
        # Fall back to key_findings if the brief had no lead
        findings = manifest.get("key_findings", [])
        if findings:
            parts.append('<ul class="lead">')
            for f in findings[:3]:
                parts.append(f'  <li>{escape(str(f))}</li>')
            parts.append('</ul>')
        else:
            parts.append(
                '<p class="sub">(Executive summary not yet populated in the '
                'project brief. See detailed findings below.)</p>'
            )

    # SCQA expansion if available
    if scqa:
        parts.append('<div class="card" style="margin-top:1rem">')
        for key, label in [("situation", "Situation"),
                           ("complication", "Complication"),
                           ("question", "Question"),
                           ("answer", "Answer")]:
            v = scqa.get(key)
            if v:
                parts.append(
                    f'  <p style="margin:.3rem 0"><strong>{label}.</strong> '
                    f'{escape(v)}</p>'
                )
        parts.append('</div>')
    return parts


def _build_kpis(kpis: list[dict]) -> list[str]:
    parts = ['<div class="kpis">']
    for k in kpis:
        parts.append(
            f'  <div class="kpi">'
            f'<div class="v">{escape(k["value"])}</div>'
            f'<div class="l">{escape(k["label"])}</div></div>'
        )
    parts.append('</div>')
    return parts


def _caption_from_sidecar(png_path: Path) -> str | None:
    """Read the title/legend_title from the .style.json next to a map PNG."""
    sidecar = png_path.with_suffix(".style.json")
    if not sidecar.exists():
        return None
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("title") or data.get("legend_title")


def _build_maps_section(
    discovered: dict, analysis_dir: Path | None,
) -> list[str]:
    maps = discovered.get("maps", [])
    if not maps:
        return []
    parts: list[str] = ['<h2>Maps</h2>']
    for rel in maps:
        abs_path = _resolve(rel, analysis_dir)
        if abs_path is None:
            continue
        b64 = _b64_png(abs_path)
        if not b64:
            continue
        caption = _caption_from_sidecar(abs_path) or abs_path.stem.replace("_", " ").title()
        parts.append(
            f'<figure class="full">'
            f'<img src="data:image/png;base64,{b64}" alt="{escape(caption)}">'
            f'<figcaption>{escape(caption)}</figcaption>'
            f'</figure>'
        )
    return parts


def _build_charts_section(
    discovered: dict, analysis_dir: Path | None,
) -> list[str]:
    charts = discovered.get("charts", [])
    if not charts:
        return []
    parts: list[str] = ['<h2>Charts</h2>']

    # Pair up charts that have a "pairs_with" — fall back to 2-column grid.
    # Simpler approach: group consecutively into pairs of 2.
    queue: list[tuple[str, str | None]] = []
    for c in charts:
        if isinstance(c, dict):
            path_val = c.get("path") or ""
            title = c.get("title") or Path(path_val).stem.replace("_", " ").title()
        else:
            path_val = str(c)
            title = Path(path_val).stem.replace("_", " ").title()
        abs_path = _resolve(path_val, analysis_dir)
        if abs_path is None:
            continue
        b64 = _b64_png(abs_path)
        if b64:
            queue.append((b64, title))

    i = 0
    while i < len(queue):
        chunk = queue[i:i + 2]
        parts.append('<div class="grid2">')
        for b64, title in chunk:
            parts.append(
                f'  <figure class="card">'
                f'<img src="data:image/png;base64,{b64}" alt="{escape(title)}">'
                f'<figcaption>{escape(title)}</figcaption>'
                f'</figure>'
            )
        parts.append('</div>')
        i += 2
    return parts


def _build_interactive_map(
    discovered: dict, analysis_dir: Path | None,
) -> list[str]:
    web_files = discovered.get("web", [])
    if not web_files:
        return []
    # Use the first discovered web file.
    rel = web_files[0]
    abs_path = _resolve(rel, analysis_dir)
    if abs_path is None:
        return []
    # Build a relative href so the iframe points at the web file on disk.
    # analysis_dir is typically the parent of outputs/reports, and the web
    # file lives at outputs/web/<name>.html. A path relative to the report
    # location works: "../web/<name>.html".
    if analysis_dir is not None:
        try:
            rel_href = Path("..") / abs_path.relative_to(analysis_dir / "outputs")
            href = str(rel_href).replace("\\", "/")
        except ValueError:
            href = abs_path.name
    else:
        href = abs_path.name
    parts = [
        '<h2>Interactive map</h2>',
        '<p class="sub">Toggle layers in the upper-right; click any feature '
        'for details.</p>',
        f'<iframe class="embed" src="{escape(href)}" '
        f'title="Interactive map"></iframe>',
        f'<p><a class="btn" href="{escape(href)}" target="_blank">'
        f'Open interactive map in new tab</a></p>',
    ]
    return parts


def _build_methods(manifest: dict) -> list[str]:
    parts: list[str] = ['<h2>Methods</h2>']
    processing_steps = manifest.get("processing_steps", [])
    analysis = manifest.get("analysis", {})
    analysis_steps = analysis.get("steps", [])
    assumptions = analysis.get("assumptions", [])

    if processing_steps:
        parts.append('<h3>Processing</h3><ul>')
        for s in processing_steps:
            parts.append(f'  <li>{escape(str(s))}</li>')
        parts.append('</ul>')
    if analysis_steps:
        parts.append('<h3>Analysis</h3><ul>')
        for s in analysis_steps:
            parts.append(f'  <li>{escape(str(s))}</li>')
        parts.append('</ul>')
    if assumptions:
        parts.append('<h3>Assumptions</h3><ul>')
        for a in assumptions:
            parts.append(f'  <li>{escape(str(a))}</li>')
        parts.append('</ul>')
    if not (processing_steps or analysis_steps or assumptions):
        parts.append(
            '<p class="sub">No processing or analysis steps were recorded '
            'for this run.</p>'
        )
    return parts


def _build_qa(manifest: dict) -> list[str]:
    v = manifest.get("validation", {})
    status = v.get("overall_status", "UNKNOWN")
    scls = _status_class(status)
    parts: list[str] = [
        '<h2>QA status</h2>',
        f'<p><strong>Overall:</strong> <span class="chip {scls}">'
        f'{escape(status)}</span></p>',
    ]
    parts.append(
        f'<ul>'
        f'<li>Total checks: {v.get("total_checks", 0)}</li>'
        f'<li>Passed: {v.get("checks_pass", 0)}</li>'
        f'<li>Warnings: {v.get("checks_warn", 0)}</li>'
        f'<li>Failed: {v.get("checks_fail", 0)}</li>'
        f'</ul>'
    )
    rec = v.get("recommendation", "")
    if rec:
        parts.append(f'<p><strong>Recommendation.</strong> {escape(rec)}</p>')
    return parts


def _build_caveats(manifest: dict, brief: dict) -> list[str]:
    """Auto-inject the 4 standard disclosures plus any project-specific warnings."""
    parts: list[str] = ['<h2>Caveats &amp; limitations</h2>']

    # Project-specific warnings from upstream stages
    run_warnings: list[str] = []
    run_warnings.extend(manifest.get("warnings", []))
    run_warnings.extend(manifest.get("analysis", {}).get("warnings", []))
    run_warnings.extend(manifest.get("validation", {}).get("warnings", []))
    # De-duplicate while preserving order
    seen = set()
    project_warnings = [w for w in run_warnings
                        if not (w in seen or seen.add(w))]

    if project_warnings:
        parts.append('<h3>This analysis specifically</h3>')
        parts.append('<ul>')
        for w in project_warnings:
            parts.append(f'  <li>{escape(str(w))}</li>')
        parts.append('</ul>')

    # Standard disclosures every analysis should carry. Peer-reviewer will
    # flag their absence every time; shipping them by default.
    parts.append('<h3>Standard disclosures</h3>')
    for c in STANDARD_CAVEATS:
        parts.append(
            f'<div class="caveat">'
            f'<span class="topic">{escape(c["topic"])}.</span> '
            f'<p>{c["body"]}</p>'
            f'</div>'
        )

    # Brief-declared sensitivities — the brief's explicit flags about how
    # findings should be handled. These pre-empt hostile readings.
    sensitives = brief.get("engagement", {}).get(
        "sensitive_findings_to_handle_carefully", [])
    if sensitives:
        parts.append('<h3>Framing sensitivities</h3>')
        parts.append('<ul>')
        for s in sensitives:
            parts.append(f'  <li>{escape(str(s))}</li>')
        parts.append('</ul>')
    return parts


def _build_alternatives() -> list[str]:
    parts: list[str] = [
        '<h2>Alternative explanations</h2>',
        '<p class="sub">Hostile-reader check: here are mechanisms that could '
        'produce the observed patterns without supporting the policy '
        'conclusions you might draw from them.</p>',
    ]
    for a in ALTERNATIVE_EXPLANATIONS:
        parts.append(
            f'<p><strong>{escape(a["label"])}.</strong> {a["body"]}</p>'
        )
    return parts


def _build_sources(manifest: dict) -> list[str]:
    sources = manifest.get("sources", [])
    parts: list[str] = ['<h2>Sources &amp; provenance</h2>']
    if not sources:
        parts.append('<p class="sub">No provenance records found.</p>')
        return parts
    parts.append('<table>')
    parts.append(
        '<thead><tr><th>Source</th><th>Dataset</th><th>Vintage</th>'
        '<th>Geography</th><th>Retrieved</th></tr></thead>'
    )
    parts.append('<tbody>')
    for s in sources:
        parts.append('<tr>')
        parts.append(f'  <td>{escape(s.get("source_name", "Unknown"))}</td>')
        parts.append(f'  <td><code>{escape(s.get("dataset_id", "unknown"))}</code></td>')
        parts.append(f'  <td>{escape(str(s.get("vintage", "unknown")))}</td>')
        parts.append(f'  <td>{escape(s.get("geography_level", "unknown"))}</td>')
        retrieved = str(s.get("retrieved_at", ""))[:10]
        parts.append(f'  <td>{escape(retrieved)}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')
    return parts


# ═════════════════════════════════════════════════════════════════════════
# Top-level builder
# ═════════════════════════════════════════════════════════════════════════

def build_html(
    manifest: dict, title: str, run_id: str,
    *, analysis_dir: Path | None = None, project_brief: dict | None = None,
) -> str:
    brief = project_brief or {}
    validation = manifest.get("validation", {})
    overall_status = validation.get("overall_status", "UNKNOWN")
    kpis = _derive_kpis(manifest, brief, analysis_dir)
    discovered = manifest.get("discovered_outputs", {})

    parts: list[str] = []
    parts.append('<!doctype html>')
    parts.append('<html lang="en">')
    parts.append('<head>')
    parts.append('<meta charset="utf-8">')
    parts.append(f'<title>{escape(title)}</title>')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append(f'<style>{CSS}</style>')
    parts.append('</head>')
    parts.append('<body>')
    parts.append('<div class="wrap">')

    parts.extend(_build_header(title, run_id, brief, overall_status))
    parts.extend(_build_executive_summary(brief, manifest))
    parts.extend(_build_kpis(kpis))
    parts.extend(_build_maps_section(discovered, analysis_dir))
    parts.extend(_build_charts_section(discovered, analysis_dir))
    parts.extend(_build_interactive_map(discovered, analysis_dir))
    parts.extend(_build_methods(manifest))
    parts.extend(_build_qa(manifest))
    parts.extend(_build_caveats(manifest, brief))
    parts.extend(_build_alternatives())
    parts.extend(_build_sources(manifest))

    parts.append('<footer>')
    parts.append('  Generated by <strong>spatial-machines</strong> &middot; ')
    parts.append('  report assembled from per-stage handoff artifacts and the '
                 'project brief.')
    parts.append('</footer>')
    parts.append('</div>')
    parts.append('</body>')
    parts.append('</html>')
    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a static HTML report from an asset manifest."
    )
    parser.add_argument("manifest", help="Path to report asset manifest JSON")
    parser.add_argument("--title", default="GIS Analysis Report",
                        help="Report title")
    parser.add_argument("--run-id", default="unknown",
                        help="Run ID for this reporting run")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to write the HTML report")
    parser.add_argument("--analysis-dir",
                        help="Project analysis directory (for resolving "
                             "asset paths and reading project_brief.json + "
                             "summary_stats.csv). Defaults to the manifest's "
                             "parent's parent when the manifest lives under "
                             "<analysis>/runs/.")
    parser.add_argument("--project-brief",
                        help="Explicit path to project_brief.json. "
                             "Defaults to <analysis-dir>/project_brief.json.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = load_json(manifest_path)

    # Resolve analysis_dir: explicit arg wins; else infer when the manifest
    # lives at <analysis>/runs/<name>.json.
    analysis_dir: Path | None
    if args.analysis_dir:
        analysis_dir = Path(args.analysis_dir).expanduser().resolve()
    elif manifest_path.parent.name == "runs":
        analysis_dir = manifest_path.parent.parent
    else:
        analysis_dir = None

    brief: dict = {}
    brief_path = (
        Path(args.project_brief).expanduser().resolve()
        if args.project_brief
        else (analysis_dir / "project_brief.json" if analysis_dir else None)
    )
    if brief_path and brief_path.exists():
        try:
            brief = load_json(brief_path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARN: could not read project brief {brief_path}: {exc}",
                  file=sys.stderr)

    html = build_html(
        manifest, args.title, args.run_id,
        analysis_dir=analysis_dir, project_brief=brief,
    )

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    print(f"wrote HTML report -> {out}")
    print(f"  length: {len(html):,} chars")
    print(f"  analysis_dir: {analysis_dir}")
    print(f"  brief loaded: {bool(brief)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
