from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

from handoff_utils import add_common_handoff_args, build_handoff_provenance

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Write a publishing handoff artifact with publish verification context."
    )
    parser.add_argument("run_id", help="Run identifier for the publishing stage")
    parser.add_argument("summary", help="One-line summary of what was published")
    parser.add_argument(
        "--artifact-files", nargs="*", default=[],
        help="Primary publish artifacts such as project page, web map, or qgis package"
    )
    parser.add_argument(
        "--project-id", help="Project id that was published"
    )
    parser.add_argument(
        "--project-url", help="Expected live or local project URL"
    )
    parser.add_argument(
        "--publish-audit", help="Path to publish audit JSON from publish_site.py"
    )
    parser.add_argument(
        "--source-handoff", help="Path to upstream reporting handoff JSON to reference"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for handoff (default: runs/)"
    )
    parser.add_argument(
        "--arcgis-pro-manifest",
        help="Path to outputs/arcgis/manifest.json produced by package_arcgis_pro.py",
    )
    parser.add_argument(
        "--arcgis-online-status",
        help="Path to outputs/arcgis/publish-status.json produced by publish_arcgis_online.py",
    )
    add_common_handoff_args(parser)
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    audit_summary = None
    if args.publish_audit:
        ap = Path(args.publish_audit).expanduser().resolve()
        if ap.exists():
            try:
                audit = json.loads(ap.read_text())
                audit_summary = {
                    "path": str(ap),
                    "ready_for_human_browsing": audit.get("ready_for_human_browsing"),
                    "verify_url": audit.get("verify_url"),
                    "final_verify": audit.get("final_verify"),
                    "restart_attempted": audit.get("restart_attempted"),
                }
                if not audit.get("ready_for_human_browsing"):
                    warnings.append("publish audit does not mark the project ready for human browsing")
            except Exception:
                warnings.append(f"could not parse publish audit: {args.publish_audit}")
        else:
            warnings.append(f"publish audit not found: {args.publish_audit}")
    else:
        warnings.append("publish audit not provided")

    upstream = None
    if args.source_handoff:
        hp = Path(args.source_handoff).expanduser().resolve()
        if hp.exists():
            try:
                upstream_data = json.loads(hp.read_text())
                upstream = {
                    "run_id": upstream_data.get("run_id", "unknown"),
                    "handoff_type": upstream_data.get("handoff_type", "unknown"),
                    "output_files": upstream_data.get("output_files", []),
                }
            except Exception:
                warnings.append(f"could not parse upstream handoff: {args.source_handoff}")
        else:
            warnings.append(f"upstream handoff not found: {args.source_handoff}")

    ready_for = "peer-review"
    if audit_summary and audit_summary.get("ready_for_human_browsing") is False:
        ready_for = "review"

    # ArcGIS Pro package summary (read from packager's manifest.json if provided)
    arcgis_pro_package: dict | None = None
    if args.arcgis_pro_manifest:
        mp = Path(args.arcgis_pro_manifest).expanduser().resolve()
        if mp.exists():
            try:
                mf = json.loads(mp.read_text())
                files = mf.get("files", [])
                arcgis_pro_package = {
                    "manifest": str(mp),
                    "gdb": next(
                        (f["path"] for f in files
                         if f["path"].startswith("data/") and f["path"].endswith(".gdb/gdb")),
                        "data/project.gdb",
                    ),
                    "lyrx_count": sum(1 for f in files if f.get("category") == "layer"),
                    "chart_count": sum(1 for f in files if f.get("category") == "chart"),
                    "aprx_built": bool(mf.get("arcpy_built_aprx")),
                    "total_size_mb": mf.get("total_size_mb"),
                    "warnings": mf.get("warnings", []),
                }
            except Exception as exc:
                warnings.append(f"could not parse arcgis pro manifest: {exc}")
        else:
            warnings.append(f"arcgis pro manifest not found: {args.arcgis_pro_manifest}")

    # ArcGIS Online publish summary (read from adapter's publish-status.json)
    arcgis_online_publish: dict | None = None
    if args.arcgis_online_status:
        sp = Path(args.arcgis_online_status).expanduser().resolve()
        if sp.exists():
            try:
                ps = json.loads(sp.read_text())
                arcgis_online_publish = {
                    "status_file": str(sp),
                    "status": ps.get("status"),
                    "item_count": len(ps.get("items", [])),
                    "web_map_url": ps.get("web_map_url"),
                    "sharing": (ps.get("request") or {}).get("sharing"),
                    "started_at": ps.get("started_at"),
                    "ended_at": ps.get("ended_at"),
                    "warnings": ps.get("warnings", []),
                    "errors": ps.get("errors", []),
                }
                if ps.get("status") not in (None, "ok", "dry-run"):
                    warnings.append(
                        f"arcgis online publish status: {ps.get('status')} "
                        "(check publish-status.json)"
                    )
            except Exception as exc:
                warnings.append(f"could not parse arcgis online status: {exc}")
        else:
            warnings.append(f"arcgis online status not found: {args.arcgis_online_status}")

    handoff = {
        "handoff_type": "publishing",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "project_id": args.project_id,
        "project_url": args.project_url,
        "artifact_files": args.artifact_files,
        "publish_audit": audit_summary,
        "upstream_handoff": upstream,
        "provenance": build_handoff_provenance(
            args, Path(__file__), output_files=args.artifact_files
        ),
        "warnings": warnings,
        "ready_for": ready_for,
        "notes": args.notes,
    }
    if arcgis_pro_package is not None:
        handoff["arcgis_pro_package"] = arcgis_pro_package
    if arcgis_online_publish is not None:
        handoff["arcgis_online_publish"] = arcgis_online_publish

    out = runs_dir / f"{args.run_id}.publishing-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))
    print(f"wrote publishing handoff -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
