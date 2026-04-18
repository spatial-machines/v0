#!/usr/bin/env python3
"""spatial-machines demo — run a complete analysis in under 60 seconds.

Uses bundled Census data for Sedgwick County, KS (135 census tracts).
No API keys needed. No internet required. Just results.

Usage:
    python demo.py
    make demo
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows terminals default to cp1252 which can't encode the check-mark (✓)
# and other box-drawing characters this script uses for progress output.
# Force UTF-8 so the demo doesn't crash on a fresh Windows install.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_CORE = PROJECT_ROOT / "scripts" / "core"
DEMO_DATA = PROJECT_ROOT / "demos" / "sedgwick-poverty"
ANALYSIS_DIR = PROJECT_ROOT / "analyses" / "demo-sedgwick-poverty"


# ── Output helpers ───────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RESET = "\033[0m"
CHECK = "\u2713"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _fmt(text: str, *codes: str) -> str:
    if not USE_COLOR:
        return text
    return "".join(codes) + text + RESET


def banner() -> None:
    print()
    print(_fmt("  spatial-machines demo", BOLD))
    print(_fmt("  Sedgwick County, KS — Poverty Rate Analysis", DIM))
    print(_fmt("  135 census tracts, bundled data, no API keys", DIM))
    print()


def step(n: int, total: int, msg: str) -> None:
    print(f"  [{n}/{total}] {msg} ", end="", flush=True)


def done(elapsed: float, detail: str = "") -> None:
    suffix = f" {_fmt(detail, DIM)}" if detail else ""
    print(f"{_fmt(CHECK, GREEN, BOLD)} {_fmt(f'{elapsed:.1f}s', DIM)}{suffix}")


def skip(reason: str = "") -> None:
    suffix = f" {_fmt(reason, DIM)}" if reason else ""
    print(f"{_fmt('skipped', YELLOW)} {suffix}")


def fail(msg: str) -> None:
    print(f"\n  ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ── Steps ────────────────────────────────────────────────────────────

def setup() -> None:
    """Create analysis directory and copy bundled data."""
    gpkg = DEMO_DATA / "sedgwick_poverty_tracts.gpkg"
    if not gpkg.exists():
        fail(
            f"Demo data not found: {gpkg}\n"
            f"  Make sure you're running from the repo root:\n"
            f"  python demo.py"
        )

    # Clean previous demo run
    if ANALYSIS_DIR.exists():
        shutil.rmtree(ANALYSIS_DIR)

    for d in ["data/raw", "data/processed", "outputs/maps", "outputs/charts",
              "outputs/web", "outputs/qgis", "outputs/arcgis",
              "outputs/reports", "outputs/qa", "runs"]:
        (ANALYSIS_DIR / d).mkdir(parents=True, exist_ok=True)

    shutil.copy2(gpkg, ANALYSIS_DIR / "data" / "processed" / gpkg.name)

    # Write a minimal activity log so the solution graph can reconstruct the
    # pipeline. Each step below also appends to this file via _log_stage.
    (ANALYSIS_DIR / "runs" / "activity.log").write_text("")


def run_script(args: list[str], timeout: int = 300,
               python: str | None = None) -> subprocess.CompletedProcess:
    """Run a script and capture output.

    `python` overrides the interpreter (e.g. QGIS's python-qgis.bat for the
    QGIS packaging step). Defaults to the current interpreter.
    """
    py = python or sys.executable
    return subprocess.run(
        [py] + args,
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True, timeout=timeout,
    )


def _find_qgis_python() -> str | None:
    """Locate a Python interpreter that can import PyQGIS.

    Checks, in order:
      1. $QGIS_PYTHON env var (full path to python-qgis.bat or similar)
      2. Current interpreter (e.g. when demo runs inside OSGeo4W shell)
      3. Windows: common QGIS and OSGeo4W install locations — newest wins
      4. macOS: /Applications/QGIS*.app/Contents/MacOS/bin/python3
      5. Linux: python3 itself, IF `from qgis.core import QgsApplication` succeeds

    Returns the interpreter path or None when no QGIS Python is found.
    """
    override = os.environ.get("QGIS_PYTHON")
    if override and Path(override).exists():
        return override

    # Quick check: current interpreter already has PyQGIS?
    try:
        probe = subprocess.run(
            [sys.executable, "-c", "from qgis.core import QgsApplication"],
            capture_output=True, timeout=10,
        )
        if probe.returncode == 0:
            return sys.executable
    except (subprocess.TimeoutExpired, OSError):
        pass

    if os.name == "nt":
        # Standalone QGIS installer puts python-qgis.bat under Program Files.
        # System-wide OSGeo4W: C:\OSGeo4W\bin.
        # Per-user OSGeo4W (newer default): %LOCALAPPDATA%\Programs\OSGeo4W\bin.
        local_app = os.environ.get("LOCALAPPDATA",
                                    rf"C:\Users\{os.environ.get('USERNAME', '')}\AppData\Local")
        search_roots = [
            Path(r"C:\Program Files"),
            Path(r"C:\Program Files (x86)"),
            Path(r"C:\OSGeo4W"),
            Path(local_app) / "Programs" / "OSGeo4W",
            Path(local_app) / "Programs" / "OSGeo4W64",
        ]
        candidates: list[Path] = []
        for root in search_roots:
            if not root.exists():
                continue
            # QGIS standalone installer layout: "QGIS 3.xx/bin/python-qgis*.bat"
            candidates.extend(root.glob("QGIS */bin/python-qgis.bat"))
            candidates.extend(root.glob("QGIS */bin/python-qgis-ltr.bat"))
            # OSGeo4W layout (both system-wide and per-user): bin/python-qgis*.bat
            candidates.extend((root / "bin").glob("python-qgis*.bat"))
        if candidates:
            # Prefer LTR over the latest release when both exist (more stable).
            ltr = [c for c in candidates if "ltr" in c.name.lower()]
            pool = ltr or candidates
            # Newest version wins (lexicographic — "QGIS 3.40" > "QGIS 3.34").
            return str(sorted(pool)[-1])
        return None

    if sys.platform == "darwin":
        macs = list(Path("/Applications").glob("QGIS*.app/Contents/MacOS/bin/python3"))
        if macs:
            return str(sorted(macs)[-1])
        return None

    # Linux fallback — check that `python3` can import qgis.core
    try:
        probe = subprocess.run(
            ["python3", "-c", "from qgis.core import QgsApplication"],
            capture_output=True, timeout=10,
        )
        if probe.returncode == 0:
            return "python3"
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _log_stage(role: str, stage: str, scripts: list[str], outputs: list[str],
               description: str = "") -> None:
    """Append stage_start + stage_end entries to the demo's activity.log.

    The demo runs scripts in-process (no agents), so we emit both entries
    back-to-back after each step completes. This gives the solution graph
    real provenance without the overhead of sub-agent delegation.
    """
    import json as _json
    import uuid as _uuid
    log = ANALYSIS_DIR / "runs" / "activity.log"
    now = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
    run_id = str(_uuid.uuid4())[:12]
    start = {"event": "stage_start", "run_id": run_id, "timestamp": now,
             "role": role, "stage": stage, "description": description}
    end = {"event": "stage_end", "run_id": run_id, "timestamp": now,
           "role": role, "stage": stage, "status": "completed",
           "scripts_used": scripts,
           "outputs": [str(Path(o).relative_to(ANALYSIS_DIR)) for o in outputs]}
    with log.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(start) + "\n")
        f.write(_json.dumps(end) + "\n")


def run_choropleth() -> Path:
    """Generate poverty rate choropleth map."""
    gpkg = ANALYSIS_DIR / "data" / "processed" / "sedgwick_poverty_tracts.gpkg"
    out = ANALYSIS_DIR / "outputs" / "maps" / "poverty_choropleth.png"
    result = run_script([
        str(SCRIPTS_CORE / "analyze_choropleth.py"),
        str(gpkg), "poverty_rate",
        "--title", "Poverty Rate by Census Tract \u2014 Sedgwick County, KS",
        "--attribution", "Source: U.S. Census Bureau, ACS 5-Year Estimates",
        "--basemap", "light",
        "--legend-pos", "upper-left",
        "-o", str(out),
    ])
    if result.returncode != 0:
        fail(f"Choropleth failed:\n{result.stderr[-500:]}")
    _log_stage("cartography", "cartography",
               ["analyze_choropleth.py"], [out],
               description="Poverty rate choropleth")
    return out


def run_charts() -> list[Path]:
    """Generate paired statistical charts: distribution + top-N comparison."""
    gpkg = ANALYSIS_DIR / "data" / "processed" / "sedgwick_poverty_tracts.gpkg"
    charts_dir = ANALYSIS_DIR / "outputs" / "charts"

    hist = charts_dir / "poverty_histogram.png"
    result = run_script([
        str(SCRIPTS_CORE / "generate_chart.py"), "distribution",
        "--data", str(gpkg), "--layer", "sedgwick_poverty_tracts",
        "--field", "poverty_rate", "--kind", "histogram",
        "--output", str(hist.with_suffix("")),
        "--title", "Poverty rate distribution \u2014 Sedgwick County tracts",
        "--attribution", "Source: U.S. Census Bureau, ACS 5-Year Estimates",
    ])
    if result.returncode != 0:
        fail(f"Histogram chart failed:\n{result.stderr[-500:]}")

    top = charts_dir / "poverty_top_tracts.png"
    result = run_script([
        str(SCRIPTS_CORE / "generate_chart.py"), "comparison",
        "--data", str(gpkg), "--layer", "sedgwick_poverty_tracts",
        "--category-field", "NAMELSAD", "--value-field", "poverty_rate",
        "--kind", "lollipop", "--top-n", "15",
        "--output", str(top.with_suffix("")),
        "--title", "Top 15 tracts by poverty rate",
        "--attribution", "Source: U.S. Census Bureau, ACS 5-Year Estimates",
    ])
    if result.returncode != 0:
        fail(f"Comparison chart failed:\n{result.stderr[-500:]}")

    _log_stage("cartography", "cartography",
               ["generate_chart.py", "generate_chart.py"],
               [hist, top],
               description="Paired charts (distribution + top-N)")
    return [hist, top]


def run_solution_graph() -> Path:
    """Build the solution graph for this demo analysis."""
    out_stem = ANALYSIS_DIR / "outputs" / "solution_graph"
    result = run_script([
        str(SCRIPTS_CORE / "build_solution_graph.py"),
        str(ANALYSIS_DIR),
        "--out", str(out_stem),
    ])
    if result.returncode != 0:
        fail(f"Solution graph failed:\n{result.stderr[-500:]}")
    return out_stem.with_suffix(".png")


def run_web_map() -> Path:
    """Generate interactive web map."""
    gpkg = ANALYSIS_DIR / "data" / "processed" / "sedgwick_poverty_tracts.gpkg"
    out = ANALYSIS_DIR / "outputs" / "web" / "poverty_map.html"
    result = run_script([
        str(SCRIPTS_CORE / "render_web_map.py"),
        "--input", str(gpkg),
        "--layers",
        "poverty_rate:YlOrRd:Poverty Rate (%)",
        "pop_below_poverty:Reds:Population Below Poverty",
        "--tooltip-col", "NAMELSAD",
        "--popup-cols",
        "NAMELSAD", "poverty_rate", "pop_below_poverty",
        "total_pop_poverty_universe", "GEOID",
        "--title", "Poverty Analysis \u2014 Sedgwick County, KS",
        "-o", str(out),
    ])
    if result.returncode != 0:
        fail(f"Web map failed:\n{result.stderr[-500:]}")
    _log_stage("cartography", "cartography", ["render_web_map.py"], [out],
               description="Interactive web map")
    return out


def build_report(choropleth: Path, charts: list[Path],
                 solution_graph: Path, web_map: Path) -> Path:
    """Assemble a single self-contained HTML report with map + charts +
    solution graph + embedded interactive web map.

    The report is written to outputs/reports/demo_report.html. The demo
    opens this in the browser instead of the raw Folium map.
    """
    import base64
    import geopandas as gpd

    gpkg = ANALYSIS_DIR / "data" / "processed" / "sedgwick_poverty_tracts.gpkg"
    try:
        gdf = gpd.read_file(gpkg)
        n = len(gdf)
        mean_rate = float(gdf["poverty_rate"].mean())
        median_rate = float(gdf["poverty_rate"].median())
        max_rate = float(gdf["poverty_rate"].max())
        top_row = gdf.loc[gdf["poverty_rate"].idxmax()]
        top_name = str(top_row.get("NAMELSAD", "?"))
        below = int(gdf["pop_below_poverty"].sum())
        total_universe = int(gdf["total_pop_poverty_universe"].sum())
        county_rate = (below / total_universe * 100.0) if total_universe else 0.0
        top3 = gdf.nlargest(3, "poverty_rate")[
            ["NAMELSAD", "GEOID", "poverty_rate",
             "pop_below_poverty", "total_pop_poverty_universe"]
        ].to_dict("records")
        # Spatial pattern hint: are top-10 tracts clustered or scattered?
        top10 = gdf.nlargest(10, "poverty_rate")
        top10_bbox = top10.total_bounds  # minx, miny, maxx, maxy
        county_bbox = gdf.total_bounds
        top10_width = top10_bbox[2] - top10_bbox[0]
        top10_height = top10_bbox[3] - top10_bbox[1]
        county_width = county_bbox[2] - county_bbox[0]
        county_height = county_bbox[3] - county_bbox[1]
        concentration_ratio = (
            (top10_width * top10_height) / (county_width * county_height)
            if county_width * county_height else 1.0
        )
    except Exception:
        n, mean_rate, median_rate, max_rate, top_name, below = (
            0, 0.0, 0.0, 0.0, "?", 0,
        )
        total_universe, county_rate = 0, 0.0
        top3 = []
        concentration_ratio = 1.0

    def b64(path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode()

    # Inline images so the single HTML file is portable.
    choro_b64 = b64(choropleth)
    chart_cards = []
    for c in charts:
        chart_cards.append(
            f'<figure class="card"><img src="data:image/png;base64,{b64(c)}" '
            f'alt="{c.stem}"><figcaption>{c.stem.replace("_", " ").title()}'
            f'</figcaption></figure>'
        )
    # The solution_graph is still generated on disk (outputs/solution_graph.png)
    # but intentionally NOT embedded in the report — for a one-county, one-variable
    # demo the DAG is too thin to be illustrative of what a real analysis produces.
    _ = solution_graph  # noqa: F841 — keep the parameter for backwards-compat
    # Relative link to the Folium map for the "open interactive map" button.
    web_rel = web_map.resolve().relative_to((ANALYSIS_DIR / "outputs" / "reports").resolve().parent)
    web_href = f"../{web_rel.as_posix()}"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Poverty Analysis — Sedgwick County, KS</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root {{
    --fg: #1c1c1c; --muted: #666; --line: #e0e0e0; --accent: #c04040;
    --bg: #fafafa; --card: #ffffff;
  }}
  * {{ box-sizing: border-box }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
         background: var(--bg); color: var(--fg); margin: 0;
         line-height: 1.55; -webkit-font-smoothing: antialiased; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }}
  header.title {{ border-bottom: 1px solid var(--line); padding-bottom: 1rem; margin-bottom: 2rem; }}
  h1 {{ margin: 0 0 .25rem; font-size: 1.85rem; }}
  h2 {{ font-size: 1.2rem; margin: 2.25rem 0 .9rem; color: #222; }}
  .sub {{ color: var(--muted); font-size: .95rem; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
          margin: 1.5rem 0; }}
  .kpi {{ background: var(--card); border: 1px solid var(--line); border-radius: 6px;
         padding: .85rem 1rem; }}
  .kpi .v {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
  .kpi .l {{ color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; }}
  .top3-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0 1.5rem; }}
  .top3-card {{ background: #ffffff; color: #1c1c1c; border: 1px solid var(--line);
                border-left: 4px solid var(--accent); border-radius: 6px;
                padding: 1rem 1.1rem; }}
  .top3-rank {{ color: var(--accent); font-weight: 700; font-size: .85rem; letter-spacing: .04em; }}
  .top3-label {{ color: var(--muted); font-size: .7rem; text-transform: uppercase;
                 letter-spacing: .06em; margin-top: .35rem; }}
  .top3-name {{ font-weight: 700; font-size: 1.05rem; color: #1c1c1c;
                font-family: "SF Mono", "Consolas", monospace; margin-bottom: .5rem; }}
  .top3-rate {{ font-size: 2.1rem; font-weight: 700; color: var(--accent); line-height: 1; margin: .4rem 0; }}
  .top3-det {{ color: #333; font-size: .88rem; line-height: 1.4; }}
  .caveats {{ background: #fff9e6; border: 1px solid #e8cc5c; border-left: 4px solid #c89c00;
              border-radius: 6px; padding: 1rem 1.2rem; margin: 1.5rem 0; }}
  .caveats h3 {{ margin: 0 0 .5rem; font-size: 1rem; color: #6b5600; }}
  .caveats ul {{ margin: 0; padding-left: 1.2rem; color: #3d3000; font-size: .88rem; }}
  .caveats li {{ margin-bottom: .25rem; }}
  @media (max-width: 740px) {{ .top3-grid {{ grid-template-columns: 1fr; }} }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 6px;
          padding: .6rem; margin: 0; }}
  .card img {{ width: 100%; height: auto; display: block; border-radius: 4px; }}
  .card figcaption {{ padding: .5rem .25rem 0; color: var(--muted); font-size: .85rem; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
  .full {{ width: 100%; border: 1px solid var(--line); border-radius: 6px; background: var(--card); padding: .6rem; }}
  .full img {{ width: 100%; height: auto; display: block; }}
  .embed {{ width: 100%; height: 560px; border: 1px solid var(--line); border-radius: 6px; }}
  .btn {{ display: inline-block; padding: .55rem 1rem; margin: .5rem 0;
         background: #1f4e79; color: #fff; text-decoration: none; border-radius: 4px;
         font-size: .9rem; }}
  .btn:hover {{ background: #163a5b; }}
  footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line);
            color: var(--muted); font-size: .85rem; }}
  @media (max-width: 740px) {{
    .kpis, .grid2 {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header class="title">
    <h1>Poverty Analysis — Sedgwick County, KS</h1>
    <p class="sub">Demo analysis · spatial-machines · {datetime.now().strftime('%Y-%m-%d')}</p>
  </header>

  <section>
    <p><strong>The headline.</strong> In Sedgwick County (Wichita and surrounding
    area), roughly {below:,} residents live below the federal poverty threshold —
    {county_rate:.1f}% of the county's {total_universe:,}-person poverty universe.
    That rate is nearly evenly split above and below the county mean
    ({mean_rate:.1f}%), but the <em>spatial</em> distribution tells a sharper story:
    the top 10 highest-poverty tracts cover just {concentration_ratio:.0%} of the
    county's geographic footprint. Poverty here is concentrated, not diffuse.</p>

    <div class="kpis">
      <div class="kpi"><div class="v">{n:,}</div><div class="l">Tracts</div></div>
      <div class="kpi"><div class="v">{county_rate:.1f}%</div><div class="l">Countywide poverty rate</div></div>
      <div class="kpi"><div class="v">{max_rate:.1f}%</div><div class="l">Highest tract rate</div></div>
      <div class="kpi"><div class="v">{below:,}</div><div class="l">Residents below poverty</div></div>
    </div>
  </section>

  <section class="top3">
    <h2>Three tracts driving the upper tail</h2>
    <p class="sub">Ranked by poverty rate. These three alone account for
    {sum(t['pop_below_poverty'] for t in top3):,} residents in poverty — roughly
    {(sum(t['pop_below_poverty'] for t in top3) / below * 100.0 if below else 0):.1f}%
    of the county total, from {sum(t['total_pop_poverty_universe'] for t in top3):,}
    residents in the combined poverty universe.</p>
    <div class="top3-grid">
{''.join([
    f'<div class="top3-card"><div class="top3-rank">#{i+1}</div>'
    f'<div class="top3-label">Census tract</div>'
    f'<div class="top3-name">{t["GEOID"]}</div>'
    f'<div class="top3-rate">{t["poverty_rate"]:.1f}%</div>'
    f'<div class="top3-det">'
    f'<strong>{int(t["pop_below_poverty"]):,}</strong> below poverty of '
    f'<strong>{int(t["total_pop_poverty_universe"]):,}</strong> residents in the poverty universe'
    f'</div></div>'
    for i, t in enumerate(top3)
])}
    </div>
  </section>

  <h2>Choropleth map</h2>
  <div class="full">
    <img src="data:image/png;base64,{choro_b64}" alt="Poverty rate choropleth">
  </div>

  <h2>Statistical charts</h2>
  <div class="grid2">
    {chart_cards[0] if len(chart_cards) > 0 else ""}
    {chart_cards[1] if len(chart_cards) > 1 else ""}
  </div>
  <p class="sub">The histogram reveals skew hidden by the map's color classes; the lollipop
  chart names the tracts where poverty concentrates. Tract <em>{top_name}</em> has the highest
  rate at {max_rate:.1f}%.</p>

  <h2>Interactive map</h2>
  <p class="sub">Click any tract for its poverty rate, resident counts, and GEOID.
  Toggle between the poverty-rate and below-poverty-count layers in the upper right.</p>
  <iframe class="embed" src="{web_href}" title="Interactive poverty map"></iframe>
  <p><a class="btn" href="{web_href}" target="_blank">Open interactive map in new tab</a></p>

  <h2>How to read this</h2>
  <p>Natural-breaks classification groups tracts so that within-class variance is
  minimized — visually, classes separate where the distribution has natural gaps.
  The upper classes on this map aren't "slightly worse than the middle"; they're
  meaningfully disconnected from it. That's what the paired histogram shows
  (a long right tail), and it's what makes the three tracts called out above
  worth individual attention in a real engagement.</p>

  <div class="caveats">
    <h3>Caveats — read before citing</h3>
    <ul>
      <li><strong>ACS margins of error.</strong> These estimates come from the
      5-year American Community Survey sample, not a full count. Small tracts
      can have wide confidence intervals; the pipeline flags tracts with
      CV &gt; 0.15 when running the full statistics stage.</li>
      <li><strong>Poverty universe vs. total population.</strong> The denominator
      here is "population for whom poverty status is determined" — it excludes
      residents of group quarters (nursing homes, prisons, dorms). A tract
      dominated by one of those institutions can look artificially low.</li>
      <li><strong>This is a demo.</strong> Real engagements would add MOE maps,
      a significant-hotspot analysis (Getis-Ord Gi* with FDR correction), and
      a peer-review pass before shipping — all supported by the pipeline but
      out of scope for a 20-second reproducible demo.</li>
    </ul>
  </div>

  <h2>What this demo is showing you</h2>
  <p>Everything on this page came out of one command (<code>make demo</code>
  or <code>python demo.py</code>) on bundled Census data, with no API keys and
  no internet. Deliberately minimal: one variable, one county, one map,
  two charts, one interactive layer, one report.</p>
  <p>The full pipeline, given an AI coding agent and a real question, does much
  more: retrieval from 20+ data sources, join + CRS standardization, MOE
  propagation, significant-hotspot analysis (Getis-Ord Gi* with FDR correction),
  spatial autocorrelation (Moran's I / LISA), independent validation, peer
  review, and a <strong>solution graph</strong> — a DAG capturing every input,
  operation, and output across all 9 agents and their intermediate handoffs.
  The solution graph from a full run is dense and genuinely useful; the one
  this demo would produce is thin enough to be more confusing than helpful, so
  it's not shown here. See the project README for example prompts that
  exercise the real pipeline.</p>

  <footer>
    Generated by <strong>spatial-machines</strong> ·
    Data: U.S. Census Bureau ACS 5-Year Estimates ·
    Outputs in <code>{ANALYSIS_DIR.relative_to(PROJECT_ROOT)}/outputs/</code>
  </footer>
</div>
</body>
</html>
"""

    out = ANALYSIS_DIR / "outputs" / "reports" / "demo_report.html"
    out.write_text(html, encoding="utf-8")
    _log_stage("report-writer", "reporting", ["demo.build_report"], [out],
               description="Combined demo HTML report")
    return out


