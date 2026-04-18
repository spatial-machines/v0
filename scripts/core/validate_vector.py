from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a vector dataset: CRS, geometry validity, and feature count."
    )
    parser.add_argument("input", help="Path to spatial file (gpkg, shp, geojson)")
    parser.add_argument(
        "--expected-crs",
        help="Expected CRS authority code (e.g. EPSG:4269). Warns if mismatch."
    )
    parser.add_argument(
        "--min-features", type=int, default=1,
        help="Minimum expected feature count (default: 1)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to write JSON result"
    )
    args = parser.parse_args()

    import geopandas as gpd

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    gdf = gpd.read_file(src)
    checks = []
    warnings = []

    # --- CRS check ---
    crs = gdf.crs
    if crs is None:
        checks.append({
            "check": "crs_present",
            "status": "FAIL",
            "message": "no CRS defined on dataset",
        })
    else:
        crs_str = str(crs)
        authority = crs.to_authority()
        crs_label = f"{authority[0]}:{authority[1]}" if authority else crs_str
        checks.append({
            "check": "crs_present",
            "status": "PASS",
            "message": f"CRS: {crs_label}",
            "crs": crs_label,
        })
        if args.expected_crs:
            if crs_label.upper() == args.expected_crs.upper():
                checks.append({
                    "check": "crs_match",
                    "status": "PASS",
                    "message": f"CRS matches expected {args.expected_crs}",
                })
            else:
                checks.append({
                    "check": "crs_match",
                    "status": "WARN",
                    "message": f"CRS {crs_label} != expected {args.expected_crs}",
                })
                warnings.append(f"CRS mismatch: got {crs_label}, expected {args.expected_crs}")

    # --- Feature count ---
    n_features = len(gdf)
    if n_features >= args.min_features:
        checks.append({
            "check": "feature_count",
            "status": "PASS",
            "message": f"{n_features} features (min: {args.min_features})",
            "count": n_features,
        })
    else:
        checks.append({
            "check": "feature_count",
            "status": "FAIL",
            "message": f"{n_features} features < minimum {args.min_features}",
            "count": n_features,
        })

    # --- Geometry validity ---
    null_geom = int(gdf.geometry.isna().sum())
    if null_geom > 0:
        checks.append({
            "check": "geometry_nulls",
            "status": "WARN",
            "message": f"{null_geom} features have null geometry",
            "null_count": null_geom,
        })
        warnings.append(f"{null_geom} null geometries")

    valid_mask = gdf.geometry.dropna().is_valid
    invalid_count = int((~valid_mask).sum())
    valid_count = int(valid_mask.sum())
    if invalid_count == 0:
        checks.append({
            "check": "geometry_validity",
            "status": "PASS",
            "message": f"all {valid_count} non-null geometries are valid",
            "valid": valid_count,
            "invalid": 0,
        })
    else:
        checks.append({
            "check": "geometry_validity",
            "status": "WARN",
            "message": f"{invalid_count} invalid geometries out of {valid_count + invalid_count}",
            "valid": valid_count,
            "invalid": invalid_count,
        })
        warnings.append(f"{invalid_count} invalid geometries")

    # --- Geometry type consistency ---
    geom_types = gdf.geometry.dropna().geom_type.value_counts().to_dict()
    checks.append({
        "check": "geometry_types",
        "status": "PASS",
        "message": f"geometry types: {geom_types}",
        "types": geom_types,
    })

    # --- Summarize ---
    statuses = [c["status"] for c in checks]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "WARN" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    report = {
        "check": "vector_qa",
        "source": str(src),
        "checked_at": datetime.now(UTC).isoformat(),
        "feature_count": n_features,
        "overall_status": overall,
        "checks": checks,
        "warnings": warnings,
    }

    print(f"vector QA [{overall}]: {src.name} — {n_features} features")
    for c in checks:
        print(f"  [{c['status']}] {c['check']}: {c['message']}")

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        print(f"wrote result -> {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
