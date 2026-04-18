#!/usr/bin/env python3
"""Generate a scoped consulting proposal from a project brief JSON.

Reads a project_brief.json and produces a structured Markdown (and optionally
HTML) proposal covering overview, methodology, deliverables, timeline,
data limitations, and assumptions.

Data source descriptions are pulled from:
  - fetch_federal_data.py SOURCES registry (built-in)
  - scripts/tool-registry/tool_registry.json

Usage:
    python generate_proposal.py \\
        --brief analyses/my_project/project_brief.json \\
        --output analyses/my_project/proposal.md \\
        --format markdown

    python generate_proposal.py \\
        --brief analyses/my_project/project_brief.json \\
        --output analyses/my_project/proposal.md \\
        --format html

Expected project_brief.json schema (all fields optional except client_name):
{
    "client_name":      "Sunflower County Health Dept.",
    "client_context":   "Planning a mobile health clinic expansion.",
    "hero_question":    "Where are the highest-need areas for a new mobile clinic?",
    "geography":        "Sunflower County, MS — census tract level",
    "state":            "MS",
    "analysis_types":   ["choropleth", "hotspot", "service_area"],
    "data_sources":     ["cdc_places", "hrsa_hpsas", "hrsa_fqhcs"],
    "deliverables":     ["choropleth maps", "hotspot map", "web map", "PDF report"],
    "complexity":       "standard",      // quick | standard | deep
    "notes":            "Client wants to present findings at a board meeting.",
    "analyst":          "GIS Consulting Team"
}
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import textwrap
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Load SOURCES registry from fetch_federal_data.py dynamically
# ---------------------------------------------------------------------------

def _load_federal_sources() -> dict:
    """Import SOURCES dict from fetch_federal_data.py without executing main()."""
    script = PROJECT_ROOT / "scripts" / "fetch_federal_data.py"
    if not script.exists():
        return {}
    try:
        spec = importlib.util.spec_from_file_location("fetch_federal_data", script)
        mod = importlib.util.module_from_spec(spec)
        # Provide stubs for heavy imports so we don't need geopandas at proposal time
        import types, sys as _sys
        stubs = ["geopandas", "pandas", "numpy", "shapely", "requests",
                 "pyproj", "fiona", "pyogrio"]
        originals = {}
        for name in stubs:
            if name not in _sys.modules:
                originals[name] = None
                _sys.modules[name] = types.ModuleType(name)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            pass
        finally:
            for name, orig in originals.items():
                if orig is None:
                    _sys.modules.pop(name, None)
        return getattr(mod, "SOURCES", {})
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Load tool registry
# ---------------------------------------------------------------------------

def _load_tool_registry() -> list:
    reg = PROJECT_ROOT / "scripts" / "tool-registry" / "tool_registry.json"
    if not reg.exists():
        return []
    try:
        return json.loads(reg.read_text())
    except Exception:
        return []


def _tool_registry_summary(tools: list) -> dict[str, str]:
    """Return {tool_id: brief_description} for quick lookup."""
    return {t.get("tool_id", ""): t.get("brief_description", "") for t in tools if t.get("tool_id")}


# ---------------------------------------------------------------------------
# Timeline logic
# ---------------------------------------------------------------------------

TIMELINE = {
    "quick": ("1 business day", "Straightforward analysis with 1–2 data sources and standard deliverables."),
    "standard": ("3 business days", "Multi-source analysis with custom joins, validation, and polished map outputs."),
    "deep": ("~1 week", "Complex spatial analysis with iterative QA, multi-layer synthesis, and interactive outputs."),
}

# Heuristic: bump complexity based on analysis_types count and data_sources count
def _infer_complexity(brief: dict) -> str:
    explicit = brief.get("complexity", "").lower()
    if explicit in TIMELINE:
        return explicit
    n_analyses = len(brief.get("analysis_types", []))
    n_sources = len(brief.get("data_sources", []))
    if n_analyses >= 4 or n_sources >= 4:
        return "deep"
    elif n_analyses >= 2 or n_sources >= 2:
        return "standard"
    return "quick"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_overview(brief: dict) -> list[str]:
    lines = ["## 1. Project Overview", ""]
    hero = brief.get("hero_question", "_Not specified._")
    client = brief.get("client_name", "_Client TBD_")
    context = brief.get("client_context", "_No context provided._")
    geo = brief.get("geography", "_Geography TBD_")

    lines += [
        f"**Client:** {client}",
        "",
        f"**Hero Question:** {hero}",
        "",
        f"**Geography:** {geo}",
        "",
        f"**Client Context:** {context}",
        "",
    ]
    if brief.get("notes"):
        lines += [f"**Additional Notes:** {brief['notes']}", ""]
    return lines


def _section_methodology(brief: dict, federal_sources: dict, tool_registry: dict[str, str]) -> list[str]:
    lines = ["## 2. Proposed Methodology", ""]

    analysis_types = brief.get("analysis_types", [])
    data_sources = brief.get("data_sources", [])

    # Data sources block
    if data_sources:
        lines += ["### Data Sources", ""]
        for ds_key in data_sources:
            if ds_key in federal_sources:
                src = federal_sources[ds_key]
                lines += [
                    f"- **{ds_key}** — {src.get('description', '_No description_')}",
                    f"  - Geography: {src.get('geography', 'N/A')}",
                    f"  - Vintage: {src.get('vintage', 'N/A')}",
                    f"  - Notes: {src.get('notes', 'N/A')}",
                    "",
                ]
            else:
                lines += [f"- **{ds_key}** — _(description not found in federal registry)_", ""]
        lines.append("")

    # Analysis types block
    if analysis_types:
        lines += ["### Analysis Types", ""]
        # Map friendly names → tool registry entries where possible
        analysis_labels = {
            "choropleth": "Choropleth mapping — classify and symbolise a numeric variable by geography.",
            "hotspot": "Hot-spot analysis — identify spatial clusters of high/low values (Getis-Ord Gi*).",
            "service_area": "Service area analysis — compute drive-time isochrones around facilities.",
            "spatial_regression": "Spatial regression — model a variable controlling for spatial autocorrelation.",
            "bivariate": "Bivariate choropleth — compare two variables simultaneously on one map.",
            "dot_density": "Dot density map — represent count data as randomly placed dots.",
            "small_multiples": "Small multiples — compare a variable across sub-populations or time periods.",
            "change_detection": "Change detection — quantify and map change between two time periods.",
            "time_series_animation": "Time-series animation — animated GIF/MP4 choropleth across multiple years.",
            "kde": "Kernel density estimation — continuous surface of event intensity.",
            "zonal_stats": "Zonal statistics — summarise raster values within polygon zones.",
            "spatial_join": "Spatial join — append attributes based on geographic proximity or containment.",
            "overlay": "Overlay analysis — intersect, union, or difference polygon layers.",
            "proportional_symbols": "Proportional symbols — scale point markers to represent magnitude.",
            "top_n": "Top-N analysis — rank and highlight leading/lagging geographies.",
        }
        for atype in analysis_types:
            desc = analysis_labels.get(atype.lower().replace(" ", "_"), f"Custom analysis: {atype}")
            lines += [f"- **{atype}:** {desc}", ""]
        lines.append("")

    if not analysis_types and not data_sources:
        lines += [
            "_No analysis types or data sources specified in brief. "
            "Methodology will be defined in consultation with the client._",
            "",
        ]

    return lines


def _section_deliverables(brief: dict) -> list[str]:
    lines = ["## 3. Deliverables", ""]
    deliverables = brief.get("deliverables", [])

    # Defaults keyed to analysis types if no deliverables specified
    if not deliverables:
        analysis_types = brief.get("analysis_types", [])
        defaults = {
            "choropleth": "Choropleth PNG maps (one per variable)",
            "hotspot": "Hot-spot map PNG + GeoPackage with cluster scores",
            "service_area": "Service area polygons (GeoPackage + PNG)",
            "spatial_regression": "Regression output CSV + coefficient map",
            "bivariate": "Bivariate choropleth PNG",
            "dot_density": "Dot density map PNG",
            "small_multiples": "Small-multiples panel PNG",
            "change_detection": "Change map PNG + change GeoPackage",
            "time_series_animation": "Animated GIF or MP4",
            "kde": "KDE raster (GeoTIFF) + PNG",
            "zonal_stats": "Zonal statistics GeoPackage",
            "spatial_join": "Joined GeoPackage",
        }
        deliverables = [defaults[a] for a in analysis_types if a in defaults]
        deliverables += [
            "Data dictionary (Markdown)",
            "Provenance log (JSON)",
            "Written summary report (Markdown)",
        ]

    for d in deliverables:
        lines += [f"- {d}"]
    lines.append("")
    return lines


def _section_timeline(brief: dict, complexity: str) -> list[str]:
    lines = ["## 4. Timeline Estimate", ""]
    duration, rationale = TIMELINE[complexity]
    lines += [
        f"**Complexity:** {complexity.title()}",
        "",
        f"**Estimated Duration:** {duration}",
        "",
        f"**Rationale:** {rationale}",
        "",
    ]

    # Rough phase breakdown
    if complexity == "quick":
        phases = [
            ("Data acquisition & validation", "0.5 day"),
            ("Analysis & map production", "0.5 day"),
        ]
    elif complexity == "standard":
        phases = [
            ("Data acquisition & validation", "1 day"),
            ("Analysis & map production", "1 day"),
            ("Report writing & QA", "1 day"),
        ]
    else:
        phases = [
            ("Data acquisition & validation", "1–2 days"),
            ("Exploratory analysis & QA", "1 day"),
            ("Core analysis & map production", "2 days"),
            ("Report, web map, and final QA", "1–2 days"),
        ]

    lines += ["| Phase | Estimate |", "|-------|----------|"]
    for phase, est in phases:
        lines += [f"| {phase} | {est} |"]
    lines.append("")
    return lines


def _section_limitations(brief: dict, federal_sources: dict) -> list[str]:
    lines = ["## 5. Data Limitations", ""]
    data_sources = brief.get("data_sources", [])

    if data_sources:
        for ds_key in data_sources:
            if ds_key in federal_sources:
                src = federal_sources[ds_key]
                vintage = src.get("vintage", "unknown")
                geo = src.get("geography", "unspecified geography")
                notes = src.get("notes", "")
                lines += [
                    f"- **{ds_key}** ({vintage}): Coverage limited to {geo}.",
                ]
                if notes:
                    lines += [f"  - {notes}"]
            else:
                lines += [f"- **{ds_key}**: Source metadata not available — verify coverage and vintage before use."]
        lines.append("")

    # Generic standing limitations
    lines += [
        "- All federal datasets are subject to **vintage lag** — estimates may not reflect recent conditions.",
        "- **Small-area statistics** (tract and block group level) carry higher margins of error than county-level estimates.",
        "- **Geographic edge effects**: features near study area boundaries may be under-represented in spatial statistics.",
        "- Data joins depend on consistent **GEOID / FIPS codes** — mismatches will generate null records.",
        "",
    ]
    return lines


def _section_assumptions(brief: dict) -> list[str]:
    lines = ["## 6. Assumptions & Client Confirmations Needed", ""]
    lines += [
        "Please confirm the following before work begins:",
        "",
        "- [ ] The **hero question** accurately captures the primary analytical goal.",
        "- [ ] The **geographic scope** (state, county, tract) is correct and complete.",
        "- [ ] The **analysis complexity level** (`" + _infer_complexity(brief) + "`) is acceptable for the timeline.",
        "- [ ] All listed **data sources** are approved for use in this engagement.",
        "- [ ] **Deliverable formats** (PNG maps, GeoPackage, Markdown report) are suitable for the client audience.",
    ]
    if brief.get("data_sources"):
        lines += ["- [ ] Client has no proprietary datasets to overlay (or will provide them before work starts)."]
    if "service_area" in brief.get("analysis_types", []):
        lines += ["- [ ] Drive-time radii / service area parameters have been confirmed (e.g., 30-minute drive)."]
    if brief.get("notes"):
        lines += [f"- [ ] Additional context confirmed: _{brief['notes']}_"]
    lines += [
        "- [ ] Point of contact and preferred delivery format for final outputs confirmed.",
        "",
    ]
    return lines


# ---------------------------------------------------------------------------
# Full proposal assembly
# ---------------------------------------------------------------------------

def build_proposal(brief: dict, federal_sources: dict, tool_registry: list) -> str:
    complexity = _infer_complexity(brief)
    tool_lookup = _tool_registry_summary(tool_registry)

    now_str = datetime.now(UTC).strftime("%B %d, %Y")
    analyst = brief.get("analyst", "GIS Consulting Team")
    client = brief.get("client_name", "Client")

    header = [
        f"# Consulting Proposal: {client}",
        "",
        f"**Prepared by:** {analyst}  ",
        f"**Date:** {now_str}  ",
        f"**Status:** Draft — pending client review",
        "",
        "---",
        "",
    ]

    body: list[str] = []
    body += _section_overview(brief)
    body += _section_methodology(brief, federal_sources, tool_lookup)
    body += _section_deliverables(brief)
    body += _section_timeline(brief, complexity)
    body += _section_limitations(brief, federal_sources)
    body += _section_assumptions(brief)

    footer = [
        "---",
        "",
        f"*This proposal was generated by the GIS Agent pipeline on {now_str}. "
        "All estimates are subject to revision after scoping confirmation.*",
        "",
    ]

    return "\n".join(header + body + footer)


# ---------------------------------------------------------------------------
# Markdown → HTML
# ---------------------------------------------------------------------------

def md_to_html(md: str, title: str = "Consulting Proposal") -> str:
    try:
        import markdown  # type: ignore
        body = markdown.markdown(md, extensions=["tables", "toc"])
    except ImportError:
        # Minimal fallback: wrap paragraphs in <p>
        import re
        body = "<br>".join(md.splitlines())

    return textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{title}</title>
          <style>
            body {{ font-family: Georgia, serif; max-width: 860px; margin: 48px auto;
                   padding: 0 24px; color: #222; line-height: 1.7; }}
            h1 {{ border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
            h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 2em; }}
            table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
            th {{ background: #f0f4ff; font-weight: bold; }}
            code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            blockquote {{ border-left: 4px solid #2563eb; margin: 0; padding: 8px 16px;
                          background: #f8f8ff; color: #444; }}
            hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
            input[type=checkbox] {{ margin-right: 6px; }}
          </style>
        </head>
        <body>
        {body}
        </body>
        </html>
    """)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a consulting proposal from a project brief JSON."
    )
    parser.add_argument("--brief", required=True, help="Path to project_brief.json")
    parser.add_argument(
        "--output", required=True,
        help="Output path for the proposal (.md)",
    )
    parser.add_argument(
        "--format", default="markdown", choices=["markdown", "html"],
        help="Output format: markdown (default) or html",
    )
    args = parser.parse_args()

    brief_path = Path(args.brief).expanduser().resolve()
    if not brief_path.exists():
        print(f"ERROR: brief not found: {brief_path}", file=sys.stderr)
        return 1

    try:
        brief = json.loads(brief_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: could not parse brief JSON: {e}", file=sys.stderr)
        return 1

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading data source registries...")
    federal_sources = _load_federal_sources()
    tool_registry = _load_tool_registry()
    print(f"  Federal sources: {len(federal_sources)} entries")
    print(f"  Tool registry:   {len(tool_registry)} entries")

    print("Generating proposal...")
    complexity = _infer_complexity(brief)
    duration, _ = TIMELINE[complexity]
    print(f"  Complexity: {complexity} → {duration}")

    md_content = build_proposal(brief, federal_sources, tool_registry)

    # Write Markdown
    output_path.write_text(md_content)
    print(f"Proposal (Markdown): {output_path}")

    # Write HTML if requested
    html_path = None
    if args.format == "html":
        html_path = output_path.with_suffix(".html")
        client_name = brief.get("client_name", "Consulting Proposal")
        html_content = md_to_html(md_content, title=f"Proposal — {client_name}")
        html_path.write_text(html_content)
        print(f"Proposal (HTML):     {html_path}")

    # Log
    log = {
        "step": "generate_proposal",
        "brief": str(brief_path),
        "output_md": str(output_path),
        "output_html": str(html_path) if html_path else None,
        "format": args.format,
        "complexity": complexity,
        "timeline": duration,
        "client_name": brief.get("client_name"),
        "data_sources": brief.get("data_sources", []),
        "analysis_types": brief.get("analysis_types", []),
        "federal_sources_loaded": len(federal_sources),
        "tool_registry_loaded": len(tool_registry),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = output_path.with_name(f"{output_path.stem}.proposal.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
