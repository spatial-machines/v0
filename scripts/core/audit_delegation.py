#!/usr/bin/env python3
"""Delegation fidelity auditor — verify agents followed their SOUL.md contracts.

Post-hoc audit that checks:
  - Did each stage produce its required handoff?
  - Did agents use approved scripts (from their TOOLS.md)?
  - Do all output files referenced in handoffs actually exist?
  - Is the handoff chain complete (upstream references valid)?
  - Did the cartography stage produce style sidecars?
  - Are there any role boundary violations?

Usage:
    python scripts/core/audit_delegation.py analyses/my-project/

    python scripts/core/audit_delegation.py analyses/my-project/ --strict
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Approved scripts per role (from TOOLS.md — kept minimal, checks against core/)
ROLE_APPROVED_SCRIPTS = {
    "lead-analyst": {
        "parse_task.py", "create_run_plan.py", "list_projects.py", "project_status.py",
        "check_pipeline_status.py", "check_data_freshness.py", "check_reanalysis_needed.py",
        "search_project_inventory.py", "build_project_inventory.py",
        "write_lead_handoff.py", "synthesize_run_summary.py",
        "run_peer_review.py", "compare_projects.py", "log_activity.py",
    },
    "data-retrieval": {
        "fetch_acs_data.py", "fetch_census_population.py", "retrieve_tiger.py",
        "fetch_poi.py", "fetch_ejscreen.py", "fetch_cdc_places.py", "fetch_fema_nfhl.py",
        "fetch_usda_food_access.py", "fetch_hud_data.py", "fetch_lehd_lodes.py",
        "fetch_noaa_climate.py", "fetch_bls_employment.py", "fetch_fbi_crime.py",
        "fetch_socrata.py", "fetch_usgs_elevation.py", "fetch_gtfs.py",
        "fetch_overture.py", "fetch_openweather.py", "retrieve_remote.py",
        "retrieve_local.py", "geocode_addresses.py", "inspect_dataset.py",
        "search_project_inventory.py", "build_project_inventory.py", "log_activity.py",
    },
    "data-processing": {
        "process_vector.py", "process_table.py", "extract_archive.py",
        "join_data.py", "batch_join.py", "spatial_join.py",
        "derive_fields.py", "compute_rate.py", "enrich_points.py",
        "raster_clip.py", "raster_calc.py", "raster_mosaic.py",
        "raster_proximity.py", "terrain_analysis.py",
        "write_processing_handoff.py", "log_activity.py",
    },
    "spatial-stats": {
        "compute_hotspots.py", "compute_spatial_autocorrelation.py",
        "analyze_summary_stats.py", "analyze_top_n.py",
        "compute_change_detection.py", "score_sites.py",
        "write_analysis_handoff.py", "log_activity.py",
    },
    "cartography": {
        "analyze_choropleth.py", "analyze_bivariate.py", "overlay_points.py",
        "compute_hotspots.py", "compute_spatial_autocorrelation.py",
        "analyze_dot_density.py", "analyze_proportional_symbols.py",
        "analyze_small_multiples.py", "analyze_uncertainty.py",
        "render_web_map.py", "validate_cartography.py", "check_colorblind.py",
        "write_style_sidecar.py", "write_cartography_handoff.py",
        "generate_chart.py", "build_solution_graph.py", "log_activity.py",
    },
    "validation-qa": {
        "validate_outputs.py", "validate_vector.py", "validate_tabular.py",
        "validate_join_coverage.py", "validate_analysis.py",
        "validate_cartography.py", "validate_handoffs.py",
        "check_report_sensitivity.py",
        "write_validation_handoff.py", "log_activity.py",
    },
    "report-writer": {
        "write_html_report.py", "write_markdown_report.py",
        "collect_report_assets.py", "write_data_dictionary.py",
        "generate_citations.py",
        "write_reporting_handoff.py", "log_activity.py",
    },
    "site-publisher": {
        "package_qgis_review.py", "write_qgis_project.py",
        "package_arcgis_pro.py", "lyrx_writer.py", "aprx_scaffold.py",
        "validate_arcgis_package.py", "publish_arcgis_online.py",
        "write_data_catalog.py", "generate_all_catalogs.py",
        "collect_report_assets.py",
        "write_publishing_handoff.py", "log_activity.py",
    },
    "peer-reviewer": {
        "run_peer_review.py", "log_activity.py",
    },
}

REQUIRED_HANDOFFS = {
    "retrieval": "provenance",
    "processing": "processing",
    "analysis": "analysis",
    "validation": "validation",
    "reporting": "reporting",
    "delivery": "lead-analyst",
}


def _read_activity_log(project_dir: Path) -> list[dict]:
    log_path = project_dir / "runs" / "activity.log"
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _read_handoffs(project_dir: Path) -> dict:
    runs_dir = project_dir / "runs"
    if not runs_dir.exists():
        return {}
    handoffs = {}
    for f in runs_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            ht = data.get("handoff_type")
            if ht:
                handoffs[ht] = {"data": data, "file": f.name}
        except (json.JSONDecodeError, KeyError):
            pass
    return handoffs


def audit(project_dir: Path, strict: bool = False) -> dict:
    """Run the full delegation fidelity audit."""
    findings = []
    entries = _read_activity_log(project_dir)
    handoffs = _read_handoffs(project_dir)

    # 1. Check handoff completeness
    for stage, expected_type in REQUIRED_HANDOFFS.items():
        if expected_type not in handoffs:
            findings.append({
                "check": "handoff_completeness",
                "severity": "error" if strict else "warning",
                "stage": stage,
                "message": f"Missing {expected_type} handoff",
            })

    # 2. Check handoff chain integrity (upstream references)
    known_run_ids = set()
    for ht, info in handoffs.items():
        rid = info["data"].get("run_id")
        if rid:
            known_run_ids.add(rid)

    for ht, info in handoffs.items():
        upstream = info["data"].get("upstream_handoff")
        if upstream and isinstance(upstream, dict):
            upstream_rid = upstream.get("run_id")
            if upstream_rid and upstream_rid not in known_run_ids:
                findings.append({
                    "check": "chain_integrity",
                    "severity": "warning",
                    "handoff": ht,
                    "message": f"References unknown upstream run_id: {upstream_rid}",
                })

    # 3. Check output files exist
    for ht, info in handoffs.items():
        for output_path in info["data"].get("output_files", []):
            full = project_dir / output_path if not Path(output_path).is_absolute() else Path(output_path)
            # Also try from PROJECT_ROOT
            if not full.exists():
                full = PROJECT_ROOT / output_path
            if not full.exists():
                findings.append({
                    "check": "output_exists",
                    "severity": "error",
                    "handoff": ht,
                    "file": info["file"],
                    "message": f"Output file missing: {output_path}",
                })

    # 4. Check script usage against approved lists (from activity log)
    for e in entries:
        if e.get("event") == "stage_end":
            role = e.get("role", "")
            scripts = e.get("scripts_used", [])
            approved = ROLE_APPROVED_SCRIPTS.get(role, set())
            for script in scripts:
                script_name = Path(script).name
                if script_name not in approved and approved:
                    findings.append({
                        "check": "approved_scripts",
                        "severity": "warning",
                        "role": role,
                        "message": f"Used non-approved script: {script_name}",
                    })

    # 5. Check style sidecars for maps
    maps_dir = project_dir / "outputs" / "maps"
    if maps_dir.exists():
        for png in maps_dir.glob("*.png"):
            sidecar = png.with_suffix(".style.json")
            if not sidecar.exists():
                findings.append({
                    "check": "style_sidecar",
                    "severity": "warning",
                    "message": f"Map missing style sidecar: {png.name}",
                })

    # 6. Check QGIS package completeness
    qgis_dir = project_dir / "outputs" / "qgis"
    if qgis_dir.exists():
        qgs_files = list(qgis_dir.glob("*.qgs"))
        if not qgs_files:
            findings.append({
                "check": "qgis_package",
                "severity": "warning",
                "message": "QGIS directory exists but no .qgs project file found",
            })
        for expected in ["review-spec.json", "review-notes.md", "manifest.json", "README.md"]:
            if not (qgis_dir / expected).exists():
                findings.append({
                    "check": "qgis_package",
                    "severity": "info",
                    "message": f"QGIS package missing: {expected}",
                })

    # 7. Cartography handoff declares charts[] when the brief requires them
    brief_path = project_dir / "project_brief.json"
    brief = {}
    if brief_path.exists():
        try:
            brief = json.loads(brief_path.read_text())
        except (OSError, json.JSONDecodeError):
            brief = {}
    outputs_cfg = brief.get("outputs", {}) if isinstance(brief, dict) else {}

    required_charts = outputs_cfg.get("required_charts") or []
    cart = handoffs.get("cartography")
    if required_charts:
        if not cart:
            findings.append({
                "check": "charts_declared",
                "severity": "warning",
                "message": (
                    "Project brief requires charts but no cartography handoff "
                    "declares them. Run scripts/core/write_cartography_handoff.py."
                ),
            })
        else:
            declared = cart["data"].get("charts") or []
            if len(declared) < len(required_charts):
                findings.append({
                    "check": "charts_declared",
                    "severity": "warning",
                    "handoff": "cartography",
                    "message": (
                        f"Cartography handoff declares {len(declared)} chart(s); "
                        f"project brief requires at least {len(required_charts)}."
                    ),
                })

    # 8. ArcGIS Pro package delivered when required by the brief
    if outputs_cfg.get("arcgis_package_required"):
        arcgis_dir = project_dir / "outputs" / "arcgis"
        has_gdb = (arcgis_dir / "data" / "project.gdb").exists()
        has_manifest = (arcgis_dir / "manifest.json").exists()
        if not (has_gdb and has_manifest):
            findings.append({
                "check": "arcgis_pro_package",
                "severity": "error",
                "message": (
                    "Project brief sets arcgis_package_required=true but "
                    "outputs/arcgis/ is missing data/project.gdb or manifest.json. "
                    "Run scripts/core/package_arcgis_pro.py."
                ),
            })
        pub = handoffs.get("publishing")
        if pub and "arcgis_pro_package" not in pub["data"]:
            findings.append({
                "check": "arcgis_pro_package",
                "severity": "warning",
                "handoff": "publishing",
                "message": (
                    "Publishing handoff does not reference arcgis_pro_package — "
                    "re-run write_publishing_handoff.py --arcgis-pro-manifest …"
                ),
            })

    # 9. AGOL publish status recorded when the brief opts in
    publish_targets = outputs_cfg.get("publish_targets") or []
    if "arcgis_online" in publish_targets:
        status_file = project_dir / "outputs" / "arcgis" / "publish-status.json"
        if not status_file.exists():
            findings.append({
                "check": "arcgis_online_publish",
                "severity": "error",
                "message": (
                    "Project brief opts into arcgis_online but no publish-status.json "
                    "exists. Run scripts/core/publish_arcgis_online.py --dry-run "
                    "first, then without --dry-run to publish."
                ),
            })
        pub = handoffs.get("publishing")
        if pub and "arcgis_online_publish" not in pub["data"]:
            findings.append({
                "check": "arcgis_online_publish",
                "severity": "warning",
                "handoff": "publishing",
                "message": (
                    "Publishing handoff does not reference arcgis_online_publish — "
                    "re-run write_publishing_handoff.py --arcgis-online-status …"
                ),
            })

    # Summary
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    infos = [f for f in findings if f["severity"] == "info"]

    verdict = "PASS"
    if errors:
        verdict = "FAIL"
    elif warnings:
        verdict = "PASS WITH WARNINGS"

    return {
        "project": str(project_dir),
        "audited_at": datetime.now(UTC).isoformat(),
        "verdict": verdict,
        "errors": len(errors),
        "warnings": len(warnings),
        "info": len(infos),
        "handoffs_found": list(handoffs.keys()),
        "activity_entries": len(entries),
        "findings": findings,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Audit delegation fidelity for a completed analysis.")
    parser.add_argument("project_dir", help="Path to analysis directory")
    parser.add_argument("--strict", action="store_true", help="Treat missing handoffs as errors")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Project directory not found: {project_dir}")
        return 1

    result = audit(project_dir, strict=args.strict)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"\n  Delegation Audit: {project_dir.name}")
    print(f"  {'=' * 55}")
    print(f"  Verdict:    {result['verdict']}")
    print(f"  Handoffs:   {', '.join(result['handoffs_found']) or 'none'}")
    print(f"  Activity:   {result['activity_entries']} log entries")
    print(f"  Errors:     {result['errors']}")
    print(f"  Warnings:   {result['warnings']}")
    print()

    for f in result["findings"]:
        icon = {"error": "X", "warning": "!", "info": "-"}.get(f["severity"], "?")
        check = f["check"]
        msg = f["message"]
        extra = f.get("role") or f.get("stage") or f.get("handoff") or ""
        if extra:
            print(f"  [{icon}] {check:25s} {extra:20s} {msg}")
        else:
            print(f"  [{icon}] {check:25s} {msg}")

    if not result["findings"]:
        print("  No issues found.")

    print()
    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
