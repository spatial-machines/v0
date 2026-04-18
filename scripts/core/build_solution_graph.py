#!/usr/bin/env python3
"""Build a 'solution graph' for an analysis — a DAG showing data flow
from input sources through operations to final outputs, per the
autonomous-GIS paradigm established by Ning et al. (2023).

The graph is reconstructed retroactively from the analysis directory:

  Input data:        files in data/raw/ and data/processed/
  Operation nodes:   entries in runs/activity.log (stage_end events) —
                     falls back to inferring operations from output
                     sidecars when no activity log exists
  Intermediate data: processed GeoPackages / CSVs referenced by sidecars
  Output data:       maps, charts, reports, QGIS/ArcGIS packages

Outputs:
  outputs/solution_graph.png        — static, publication-quality
  outputs/solution_graph.svg        — vector, embeddable in HTML reports
  outputs/solution_graph.json       — machine-readable {nodes, edges, meta}
  outputs/solution_graph.mmd        — Mermaid flowchart for docs

No new Python dependencies: matplotlib only.

Usage:
    python scripts/core/build_solution_graph.py analyses/my-project/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


STAGE_ORDER = [
    "intake", "retrieval", "processing", "analysis", "cartography",
    "validation", "reporting", "packaging", "synthesis",
]

ROLE_COLORS = {
    "lead-analyst":    "#6a5acd",
    "data-retrieval":  "#2f7fae",
    "data-processing": "#3e9e7a",
    "spatial-stats":   "#b97a26",
    "cartography":     "#c05353",
    "validation-qa":   "#757575",
    "report-writer":   "#8e5ab2",
    "site-publisher":  "#2f9688",
    "peer-reviewer":   "#777777",
    "unknown":         "#999999",
}

NODE_TYPE_STYLES = {
    # type -> (fill, edge, shape)
    "input":        ("#e8f3ff", "#2f7fae", "box"),
    "intermediate": ("#fff7e0", "#b97a26", "box"),
    "output":       ("#e9f7ec", "#2f9688", "box"),
    "operation":    ("#ffffff", "#444444", "round"),
}


@dataclass
class Node:
    id: str
    label: str
    kind: str            # input | intermediate | output | operation
    role: str = "unknown"
    stage: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""


# ── Discovery ────────────────────────────────────────────────────────

def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _walk_files(root: Path, *exts: str) -> list[Path]:
    out: list[Path] = []
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file() and (not exts or p.suffix.lower() in exts):
            out.append(p)
    return out


def _collect_data_files(analysis_dir: Path) -> tuple[list[Path], list[Path]]:
    raw = _walk_files(analysis_dir / "data" / "raw",
                      ".csv", ".gpkg", ".geojson", ".shp", ".parquet",
                      ".zip", ".tif", ".json", ".xlsx")
    processed = _walk_files(analysis_dir / "data" / "processed",
                            ".csv", ".gpkg", ".geojson", ".parquet")
    return raw, processed


def _collect_outputs(analysis_dir: Path) -> list[Path]:
    out: list[Path] = []
    outputs = analysis_dir / "outputs"
    if not outputs.exists():
        return out
    for subdir, exts in [
        ("maps",    (".png",)),
        ("charts",  (".png",)),
        ("web",     (".html",)),
        ("reports", (".md", ".html", ".pdf")),
    ]:
        out.extend(_walk_files(outputs / subdir, *exts))
    # Packages as single "output" nodes — only when the package is non-empty
    for pkg in ("qgis", "arcgis"):
        pkg_dir = outputs / pkg
        if pkg_dir.exists() and pkg_dir.is_dir():
            has_real_content = any(
                p.is_file() and p.suffix.lower() in (
                    ".qgs", ".qgz", ".gpkg", ".lyrx", ".aprx",
                ) or (p.is_dir() and p.name.endswith(".gdb"))
                for p in pkg_dir.iterdir()
            ) or any(
                p.is_file() for p in pkg_dir.rglob("manifest.json")
            )
            if has_real_content:
                out.append(pkg_dir)
    return out


def _read_activity(analysis_dir: Path) -> list[dict]:
    log = analysis_dir / "runs" / "activity.log"
    if not log.exists():
        return []
    entries = []
    for line in log.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _stage_from_role(role: str) -> str:
    return {
        "lead-analyst":    "intake",
        "data-retrieval":  "retrieval",
        "data-processing": "processing",
        "spatial-stats":   "analysis",
        "cartography":     "cartography",
        "validation-qa":   "validation",
        "report-writer":   "reporting",
        "site-publisher":  "packaging",
        "peer-reviewer":   "validation",
    }.get(role, "")


def _script_role(script: str) -> str:
    s = script.lower()
    if s.startswith("fetch_") or s.startswith("retrieve_"):
        return "data-retrieval"
    if s.startswith("process_") or s.startswith("join_") or s.startswith("batch_join") or s.startswith("derive_") or s.startswith("compute_rate"):
        return "data-processing"
    if s.startswith("analyze_") or s.startswith("compute_"):
        return "spatial-stats"
    if "chart" in s or "choropleth" in s or "hotspot" in s or "bivariate" in s or "cartography" in s or "dot_density" in s or "web_map" in s:
        return "cartography"
    if s.startswith("validate_"):
        return "validation-qa"
    if s.startswith("write_") and "report" in s:
        return "report-writer"
    if "package_" in s:
        return "site-publisher"
    return "unknown"


def _node_id(prefix: str, key: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9_]", "_", key)
    return f"{prefix}__{key}"


# ── Graph construction ──────────────────────────────────────────────

def build_graph(analysis_dir: Path) -> dict:
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    raw_files, proc_files = _collect_data_files(analysis_dir)
    outputs = _collect_outputs(analysis_dir)
    activity = _read_activity(analysis_dir)

    # Pre-compute the set of scripts that appear in the activity log so
    # sidecar-based inference doesn't duplicate what we already know.
    logged_scripts: set[str] = set()
    for e in activity:
        if e.get("event") == "stage_end":
            for s in e.get("scripts_used") or []:
                logged_scripts.add(s)

    # Input data nodes
    for p in raw_files:
        nid = _node_id("input", p.name)
        nodes[nid] = Node(id=nid, label=p.name, kind="input",
                          stage="retrieval",
                          meta={"path": str(p.relative_to(analysis_dir))})

    # Intermediate data nodes (processed)
    for p in proc_files:
        nid = _node_id("inter", p.name)
        nodes[nid] = Node(id=nid, label=p.name, kind="intermediate",
                          stage="processing",
                          meta={"path": str(p.relative_to(analysis_dir))})

    # Output data nodes
    for p in outputs:
        rel = p.relative_to(analysis_dir)
        is_pkg = p.is_dir()
        label = rel.name + ("/" if is_pkg else "")
        nid = _node_id("output", str(rel))
        stage = "packaging" if is_pkg else (
            "cartography" if "maps" in str(rel) or "charts" in str(rel)
            else "reporting" if "reports" in str(rel) or "web" in str(rel)
            else "packaging"
        )
        nodes[nid] = Node(id=nid, label=label, kind="output",
                          stage=stage,
                          meta={"path": str(rel)})

        # Inspect sidecar to link chart/map back to its source gpkg/field
        if p.suffix.lower() == ".png":
            sidecar = p.with_suffix(".style.json")
            sc = _read_json(sidecar)
            if sc:
                src_gpkg = sc.get("source_gpkg")
                if src_gpkg:
                    src_name = Path(src_gpkg).name
                    src_id = _node_id("inter", src_name)
                    if src_id not in nodes:
                        src_id = _node_id("input", src_name)
                    if src_id in nodes:
                        op_id = _infer_operation_for_sidecar(
                            sc, nodes, edges, logged_scripts
                        )
                        if op_id:
                            edges.append(Edge(src=src_id, dst=op_id))
                            edges.append(Edge(src=op_id, dst=nid))
                        else:
                            edges.append(Edge(src=src_id, dst=nid,
                                              label=sc.get("field", "")))
                nodes[nid].role = "cartography"
                nodes[nid].meta["chart_family"] = sc.get("chart_family")
                nodes[nid].meta["map_family"] = sc.get("map_family")

    # Operations + per-stage linkage from activity log
    activity_script_labels: set[str] = set()
    for e in activity:
        if e.get("event") != "stage_end":
            continue
        role = e.get("role", "unknown")
        stage = e.get("stage") or _stage_from_role(role)
        scripts = e.get("scripts_used") or []
        out_paths = e.get("outputs") or []

        # Create one operation node per script (deduped by script within run)
        op_ids_for_run: list[str] = []
        for script in scripts:
            op_id = _node_id("op", f"{role}_{script}_{e.get('run_id','')}")
            if op_id not in nodes:
                nodes[op_id] = Node(
                    id=op_id,
                    label=script,
                    kind="operation",
                    role=role,
                    stage=stage,
                    meta={"run_id": e.get("run_id"),
                          "description": e.get("description", "")},
                )
            op_ids_for_run.append(op_id)
            activity_script_labels.add(script)

        # Link operations to declared outputs. Prefer positional pairing when
        # cardinalities match (common case); otherwise link each output to the
        # single script if there is only one, or fall back to filename
        # heuristics (script stem in output name, or family-based guess).
        output_nodes_for_paths: list[str | None] = []
        for outp in out_paths:
            tail = Path(outp).name
            match = next(
                (nid for nid, n in nodes.items()
                 if n.kind == "output" and Path(n.meta.get("path", "")).name == tail),
                None,
            )
            output_nodes_for_paths.append(match)

        if len(op_ids_for_run) == 1:
            only_op = op_ids_for_run[0]
            for nid in output_nodes_for_paths:
                if nid:
                    edges.append(Edge(src=only_op, dst=nid))
        elif len(op_ids_for_run) == len(out_paths):
            # 1:1 positional pairing
            for op_id, nid in zip(op_ids_for_run, output_nodes_for_paths):
                if nid:
                    edges.append(Edge(src=op_id, dst=nid))
        else:
            # Heuristic: match each output to the script whose stem most
            # resembles the output's filename or its sidecar's family.
            for nid in output_nodes_for_paths:
                if not nid:
                    continue
                best = _best_script_for_output(nid, nodes, op_ids_for_run)
                if best:
                    edges.append(Edge(src=best, dst=nid))

    # Ensure every output has at least one inbound edge by inferring from
    # sidecar or by a best-effort attachment to a matching intermediate.
    _fill_in_missing_edges(nodes, edges)

    meta = {
        "analysis_dir": str(analysis_dir),
        "generated_at": datetime.now(UTC).isoformat(),
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "has_activity_log": bool(activity),
    }
    return {
        "meta": meta,
        "nodes": [asdict(n) for n in nodes.values()],
        "edges": [asdict(e) for e in edges],
    }


def _best_script_for_output(
    output_id: str, nodes: dict[str, Node], op_ids: list[str],
) -> str | None:
    """Pick the operation most likely to have produced a given output.

    Heuristics:
      1. If the output's name contains a script's stem (minus `.py`,
         `analyze_`, `compute_`, etc.), pick that script.
      2. Otherwise fall back to family-based matching via the sidecar
         (e.g. chart_family=distribution -> generate_chart.py or
         any script with 'chart' in its name).
      3. Otherwise the first op (positional fallback).
    """
    if not op_ids:
        return None
    out_node = nodes[output_id]
    out_name = out_node.label.lower()
    for op_id in op_ids:
        script = nodes[op_id].label.lower()
        stem = script.removesuffix(".py")
        for prefix in ("analyze_", "compute_", "fetch_", "retrieve_",
                       "render_", "write_", "package_", "generate_",
                       "build_", "batch_", "derive_", "process_"):
            stem = stem.removeprefix(prefix)
        if stem and stem in out_name:
            return op_id
    # Chart family check
    for op_id in op_ids:
        script = nodes[op_id].label.lower()
        if "chart" in script and "chart" in out_name:
            return op_id
        if "choropleth" in script and "choropleth" in out_name:
            return op_id
        if "web_map" in script and out_name.endswith(".html"):
            return op_id
    return op_ids[0]


def _infer_operation_for_sidecar(
    sidecar: dict, nodes: dict[str, Node], edges: list[Edge],
    logged_scripts: set[str] | None = None,
) -> str | None:
    """Return (or create) an operation node for a sidecar that has no matching
    activity log entry.  Uses map_family / chart_family to guess the producing
    script. Skips inference when the guessed script is already known from the
    activity log — in that case the activity-log operation owns the edge and
    we return None.
    """
    family = sidecar.get("chart_family") or sidecar.get("map_family") or ""
    if family.startswith("chart_"):
        label = "generate_chart.py"
        role = "cartography"
    elif family == "thematic_choropleth":
        label = "analyze_choropleth.py"
        role = "cartography"
    elif family == "thematic_categorical":
        label = "compute_hotspots.py"
        role = "cartography"
    elif family == "point_overlay":
        label = "overlay_points.py"
        role = "cartography"
    elif family == "bivariate_3x3":
        label = "analyze_bivariate.py"
        role = "cartography"
    else:
        return None
    if logged_scripts and label in logged_scripts:
        return None
    op_id = _node_id("op_inf", label)
    if op_id not in nodes:
        nodes[op_id] = Node(id=op_id, label=label, kind="operation",
                            role=role, stage="cartography",
                            meta={"inferred": True})
    return op_id


def _fill_in_missing_edges(nodes: dict[str, Node], edges: list[Edge]) -> None:
    """If an output has no inbound edge, link it to any available
    intermediate whose name appears in a sidecar, or pin it to the first
    input as a last resort so the graph stays connected.
    """
    have_inbound = {e.dst for e in edges}
    # Pick any input node to anchor orphans to
    first_input = next((n.id for n in nodes.values() if n.kind == "input"), None)
    for nid, n in nodes.items():
        if n.kind == "output" and nid not in have_inbound and first_input:
            edges.append(Edge(src=first_input, dst=nid, label="(inferred)"))


# ── Rendering ───────────────────────────────────────────────────────

def render(graph: dict, out_path: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    nodes = graph["nodes"]
    edges = graph["edges"]

    # Layout: columns by stage, rows assigned greedily to avoid overlap
    stage_cols = {stg: i for i, stg in enumerate(STAGE_ORDER)}
    stage_cols[""] = len(STAGE_ORDER)

    node_col: dict[str, int] = {}
    for n in nodes:
        node_col[n["id"]] = stage_cols.get(n["stage"] or "", 0)

    # Group nodes by column, then by kind order (input>operation>intermediate>output)
    kind_rank = {"input": 0, "intermediate": 1, "operation": 2, "output": 3}
    col_to_nodes: dict[int, list[dict]] = {}
    for n in nodes:
        col_to_nodes.setdefault(node_col[n["id"]], []).append(n)
    for col in col_to_nodes:
        col_to_nodes[col].sort(key=lambda n: (kind_rank.get(n["kind"], 4), n["label"]))

    # Assign y positions — each column centers its own stack around y=0
    max_col = max(col_to_nodes) if col_to_nodes else 0
    positions: dict[str, tuple[float, float]] = {}
    col_height = max(len(v) for v in col_to_nodes.values()) if col_to_nodes else 1
    spacing = 1.2  # vertical spacing between node centers
    for col, ns in col_to_nodes.items():
        n_in_col = len(ns)
        for i, n in enumerate(ns):
            # center stack around 0: top node at +((n-1)/2 * spacing), bottom at -((n-1)/2 * spacing)
            y = ((n_in_col - 1) / 2 - i) * spacing
            positions[n["id"]] = (col * 3.6, y)

    # Figure
    y_extent = (col_height - 1) / 2 * spacing + 0.9  # half-height needed to contain tallest column
    w = max(14, (max_col + 1) * 3.6 + 2)
    h = max(7, 2 * y_extent + 2.5)
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(-1.8, (max_col + 1) * 3.6)
    ax.set_ylim(-y_extent - 0.5, y_extent + 1.2)
    ax.set_axis_off()

    # Column headers just above the tallest stack
    header_y = y_extent + 0.6
    for stg, col in stage_cols.items():
        if col in col_to_nodes and stg:
            ax.text(col * 3.6, header_y,
                    stg.upper(), ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="#555555")

    # Edges (draw first so nodes sit on top).
    # Curve cross-column arrows slightly to reduce overlap when many
    # nodes stack in the same column.
    pos = positions
    for e in edges:
        if e["src"] not in pos or e["dst"] not in pos:
            continue
        x1, y1 = pos[e["src"]]
        x2, y2 = pos[e["dst"]]
        col_span = abs(x2 - x1) / 3.6
        # slight curve so edges don't overplot node boxes
        if col_span >= 1 and abs(y2 - y1) < 0.1:
            rad = 0.04
        elif col_span >= 1:
            rad = 0.08 if y2 < y1 else -0.08
        else:
            rad = 0.15 if y2 < y1 else -0.15
        ax.add_patch(FancyArrowPatch(
            (x1 + 1.4, y1), (x2 - 1.4, y2),
            arrowstyle="-|>", mutation_scale=11,
            color="#888888", linewidth=0.85,
            connectionstyle=f"arc3,rad={rad}",
            zorder=1,
        ))
        if e.get("label"):
            ax.text((x1 + x2) / 2 + 1.4, (y1 + y2) / 2 + 0.08,
                    e["label"], fontsize=7, color="#666666",
                    ha="center", va="bottom")

    # Nodes
    for n in nodes:
        x, y = positions[n["id"]]
        fill, edge_c, shape = NODE_TYPE_STYLES[n["kind"]]
        if n["kind"] == "operation":
            edge_c = ROLE_COLORS.get(n["role"], "#444444")
        box = FancyBboxPatch(
            (x - 1.4, y - 0.35), 2.8, 0.7,
            boxstyle=("round,pad=0.08,rounding_size=0.18"
                      if shape == "round" else "round,pad=0.02,rounding_size=0.03"),
            linewidth=1.1, edgecolor=edge_c, facecolor=fill, zorder=2,
        )
        ax.add_patch(box)
        # Label (truncate long filenames)
        label = n["label"]
        if len(label) > 30:
            label = label[:27] + "…"
        ax.text(x, y + 0.02, label, ha="center", va="center",
                fontsize=8, color="#222222", zorder=3)
        # role/kind small tag
        tag = n["role"] if n["kind"] == "operation" else n["kind"]
        ax.text(x, y - 0.23, tag, ha="center", va="center",
                fontsize=6, color="#777777", style="italic", zorder=3)

    # Legend
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=NODE_TYPE_STYLES["input"][0],    edgecolor=NODE_TYPE_STYLES["input"][1],    label="Input data"),
        Patch(facecolor=NODE_TYPE_STYLES["intermediate"][0], edgecolor=NODE_TYPE_STYLES["intermediate"][1], label="Intermediate data"),
        Patch(facecolor=NODE_TYPE_STYLES["operation"][0], edgecolor="#444",                          label="Operation"),
        Patch(facecolor=NODE_TYPE_STYLES["output"][0],   edgecolor=NODE_TYPE_STYLES["output"][1],   label="Output"),
    ]
    ax.legend(handles=legend_handles, loc="lower left",
              frameon=True, framealpha=0.95, edgecolor="#cccccc",
              fontsize=8, ncol=4, bbox_to_anchor=(0.0, -0.02))

    # Title
    ax.set_title(
        f"Solution Graph — {Path(graph['meta']['analysis_dir']).name}",
        fontsize=12, fontweight="bold", color="#222222", loc="left", pad=10,
    )

    png_path = out_path.with_suffix(".png")
    svg_path = out_path.with_suffix(".svg")
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.3)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return {"png": str(png_path), "svg": str(svg_path)}


# ── Mermaid export ──────────────────────────────────────────────────

def to_mermaid(graph: dict) -> str:
    lines = ["```mermaid", "flowchart LR"]
    shape_wrap = {
        "input":        ("([", "])"),
        "intermediate": ("[", "]"),
        "output":       ("(((", ")))"),
        "operation":    ("{{", "}}"),
    }
    for n in graph["nodes"]:
        open_s, close_s = shape_wrap.get(n["kind"], ("[", "]"))
        label = n["label"].replace('"', "'")
        if len(label) > 40:
            label = label[:37] + "…"
        lines.append(f'  {n["id"]}{open_s}"{label}"{close_s}')
    for e in graph["edges"]:
        label = f'|{e.get("label", "")}|' if e.get("label") else ""
        lines.append(f'  {e["src"]} -->{label} {e["dst"]}')
    lines.append("```")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("analysis_dir")
    ap.add_argument("--out", default=None,
                    help="Stem for output files (default: <analysis>/outputs/solution_graph)")
    args = ap.parse_args()

    analysis = Path(args.analysis_dir).resolve()
    stem = Path(args.out) if args.out else (analysis / "outputs" / "solution_graph")
    stem.parent.mkdir(parents=True, exist_ok=True)

    graph = build_graph(analysis)
    (stem.with_suffix(".json")).write_text(json.dumps(graph, indent=2))
    (stem.with_suffix(".mmd")).write_text(to_mermaid(graph))
    render_paths = render(graph, stem)

    print(f"Solution graph for {analysis.name}:")
    print(f"  nodes: {graph['meta']['n_nodes']}")
    print(f"  edges: {graph['meta']['n_edges']}")
    print(f"  png:     {render_paths['png']}")
    print(f"  svg:     {render_paths['svg']}")
    print(f"  json:    {stem.with_suffix('.json')}")
    print(f"  mermaid: {stem.with_suffix('.mmd')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