def run_qgis_package(qgis_python: str) -> Path | None:
    """Generate QGIS project package using the supplied QGIS Python interpreter.

    Returns None on failure. `qgis_python` should be the path to a Python
    that can `import qgis.core` — typically `python-qgis.bat` on Windows,
    QGIS.app's bundled python3 on macOS, or the system python3 on Linux
    when `python3-qgis` is installed.
    """
    gpkg = ANALYSIS_DIR / "data" / "processed" / "sedgwick_poverty_tracts.gpkg"
    qgis_dir = ANALYSIS_DIR / "outputs" / "qgis"
    qgis_data = qgis_dir / "data"
    qgis_data.mkdir(parents=True, exist_ok=True)

    # Copy data into the QGIS package (self-contained)
    shutil.copy2(gpkg, qgis_data / gpkg.name)

    out = qgis_dir / "demo_sedgwick_poverty.qgs"
    style_dir = ANALYSIS_DIR / "outputs" / "maps"
    result = run_script(
        [
            str(SCRIPTS_CORE / "write_qgis_project.py"),
            "--gpkg", str(Path("data") / "sedgwick_poverty_tracts.gpkg"),
            "--title", "Poverty Rate Analysis \u2014 Sedgwick County, KS",
            "--style-dir", str(style_dir),
            "--basemap", "carto-light",
            "-o", str(out),
        ],
        python=qgis_python,
    )
    if result.returncode != 0:
        # Print stderr tail so the user can see why QGIS gave up
        err = (result.stderr or "")[-500:]
        if err.strip():
            print(f"      QGIS stderr: {err.strip()}")
        return None
    return out


