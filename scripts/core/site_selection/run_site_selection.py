#!/usr/bin/env python3
"""Master orchestrator for site selection & market analysis pipeline.

Runs the full pipeline: brand resolution → POI fetch → trade areas →
demographic enrichment → drive-time population → white space analysis →
candidate generation → scoring → maps → report.

Usage:
    python scripts/core/site_selection/run_site_selection.py \
        --brand "Starbucks" \
        --study-area "Denver, CO" \
        --project-id starbucks-denver-demo

    python scripts/core/site_selection/run_site_selection.py \
        --brand "Chipotle" \
        --bbox "-105.1,39.6,-104.7,39.9" \
        --project-id chipotle-denver \
        --trade-area-mode buffer \
        --top-candidates 15

    python scripts/core/site_selection/run_site_selection.py \
        --brand "Planet Fitness" \
        --study-area-file data/raw/metro_boundary.gpkg \
        --project-id planet-fitness-metro \
        --skip-whitespace
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORE_DIR = PROJECT_ROOT / "scripts" / "core"
SITE_DIR = CORE_DIR / "site_selection"

STATE_ABBREV_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11",
}

# State name → abbreviation for geocoding results
STATE_NAME_TO_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}


def _geocode_study_area(place_name: str):
    """Geocode a place name via Nominatim. Returns (bbox, state_abbrev, display_name)."""
    from urllib.parse import quote
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={quote(place_name)}&format=json&limit=1&addressdetails=1"
    )
    req = Request(url)
    req.add_header("User-Agent", "GIS-Agent-Pipeline/1.0")

    for attempt in range(3):
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                raise ConnectionError(f"Nominatim geocoding failed: {exc}") from exc

    if not data:
        raise ValueError(f"Could not geocode: {place_name}")

    result = data[0]
    bb = result["boundingbox"]  # [south, north, west, east]
    bbox = (float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1]))  # minx,miny,maxx,maxy

    # Extract state from address
    address = result.get("address", {})
    state_name = address.get("state", "")
    state_abbrev = STATE_NAME_TO_ABBREV.get(state_name, "")

    # Fallback: try parsing from place name
    if not state_abbrev:
        for sn, sa in STATE_NAME_TO_ABBREV.items():
            if sn.lower() in place_name.lower():
                state_abbrev = sa
                break
        # Try abbreviation directly
        if not state_abbrev:
            parts = place_name.replace(",", " ").split()
            for p in parts:
                if p.upper() in STATE_ABBREV_TO_FIPS:
                    state_abbrev = p.upper()
                    break

    return bbox, state_abbrev, result.get("display_name", place_name)


def _create_study_area_gpkg(bbox, output_path: Path):
    """Create a GeoPackage with the study area boundary from a bbox."""
    import geopandas as gpd
    from shapely.geometry import box
    geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
    gdf = gpd.GeoDataFrame([{"name": "study_area", "geometry": geom}],
                            geometry="geometry", crs="EPSG:4326")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG")
    return gdf


def _run_step(cmd: list[str], step_name: str) -> int:
    """Run a pipeline step as subprocess. Returns exit code."""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}")
    print(f"  Command: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"  WARNING: {step_name} returned code {result.returncode}")
    return result.returncode


def _generate_maps(
    project_dir: Path,
    brand_name: str,
    brand_gdf,
    competitor_gdf,
    trade_areas_path: Path,
    enriched_path: Path,
    whitespace_path: Path,
    coverage_path: Path,
    candidates_path: Path,
    study_area_gdf,
    top_n: int,
):
    """Generate all 6 pipeline maps with professional cartography.

    Every map includes: contextily basemap, scale bar, north arrow,
    proper styling (edgecolor=#555555, linewidth=0.35), legends,
    150 DPI, figsize=(12,10), facecolor=white.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import geopandas as gpd
    import numpy as np
    import contextily as ctx
    from matplotlib_scalebar.scalebar import ScaleBar

    maps_dir = project_dir / "outputs" / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)

    FIGSIZE = (12, 10)
    DPI = 150
    EDGE = "#555555"
    LW = 0.35
    BASEMAP = ctx.providers.CartoDB.Positron

    def _add_cartographic_elements(ax, title, study_area_name=""):
        """Add basemap, scale bar, north arrow, and title to an axes."""
        try:
            ctx.add_basemap(ax, source=BASEMAP, zoom="auto")
        except Exception as exc:
            print(f"    WARNING: basemap failed ({exc}), continuing without")
        ax.add_artist(ScaleBar(1, units="m", location="lower right",
                               box_alpha=0.7, font_properties={"size": 9}))
        ax.annotate("N", xy=(0.97, 0.15), xycoords="axes fraction",
                    fontsize=14, ha="center", va="center", fontweight="bold",
                    arrowprops=dict(arrowstyle="->", lw=2),
                    xytext=(0.97, 0.05))
        full_title = title
        if study_area_name:
            full_title += f" — {study_area_name}"
        ax.set_title(full_title, fontsize=14, fontweight="bold")
        ax.set_axis_off()

    # Reproject everything to Web Mercator (EPSG:3857) for contextily
    study_3857 = study_area_gdf.to_crs(epsg=3857)
    brand_3857 = brand_gdf.to_crs(epsg=3857) if brand_gdf is not None and len(brand_gdf) > 0 else None
    comp_3857 = competitor_gdf.to_crs(epsg=3857) if competitor_gdf is not None and len(competitor_gdf) > 0 else None

    generated = []

    # --- 1. Locations Overview ---
    try:
        print("  Generating locations_overview.png...")
        fig, ax = plt.subplots(figsize=FIGSIZE)

        study_3857.boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.5,
                                linestyle="--", zorder=3)

        if comp_3857 is not None:
            comp_3857.plot(ax=ax, color="#e74c3c", markersize=40, alpha=0.8,
                          edgecolor=EDGE, linewidth=LW,
                          label="Competitors", zorder=5)

        if brand_3857 is not None:
            brand_3857.plot(ax=ax, color="#27ae60", markersize=60, marker="*",
                           alpha=0.9, edgecolor=EDGE, linewidth=LW,
                           label=brand_name, zorder=6)

        _add_cartographic_elements(ax, f"{brand_name} Locations & Competitors")
        ax.legend(loc="lower left", framealpha=0.9, fontsize=10)
        plt.tight_layout()
        out = maps_dir / "locations_overview.png"
        fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        generated.append(str(out))
        print(f"    Saved: {out}")
    except Exception as exc:
        print(f"    WARNING: locations_overview failed: {exc}")

    # --- 2. Trade Areas ---
    try:
        if trade_areas_path.exists():
            print("  Generating trade_areas_5min.png...")
            import fiona
            layers = fiona.listlayers(trade_areas_path)
            ring_layer = None
            for l in layers:
                if "5" in l or "1mi" in l:
                    ring_layer = l
                    break
            if not ring_layer and layers:
                ring_layer = layers[0]

            if ring_layer:
                ta = gpd.read_file(trade_areas_path, layer=ring_layer).to_crs(epsg=3857)
                fig, ax = plt.subplots(figsize=FIGSIZE)

                study_3857.boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.5,
                                        linestyle="--", zorder=2)
                ta.plot(ax=ax, facecolor="#3498db", alpha=0.2,
                        edgecolor="#2980b9", linewidth=0.8, zorder=4,
                        label=f"Trade Area ({ring_layer})")

                if brand_3857 is not None:
                    brand_3857.plot(ax=ax, color="#27ae60", markersize=30, zorder=6,
                                   edgecolor=EDGE, linewidth=LW, label=brand_name)

                _add_cartographic_elements(ax, f"{brand_name} — Trade Areas ({ring_layer})")
                ax.legend(loc="lower left", framealpha=0.9, fontsize=10)
                plt.tight_layout()
                out = maps_dir / "trade_areas_5min.png"
                fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
                plt.close(fig)
                generated.append(str(out))
                print(f"    Saved: {out}")
    except Exception as exc:
        print(f"    WARNING: trade_areas_5min failed: {exc}")

    # --- 3. Demographic Overview (choropleth on census tracts) ---
    try:
        if enriched_path.exists():
            print("  Generating demographic_overview.png...")
            enriched = gpd.read_file(enriched_path).to_crs(epsg=3857)

            demo_col = None
            for c in ["median_income", "population_density", "total_population"]:
                if c in enriched.columns:
                    demo_col = c
                    break

            if demo_col:
                fig, ax = plt.subplots(figsize=FIGSIZE)

                valid = enriched[enriched[demo_col].notna() & (enriched[demo_col] > 0)]
                if len(valid) > 0:
                    valid.plot(ax=ax, column=demo_col, cmap="YlGnBu",
                              scheme="natural_breaks", k=5,
                              edgecolor=EDGE, linewidth=LW,
                              legend=True,
                              legend_kwds={"fontsize": 9, "loc": "lower right",
                                           "title": demo_col.replace("_", " ").title()},
                              missing_kwds={"color": "#d9d9d9", "label": "No data"},
                              zorder=3)

                # Overlay trade area outlines (not fill)
                if trade_areas_path.exists():
                    import fiona
                    layers = fiona.listlayers(trade_areas_path)
                    for lyr in layers:
                        ta_lyr = gpd.read_file(trade_areas_path, layer=lyr).to_crs(epsg=3857)
                        ta_lyr.boundary.plot(ax=ax, edgecolor="#e74c3c", linewidth=0.6,
                                            linestyle="--", alpha=0.7, zorder=5)

                _add_cartographic_elements(
                    ax, f"Demographic Overview — {demo_col.replace('_', ' ').title()}")
                plt.tight_layout()
                out = maps_dir / "demographic_overview.png"
                fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
                plt.close(fig)
                generated.append(str(out))
                print(f"    Saved: {out}")
    except Exception as exc:
        print(f"    WARNING: demographic_overview failed: {exc}")

    # --- 4. Whitespace Zones ---
    try:
        if whitespace_path.exists() and coverage_path.exists():
            print("  Generating whitespace_zones.png...")
            ws = gpd.read_file(whitespace_path).to_crs(epsg=3857)
            cov = gpd.read_file(coverage_path).to_crs(epsg=3857)

            fig, ax = plt.subplots(figsize=FIGSIZE)

            study_3857.boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.5,
                                    linestyle="--", zorder=2)

            covered = cov[cov["status"] == "covered"] if "status" in cov.columns else cov
            if len(covered) > 0:
                covered.plot(ax=ax, facecolor="#c8e6c9", alpha=0.5,
                            edgecolor=EDGE, linewidth=LW,
                            label="Covered Areas", zorder=3)

            if len(ws) > 0 and "demand_score" in ws.columns:
                ws.plot(ax=ax, column="demand_score", cmap="YlOrRd",
                        edgecolor="#d32f2f", linewidth=0.8,
                        legend=True,
                        legend_kwds={"label": "Demand Score", "shrink": 0.7},
                        zorder=4)

            _add_cartographic_elements(
                ax, f"{brand_name} — White Space Zones (Underserved Areas)")
            ax.legend(loc="lower left", framealpha=0.9, fontsize=10)
            plt.tight_layout()
            out = maps_dir / "whitespace_zones.png"
            fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            generated.append(str(out))
            print(f"    Saved: {out}")
    except Exception as exc:
        print(f"    WARNING: whitespace_zones failed: {exc}")

    # --- 5. Candidate Sites ---
    try:
        if candidates_path.exists():
            print("  Generating candidate_sites.png...")
            cands = gpd.read_file(candidates_path).to_crs(epsg=3857)

            fig, ax = plt.subplots(figsize=FIGSIZE)

            study_3857.boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.5,
                                    linestyle="--", zorder=2)

            if whitespace_path.exists():
                ws = gpd.read_file(whitespace_path).to_crs(epsg=3857)
                if len(ws) > 0:
                    ws.plot(ax=ax, facecolor="#fff9c4", alpha=0.4,
                            edgecolor="#f57f17", linewidth=0.5, zorder=3,
                            label="Whitespace Zones")

            if len(cands) > 0:
                top = cands.head(top_n)
                sizes = 200 - (top["rank"] - 1) * (150 / max(len(top), 1))
                sizes = sizes.clip(lower=30)
                ax.scatter(top.geometry.x, top.geometry.y,
                          s=sizes, c="#d32f2f", edgecolor="white",
                          linewidth=1.5, zorder=7, alpha=0.9, label="Candidates")
                for _, row in top.iterrows():
                    ax.annotate(f"#{int(row['rank'])}",
                               (row.geometry.x, row.geometry.y),
                               fontsize=8, fontweight="bold",
                               ha="center", va="bottom",
                               xytext=(0, 8), textcoords="offset points",
                               zorder=8)

            _add_cartographic_elements(ax, f"{brand_name} — Top {top_n} Candidate Sites")
            ax.legend(loc="lower left", framealpha=0.9, fontsize=10)
            plt.tight_layout()
            out = maps_dir / "candidate_sites.png"
            fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            generated.append(str(out))
            print(f"    Saved: {out}")
    except Exception as exc:
        print(f"    WARNING: candidate_sites failed: {exc}")

    # --- 6. Competitor Density (KDE as imshow with colorbar) ---
    try:
        if comp_3857 is not None and len(comp_3857) >= 3:
            print("  Generating competitor_density.png...")
            from scipy.stats import gaussian_kde

            fig, ax = plt.subplots(figsize=FIGSIZE)

            study_3857.boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.5,
                                    linestyle="--", zorder=2)

            xs = comp_3857.geometry.x.values
            ys = comp_3857.geometry.y.values
            xmin, xmax = xs.min(), xs.max()
            ymin, ymax = ys.min(), ys.max()

            pad_x = (xmax - xmin) * 0.15
            pad_y = (ymax - ymin) * 0.15

            xx, yy = np.mgrid[
                (xmin - pad_x):(xmax + pad_x):200j,
                (ymin - pad_y):(ymax + pad_y):200j,
            ]
            positions = np.vstack([xx.ravel(), yy.ravel()])
            values = np.vstack([xs, ys])

            try:
                kernel = gaussian_kde(values)
                zz = np.reshape(kernel(positions), xx.shape)
                kde_extent = [xmin - pad_x, xmax + pad_x, ymin - pad_y, ymax + pad_y]
                im = ax.imshow(np.rot90(zz), cmap="YlOrRd", alpha=0.65,
                               extent=kde_extent, aspect="auto", zorder=3)
                cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
                cbar.set_label("Competitor locations per km²", fontsize=10)
            except Exception:
                pass  # KDE can fail with collinear points

            comp_3857.plot(ax=ax, color="#333333", markersize=12, alpha=0.8,
                          edgecolor="white", linewidth=0.5, zorder=5,
                          label="Competitors")

            _add_cartographic_elements(ax, f"Competitor Density — {brand_name} Market")
            ax.legend(loc="lower left", framealpha=0.9, fontsize=10)
            plt.tight_layout()
            out = maps_dir / "competitor_density.png"
            fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            generated.append(str(out))
            print(f"    Saved: {out}")
    except Exception as exc:
        print(f"    WARNING: competitor_density failed: {exc}")

    # --- Validate all generated maps ---
    try:
        sys.path.insert(0, str(CORE_DIR))
        from validate_cartography import validate_map
        for png_path_str in generated:
            result = validate_map(Path(png_path_str))
            status = "PASS" if result["passed"] else "FAIL"
            print(f"    [{status}] {Path(png_path_str).name}")
            if not result["passed"]:
                for reason in result["reasons"]:
                    print(f"           {reason}")
                raise RuntimeError(
                    f"Cartographic validation failed for {Path(png_path_str).name}: {result['reasons']}")
    except ImportError:
        print("    WARNING: validate_cartography not available, skipping validation")

    return generated


