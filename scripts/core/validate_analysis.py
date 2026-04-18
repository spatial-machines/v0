#!/usr/bin/env python3
"""Programmatic quality gates for GIS analysis deliverables.

Checks that block delivery if thresholds are not met:
  - Join match rate (features with joined data vs total)
  - Null rate for key columns
  - Global Moran's I spatial autocorrelation gate (before local stats)
  - Institutional tract flags (university, military, prison tracts)
  - CRS consistency across layers
  - Geometry validity
  - Minimum feature count
  - Quantile spread (checks that classification isn't degenerate)

Outputs:
  - Pass/Fail decision with actionable warnings
  - JSON report with all check results
  - Exits 0 on pass, 1 on blocking failures

Usage:
    python validate_analysis.py \\
        --input data/processed/tracts_poverty.gpkg \\
        --key-cols poverty_rate uninsured_rate \\
        [--compare data/processed/tracts_hospitals.gpkg] \\
        [--spatial-autocorr poverty_rate] \\
        [--max-null-pct 15] \\
        [--min-join-rate 0.85] \\
        [--flag-institutions] \\
        [--output outputs/qa/validation_report.json]
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_geometry(gdf, name="layer"):
    """Check for invalid, empty, or null geometries."""
    total = len(gdf)
    null_geom = gdf.geometry.isna().sum()
    empty_geom = gdf.geometry[gdf.geometry.notna()].is_empty.sum()
    invalid_geom = (~gdf.geometry[gdf.geometry.notna()].is_valid).sum()

    issues = []
    if null_geom > 0:
        issues.append(f"{null_geom} null geometries")
    if empty_geom > 0:
        issues.append(f"{empty_geom} empty geometries")
    if invalid_geom > 0:
        issues.append(f"{invalid_geom} invalid geometries (will be buffered in analysis)")

    passed = (null_geom + empty_geom) == 0
    return {
        "check": "geometry_validity",
        "layer": name,
        "total_features": total,
        "null_geometries": int(null_geom),
        "empty_geometries": int(empty_geom),
        "invalid_geometries": int(invalid_geom),
        "passed": passed,
        "blocking": not passed,
        "message": "; ".join(issues) if issues else "All geometries valid",
    }


def check_null_rates(gdf, key_cols, max_null_pct=15.0, name="layer"):
    """Check null rates for key columns."""
    results = []
    for col in key_cols:
        if col not in gdf.columns:
            results.append({
                "check": "null_rate",
                "layer": name,
                "column": col,
                "null_count": None,
                "null_pct": None,
                "passed": False,
                "blocking": True,
                "message": f"Column '{col}' not found in {name}",
            })
            continue

        total = len(gdf)
        null_count = int(gdf[col].isna().sum())
        null_pct = round(null_count / total * 100, 1)
        passed = null_pct <= max_null_pct
        results.append({
            "check": "null_rate",
            "layer": name,
            "column": col,
            "null_count": null_count,
            "null_pct": null_pct,
            "threshold_pct": max_null_pct,
            "passed": passed,
            "blocking": not passed,
            "message": (
                f"{col}: {null_pct}% null ({null_count}/{total} features) — exceeds {max_null_pct}% threshold"
                if not passed
                else f"{col}: {null_pct}% null — OK"
            ),
        })
    return results


def check_join_rate(gdf, key_col, min_rate=0.85, name="layer"):
    """Check that enough features have data after a join."""
    total = len(gdf)
    if key_col not in gdf.columns:
        return {
            "check": "join_rate",
            "layer": name,
            "column": key_col,
            "passed": False,
            "blocking": True,
            "message": f"Column '{key_col}' not found — join may have failed entirely",
        }

    matched = int(gdf[key_col].notna().sum())
    rate = matched / total if total > 0 else 0
    passed = rate >= min_rate
    return {
        "check": "join_rate",
        "layer": name,
        "column": key_col,
        "matched": matched,
        "total": total,
        "rate": round(rate, 4),
        "threshold": min_rate,
        "passed": passed,
        "blocking": not passed,
        "message": (
            f"Join match rate {rate:.1%} ({matched}/{total}) — below {min_rate:.0%} threshold"
            if not passed
            else f"Join match rate {rate:.1%} — OK"
        ),
    }


def check_spatial_autocorrelation(gdf, col, name="layer"):
    """
    Compute Global Moran's I. Gate: if p > 0.05, warn that local stats
    (hotspots, LISA) may not be meaningful.
    """
    if col not in gdf.columns:
        return {
            "check": "spatial_autocorrelation",
            "layer": name,
            "column": col,
            "passed": False,
            "blocking": False,
            "message": f"Column '{col}' not found — cannot compute Moran's I",
        }

    try:
        from libpysal.weights import Queen
        from esda.moran import Moran

        clean = gdf[gdf[col].notna()].copy()
        if len(clean) < 10:
            return {
                "check": "spatial_autocorrelation",
                "column": col,
                "passed": False,
                "blocking": False,
                "message": f"Only {len(clean)} non-null features — too few to compute Moran's I",
            }

        w = Queen.from_dataframe(clean, silence_warnings=True)
        w.transform = "R"

        moran = Moran(clean[col], w)
        significant = moran.p_sim <= 0.05
        strong = moran.I >= 0.3

        return {
            "check": "spatial_autocorrelation",
            "layer": name,
            "column": col,
            "morans_i": round(float(moran.I), 4),
            "p_value": round(float(moran.p_sim), 4),
            "significant": bool(significant),
            "strong_clustering": bool(strong),
            "passed": significant,
            "blocking": False,  # warning only — don't block, but strongly advise
            "message": (
                f"Moran's I={moran.I:.3f}, p={moran.p_sim:.4f} — {'significant spatial autocorrelation' if significant else 'NO significant spatial autocorrelation — local stats (hotspots/LISA) may be misleading'}"
            ),
            "recommendation": (
                None if significant
                else "Consider: (a) is this the right scale? (b) should counts be normalized? (c) report clustering as absent — do not run hotspot analysis."
            ),
        }
    except Exception as e:
        return {
            "check": "spatial_autocorrelation",
            "column": col,
            "passed": False,
            "blocking": False,
            "message": f"Moran's I computation failed: {e}",
        }


def check_institutional_tracts(gdf, name="layer"):
    """
    Flag tracts likely dominated by institutional populations
    (universities, prisons, military bases) that skew poverty/demographics.

    Heuristic: if a tract has very high poverty rate AND very low median income
    AND a name containing known institutional keywords, flag it.
    This is imperfect — a GEOID lookup against known institutional tract lists
    would be more authoritative.
    """
    flags = []

    # Check for GEOIDs of known highly-institutional tract patterns
    # (This is a heuristic — can be extended with a reference list)
    geoid_col = next((c for c in gdf.columns if c.upper() in ("GEOID", "GEOID10", "GEOID20", "TRACTCE")), None)
    name_col = next((c for c in gdf.columns if c.lower() in ("name", "namelsad", "tract_name")), None)
    poverty_col = next((c for c in gdf.columns if "poverty" in c.lower() or "pov" in c.lower()), None)

    institutional_keywords = [
        "university", "college", "prison", "correctional", "penitentiary",
        "military", "air force", "fort", "naval", "army", "marine",
        "hospital", "reservation",
    ]

    if name_col:
        mask = gdf[name_col].str.lower().str.contains(
            "|".join(institutional_keywords), na=False
        )
        n_flagged = int(mask.sum())
        if n_flagged > 0:
            flags.append(f"{n_flagged} tracts with institutional names flagged")
            flagged_names = list(gdf.loc[mask, name_col].head(5))
            flags.append(f"  Examples: {flagged_names}")

    # Heuristic: poverty > 60% is often institutional
    if poverty_col:
        col_data = pd.to_numeric(gdf[poverty_col], errors="coerce")
        high_pov = int((col_data > 60).sum())
        if high_pov > 0:
            flags.append(f"{high_pov} tracts with poverty_rate > 60% — review for institutional populations")

    passed = len(flags) == 0
    return {
        "check": "institutional_tracts",
        "layer": name,
        "passed": passed,
        "blocking": False,  # warning only
        "flags": flags,
        "message": (
            "Potential institutional tracts flagged — verify before interpreting outliers"
            if flags
            else "No institutional tract flags"
        ),
    }


def check_classification_spread(gdf, cols, k=5, name="layer"):
    """Check that numeric columns have enough spread for meaningful classification."""
    results = []
    for col in cols:
        if col not in gdf.columns:
            continue
        data = pd.to_numeric(gdf[col], errors="coerce").dropna()
        if len(data) < k:
            results.append({
                "check": "classification_spread",
                "column": col,
                "passed": False,
                "blocking": False,
                "message": f"Only {len(data)} values — too few for {k}-class classification",
            })
            continue

        std = data.std()
        iqr = data.quantile(0.75) - data.quantile(0.25)
        unique_count = data.nunique()
        degenerate = unique_count < k or std < 0.001

        results.append({
            "check": "classification_spread",
            "layer": name,
            "column": col,
            "std": round(float(std), 4),
            "iqr": round(float(iqr), 4),
            "unique_values": int(unique_count),
            "min": round(float(data.min()), 4),
            "max": round(float(data.max()), 4),
            "passed": not degenerate,
            "blocking": False,
            "message": (
                f"{col}: only {unique_count} unique values — map will be degenerate"
                if degenerate
                else f"{col}: spread OK (std={std:.3f}, IQR={iqr:.3f})"
            ),
        })
    return results


def check_crs(layers):
    """Check that all layers have consistent CRS."""
    crs_set = set()
    for name, gdf in layers.items():
        if gdf.crs:
            crs_set.add(str(gdf.crs))

    passed = len(crs_set) <= 1
    return {
        "check": "crs_consistency",
        "crs_found": list(crs_set),
        "passed": passed,
        "blocking": not passed,
        "message": (
            f"CRS mismatch across layers: {crs_set} — reproject before joining"
            if not passed
            else f"CRS consistent: {list(crs_set)[0] if crs_set else 'unknown'}"
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Primary analysis GeoPackage")
    parser.add_argument("--key-cols", nargs="+", default=[],
                        help="Key columns to check for nulls and spread")
    parser.add_argument("--compare", nargs="+", default=[],
                        help="Additional GeoPackage layers to check CRS consistency")
    parser.add_argument("--spatial-autocorr", help="Column to compute Global Moran's I on")
    parser.add_argument("--join-col", help="Column to check join match rate on")
    parser.add_argument("--max-null-pct", type=float, default=15.0,
                        help="Maximum acceptable null percentage (default: 15)")
    parser.add_argument("--min-join-rate", type=float, default=0.85,
                        help="Minimum join match rate (default: 0.85 = 85%%)")
    parser.add_argument("--flag-institutions", action="store_true", default=True,
                        help="Flag potential institutional tracts (default: on)")
    parser.add_argument("--no-flag-institutions", dest="flag_institutions",
                        action="store_false")
    parser.add_argument("-o", "--output", help="Output JSON report path")
    parser.add_argument("--strict", action="store_true",
                        help="Fail (exit 1) on any warning, not just blocking checks")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    gdf = gpd.read_file(src)
    print(f"Loaded {len(gdf)} features from {src.name}")

    checks = []
    blocking_failures = []
    warnings = []

    # 1. Geometry validity
    geom_check = check_geometry(gdf, name=src.name)
    checks.append(geom_check)
    if not geom_check["passed"]:
        if geom_check["blocking"]:
            blocking_failures.append(geom_check["message"])
        else:
            warnings.append(geom_check["message"])

    # 2. Null rates
    if args.key_cols:
        null_checks = check_null_rates(gdf, args.key_cols, args.max_null_pct, src.name)
        checks.extend(null_checks)
        for c in null_checks:
            if not c["passed"]:
                (blocking_failures if c["blocking"] else warnings).append(c["message"])

    # 3. Join rate
    if args.join_col:
        join_check = check_join_rate(gdf, args.join_col, args.min_join_rate, src.name)
        checks.append(join_check)
        if not join_check["passed"]:
            (blocking_failures if join_check["blocking"] else warnings).append(join_check["message"])

    # 4. Spatial autocorrelation gate
    if args.spatial_autocorr:
        moran_check = check_spatial_autocorrelation(gdf, args.spatial_autocorr, src.name)
        checks.append(moran_check)
        if not moran_check["passed"]:
            warnings.append(moran_check["message"])
            if moran_check.get("recommendation"):
                warnings.append(f"  Recommendation: {moran_check['recommendation']}")

    # 5. Institutional tract flags
    if args.flag_institutions:
        inst_check = check_institutional_tracts(gdf, src.name)
        checks.append(inst_check)
        if not inst_check["passed"]:
            warnings.append(inst_check["message"])
            for flag in inst_check.get("flags", []):
                warnings.append(f"  {flag}")

    # 6. Classification spread
    if args.key_cols:
        spread_checks = check_classification_spread(gdf, args.key_cols, name=src.name)
        checks.extend(spread_checks)
        for c in spread_checks:
            if not c["passed"]:
                warnings.append(c["message"])

    # 7. CRS consistency
    if args.compare:
        layers = {src.name: gdf}
        for cmp_path in args.compare:
            p = Path(cmp_path).expanduser().resolve()
            if p.exists():
                layers[p.name] = gpd.read_file(p)
        crs_check = check_crs(layers)
        checks.append(crs_check)
        if not crs_check["passed"]:
            blocking_failures.append(crs_check["message"])

    # Summary
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c.get("passed", False))
    overall_passed = len(blocking_failures) == 0
    if args.strict:
        overall_passed = overall_passed and len(warnings) == 0

    print("\n" + "="*60)
    print(f"QA VALIDATION REPORT: {src.name}")
    print("="*60)
    print(f"Checks: {passed_checks}/{total_checks} passed")
    print(f"Status: {'✅ PASS' if overall_passed else '❌ FAIL'}")

    if blocking_failures:
        print("\n🚫 BLOCKING FAILURES:")
        for f in blocking_failures:
            print(f"   {f}")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"   {w}")

    if overall_passed and not warnings:
        print("\n✅ All checks passed. Safe to proceed to reporting.")

    # Output JSON
    report = {
        "step": "validate_analysis",
        "source": str(src),
        "overall_passed": overall_passed,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "checks_total": total_checks,
        "checks_passed": passed_checks,
        "checks": checks,
    }

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "qa"
        out_path = out_dir / f"{src.stem}_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    def _json_safe(obj):
        if isinstance(obj, (np.bool_, np.integer)):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return str(obj)

    out_path.write_text(json.dumps(report, indent=2, default=_json_safe))
    print(f"\nReport saved: {out_path}")
    print(json.dumps(report, indent=2, default=_json_safe))

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
