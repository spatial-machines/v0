#!/usr/bin/env python3
"""Compare two or more GIS analyses with the same methodology side-by-side.

Loads the primary GeoPackage from each project, computes comparable statistics
(mean, median, top-10 features, Moran's I), generates side-by-side small
multiples maps with a shared color scale, and writes a comparison markdown
report and JSON log.

Usage:
    python compare_projects.py \\
        --projects cook_county harris_county \\
        --cols ej_index pm25_percentile poverty_rate \\
        --output-map outputs/comparisons/ej_comparison.png \\
        --output-report outputs/comparisons/ej_comparison.md \\
        [--projects-root outputs/] \\
        [--gpkg-glob "*.gpkg"] \\
        [--id-col NAME] \\
        [--title "Cook County vs Harris County: Environmental Justice Metrics"] \\
        [--weights queen] \\
        [--top-n 10] \\
        [--dpi 200]

Output files:
    <output-map>             — Side-by-side PNG (one panel per project per column)
    <output-report>          — Markdown comparison report
    <output-report>.log.json — JSON log with statistics
"""
import argparse
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # scripts/core -> scripts -> project root


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def find_gpkg(project_dir: Path, gpkg_glob: str = "*.gpkg") -> Path | None:
    """Find the primary GeoPackage in a project directory."""
    # Prefer processed/ subdir
    for subdir in ["data/processed", "processed", "data", "outputs", "."]:
        candidates = sorted((project_dir / subdir).glob(gpkg_glob))
        if candidates:
            return candidates[0]
    return None


def load_project(project_id: str, projects_root: Path, gpkg_glob: str, cols: list[str]) -> dict:
    """Load a single project's GeoDataFrame and validate columns."""
    project_dir = projects_root / project_id
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    gpkg = find_gpkg(project_dir, gpkg_glob)
    if gpkg is None:
        raise FileNotFoundError(f"No GeoPackage found in {project_dir} matching '{gpkg_glob}'")

    gdf = gpd.read_file(gpkg)
    print(f"  {project_id}: loaded {len(gdf)} features from {gpkg.name}")

    # Coerce numeric
    for col in cols:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce")
        else:
            print(f"  WARNING: column '{col}' not found in {project_id} ({gpkg.name})")

    # Load project_brief for title
    brief = {}
    pb = project_dir / "project_brief.json"
    if pb.exists():
        try:
            brief = json.loads(pb.read_text())
        except json.JSONDecodeError:
            pass

    return {
        "id": project_id,
        "gdf": gdf,
        "gpkg": str(gpkg),
        "title": brief.get("project_title", project_id),
        "brief": brief,
    }


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def build_weights(gdf: gpd.GeoDataFrame, kind: str = "queen"):
    """Build spatial weights matrix."""
    from libpysal.weights import Queen, Rook, KNN
    kind = kind.lower()
    if kind == "queen":
        w = Queen.from_dataframe(gdf, silence_warnings=True)
    elif kind == "rook":
        w = Rook.from_dataframe(gdf, silence_warnings=True)
    elif kind.startswith("knn"):
        k = int(kind.replace("knn", "") or "5")
        w = KNN.from_dataframe(gdf, k=k, silence_warnings=True)
    else:
        w = Queen.from_dataframe(gdf, silence_warnings=True)
    w.transform = "R"
    return w


def compute_morans_i(series: pd.Series, gdf: gpd.GeoDataFrame, weights_kind: str) -> dict:
    """Compute Moran's I for a series. Returns dict with I, p, and interpretation."""
    try:
        from esda.moran import Moran
        clean = series.dropna()
        if len(clean) < 10:
            return {"I": None, "p": None, "z": None, "error": "insufficient observations"}
        w = build_weights(gdf.loc[clean.index], weights_kind)
        mi = Moran(clean.values, w)
        return {
            "I": round(float(mi.I), 4),
            "p": round(float(mi.p_sim), 4),
            "z": round(float(mi.z_sim), 4),
            "interpretation": (
                "significant positive spatial autocorrelation" if mi.p_sim < 0.05 and mi.I > 0
                else "significant negative spatial autocorrelation" if mi.p_sim < 0.05 and mi.I < 0
                else "no significant spatial autocorrelation"
            ),
        }
    except Exception as e:
        return {"I": None, "p": None, "z": None, "error": str(e)}


