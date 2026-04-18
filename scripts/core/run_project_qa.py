#!/usr/bin/env python3
"""Score every project against the firm's deliverable spec.

Produces outputs/validation/qa_score.json per project and prints a summary table.

Scoring rubric (100 points total):

  Completeness (40 pts):
    - Has analysis report (md or html, >2000 chars): 10
    - Has >=4 static maps (PNG):                     10
    - Has interactive web map (HTML in outputs/web/): 10
    - Has QGIS package (.qgz or .qgs in outputs/qgis/): 10

  Data quality (30 pts):
    - Has processed GeoPackage(s) in data/processed/: 10
    - Primary GPKG has >=1 numeric column (excl GEOID/FIPS): 10
    - Primary GPKG null rate <20% across numeric cols: 10

  Analysis depth (30 pts):
    - Has summary stats CSV in outputs/tables/: 10
    - Has any validation JSON in outputs/validation/ (excl qa_score.json): 10
    - Has project_brief.json with non-empty hero_question: 10

Usage:
    python scripts/core/run_project_qa.py [--projects p1 p2 ...] [--base-dir .]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# GEOID / FIPS patterns to exclude from numeric column checks
GEOID_PATTERNS = {"geoid", "fips", "statefp", "countyfp", "tractce", "blkgrpce",
                  "state_fips", "county_fips", "geo_id", "affgeoid", "aland", "awater"}

DEFAULT_PROJECTS = [
    "sd-tracts-demo", "ks-healthcare-access", "ks-poverty-health",
    "chicago-food-access", "tx-healthcare-access", "mn-poverty-change",
    "la-environmental-justice", "atl-housing-transit", "omaha-equity-analysis",
    "atl-heat-equity", "starbucks-denver-demo", "maury-river-watershed",
]


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _find_gpkgs(project_dir: Path) -> list[Path]:
    """Find GeoPackage files, preferring data/processed/ then data/."""
    processed = project_dir / "data" / "processed"
    if processed.is_dir():
        gpkgs = sorted(processed.glob("*.gpkg"))
        if gpkgs:
            return gpkgs
    # Fallback: data/ top-level
    data_dir = project_dir / "data"
    if data_dir.is_dir():
        gpkgs = sorted(data_dir.glob("*.gpkg"))
        if gpkgs:
            return gpkgs
    # Last resort: anywhere under the project
    return sorted(project_dir.glob("**/*.gpkg"))[:5]


def _is_numeric_col(name: str) -> bool:
    return name.lower() not in GEOID_PATTERNS and not name.lower().startswith("geometry")


def _check_completeness(project_dir: Path, project_id: str) -> dict:
    items = []
    points = 0

    # 1. Analysis report (md or html, >2000 chars)
    reports_dir = project_dir / "outputs" / "reports"
    has_report = False
    if reports_dir.is_dir():
        for ext in ("*.md", "*.html"):
            for f in reports_dir.glob(ext):
                if f.stat().st_size > 2000:
                    has_report = True
                    break
            if has_report:
                break
    if has_report:
        points += 10
        items.append("analysis_report: PASS")
    else:
        items.append("analysis_report: MISSING or <2000 chars")

    # 2. >=4 static maps (PNG)
    maps_dir = project_dir / "outputs" / "maps"
    png_count = 0
    if maps_dir.is_dir():
        png_count = len(list(maps_dir.glob("*.png")))
    if png_count >= 4:
        points += 10
        items.append(f"static_maps: PASS ({png_count} PNGs)")
    else:
        items.append(f"static_maps: MISSING ({png_count}/4 PNGs)")

    # 3. Interactive web map
    web_dir = project_dir / "outputs" / "web"
    has_web = False
    if web_dir.is_dir():
        has_web = any(web_dir.glob("*.html"))
    if has_web:
        points += 10
        items.append("web_map: PASS")
    else:
        items.append("web_map: MISSING")

    # 4. QGIS package
    qgis_dir = project_dir / "outputs" / "qgis"
    has_qgis = False
    if qgis_dir.is_dir():
        has_qgis = any(qgis_dir.glob("*.qgz")) or any(qgis_dir.glob("*.qgs"))
    if has_qgis:
        points += 10
        items.append("qgis_package: PASS")
    else:
        items.append("qgis_package: MISSING")

    return {"points_earned": points, "points_possible": 40, "items": items}


def _check_data_quality(project_dir: Path) -> dict:
    items = []
    points = 0
    warnings = []

    gpkgs = _find_gpkgs(project_dir)

    # 1. Has processed GeoPackage
    if gpkgs:
        points += 10
        items.append(f"processed_gpkg: PASS ({len(gpkgs)} files)")
    else:
        items.append("processed_gpkg: MISSING")
        return {"points_earned": points, "points_possible": 30, "items": items}

    # Use the largest GPKG as "primary"
    primary = max(gpkgs, key=lambda p: p.stat().st_size)

    try:
        import geopandas as gpd
        gdf = gpd.read_file(primary)
    except Exception as e:
        items.append(f"gpkg_read: ERROR ({e})")
        warnings.append(f"Could not read primary GPKG: {primary.name}")
        return {"points_earned": points, "points_possible": 30, "items": items, "_warnings": warnings}

    # 2. >=1 numeric column (excluding GEOID/FIPS)
    numeric_cols = [
        c for c in gdf.select_dtypes(include=["number"]).columns
        if _is_numeric_col(c)
    ]
    if numeric_cols:
        points += 10
        items.append(f"numeric_columns: PASS ({len(numeric_cols)} cols)")
    else:
        items.append("numeric_columns: MISSING (no non-ID numeric columns)")

    # 3. Null rate <20% across numeric cols
    if numeric_cols:
        total_cells = len(gdf) * len(numeric_cols)
        null_cells = sum(gdf[c].isna().sum() for c in numeric_cols)
        null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0
        if null_pct < 20:
            points += 10
            items.append(f"null_rate: PASS ({null_pct:.1f}%)")
        else:
            items.append(f"null_rate: FAIL ({null_pct:.1f}% nulls)")
            warnings.append(f"Null rate {null_pct:.1f}% exceeds 20% threshold in {primary.name}")
    else:
        items.append("null_rate: SKIP (no numeric columns)")

    result = {"points_earned": points, "points_possible": 30, "items": items}
    if warnings:
        result["_warnings"] = warnings
    return result


def _check_analysis_depth(project_dir: Path, project_id: str) -> dict:
    items = []
    points = 0

    # 1. Summary stats CSV in outputs/tables/
    tables_dir = project_dir / "outputs" / "tables"
    has_csv = False
    if tables_dir.is_dir():
        has_csv = any(tables_dir.glob("*.csv"))
    if has_csv:
        points += 10
        items.append("summary_stats_csv: PASS")
    else:
        items.append("summary_stats_csv: MISSING")

    # 2. Validation JSON in outputs/validation/ (excluding qa_score.json)
    val_dir = project_dir / "outputs" / "validation"
    has_val = False
    if val_dir.is_dir():
        for f in val_dir.glob("*.json"):
            if f.name != "qa_score.json":
                has_val = True
                break
    # Also check outputs/qa/ as some projects use that
    if not has_val:
        qa_dir = project_dir / "outputs" / "qa"
        if qa_dir.is_dir():
            has_val = any(qa_dir.glob("*.json"))
    if has_val:
        points += 10
        items.append("validation_json: PASS")
    else:
        items.append("validation_json: MISSING")

    # 3. project_brief.json with non-empty hero_question
    brief_path = project_dir / "project_brief.json"
    has_hero = False
    if brief_path.is_file():
        try:
            brief = json.loads(brief_path.read_text())
            hero = brief.get("engagement", {}).get("hero_question", "")
            if hero and hero.strip() and hero.strip().lower() not in ("tbd", ""):
                has_hero = True
        except (json.JSONDecodeError, KeyError):
            pass
    if has_hero:
        points += 10
        items.append("hero_question: PASS")
    else:
        items.append("hero_question: MISSING or TBD")

    return {"points_earned": points, "points_possible": 30, "items": items}


def score_project(project_dir: Path, project_id: str) -> dict:
    completeness = _check_completeness(project_dir, project_id)
    data_quality = _check_data_quality(project_dir)
    analysis_depth = _check_analysis_depth(project_dir, project_id)

    total = completeness["points_earned"] + data_quality["points_earned"] + analysis_depth["points_earned"]
    grade = _grade(total)

    # Collect warnings
    warnings = []
    for section in (completeness, data_quality, analysis_depth):
        warnings.extend(section.pop("_warnings", []))

    # Collect missing items
    missing = []
    for section in (completeness, data_quality, analysis_depth):
        for item in section["items"]:
            if "MISSING" in item or "FAIL" in item or "ERROR" in item:
                missing.append(item.split(":")[0].strip())

    result = {
        "project_id": project_id,
        "score": total,
        "grade": grade,
        "breakdown": {
            "completeness": completeness,
            "data_quality": data_quality,
            "analysis_depth": analysis_depth,
        },
        "warnings": warnings,
        "missing": missing,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="QA score all projects against deliverable spec.")
    parser.add_argument("--projects", nargs="*", default=DEFAULT_PROJECTS,
                        help="Project IDs to score (default: all 12)")
    parser.add_argument("--base-dir", default=".", help="GIS agent project root")
    args = parser.parse_args()

    base = Path(args.base_dir).resolve()
    analyses_dir = base / "analyses"

    results = []
    for pid in args.projects:
        pdir = analyses_dir / pid
        if not pdir.is_dir():
            print(f"  SKIP {pid}: directory not found")
            continue
        score = score_project(pdir, pid)
        results.append(score)

        # Write per-project qa_score.json
        val_dir = pdir / "outputs" / "validation"
        val_dir.mkdir(parents=True, exist_ok=True)
        out_path = val_dir / "qa_score.json"
        out_path.write_text(json.dumps(score, indent=2))

    # Print summary table
    print()
    print(f"{'Project':<30} {'Score':>5} {'Grade':>5}  {'Missing'}")
    print("-" * 80)
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        missing_str = ", ".join(r["missing"][:3]) if r["missing"] else "—"
        print(f"{r['project_id']:<30} {r['score']:>5} {r['grade']:>5}  {missing_str}")
    print("-" * 80)

    avg = sum(r["score"] for r in results) / len(results) if results else 0
    print(f"{'Average':<30} {avg:>5.0f} {_grade(int(avg)):>5}")
    print(f"\nScored {len(results)} projects. Results written to outputs/validation/qa_score.json per project.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
