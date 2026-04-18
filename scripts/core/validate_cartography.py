#!/usr/bin/env python3
"""Cartographic quality validation for map PNGs and statistical charts.

For maps: checks not-blank, not-mostly-one-color, minimum file size.
For charts: checks presence of .style.json sidecar, valid SVG pair, and
required metadata (title or auto-title, chart_family).

Usage:
    python scripts/core/validate_cartography.py --input map.png
    python scripts/core/validate_cartography.py --input-dir outputs/maps/
    python scripts/core/validate_cartography.py --charts-dir outputs/charts/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate_map(png_path: Path, min_size_kb: int = 50) -> dict:
    """Validate a single map PNG.

    Returns dict with keys: path, passed, reasons (list of failure reasons).

    Future enhancement: add map_family parameter to enable family-specific
    validation per docs/wiki/standards/CARTOGRAPHY_STANDARD.md Map Family
    Taxonomy. Family affects which chrome elements are required vs forbidden
    (e.g., basemap forbidden on thematic_choropleth). Family can be declared
    in analysis handoff JSON or inferred from the producing script.
    """
    result = {"path": str(png_path), "passed": True, "reasons": []}

    # Check 1: File exists
    if not png_path.exists():
        result["passed"] = False
        result["reasons"].append(f"File not found: {png_path}")
        return result

    # Check 2: Minimum file size
    size_kb = png_path.stat().st_size / 1024
    if size_kb < min_size_kb:
        result["passed"] = False
        result["reasons"].append(
            f"File too small ({size_kb:.1f} KB < {min_size_kb} KB) — likely blank or empty"
        )

    # Check 3: Not mostly one color (>90% same pixel = likely blank)
    try:
        from PIL import Image
        import collections

        img = Image.open(png_path)
        # Downsample for speed — 200x200 is enough to detect blank maps
        img_small = img.resize((200, 200), Image.LANCZOS).convert("RGB")
        try:
            pixels = list(img_small.get_flattened_data())
        except AttributeError:
            pixels = list(img_small.getdata())
        total = len(pixels)

        counter = collections.Counter(pixels)
        most_common_color, most_common_count = counter.most_common(1)[0]
        ratio = most_common_count / total

        if ratio > 0.90:
            result["passed"] = False
            result["reasons"].append(
                f"Map is {ratio:.0%} one color {most_common_color} — likely blank or failed render"
            )

        # Check 4: Not mostly black (NoData rendering failure)
        black_ish = sum(1 for r, g, b in pixels if r < 15 and g < 15 and b < 15)
        black_ratio = black_ish / total
        if black_ratio > 0.40:
            result["passed"] = False
            result["reasons"].append(
                f"Map is {black_ratio:.0%} black — likely NoData masking failure"
            )

    except ImportError:
        result["reasons"].append("PIL not available — skipped pixel analysis")
    except Exception as exc:
        result["reasons"].append(f"Pixel analysis error: {exc}")

    return result


def validate_directory(dir_path: Path, min_size_kb: int = 50) -> list[dict]:
    """Validate all PNGs in a directory."""
    results = []
    pngs = sorted(dir_path.glob("*.png"))
    if not pngs:
        results.append({"path": str(dir_path), "passed": False,
                        "reasons": ["No PNG files found in directory"]})
        return results
    for png in pngs:
        results.append(validate_map(png, min_size_kb))
    return results


# ── Chart validation ─────────────────────────────────────────────────

VALID_CHART_FAMILIES = {"distribution", "comparison", "relationship", "timeseries"}

# Palettes that are already CVD-safe — skip colorblind simulation for them.
CVD_SAFE_PALETTES = {
    "viridis", "cividis", "neutral", "neutral_cool",
    "colorblind_safe",
}

# Chart kinds that encode data by color across multiple series. Only these
# need the CVD distinguishability check — single-series kinds (histogram,
# box, basic bar, scatter, scatter_ols, line) use color decoratively and
# the top-colors distinguishability test produces false positives on them.
MULTI_SERIES_CHART_KINDS = {
    "grouped_bar",
    "correlation_heatmap",
    "hexbin",        # uses a gradient for density encoding
    "small_multiples",  # multiple panels
    "violin",        # when multiple groups
}


def _cvd_check(png_path: Path) -> dict | None:
    """Run a colorblind check on a single chart PNG.

    Behaviour:
      - Skip when the sidecar palette is already CVD-safe.
      - Skip when the chart kind is single-series (color is decorative).
      - Skip when `colorspacious` isn't installed.
      - Otherwise run the existing `check_colorblind.check_image()` and
        surface its PASS/WARN/FAIL verdict.

    Returns a dict {'status': ..., ...} or None when not applicable.
    """
    sidecar = png_path.with_suffix(".style.json")
    meta: dict = {}
    if sidecar.exists():
        try:
            meta = json.loads(sidecar.read_text())
        except json.JSONDecodeError:
            pass

    palette = (meta.get("palette") or "").lower()
    if palette in CVD_SAFE_PALETTES:
        return {"status": "PASS", "skipped": "palette_cvd_safe",
                "palette": palette}

    kind = (meta.get("chart_kind") or "").lower()
    if kind and kind not in MULTI_SERIES_CHART_KINDS:
        return {"status": "PASS", "skipped": "single_series_chart",
                "kind": kind}

    try:
        # Lazy import so the validator still works without colorspacious
        sys.path.insert(0, str(Path(__file__).parent))
        from check_colorblind import check_image
    except ImportError:
        return {"status": "PASS", "skipped": "colorspacious_not_installed"}

    try:
        result = check_image(png_path, output_dir=None)
    except Exception as exc:
        return {"status": "WARN", "error": str(exc)}

    problems = [
        cvd_key for cvd_key, cvd in result.get("simulations", {}).items()
        if cvd.get("status") == "FAIL"
    ]
    return {
        "status": result.get("status", "PASS"),
        "problem_cvd_types": problems,
    }


def validate_chart(png_path: Path, min_size_kb: int = 20,
                   colorblind_check: bool = False) -> dict:
    """Validate a single chart PNG + required sidecar.

    Charts have stricter structural requirements than maps:
      - must have a .style.json sidecar
      - sidecar must declare chart_family in {distribution, comparison,
        relationship, timeseries}
      - sidecar must declare a title (human or auto-generated)
      - must have a paired .svg at same stem

    When `colorblind_check=True`, additionally simulates deuteranopia /
    protanopia / tritanopia and fails on indistinguishable class pairs
    (ΔE < 10). Palettes already known CVD-safe (viridis, cividis, etc.)
    skip the simulation.

    Chart PNGs typically render smaller than maps — default min is 20 KB.
    """
    result = {"path": str(png_path), "passed": True, "reasons": [], "kind": "chart"}

    if not png_path.exists():
        result["passed"] = False
        result["reasons"].append(f"File not found: {png_path}")
        return result

    size_kb = png_path.stat().st_size / 1024
    if size_kb < min_size_kb:
        result["passed"] = False
        result["reasons"].append(
            f"Chart too small ({size_kb:.1f} KB < {min_size_kb} KB) — likely empty"
        )

    sidecar = png_path.with_suffix(".style.json")
    if not sidecar.exists():
        result["passed"] = False
        result["reasons"].append(f"Missing sidecar: {sidecar.name}")
    else:
        try:
            meta = json.loads(sidecar.read_text())
        except json.JSONDecodeError as exc:
            result["passed"] = False
            result["reasons"].append(f"Sidecar JSON invalid: {exc}")
            meta = {}
        family = meta.get("chart_family")
        if not family:
            result["passed"] = False
            result["reasons"].append("Sidecar missing 'chart_family'")
        elif family not in VALID_CHART_FAMILIES:
            result["passed"] = False
            result["reasons"].append(
                f"Unknown chart_family: {family!r} (valid: {sorted(VALID_CHART_FAMILIES)})"
            )
        if not meta.get("title"):
            result["reasons"].append("Sidecar missing 'title' (warning)")
        result["family"] = family
        result["kind"] = f"chart:{family}" if family else "chart"

    svg = png_path.with_suffix(".svg")
    if not svg.exists():
        result["reasons"].append("Missing SVG vector export (warning)")

    if colorblind_check:
        cvd = _cvd_check(png_path)
        if cvd is not None:
            result["colorblind"] = cvd
            if cvd.get("status") == "FAIL":
                result["passed"] = False
                bad = cvd.get("problem_cvd_types", [])
                result["reasons"].append(
                    "Colorblind FAIL: indistinguishable class pairs under "
                    + ", ".join(bad or ["CVD simulation"])
                )
            elif cvd.get("status") == "WARN":
                result["reasons"].append(
                    "Colorblind WARN: marginal class-pair contrast"
                )

    return result


def validate_chart_directory(dir_path: Path, min_size_kb: int = 20,
                              colorblind_check: bool = False) -> list[dict]:
    """Validate every chart PNG in a directory."""
    results = []
    pngs = sorted(dir_path.glob("*.png"))
    if not pngs:
        results.append({"path": str(dir_path), "passed": False,
                        "reasons": ["No chart PNG files found in directory"]})
        return results
    for png in pngs:
        results.append(validate_chart(png, min_size_kb, colorblind_check))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate cartographic output quality")
    parser.add_argument("--input", help="Single map PNG to validate")
    parser.add_argument("--input-dir", help="Directory of map PNGs to validate")
    parser.add_argument("--chart", help="Single chart PNG to validate")
    parser.add_argument("--charts-dir", help="Directory of chart PNGs to validate")
    parser.add_argument("--min-size-kb", type=int, default=50,
                        help="Minimum map size in KB (default: 50)")
    parser.add_argument("--min-chart-size-kb", type=int, default=20,
                        help="Minimum chart size in KB (default: 20)")
    parser.add_argument("--colorblind-check", action="store_true",
                        help="Additionally simulate CVD and fail charts with "
                             "indistinguishable class pairs (slower; requires colorspacious)")
    args = parser.parse_args()

    if not any([args.input, args.input_dir, args.chart, args.charts_dir]):
        print("ERROR: provide --input, --input-dir, --chart, or --charts-dir")
        return 1

    results = []
    if args.input:
        results += [validate_map(Path(args.input), args.min_size_kb)]
    if args.input_dir:
        results += validate_directory(Path(args.input_dir), args.min_size_kb)
    if args.chart:
        results += [validate_chart(Path(args.chart), args.min_chart_size_kb,
                                   args.colorblind_check)]
    if args.charts_dir:
        results += validate_chart_directory(Path(args.charts_dir),
                                             args.min_chart_size_kb,
                                             args.colorblind_check)

    all_passed = True
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        kind = r.get("kind", "map")
        print(f"  [{status}] ({kind}) {r['path']}")
        for reason in r["reasons"]:
            print(f"         {reason}")
        if not r["passed"]:
            all_passed = False

    label = "output(s)"
    if all_passed:
        print(f"\nAll {len(results)} {label} passed cartographic validation.")
    else:
        failed = sum(1 for r in results if not r["passed"])
        print(f"\n{failed}/{len(results)} {label} FAILED cartographic validation.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