def compute_stats(gdf: gpd.GeoDataFrame, col: str, top_n: int, id_col: str | None,
                  weights_kind: str) -> dict:
    """Compute summary statistics for one column in one project."""
    if col not in gdf.columns:
        return {"error": f"column '{col}' not found"}

    series = pd.to_numeric(gdf[col], errors="coerce").dropna()
    if series.empty:
        return {"error": "all values null"}

    top_idx = series.nlargest(top_n).index
    top_features = []
    for idx in top_idx:
        feature = {"value": round(float(series[idx]), 4), "index": int(idx)}
        if id_col and id_col in gdf.columns:
            feature["name"] = str(gdf.loc[idx, id_col])
        top_features.append(feature)

    mi = compute_morans_i(series, gdf, weights_kind)

    return {
        "n": int(series.count()),
        "n_null": int(pd.to_numeric(gdf[col], errors="coerce").isna().sum()),
        "mean": round(float(series.mean()), 4),
        "median": round(float(series.median()), 4),
        "std": round(float(series.std()), 4),
        "min": round(float(series.min()), 4),
        "max": round(float(series.max()), 4),
        "p25": round(float(series.quantile(0.25)), 4),
        "p75": round(float(series.quantile(0.75)), 4),
        "p90": round(float(series.quantile(0.90)), 4),
        "p95": round(float(series.quantile(0.95)), 4),
        f"top_{top_n}_features": top_features,
        "morans_i": mi,
    }


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def make_comparison_map(
    projects: list[dict],
    cols: list[str],
    output_path: Path,
    dpi: int = 200,
    title: str = "",
) -> None:
    """Generate side-by-side small multiples map.

    Layout: rows = columns (metrics), columns = projects.
    Shared color scale per row (metric), computed from all projects combined.
    """
    n_rows = len(cols)
    n_cols = len(projects)

    fig_width = max(6 * n_cols, 10)
    fig_height = max(5 * n_rows + 1, 6)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("white")

    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes[np.newaxis, :]
    elif n_cols == 1:
        axes = axes[:, np.newaxis]

    cmap = cm.get_cmap("YlOrRd")

    for row_idx, col_name in enumerate(cols):
        # Compute shared vmin/vmax across all projects for this metric
        all_vals = []
        for proj in projects:
            gdf = proj["gdf"]
            if col_name in gdf.columns:
                series = pd.to_numeric(gdf[col_name], errors="coerce").dropna()
                all_vals.extend(series.tolist())

        if not all_vals:
            for col_idx in range(n_cols):
                axes[row_idx, col_idx].set_visible(False)
            continue

        vmin = float(np.percentile(all_vals, 2))
        vmax = float(np.percentile(all_vals, 98))
        if vmin == vmax:
            vmin -= 0.001
            vmax += 0.001

        for col_idx, proj in enumerate(projects):
            ax = axes[row_idx, col_idx]
            ax.set_facecolor("#f5f5f5")
            gdf = proj["gdf"]

            if col_name not in gdf.columns:
                ax.text(0.5, 0.5, f"'{col_name}'\nnot in data",
                        ha="center", va="center", transform=ax.transAxes, color="#999", fontsize=9)
                ax.set_axis_off()
                continue

            gdf_plot = gdf.copy()
            gdf_plot[col_name] = pd.to_numeric(gdf_plot[col_name], errors="coerce")

            gdf_plot.plot(
                column=col_name,
                ax=ax,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                missing_kwds={"color": "#cccccc", "label": "No data"},
                edgecolor="white",
                linewidth=0.15,
            )

            # Boundary outline
            try:
                gdf_plot.dissolve().boundary.plot(ax=ax, edgecolor="#555", linewidth=0.8, zorder=5)
            except Exception:
                pass

            ax.set_axis_off()

            # Column header (project name) on first row
            if row_idx == 0:
                ax.set_title(proj["id"], fontsize=11, fontweight="bold", pad=6)

            # Row label (metric name) on first column
            if col_idx == 0:
                ax.text(-0.04, 0.5, col_name.replace("_", " ").title(),
                        transform=ax.transAxes, rotation=90, va="center", ha="right",
                        fontsize=9, fontweight="bold")

        # Shared colorbar for this row — placed to the right of the last column
        sm = cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar_ax = fig.add_axes([
            axes[row_idx, -1].get_position().x1 + 0.01,
            axes[row_idx, -1].get_position().y0,
            0.012,
            axes[row_idx, -1].get_position().height,
        ])
        fig.colorbar(sm, cax=cbar_ax, label=col_name.replace("_", " ").title())

    # Main title
    main_title = title or " vs ".join(p["id"] for p in projects)
    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=1.01)

    fig.text(0.01, 0.005,
             f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} | Shared color scale per row (2nd–98th pct)",
             fontsize=7, color="#888")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved comparison map: {output_path}")


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def format_morans(mi: dict) -> str:
    if mi.get("I") is None:
        return f"N/A ({mi.get('error', 'unknown')})"
    sig = "✓" if mi.get("p", 1) < 0.05 else "–"
    return f"I={mi['I']:.4f}, p={mi['p']:.4f} {sig}"