def _render_report(
    project_dir: Path,
    brand_name: str,
    study_area_name: str,
    brand_count: int,
    competitor_count: int,
    competitor_names: list[str],
    whitespace_count: int,
    candidates_path: Path,
    drivetime_json_path: Path,
    top_n: int,
    trade_area_mode: str,
    bbox: tuple | None,
):
    """Render the site selection report from Jinja2 template."""
    import geopandas as gpd

    template_path = SITE_DIR / "templates" / "site_selection_report.md.j2"
    if not template_path.exists():
        print(f"  WARNING: report template not found: {template_path}")
        return None

    try:
        from jinja2 import Template
    except ImportError:
        print("  WARNING: jinja2 not installed — skipping report")
        return None

    # Load candidates
    candidates = []
    if candidates_path.exists():
        cand_gdf = gpd.read_file(candidates_path)
        for _, row in cand_gdf.head(top_n).iterrows():
            candidates.append({
                "rank": int(row.get("rank", 0)),
                "lat": round(float(row.geometry.y), 5),
                "lon": round(float(row.geometry.x), 5),
                "pop_within_1mi": int(row.get("pop_within_1mi", 0)),
                "income_index": int(round(float(row.get("income_index", 0)))),
                "competitor_count": int(row.get("competitor_count", 0)),
                "demand_score": round(float(row.get("demand_score", 0)), 1),
            })

    # Load drivetime summary
    drivetime_summary = []
    if drivetime_json_path.exists():
        dt_data = json.loads(drivetime_json_path.read_text())
        for loc in dt_data[:5]:  # Top 5
            drivetime_summary.append(loc)

    template = Template(template_path.read_text())
    report = template.render(
        brand_name=brand_name,
        study_area=study_area_name,
        brand_count=brand_count,
        competitor_count=competitor_count,
        competitor_names=competitor_names,
        whitespace_count=whitespace_count,
        candidates=candidates,
        drivetime_summary=drivetime_summary,
        top_n=top_n,
        trade_area_mode=trade_area_mode,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    )

    reports_dir = project_dir / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "site_selection_report.md"
    report_path.write_text(report)
    print(f"  Report: {report_path}")
    return report_path


