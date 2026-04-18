#!/usr/bin/env python3
"""Score POI site candidates using weighted demographic and competitive factors.

Reads enriched trade area data, normalizes factors, applies weights from a
markdown config file, and produces ranked output with a choropleth map and
markdown report.

Usage:
    python scripts/core/score_sites.py \
        --input data/processed/enriched.gpkg \
        --top-n 10 \
        --output-gpkg outputs/scored_sites.gpkg \
        --output-map outputs/maps/scored_sites.png \
        --output-report outputs/reports/site_selection.md
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_WEIGHTS_PATH = PROJECT_ROOT / "config" / "scoring" / "poi_default_weights.md"


def _parse_weights_md(path: Path) -> list[dict]:
    """Parse scoring weights from a markdown table.

    Returns list of dicts: [{factor, weight, direction, notes}, ...]
    """
    text = path.read_text()
    weights = []

    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            in_table = False
            continue

        if "|" in stripped and "Factor" in stripped and "Weight" in stripped:
            in_table = True
            continue

        # Skip separator row
        if in_table and re.match(r"^\|[-\s|]+\|$", stripped):
            continue

        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 3:
                try:
                    weights.append({
                        "factor": cells[0].strip(),
                        "weight": float(cells[1].strip()),
                        "direction": cells[2].strip().lower(),
                        "notes": cells[3].strip() if len(cells) > 3 else "",
                    })
                except (ValueError, IndexError):
                    continue

    return weights


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Score POI site candidates using weighted factors."
    )
    parser.add_argument("--input", required=True, help="Input enriched GeoPackage")
    parser.add_argument("--weights", default=str(DEFAULT_WEIGHTS_PATH),
                        help="Scoring weights markdown file")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top candidates to highlight")
    parser.add_argument("--output-gpkg", help="Output scored GeoPackage")
    parser.add_argument("--output-map", help="Output choropleth PNG")
    parser.add_argument("--output-report", help="Output markdown report")
    args = parser.parse_args()

    try:
        import geopandas as gpd
        import pandas as pd
        import numpy as np
    except ImportError as exc:
        print(f"ERROR: missing dependency: {exc.name}. Install: pip install geopandas pandas numpy")
        return 1

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: input not found: {src}")
        return 1

    weights_path = Path(args.weights).expanduser().resolve()
    if not weights_path.exists():
        print(f"ERROR: weights file not found: {weights_path}")
        return 1

    print(f"Scoring site candidates")
    print(f"  Input: {src}")
    print(f"  Weights: {weights_path}")

    t0 = time.time()

    # Load data
    gdf = gpd.read_file(src)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    print(f"  Loaded {len(gdf)} candidates")

    if len(gdf) == 0:
        print("ERROR: no candidates in input")
        return 1

    # Parse weights
    weights = _parse_weights_md(weights_path)
    if not weights:
        print("ERROR: no valid weights found in config")
        return 1

    weight_sum = sum(w["weight"] for w in weights)
    print(f"  Weights ({len(weights)} factors, sum={weight_sum:.2f}):")
    for w in weights:
        print(f"    {w['factor']}: {w['weight']} ({w['direction']})")

    if abs(weight_sum - 1.0) > 0.01:
        print(f"WARNING: weights sum to {weight_sum:.2f}, not 1.0 — normalizing")
        for w in weights:
            w["weight"] /= weight_sum

    # Ensure factor columns exist — compute placeholders for missing ones
    for w in weights:
        factor = w["factor"]
        if factor not in gdf.columns:
            if factor == "competitor_density":
                print(f"  NOTE: '{factor}' not in data — defaulting to 0 (no competitor data)")
                gdf[factor] = 0.0
            elif factor == "gap_to_nearest":
                print(f"  NOTE: '{factor}' not in data — defaulting to median distance")
                gdf[factor] = 5.0  # neutral default km
            else:
                print(f"  WARNING: factor '{factor}' not found in data — skipping")

    # Normalize each factor 0-1 (min-max)
    for w in weights:
        factor = w["factor"]
        if factor not in gdf.columns:
            continue

        vals = pd.to_numeric(gdf[factor], errors="coerce")
        vmin, vmax = vals.min(), vals.max()

        if vmin == vmax:
            # All same value — normalize to 0.5
            gdf[f"{factor}_norm"] = 0.5
        else:
            normalized = (vals - vmin) / (vmax - vmin)
            # Invert for "lower = better" factors
            if w["direction"] == "lower":
                normalized = 1.0 - normalized
            gdf[f"{factor}_norm"] = normalized

    # Compute weighted score
    gdf["site_score"] = 0.0
    for w in weights:
        factor = w["factor"]
        norm_col = f"{factor}_norm"
        if norm_col in gdf.columns:
            gdf["site_score"] += gdf[norm_col].fillna(0) * w["weight"]

    gdf["site_score"] = (gdf["site_score"] * 100).round(1)

    # Rank
    gdf = gdf.sort_values("site_score", ascending=False).reset_index(drop=True)
    gdf["rank"] = range(1, len(gdf) + 1)

    top_n = gdf.head(args.top_n)
    print(f"\n  Top {args.top_n} candidates:")
    for _, row in top_n.iterrows():
        name = row.get("name", row.get("brand", f"Site {row['rank']}"))
        city = row.get("addr_city", "")
        loc = f" ({city})" if city else ""
        print(f"    #{row['rank']}: {name}{loc} — score {row['site_score']}")

    elapsed = round(time.time() - t0, 2)

    # Write scored GeoPackage
    if args.output_gpkg:
        gpkg_path = Path(args.output_gpkg).expanduser().resolve()
        gpkg_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(gpkg_path, driver="GPKG")
        print(f"\n  Scored GeoPackage: {gpkg_path}")

    # Generate choropleth map
    if args.output_map:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.colors import Normalize
            from matplotlib.cm import ScalarMappable

            map_path = Path(args.output_map).expanduser().resolve()
            map_path.parent.mkdir(parents=True, exist_ok=True)

            fig, ax = plt.subplots(1, 1, figsize=(14, 10))
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")

            # Plot all candidates colored by score
            gdf.plot(
                column="site_score",
                ax=ax,
                cmap="RdYlGn",
                legend=True,
                legend_kwds={
                    "label": "Site Score (0-100)",
                    "shrink": 0.6,
                    "orientation": "horizontal",
                    "pad": 0.05,
                },
                edgecolor="#33333344",
                linewidth=0.5,
            )

            # Highlight top-N with markers at centroids
            top_centroids = top_n.geometry.centroid
            ax.scatter(
                top_centroids.x, top_centroids.y,
                c="red", s=80, zorder=10, edgecolors="white", linewidth=1.5,
                label=f"Top {args.top_n}",
            )
            for _, row in top_n.iterrows():
                c = row.geometry.centroid
                ax.annotate(
                    f"#{row['rank']}",
                    xy=(c.x, c.y),
                    fontsize=7, fontweight="bold", color="darkred",
                    ha="center", va="bottom",
                    xytext=(0, 6), textcoords="offset points",
                )

            ax.set_title("POI Site Selection Scores", fontsize=16, fontweight="bold", pad=16)
            ax.set_axis_off()
            ax.legend(loc="upper right", fontsize=9)
            fig.tight_layout()
            fig.savefig(map_path, dpi=200, bbox_inches="tight")
            plt.close(fig)
            print(f"  Map: {map_path}")
        except ImportError:
            print("  WARNING: matplotlib not available — skipping map output")
        except Exception as exc:
            print(f"  WARNING: map generation failed: {exc}")

    # Generate markdown report
    if args.output_report:
        report_path = Path(args.output_report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# POI Site Selection Report",
            f"",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Candidates:** {len(gdf)}",
            f"**Scoring factors:** {len(weights)}",
            f"",
            f"## Scoring Weights",
            f"",
            f"| Factor | Weight | Direction |",
            f"|--------|--------|-----------|",
        ]
        for w in weights:
            lines.append(f"| {w['factor']} | {w['weight']:.2f} | {w['direction']} |")

        lines += [
            f"",
            f"## Top {args.top_n} Candidates",
            f"",
        ]

        # Build header for top-N table
        table_cols = ["Rank", "Name", "City", "Score"]
        demo_cols = [w["factor"] for w in weights if w["factor"] in gdf.columns]
        table_cols.extend(demo_cols)
        lines.append("| " + " | ".join(table_cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(table_cols)) + " |")

        for _, row in top_n.iterrows():
            name = row.get("name", row.get("brand", "—"))
            city = row.get("addr_city", "—")
            vals = [str(int(row["rank"])), str(name), str(city), f"{row['site_score']:.1f}"]
            for dc in demo_cols:
                v = row.get(dc)
                if pd.isna(v):
                    vals.append("N/A")
                elif isinstance(v, float):
                    vals.append(f"{v:,.1f}")
                else:
                    vals.append(str(v))
            lines.append("| " + " | ".join(vals) + " |")

        lines += [
            f"",
            f"## Score Distribution",
            f"",
            f"- **Mean:** {gdf['site_score'].mean():.1f}",
            f"- **Median:** {gdf['site_score'].median():.1f}",
            f"- **Std Dev:** {gdf['site_score'].std():.1f}",
            f"- **Min:** {gdf['site_score'].min():.1f}",
            f"- **Max:** {gdf['site_score'].max():.1f}",
            f"",
            f"## Methodology",
            f"",
            f"1. Factors normalized 0-1 using min-max scaling",
            f"2. 'Lower is better' factors inverted (1 - normalized)",
            f"3. Weighted sum multiplied by 100",
            f"4. Candidates ranked by final score (higher = better site)",
            f"",
        ]

        report_path.write_text("\n".join(lines))
        print(f"  Report: {report_path}")

    # JSON log
    log = {
        "step": "score_sites",
        "input": str(src),
        "n_candidates": len(gdf),
        "top_n": args.top_n,
        "weights_used": {w["factor"]: w["weight"] for w in weights},
        "top_10_scores": [
            {"rank": int(r["rank"]), "name": r.get("name", ""), "score": float(r["site_score"])}
            for _, r in top_n.iterrows()
        ],
        "score_stats": {
            "mean": round(float(gdf["site_score"].mean()), 1),
            "median": round(float(gdf["site_score"].median()), 1),
            "std": round(float(gdf["site_score"].std()), 1),
            "min": round(float(gdf["site_score"].min()), 1),
            "max": round(float(gdf["site_score"].max()), 1),
        },
        "output_gpkg": args.output_gpkg,
        "output_map": args.output_map,
        "output_report": args.output_report,
        "elapsed_s": elapsed,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    # Write log next to gpkg if available, else next to input
    if args.output_gpkg:
        log_path = Path(args.output_gpkg).expanduser().resolve().with_suffix(".score.json")
    else:
        log_path = src.with_suffix(".score.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  Log: {log_path}")
    print(f"  Elapsed: {elapsed}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
