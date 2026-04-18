#!/usr/bin/env python3
"""Write a cartography handoff artifact declaring the maps and charts
produced by the Cartography (Visualization) stage.

Mirrors the shape of `write_publishing_handoff.py`. The handoff is how
downstream agents (validation, reporting, site-publisher) discover:

  - Every static map PNG + its `.style.json` sidecar
  - Every chart PNG + its SVG + sidecar
  - Every interactive Folium HTML
  - Whether the outputs are ready for QGIS and ArcGIS packaging

Auto-discovery: if `--maps-dir` and `--charts-dir` are provided (or
defaulted), the script walks them and picks up sidecars automatically.
Callers can still pass `--map-files` / `--chart-files` to declare
explicit lists instead.

Usage:
    python scripts/core/write_cartography_handoff.py \\
        --run-id cart-001 \\
        --summary "Styled choropleth + paired distribution/top-N charts" \\
        --maps-dir analyses/my-analysis/outputs/maps \\
        --charts-dir analyses/my-analysis/outputs/charts \\
        --web-dir analyses/my-analysis/outputs/web \\
        --output-dir analyses/my-analysis/runs \\
        --source-handoff analyses/my-analysis/runs/an-001.analysis-handoff.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from handoff_utils import add_common_handoff_args, build_handoff_provenance

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"


def _read_sidecar(png_path: Path) -> dict | None:
    sc = png_path.with_suffix(".style.json")
    if not sc.exists():
        return None
    try:
        return json.loads(sc.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _collect_maps(maps_dir: Path) -> list[dict]:
    out: list[dict] = []
    if not maps_dir.exists():
        return out
    for png in sorted(maps_dir.glob("*.png")):
        sc = _read_sidecar(png) or {}
        out.append({
            "path": str(png),
            "sidecar": str(png.with_suffix(".style.json")) if sc else None,
            "family": sc.get("map_family"),
            "field": sc.get("field"),
            "palette": sc.get("palette"),
            "scheme": sc.get("scheme"),
            "k": sc.get("k"),
            "breaks": sc.get("breaks"),
            "title": sc.get("title"),
            "legend_title": sc.get("legend_title"),
        })
    return out


def _collect_charts(charts_dir: Path) -> list[dict]:
    out: list[dict] = []
    if not charts_dir.exists():
        return out
    for png in sorted(charts_dir.glob("*.png")):
        sc = _read_sidecar(png) or {}
        svg = png.with_suffix(".svg")
        out.append({
            "path": str(png),
            "svg": str(svg) if svg.exists() else None,
            "sidecar": str(png.with_suffix(".style.json")) if sc else None,
            "family": sc.get("chart_family"),
            "kind": sc.get("chart_kind"),
            "field": sc.get("field"),
            "pairs_with": sc.get("pairs_with"),  # optional: map path this chart accompanies
            "title": sc.get("title"),
            "palette": sc.get("palette"),
        })
    return out


def _collect_interactive(web_dir: Path) -> list[dict]:
    out: list[dict] = []
    if not web_dir.exists():
        return out
    for html in sorted(web_dir.glob("*.html")):
        out.append({"path": str(html)})
    return out


def _count_by_family(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for it in items:
        fam = it.get("family") or "unknown"
        counts[fam] = counts.get(fam, 0) + 1
    return counts


def _pairing_gaps(maps: list[dict], charts: list[dict]) -> list[str]:
    """Return warnings for the pairing rule. Every thematic_choropleth
    should have at least one distribution and one comparison chart on the
    same field (per CHART_DESIGN_STANDARD.md)."""
    warnings: list[str] = []
    for m in maps:
        if m.get("family") != "thematic_choropleth":
            continue
        field = m.get("field")
        if not field:
            continue
        have_dist = any(c.get("family") == "distribution" and c.get("field") == field
                        for c in charts)
        have_cmp = any(c.get("family") == "comparison" and c.get("field") == field
                       for c in charts)
        if not have_dist:
            warnings.append(
                f"choropleth on {field!r} has no paired distribution chart "
                "(see pairing rule in CHART_DESIGN_STANDARD.md)"
            )
        if not have_cmp:
            warnings.append(
                f"choropleth on {field!r} has no paired comparison chart "
                "(see pairing rule in CHART_DESIGN_STANDARD.md)"
            )
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a cartography stage handoff artifact.",
    )
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument(
        "--summary", default="Cartography stage complete.",
        help="One-line summary",
    )
    parser.add_argument(
        "--maps-dir", default="outputs/maps",
        help="Directory containing map PNGs + sidecars",
    )
    parser.add_argument(
        "--charts-dir", default="outputs/charts",
        help="Directory containing chart PNGs + sidecars",
    )
    parser.add_argument(
        "--web-dir", default="outputs/web",
        help="Directory containing interactive HTML maps",
    )
    parser.add_argument(
        "--map-files", nargs="*", default=None,
        help="Explicit list of map PNGs (overrides --maps-dir discovery)",
    )
    parser.add_argument(
        "--chart-files", nargs="*", default=None,
        help="Explicit list of chart PNGs (overrides --charts-dir discovery)",
    )
    parser.add_argument(
        "--source-handoff",
        help="Path to upstream analysis handoff JSON to reference",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory for handoff (default: runs/)",
    )
    add_common_handoff_args(parser)
    args = parser.parse_args()

    runs_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)

    if args.map_files is not None:
        maps = [
            {"path": p,
             "sidecar": str(Path(p).with_suffix(".style.json"))
                        if Path(p).with_suffix(".style.json").exists() else None,
             **{k: v for k, v in (_read_sidecar(Path(p)) or {}).items()
                if k in ("map_family", "field", "palette", "scheme", "k", "breaks",
                          "title", "legend_title")},
             "family": (_read_sidecar(Path(p)) or {}).get("map_family"),
             }
            for p in args.map_files
        ]
    else:
        maps = _collect_maps(Path(args.maps_dir))

    if args.chart_files is not None:
        charts = [
            {"path": p,
             "svg": str(Path(p).with_suffix(".svg"))
                     if Path(p).with_suffix(".svg").exists() else None,
             "sidecar": str(Path(p).with_suffix(".style.json"))
                        if Path(p).with_suffix(".style.json").exists() else None,
             "family": (_read_sidecar(Path(p)) or {}).get("chart_family"),
             "kind": (_read_sidecar(Path(p)) or {}).get("chart_kind"),
             "field": (_read_sidecar(Path(p)) or {}).get("field"),
             "title": (_read_sidecar(Path(p)) or {}).get("title"),
             }
            for p in args.chart_files
        ]
    else:
        charts = _collect_charts(Path(args.charts_dir))

    interactive = _collect_interactive(Path(args.web_dir))

    warnings = _pairing_gaps(maps, charts)

    upstream = None
    if args.source_handoff:
        hp = Path(args.source_handoff).expanduser().resolve()
        if hp.exists():
            try:
                upstream_data = json.loads(hp.read_text())
                upstream = {
                    "run_id": upstream_data.get("run_id", "unknown"),
                    "handoff_type": upstream_data.get("handoff_type", "unknown"),
                    "recommended_charts": upstream_data.get("recommended_charts", []),
                }
            except Exception as exc:
                warnings.append(f"could not parse upstream handoff: {exc}")
        else:
            warnings.append(f"upstream handoff not found: {args.source_handoff}")

    arcgis_ready = bool(maps) and all(m.get("sidecar") for m in maps)
    qgis_ready = arcgis_ready

    handoff = {
        "handoff_type": "cartography",
        "run_id": args.run_id,
        "summary": args.summary,
        "created_at": datetime.now(UTC).isoformat(),
        "maps": maps,
        "charts": charts,
        "interactive_maps": interactive,
        "map_count": len(maps),
        "chart_count": len(charts),
        "chart_families": _count_by_family(charts),
        "map_families": _count_by_family(maps),
        "arcgis_ready": arcgis_ready,
        "qgis_ready": qgis_ready,
        "warnings": warnings,
        "upstream_handoff": upstream,
        "provenance": build_handoff_provenance(
            args, Path(__file__),
            output_files=[m["path"] for m in maps] + [c["path"] for c in charts],
        ),
        "ready_for": "validation",
        "notes": args.notes,
    }

    out = runs_dir / f"{args.run_id}.cartography-handoff.json"
    out.write_text(json.dumps(handoff, indent=2))
    print(f"wrote cartography handoff -> {out}")
    print(f"  maps: {len(maps)}  charts: {len(charts)}  interactive: {len(interactive)}")
    for w in warnings:
        print(f"  WARN: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