def open_in_browser(html_path: Path) -> bool:
    """Open the web map in the default browser."""
    import webbrowser
    try:
        url = html_path.resolve().as_uri()
        webbrowser.open(url)
        return True
    except Exception:
        return False


def summary(outputs: dict, total_time: float, browser_opened: bool) -> None:
    """Print final summary and next steps."""
    print()
    print(_fmt("  Done.", BOLD, GREEN) + f" {_fmt(f'{total_time:.0f} seconds', DIM)}")
    print()
    print(_fmt("  Outputs:", BOLD))
    for label, path in outputs.items():
        if path is None:
            continue
        try:
            rel = path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = path
        size = path.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        else:
            size_str = f"{size / 1024:.0f} KB"
        print(f"    {label:20s} {rel}  {_fmt(f'({size_str})', DIM)}")

    if not browser_opened:
        report = outputs.get("Demo report (HTML)") or outputs.get("Web map")
        if report:
            print()
            print(f"  Open the report:  {_fmt(f'open {report}', CYAN)}")

    demo_dir = "analyses/demo-sedgwick-poverty"
    gpkg = f"{demo_dir}/data/processed/sedgwick_poverty_tracts.gpkg"

    print()
    print(_fmt("  Explore the outputs:", BOLD))
    print()
    print(f"    The web map is in your browser. Click any tract for details.")
    print(f"    The choropleth PNG is in {_fmt(f'{demo_dir}/outputs/maps/', CYAN)}")
    if outputs.get("QGIS project"):
        print(f"    The QGIS project is in {_fmt(f'{demo_dir}/outputs/qgis/', CYAN)}")
    print()
    print(_fmt("  Try a script yourself:", BOLD))
    print()
    print(f"    Map a different variable from the same data:")
    print()
    choro_cmd = (
        f"python scripts/core/analyze_choropleth.py "
        f"{gpkg} "
        f"pop_below_poverty "
        f"--title \"Population Below Poverty\" "
        f"-o {demo_dir}/outputs/maps/pop_below_poverty.png"
    )
    print(f"      {_fmt(choro_cmd, CYAN)}")
    print()
    print(f"    See all available scripts:")
    print()
    dir_cmd = "dir scripts\\core\\" if os.name == "nt" else "ls scripts/core/"
    print(f"      {_fmt(dir_cmd, CYAN)}")
    print()
    print(_fmt("  Run a full AI-driven analysis:", BOLD))
    print()
    print(f"    Install Claude Code, then ask a question in this repo:")
    print()
    prompt = '"What does poverty look like in Cook County, IL?"'
    print(f"      {_fmt('claude', CYAN)} {_fmt(prompt, DIM)}")
    print()
    print(f"    The system retrieves data, runs analysis, and builds")
    print(f"    maps automatically. No API keys needed for Census data.")
    print(f"    See {_fmt('README.md', CYAN)} for full setup.")
    print()


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    os.chdir(PROJECT_ROOT)
    total_start = time.time()

    qgis_python = _find_qgis_python()
    has_qgis = qgis_python is not None
    total_steps = 6 + (1 if has_qgis else 0)

    banner()

    step(1, total_steps, "Setting up analysis directory")
    t = time.time()
    setup()
    done(time.time() - t, "analyses/demo-sedgwick-poverty/")

    step(2, total_steps, "Generating choropleth map")
    t = time.time()
    choropleth = run_choropleth()
    done(time.time() - t, "poverty_choropleth.png")

    step(3, total_steps, "Generating paired statistical charts")
    t = time.time()
    charts = run_charts()
    done(time.time() - t, f"{len(charts)} charts")

    step(4, total_steps, "Building interactive web map")
    t = time.time()
    web_map = run_web_map()
    done(time.time() - t, "poverty_map.html")

    step(5, total_steps, "Building solution graph")
    t = time.time()
    graph_png = run_solution_graph()
    done(time.time() - t, "solution_graph.png")

    step(6, total_steps, "Assembling combined HTML report")
    t = time.time()
    report = build_report(choropleth, charts, graph_png, web_map)
    done(time.time() - t, "demo_report.html")

    qgis_project = None
    if has_qgis:
        step(7, total_steps, "Packaging QGIS project")
        t = time.time()
        qgis_project = run_qgis_package(qgis_python)
        if qgis_project:
            done(time.time() - t, "demo_sedgwick_poverty.qgs")
        else:
            skip("PyQGIS error")
    else:
        print(f"  {_fmt('(QGIS not detected — skipping .qgs package)', DIM)}")
        print(f"  {_fmt('Tip: install QGIS Desktop or set QGIS_PYTHON env var.', DIM)}")

    total_time = time.time() - total_start

    # Open the combined report (includes the map, charts, solution graph,
    # and an embedded interactive web map).
    browser_opened = open_in_browser(report)

    outputs = {
        "Demo report (HTML)": report,
        "Choropleth map":      choropleth,
        "Distribution chart":  charts[0] if len(charts) > 0 else None,
        "Top-N chart":         charts[1] if len(charts) > 1 else None,
        "Solution graph":      graph_png,
        "Web map":             web_map,
    }
    if qgis_project:
        outputs["QGIS project"] = qgis_project

    summary(outputs, total_time, browser_opened)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