def _write_qa_scorecard(project_dir: Path, checks: dict) -> Path:
    """Write a QA scorecard for the pipeline run."""
    qa_dir = project_dir / "outputs" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    scorecard = {
        "step": "site_selection_qa",
        "generated_at": datetime.now(UTC).isoformat(),
        "checks": checks,
        "score": sum(v for v in checks.values() if isinstance(v, (int, float))),
        "max_score": 30,
    }
    path = qa_dir / "site_selection_scorecard.json"
    path.write_text(json.dumps(scorecard, indent=2))
    return path


def _write_data_catalog(project_dir: Path, outputs: dict) -> Path:
    """Write data catalog documenting all outputs."""
    catalog = {
        "step": "data_catalog",
        "project_dir": str(project_dir),
        "generated_at": datetime.now(UTC).isoformat(),
        "outputs": outputs,
    }
    catalog_dir = project_dir / "outputs" / "qa"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    path = catalog_dir / "data_catalog.json"
    path.write_text(json.dumps(catalog, indent=2))
    return path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Site selection & market analysis pipeline orchestrator."
    )
    parser.add_argument("--brand", required=True,
                        help="Brand name (resolved via brand_lookup)")
    parser.add_argument("--study-area", default=None,
                        help="Study area as place name (geocoded via Nominatim)")
    parser.add_argument("--bbox", default=None,
                        help="Bounding box: minx,miny,maxx,maxy (EPSG:4326)")
    parser.add_argument("--study-area-file", default=None,
                        help="Study area GeoPackage file path")
    parser.add_argument("--project-id", required=True,
                        help="Project identifier (creates analyses/<project-id>/)")
    parser.add_argument("--trade-area-mode", choices=["buffer", "isochrone"], default="isochrone",
                        help="Trade area method (default: isochrone)")
    parser.add_argument("--travel-times", nargs="+", type=int, default=[5, 10, 15],
                        help="Travel times in minutes (default: 5 10 15)")
    parser.add_argument("--radii", nargs="+", type=float, default=[1, 3, 5],
                        help="Buffer radii in miles for buffer mode (default: 1 3 5)")
    parser.add_argument("--top-candidates", type=int, default=10,
                        help="Number of top candidates to report (default: 10)")
    parser.add_argument("--min-population", type=int, default=5000,
                        help="Minimum population for white space zones (default: 5000)")
    parser.add_argument("--min-separation", type=float, default=0.5,
                        help="Minimum candidate separation in miles (default: 0.5)")
    parser.add_argument("--skip-whitespace", action="store_true",
                        help="Skip white space + candidate generation (market summary only)")
    args = parser.parse_args()

    # Validate study area input
    if not args.study_area and not args.bbox and not args.study_area_file:
        print("ERROR: provide --study-area, --bbox, or --study-area-file")
        return 1

    t0_total = time.time()

    # ---- Setup project directory ----
    project_dir = PROJECT_ROOT / "analyses" / args.project_id
    data_dir = project_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    outputs_dir = project_dir / "outputs"
    maps_dir = outputs_dir / "maps"
    reports_dir = outputs_dir / "reports"
    stats_dir = outputs_dir / "spatial_stats"
    qa_dir = outputs_dir / "qa"
    qgis_dir = outputs_dir / "qgis" / "data"

    for d in [raw_dir, processed_dir, maps_dir, reports_dir, stats_dir, qa_dir, qgis_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Site Selection Pipeline")
    print(f"  Project: {args.project_id}")
    print(f"  Directory: {project_dir}")

    # Track outputs for data catalog
    catalog_outputs = {}
    qa_checks = {}

    # ================================================================
    # STEP 1: Resolve brand
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 1: Brand Resolution")
    print(f"{'='*60}")

    sys.path.insert(0, str(SITE_DIR))
    from brand_lookup import resolve_brand, load_brands

    brands = load_brands()
    brand_result = resolve_brand(args.brand, brands)

    if not brand_result["found"]:
        print(f"WARNING: brand '{args.brand}' not found in lookup table")
        print(f"  Using brand name directly for OSM query")
        brand_entry = {
            "name": args.brand,
            "osm_tags": [["brand", args.brand]],
            "competitors": [],
            "category": "unknown",
        }
    else:
        brand_entry = brand_result["brand"]
        print(f"  Resolved: {brand_entry['name']}")
        print(f"  Category: {brand_entry.get('category', 'unknown')}")
        print(f"  Competitors: {', '.join(brand_entry.get('competitors', []))}")

    brand_name = brand_entry["name"]
    osm_tags = brand_entry["osm_tags"]
    competitor_names = brand_entry.get("competitors", [])

    qa_checks["brand_resolved"] = 3 if brand_result["found"] else 1

    # ================================================================
    # STEP 2: Geocode study area
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 2: Study Area")
    print(f"{'='*60}")

    bbox = None
    state_abbrev = ""
    study_area_name = ""

    if args.study_area_file:
        import geopandas as gpd
        sa_path = Path(args.study_area_file).expanduser().resolve()
        study_area_gdf = gpd.read_file(sa_path)
        study_area_gdf = study_area_gdf.to_crs("EPSG:4326")
        bounds = study_area_gdf.total_bounds
        bbox = (bounds[0], bounds[1], bounds[2], bounds[3])
        study_area_name = sa_path.stem
        print(f"  Loaded study area from file: {sa_path}")
    elif args.bbox:
        parts = [float(x.strip()) for x in args.bbox.split(",")]
        bbox = tuple(parts)
        study_area_name = f"bbox_{args.bbox.replace(',','_')}"
        print(f"  Using provided bbox: {bbox}")
    elif args.study_area:
        print(f"  Geocoding: {args.study_area}")
        bbox, state_abbrev, display_name = _geocode_study_area(args.study_area)
        study_area_name = args.study_area
        print(f"  Resolved: {display_name}")
        print(f"  Bbox: {bbox}")
        print(f"  State: {state_abbrev}")

    # Detect state from bbox if not set
    if not state_abbrev and bbox:
        center_lat = (bbox[1] + bbox[3]) / 2
        center_lon = (bbox[0] + bbox[2]) / 2
        # Simple reverse lookup from center point
        try:
            url = (
                f"https://nominatim.openstreetmap.org/reverse"
                f"?lat={center_lat}&lon={center_lon}&format=json&addressdetails=1"
            )
            req = Request(url)
            req.add_header("User-Agent", "GIS-Agent-Pipeline/1.0")
            with urlopen(req, timeout=10) as resp:
                rdata = json.loads(resp.read().decode())
            sn = rdata.get("address", {}).get("state", "")
            state_abbrev = STATE_NAME_TO_ABBREV.get(sn, "")
        except Exception:
            pass

    if not state_abbrev:
        print("  WARNING: could not determine state — Census enrichment may fail")

    # Create study area GeoPackage
    sa_gpkg = raw_dir / "study_area.gpkg"
    if args.study_area_file:
        import shutil
        shutil.copy2(args.study_area_file, sa_gpkg)
        import geopandas as gpd
        study_area_gdf = gpd.read_file(sa_gpkg)
    else:
        import geopandas as gpd
        study_area_gdf = _create_study_area_gpkg(bbox, sa_gpkg)

    print(f"  Study area saved: {sa_gpkg}")
    qa_checks["study_area"] = 3

    # ================================================================
    # STEP 3: Fetch brand + competitor locations
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 3: Fetch POI Locations")
    print(f"{'='*60}")

    brand_gpkg = raw_dir / f"{brand_name.lower().replace(' ', '_')}.gpkg"
    competitors_gpkg = raw_dir / "competitors.gpkg"
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}" if bbox else ""

    # Build tag args
    tag_args = []
    for tag_pair in osm_tags:
        if len(tag_pair) == 2 and tag_pair[0] != "brand":
            tag_args.extend(["--tag", f"{tag_pair[0]}={tag_pair[1]}"])

    fetch_cmd = [
        sys.executable, str(CORE_DIR / "fetch_poi.py"),
        "--brand", brand_name,
        *tag_args,
        "--output", str(brand_gpkg),
        "--fallback-overpass",
    ]
    if bbox_str:
        fetch_cmd.append(f"--bbox={bbox_str}")
    if competitor_names:
        fetch_cmd.extend(["--competitors", ",".join(competitor_names)])
        fetch_cmd.extend(["--competitors-output", str(competitors_gpkg)])

    rc = _run_step(fetch_cmd, "Fetch brand POI")

    # Load results
    brand_gdf = None
    competitor_gdf = None
    if brand_gpkg.exists():
        brand_gdf = gpd.read_file(brand_gpkg)
        print(f"  Brand locations: {len(brand_gdf)}")
        qa_checks["poi_fetched"] = 3 if len(brand_gdf) > 0 else 0
    else:
        print("  WARNING: brand POI fetch failed")
        qa_checks["poi_fetched"] = 0

    if competitors_gpkg.exists():
        competitor_gdf = gpd.read_file(competitors_gpkg)
        print(f"  Competitor locations: {len(competitor_gdf)}")
    else:
        print("  No competitor locations fetched")

    brand_count = len(brand_gdf) if brand_gdf is not None else 0
    competitor_count = len(competitor_gdf) if competitor_gdf is not None else 0

    catalog_outputs["brand_locations"] = {
        "path": str(brand_gpkg), "count": brand_count, "format": "GPKG"
    }
    catalog_outputs["competitor_locations"] = {
        "path": str(competitors_gpkg), "count": competitor_count, "format": "GPKG"
    }

    if brand_count == 0:
        print("WARNING: no brand locations found — pipeline may produce limited results")

    # ================================================================
    # STEP 4: Compute trade areas
    # ================================================================
    trade_areas_gpkg = processed_dir / "trade_areas.gpkg"

    if brand_count > 0:
        ta_cmd = [
            sys.executable, str(CORE_DIR / "compute_trade_areas.py"),
            "--input", str(brand_gpkg),
            "--mode", args.trade_area_mode,
            "--output", str(trade_areas_gpkg),
        ]
        if args.trade_area_mode == "buffer":
            ta_cmd.extend(["--radii"] + [str(r) for r in args.radii])
        else:
            ta_cmd.extend(["--isochrone-travel-time"] + [str(t) for t in args.travel_times])

        rc = _run_step(ta_cmd, "Compute trade areas")
        qa_checks["trade_areas"] = 3 if trade_areas_gpkg.exists() else 0
    else:
        qa_checks["trade_areas"] = 0

    catalog_outputs["trade_areas"] = {
        "path": str(trade_areas_gpkg), "format": "GPKG",
        "mode": args.trade_area_mode,
    }

    # ================================================================
    # STEP 5: Enrich with demographics
    # ================================================================
    enriched_gpkg = processed_dir / "enriched.gpkg"

    if trade_areas_gpkg.exists() and state_abbrev:
        # Find the outermost layer for enrichment
        import fiona
        layers = fiona.listlayers(trade_areas_gpkg)
        enrich_layer = layers[-1] if layers else None

        if enrich_layer:
            enrich_cmd = [
                sys.executable, str(CORE_DIR / "enrich_points.py"),
                "--trade-areas", str(trade_areas_gpkg),
                "--layer", enrich_layer,
                "--state", state_abbrev,
                "--output", str(enriched_gpkg),
            ]
            rc = _run_step(enrich_cmd, "Enrich with demographics")
            qa_checks["demographics"] = 3 if enriched_gpkg.exists() else 0
        else:
            qa_checks["demographics"] = 0
    else:
        print(f"\n  Skipping enrichment (trade_areas: {trade_areas_gpkg.exists()}, state: {state_abbrev})")
        qa_checks["demographics"] = 0

    catalog_outputs["enriched_demographics"] = {
        "path": str(enriched_gpkg), "format": "GPKG",
    }

    # ================================================================
    # STEP 6: Drive-time population rings
    # ================================================================
    drivetime_gpkg = stats_dir / "drivetime_demographics.gpkg"
    drivetime_json = stats_dir / "drivetime_demographics.json"

    if brand_count > 0 and trade_areas_gpkg.exists() and state_abbrev:
        dt_cmd = [
            sys.executable, str(SITE_DIR / "compute_drivetime_pop.py"),
            "--locations", str(brand_gpkg),
            "--isochrones", str(trade_areas_gpkg),
            "--state", state_abbrev,
            "--travel-times", *[str(t) for t in args.travel_times],
            "--output", str(drivetime_gpkg),
            "--output-json", str(drivetime_json),
        ]
        rc = _run_step(dt_cmd, "Drive-time population")
        qa_checks["drivetime_pop"] = 3 if drivetime_json.exists() else 0
    else:
        qa_checks["drivetime_pop"] = 0

    catalog_outputs["drivetime_demographics"] = {
        "path": str(drivetime_gpkg), "json": str(drivetime_json), "format": "GPKG+JSON",
    }

    # ================================================================
    # STEP 7: White space analysis
    # ================================================================
    whitespace_gpkg = stats_dir / "whitespace_zones.gpkg"
    coverage_gpkg = stats_dir / "whitespace_zones_coverage.gpkg"
    whitespace_count = 0

    if not args.skip_whitespace and trade_areas_gpkg.exists():
        ws_cmd = [
            sys.executable, str(SITE_DIR / "compute_whitespace.py"),
            "--trade-areas", str(trade_areas_gpkg),
            "--study-area", str(sa_gpkg),
            "--min-population", str(args.min_population),
            "--output", str(whitespace_gpkg),
            "--output-coverage", str(coverage_gpkg),
        ]
        if enriched_gpkg.exists():
            ws_cmd.extend(["--demographics", str(enriched_gpkg)])

        rc = _run_step(ws_cmd, "White space analysis")

        if whitespace_gpkg.exists():
            ws_gdf = gpd.read_file(whitespace_gpkg)
            whitespace_count = len(ws_gdf)
            qa_checks["whitespace"] = 3 if whitespace_count > 0 else 1
        else:
            qa_checks["whitespace"] = 0
    else:
        if args.skip_whitespace:
            print("\n  Skipping white space analysis (--skip-whitespace)")
        qa_checks["whitespace"] = 0

    catalog_outputs["whitespace_zones"] = {
        "path": str(whitespace_gpkg), "count": whitespace_count, "format": "GPKG",
    }

    # ================================================================
    # STEP 8: Generate + score candidates
    # ================================================================
    candidates_gpkg = stats_dir / "candidate_sites.gpkg"

    if not args.skip_whitespace and whitespace_gpkg.exists() and whitespace_count > 0:
        cand_cmd = [
            sys.executable, str(SITE_DIR / "generate_candidates.py"),
            "--whitespace", str(whitespace_gpkg),
            "--min-separation", str(args.min_separation),
            "--output", str(candidates_gpkg),
        ]
        if enriched_gpkg.exists():
            cand_cmd.extend(["--demographics", str(enriched_gpkg)])
        if competitors_gpkg.exists():
            cand_cmd.extend(["--competitors", str(competitors_gpkg)])
        if brand_gpkg.exists():
            cand_cmd.extend(["--exclusions", str(brand_gpkg)])

        rc = _run_step(cand_cmd, "Generate candidates")
        qa_checks["candidates"] = 3 if candidates_gpkg.exists() else 0
    else:
        qa_checks["candidates"] = 0

    catalog_outputs["candidate_sites"] = {
        "path": str(candidates_gpkg), "format": "GPKG",
    }

    # ================================================================
    # STEP 9: Generate maps
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 9: Generate Maps")
    print(f"{'='*60}")

    try:
        map_files = _generate_maps(
            project_dir=project_dir,
            brand_name=brand_name,
            brand_gdf=brand_gdf,
            competitor_gdf=competitor_gdf,
            trade_areas_path=trade_areas_gpkg,
            enriched_path=enriched_gpkg,
            whitespace_path=whitespace_gpkg,
            coverage_path=coverage_gpkg,
            candidates_path=candidates_gpkg,
            study_area_gdf=study_area_gdf,
            top_n=args.top_candidates,
        )
        qa_checks["maps"] = min(3, len(map_files))
        catalog_outputs["maps"] = [str(f) for f in map_files]
        print(f"  Generated {len(map_files)} maps")
    except Exception as exc:
        print(f"  WARNING: map generation failed: {exc}")
        qa_checks["maps"] = 0
        map_files = []

    # ================================================================
    # STEP 10: Render report
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 10: Generate Report")
    print(f"{'='*60}")

    report_path = _render_report(
        project_dir=project_dir,
        brand_name=brand_name,
        study_area_name=study_area_name,
        brand_count=brand_count,
        competitor_count=competitor_count,
        competitor_names=competitor_names,
        whitespace_count=whitespace_count,
        candidates_path=candidates_gpkg,
        drivetime_json_path=drivetime_json,
        top_n=args.top_candidates,
        trade_area_mode=args.trade_area_mode,
        bbox=bbox,
    )

    qa_checks["report"] = 3 if report_path and report_path.exists() else 0
    catalog_outputs["report"] = str(report_path) if report_path else None

    # ================================================================
    # STEP 11: QA scorecard
    # ================================================================
    print(f"\n{'='*60}")
    print(f"STEP 11: QA Scorecard")
    print(f"{'='*60}")

    scorecard_path = _write_qa_scorecard(project_dir, qa_checks)
    total_score = sum(v for v in qa_checks.values() if isinstance(v, (int, float)))
    print(f"  Score: {total_score}/30")
    for check, score in qa_checks.items():
        status = "PASS" if score >= 3 else ("PARTIAL" if score > 0 else "FAIL")
        print(f"    {check}: {score}/3 ({status})")
    print(f"  Scorecard: {scorecard_path}")

    # ================================================================
    # STEP 12: Data catalog
    # ================================================================
    catalog_path = _write_data_catalog(project_dir, catalog_outputs)
    print(f"  Data catalog: {catalog_path}")

    # Copy key outputs to QGIS data dir
    for src_name, src in [
        ("brand", brand_gpkg), ("competitors", competitors_gpkg),
        ("trade_areas", trade_areas_gpkg), ("enriched", enriched_gpkg),
        ("whitespace", whitespace_gpkg), ("candidates", candidates_gpkg),
    ]:
        if src.exists():
            import shutil
            dst = qgis_dir / src.name
            shutil.copy2(src, dst)

    elapsed_total = round(time.time() - t0_total, 1)

    # Final summary log
    run_log = {
        "step": "run_site_selection",
        "project_id": args.project_id,
        "brand": brand_name,
        "study_area": study_area_name,
        "state": state_abbrev,
        "trade_area_mode": args.trade_area_mode,
        "brand_locations": brand_count,
        "competitor_locations": competitor_count,
        "whitespace_zones": whitespace_count,
        "candidate_sites": len(gpd.read_file(candidates_gpkg)) if candidates_gpkg.exists() else 0,
        "maps_generated": len(map_files),
        "qa_score": f"{total_score}/30",
        "elapsed_s": elapsed_total,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = project_dir / "run_site_selection.json"
    log_path.write_text(json.dumps(run_log, indent=2))

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Brand: {brand_name}")
    print(f"  Study area: {study_area_name}")
    print(f"  Locations: {brand_count} brand, {competitor_count} competitors")
    print(f"  White space zones: {whitespace_count}")
    print(f"  Maps: {len(map_files)}")
    print(f"  QA score: {total_score}/30")
    print(f"  Elapsed: {elapsed_total}s")
    print(f"  Project dir: {project_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