def write_comparison_report(
    projects: list[dict],
    cols: list[str],
    stats: dict,  # {project_id: {col: stats_dict}}
    map_path: Path,
    report_title: str,
) -> str:
    """Generate comparison markdown report content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    project_ids = [p["id"] for p in projects]
    project_titles = {p["id"]: p["title"] for p in projects}

    lines = [
        f"# {report_title}",
        "",
        f"*Generated: {now}*",
        "",
        "---",
        "",
        "## Overview",
        "",
    ]

    for pid in project_ids:
        title = project_titles.get(pid, pid)
        n = stats.get(pid, {}).get(cols[0], {}).get("n", "?")
        lines.append(f"- **{pid}**: {title} — {n} census tracts")

    lines += [
        "",
        f"Metrics compared: {', '.join('`' + c + '`' for c in cols)}",
        "",
        "---",
        "",
    ]

    # One section per metric
    for col in cols:
        col_label = col.replace("_", " ").title()
        lines += [
            f"## {col_label}",
            "",
        ]

        # Summary statistics table
        header = "| Statistic | " + " | ".join(project_ids) + " |"
        sep = "|---|" + "---|" * len(project_ids)
        lines += [header, sep]

        stat_rows = [
            ("N (non-null)", "n"),
            ("Mean", "mean"),
            ("Median", "median"),
            ("Std Dev", "std"),
            ("Min", "min"),
            ("Max", "max"),
            ("25th pct", "p25"),
            ("75th pct", "p75"),
            ("90th pct", "p90"),
        ]

        for label, key in stat_rows:
            row = f"| {label} |"
            for pid in project_ids:
                val = stats.get(pid, {}).get(col, {}).get(key, "N/A")
                if isinstance(val, float):
                    val = f"{val:.4f}"
                row += f" {val} |"
            lines.append(row)

        # Moran's I row
        mi_row = "| Moran's I |"
        for pid in project_ids:
            mi = stats.get(pid, {}).get(col, {}).get("morans_i", {})
            mi_row += f" {format_morans(mi)} |"
        lines.append(mi_row)

        lines.append("")

        # Top-N table
        top_key = [k for k in (stats.get(project_ids[0], {}).get(col, {})) if k.startswith("top_")]
        if top_key:
            top_n_key = top_key[0]
            n_val = top_n_key.split("_")[1]
            lines += [
                f"### Top {n_val} Features by {col_label}",
                "",
            ]
            # Build side-by-side top-N
            max_rows = max(
                len(stats.get(pid, {}).get(col, {}).get(top_n_key, []))
                for pid in project_ids
            )
            if max_rows > 0:
                top_header = "| Rank | " + " | ".join(f"{pid} — Value" for pid in project_ids) + " |"
                top_sep = "|---|" + "---|" * len(project_ids)
                lines += [top_header, top_sep]
                for rank in range(max_rows):
                    row = f"| {rank + 1} |"
                    for pid in project_ids:
                        entries = stats.get(pid, {}).get(col, {}).get(top_n_key, [])
                        if rank < len(entries):
                            e = entries[rank]
                            name = e.get("name", f"feature {e.get('index', '?')}")
                            row += f" **{name}**: {e['value']:.4f} |"
                        else:
                            row += " — |"
                    lines.append(row)
                lines.append("")

        # Spatial autocorrelation interpretation
        lines += ["### Spatial Pattern", ""]
        for pid in project_ids:
            mi = stats.get(pid, {}).get(col, {}).get("morans_i", {})
            interp = mi.get("interpretation", "unknown")
            lines.append(f"- **{pid}**: {interp}")
        lines.append("")

        lines.append("---")
        lines.append("")

    # Comparison narrative section
    lines += [
        "## Key Comparisons",
        "",
        "_Auto-generated highlights based on mean and Moran's I differences:_",
        "",
    ]

    for col in cols:
        means = {}
        for pid in project_ids:
            m = stats.get(pid, {}).get(col, {}).get("mean")
            if m is not None:
                means[pid] = m
        if len(means) >= 2:
            sorted_means = sorted(means.items(), key=lambda x: x[1], reverse=True)
            high_pid, high_val = sorted_means[0]
            low_pid, low_val = sorted_means[-1]
            diff = high_val - low_val
            pct_diff = abs(diff / low_val * 100) if low_val != 0 else 0
            col_label = col.replace("_", " ").title()
            lines.append(
                f"- **{col_label}**: {high_pid} has a higher mean ({high_val:.4f}) "
                f"than {low_pid} ({low_val:.4f}) — a {pct_diff:.1f}% difference."
            )

    lines += [
        "",
        "---",
        "",
        "## Map",
        "",
        f"![Comparison Map]({map_path.name})",
        "",
        "_Each row shows one metric; each column shows one project. Color scale is shared per row (2nd–98th percentile range across all projects)._",
        "",
        "---",
        "",
        "## Methodology Notes",
        "",
        "- Statistics computed on non-null values only.",
        "- Moran's I uses Queen contiguity weights with row standardization.",
        "- Top features ranked by raw column value (descending).",
        "- Shared color scale computed from the combined 2nd–98th percentile range across all projects to enable visual comparison.",
        "- This report was generated by `compare_projects.py`.",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--projects", nargs="+", required=True,
                        help="Space-separated project IDs (directory names under --projects-root)")
    parser.add_argument("--cols", nargs="+", required=True,
                        help="Column names to compare across projects")
    parser.add_argument("--output-map", required=True, help="Output PNG path for comparison map")
    parser.add_argument("--output-report", required=True, help="Output markdown report path")
    parser.add_argument("--projects-root", default=None,
                        help="Root directory containing project subdirectories (default: PROJECT_ROOT/analyses)")
    parser.add_argument("--gpkg-glob", default="*.gpkg",
                        help="Glob pattern to find GeoPackage in each project dir (default: *.gpkg)")
    parser.add_argument("--id-col", default=None,
                        help="Column to use as feature name in top-N tables (e.g., NAME, GEOID)")
    parser.add_argument("--title", default=None, help="Report/map title (default: auto-generated)")
    parser.add_argument("--weights", default="queen", help="Spatial weights type (default: queen)")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top features to list (default: 10)")
    parser.add_argument("--dpi", type=int, default=200, help="Map DPI (default: 200)")
    args = parser.parse_args()

    projects_root = Path(args.projects_root).resolve() if args.projects_root else PROJECT_ROOT / "analyses"
    output_map = Path(args.output_map).expanduser().resolve()
    output_report = Path(args.output_report).expanduser().resolve()
    output_log = output_report.with_suffix(".log.json")

    if len(args.projects) < 2:
        print("ERROR: --projects requires at least 2 project IDs")
        return 1

    print(f"Comparing projects: {', '.join(args.projects)}")
    print(f"Metrics: {', '.join(args.cols)}")
    print(f"Projects root: {projects_root}")

    # Load projects
    projects = []
    for pid in args.projects:
        try:
            proj = load_project(pid, projects_root, args.gpkg_glob, args.cols)
            projects.append(proj)
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            return 1

    # Compute statistics
    print("\nComputing statistics...")
    all_stats: dict[str, dict] = {}
    for proj in projects:
        pid = proj["id"]
        gdf = proj["gdf"]
        all_stats[pid] = {}
        for col in args.cols:
            print(f"  {pid} / {col}...")
            all_stats[pid][col] = compute_stats(gdf, col, args.top_n, args.id_col, args.weights)

    # Generate map
    print("\nGenerating comparison map...")
    report_title = args.title or (
        " vs ".join(args.projects) + ": " + ", ".join(c.replace("_", " ").title() for c in args.cols)
    )
    make_comparison_map(
        projects=projects,
        cols=args.cols,
        output_path=output_map,
        dpi=args.dpi,
        title=report_title,
    )

    # Generate markdown report
    print("Writing comparison report...")
    report_md = write_comparison_report(
        projects=projects,
        cols=args.cols,
        stats=all_stats,
        map_path=output_map,
        report_title=report_title,
    )
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(report_md)
    print(f"Saved report: {output_report}")

    # Write JSON log
    log = {
        "step": "compare_projects",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": args.projects,
        "columns": args.cols,
        "projects_root": str(projects_root),
        "output_map": str(output_map),
        "output_report": str(output_report),
        "spatial_weights": args.weights,
        "top_n": args.top_n,
        "title": report_title,
        "statistics": all_stats,
        "gpkg_sources": {p["id"]: p["gpkg"] for p in projects},
    }
    output_log.write_text(json.dumps(log, indent=2))
    print(f"Saved log: {output_log}")

    # Print summary
    print(f"\n{'─' * 60}")
    print(f"Comparison Summary: {report_title}")
    print(f"{'─' * 60}")
    for col in args.cols:
        col_label = col.replace("_", " ").title()
        means = {pid: all_stats[pid][col].get("mean") for pid in args.projects
                 if all_stats[pid][col].get("mean") is not None}
        if means:
            mean_str = " | ".join(f"{pid}: {v:.4f}" for pid, v in means.items())
            print(f"  {col_label}: {mean_str}")
    print(f"{'─' * 60}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
