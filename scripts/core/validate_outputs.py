from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify that expected output files exist and are non-empty."
    )
    parser.add_argument(
        "files", nargs="+",
        help="Paths to expected output files (relative to project root or absolute)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to write JSON result (default: stdout only)"
    )
    parser.add_argument(
        "--brief",
        help="Path to project_brief.json. When provided, additionally enforce "
             "count minima declared in outputs.required_charts and "
             "outputs.required_maps.",
    )
    parser.add_argument(
        "--charts-dir",
        help="Path to outputs/charts/ (used when --brief sets required_charts)",
    )
    parser.add_argument(
        "--maps-dir",
        help="Path to outputs/maps/ (used when --brief sets required_maps)",
    )
    args = parser.parse_args()

    results = []
    for f in args.files:
        p = Path(f)
        if not p.is_absolute():
            p = PROJECT_ROOT / f
        p = p.resolve()

        entry = {"file": f, "resolved": str(p)}
        if p.exists():
            size = p.stat().st_size
            entry["exists"] = True
            entry["size_bytes"] = size
            if size == 0:
                entry["status"] = "WARN"
                entry["message"] = "file exists but is empty (0 bytes)"
            else:
                entry["status"] = "PASS"
                entry["message"] = f"exists ({size:,} bytes)"
        else:
            entry["exists"] = False
            entry["size_bytes"] = 0
            entry["status"] = "FAIL"
            entry["message"] = "file not found"
        results.append(entry)

    # ── Chart / map count minima from project brief ────────────────────
    if args.brief:
        brief_path = Path(args.brief)
        if not brief_path.is_absolute():
            brief_path = PROJECT_ROOT / args.brief
        try:
            brief = json.loads(brief_path.read_text())
            outputs_cfg = brief.get("outputs", {}) or {}
        except (OSError, json.JSONDecodeError) as exc:
            results.append({
                "file": str(brief_path),
                "status": "WARN",
                "message": f"could not read brief: {exc}",
            })
            outputs_cfg = {}

        def _min_count(key: str) -> int:
            val = outputs_cfg.get(key, [])
            if isinstance(val, list):
                return len(val)
            if isinstance(val, int):
                return val
            return 0

        required_charts = _min_count("required_charts")
        if required_charts > 0:
            charts_dir = (Path(args.charts_dir) if args.charts_dir
                          else (brief_path.parent / "outputs" / "charts"))
            count = len(list(charts_dir.glob("*.png"))) if charts_dir.exists() else 0
            entry = {
                "file": f"{charts_dir}/*.png",
                "status": "PASS" if count >= required_charts else "FAIL",
                "message": (
                    f"{count} chart(s) produced vs. {required_charts} required "
                    f"by project_brief.outputs.required_charts"
                ),
                "chart_count": count,
                "required": required_charts,
            }
            results.append(entry)

        required_maps = _min_count("required_maps")
        if required_maps > 0:
            maps_dir = (Path(args.maps_dir) if args.maps_dir
                        else (brief_path.parent / "outputs" / "maps"))
            count = len(list(maps_dir.glob("*.png"))) if maps_dir.exists() else 0
            entry = {
                "file": f"{maps_dir}/*.png",
                "status": "PASS" if count >= required_maps else "FAIL",
                "message": (
                    f"{count} map(s) produced vs. {required_maps} required "
                    f"by project_brief.outputs.required_maps"
                ),
                "map_count": count,
                "required": required_maps,
            }
            results.append(entry)

    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    if fail_count > 0:
        overall = "FAIL"
    elif warn_count > 0:
        overall = "WARN"
    else:
        overall = "PASS"

    report = {
        "check": "output_existence",
        "checked_at": datetime.now(UTC).isoformat(),
        "total_files": len(results),
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
        "overall_status": overall,
        "results": results,
    }

    print(f"output existence check: {pass_count} pass, {warn_count} warn, {fail_count} fail -> {overall}")
    for r in results:
        tag = r["status"]
        print(f"  [{tag}] {r['file']}: {r['message']}")

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        print(f"wrote result -> {out}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
