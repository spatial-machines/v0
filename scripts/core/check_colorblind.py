#!/usr/bin/env python3
"""Check PNG maps for colorblind accessibility by simulating color vision deficiencies.

Simulates deuteranopia (green-blind), protanopia (red-blind), and tritanopia (blue-blind)
using the colorspacious library, then evaluates whether the top-used color pairs remain
distinguishable in each simulation.

Usage:
    python check_colorblind.py \\
        --input outputs/maps/poverty_choropleth.png \\
        --output-dir outputs/maps/colorblind_check/ \\
        --report outputs/reports/colorblind_accessibility.json

    # Or check all PNGs in a directory (glob):
    python check_colorblind.py \\
        --input "outputs/maps/*.png" \\
        --output-dir outputs/maps/colorblind_check/ \\
        --report outputs/reports/colorblind_accessibility.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import glob
import warnings

import numpy as np
from PIL import Image

try:
    from colorspacious import cspace_convert
except ImportError:
    print("ERROR: colorspacious not installed. Run: pip install colorspacious")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# CVD simulation types supported by colorspacious
CVD_TYPES = {
    "deuteranopia": {"name": "Deuteranopia (green-blind)", "cvd_type": "deuteranomaly", "severity": 1.0},
    "protanopia":   {"name": "Protanopia (red-blind)",   "cvd_type": "protanomaly", "severity": 1.0},
    "tritanopia":   {"name": "Tritanopia (blue-blind)",  "cvd_type": "tritanomaly", "severity": 1.0},
}

# Thresholds for distinguishability (Euclidean distance in sRGB255 space)
DELTA_E_WARN = 20   # pairs within 20 units are similar → WARN
DELTA_E_FAIL = 10   # pairs within 10 units are indistinguishable → FAIL


def simulate_cvd(img_array: np.ndarray, cvd_type: str, severity: float = 1.0) -> np.ndarray:
    """Apply color vision deficiency simulation to an RGBA or RGB array.

    Returns simulated RGB uint8 array.
    """
    # Work with float64 in [0,1]
    if img_array.ndim == 3 and img_array.shape[2] == 4:
        alpha = img_array[:, :, 3:4].astype(np.float64) / 255.0
        rgb = img_array[:, :, :3].astype(np.float64) / 255.0
    else:
        alpha = None
        rgb = img_array[:, :, :3].astype(np.float64) / 255.0

    h, w = rgb.shape[:2]
    flat = rgb.reshape(-1, 3)

    cvd_space = {"name": "sRGB1+CVD", "cvd_type": cvd_type, "severity": severity}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        flat_sim = cspace_convert(flat, cvd_space, "sRGB1")

    flat_sim = np.clip(flat_sim, 0.0, 1.0)
    sim_rgb = (flat_sim.reshape(h, w, 3) * 255).astype(np.uint8)

    if alpha is not None:
        alpha_u8 = (alpha[:, :, 0] * 255).astype(np.uint8)
        sim_out = np.dstack([sim_rgb, alpha_u8])
    else:
        sim_out = sim_rgb

    return sim_out


def top_colors(img_array: np.ndarray, n: int = 5, ignore_alpha_zero: bool = True) -> list[tuple[int, int, int]]:
    """Return the n most-frequent RGB colors in an image (ignoring transparent pixels).

    Memory-efficient: downsample large images before quantization to avoid OOM.
    """
    if img_array.ndim == 3 and img_array.shape[2] == 4 and ignore_alpha_zero:
        mask = img_array[:, :, 3] > 10
        pixels = img_array[mask, :3]
    else:
        pixels = img_array[:, :, :3].reshape(-1, 3)

    # Downsample if too many pixels to avoid OOM (cap at 500k samples)
    MAX_PIXELS = 500_000
    if len(pixels) > MAX_PIXELS:
        step = len(pixels) // MAX_PIXELS
        pixels = pixels[::step]

    # Quantize to 16-step buckets to group near-identical colors
    quantized = (pixels // 16) * 16

    # Use pandas-style aggregation instead of np.core (deprecated)
    r, g, b = quantized[:, 0], quantized[:, 1], quantized[:, 2]
    keys = r.astype(np.int32) * 65536 + g.astype(np.int32) * 256 + b.astype(np.int32)
    unique_keys, counts = np.unique(keys, return_counts=True)
    order = np.argsort(counts)[::-1][:n]
    colors = [
        (
            int((unique_keys[i] >> 16) & 0xFF),
            int((unique_keys[i] >> 8) & 0xFF),
            int(unique_keys[i] & 0xFF),
        )
        for i in order
    ]
    return colors


def color_distance(c1: tuple, c2: tuple) -> float:
    """Euclidean distance in sRGB255 space (simple, fast perceptual proxy)."""
    return float(np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2))))


def classify_pair_status(delta: float) -> str:
    if delta < DELTA_E_FAIL:
        return "FAIL"
    elif delta < DELTA_E_WARN:
        return "WARN"
    return "PASS"


def overall_status(pair_statuses: list[str]) -> str:
    if "FAIL" in pair_statuses:
        return "FAIL"
    if "WARN" in pair_statuses:
        return "WARN"
    return "PASS"


def check_image(src: Path, output_dir: Path | None) -> dict:
    """Run full CVD check on a single image. Returns result dict."""
    print(f"  checking: {src.name}")
    img = Image.open(src).convert("RGBA")
    # Downscale large images before processing to reduce memory usage
    MAX_DIM = 1200
    if max(img.size) > MAX_DIM:
        scale = MAX_DIM / max(img.size)
        new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
        img = img.resize(new_size, Image.LANCZOS)
    img_array = np.array(img)

    orig_colors = top_colors(img_array, n=5)
    print(f"    top {len(orig_colors)} colors: {orig_colors}")

    saved_simulations: dict[str, str] = {}
    cvd_results: dict[str, dict] = {}

    for cvd_key, cvd_meta in CVD_TYPES.items():
        sim_array = simulate_cvd(img_array, cvd_meta["cvd_type"], cvd_meta["severity"])
        sim_colors = top_colors(sim_array, n=5)

        # Compare each original color to its simulated counterpart
        pairs = []
        pair_statuses = []
        for orig, sim in zip(orig_colors, sim_colors):
            delta = color_distance(orig, sim)
            status = classify_pair_status(delta)
            pair_statuses.append(status)
            pairs.append({
                "original_rgb": list(orig),
                "simulated_rgb": list(sim),
                "delta_e": round(delta, 2),
                "status": status,
            })

        # Also check pairwise distinguishability among simulated top colors
        sim_pair_statuses = []
        for i in range(len(sim_colors)):
            for j in range(i + 1, len(sim_colors)):
                delta = color_distance(sim_colors[i], sim_colors[j])
                sim_pair_statuses.append(classify_pair_status(delta))

        cvd_status = overall_status(pair_statuses + sim_pair_statuses)
        cvd_results[cvd_key] = {
            "description": cvd_meta["name"],
            "status": cvd_status,
            "color_pairs": pairs,
        }
        print(f"    {cvd_key}: {cvd_status} ({len([s for s in pair_statuses if s != 'PASS'])} problem pairs)")

        # Save simulated image
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_name = f"{src.stem}_{cvd_key}.png"
            out_path = output_dir / out_name
            sim_img = Image.fromarray(sim_array)
            sim_img.save(out_path)
            saved_simulations[cvd_key] = str(out_path)
            print(f"    saved: {out_path}")

    all_statuses = [v["status"] for v in cvd_results.values()]
    image_status = overall_status(all_statuses)
    print(f"    overall: {image_status}")

    return {
        "image": str(src),
        "status": image_status,
        "simulations": cvd_results,
        "saved_simulations": saved_simulations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", required=True,
        help="PNG path or glob pattern (e.g. 'outputs/maps/*.png')",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save CVD-simulated PNG versions alongside originals",
    )
    parser.add_argument(
        "--report",
        help="Path for JSON report output (default: <output-dir>/colorblind_report.json)",
    )
    args = parser.parse_args()

    # Resolve input paths
    input_pattern = str(Path(args.input).expanduser())
    paths = [Path(p) for p in glob.glob(input_pattern, recursive=True)]
    # Also try literal path
    if not paths:
        literal = Path(args.input).expanduser().resolve()
        if literal.exists():
            paths = [literal]

    if not paths:
        print(f"ERROR: no PNG files found matching: {args.input}")
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    print(f"colorblind accessibility check")
    print(f"  images: {len(paths)}")
    print(f"  CVD types: {', '.join(CVD_TYPES.keys())}")
    print()

    results = []
    for src in sorted(paths):
        result = check_image(src, output_dir)
        results.append(result)
        print()

    # Summary
    status_counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    overall = "FAIL" if status_counts["FAIL"] > 0 else ("WARN" if status_counts["WARN"] > 0 else "PASS")
    print(f"summary: {len(results)} images checked — "
          f"{status_counts['PASS']} PASS, {status_counts['WARN']} WARN, {status_counts['FAIL']} FAIL")
    print(f"overall: {overall}")

    report = {
        "check": "colorblind_accessibility",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "images_checked": len(results),
        "pass": status_counts["PASS"],
        "warn": status_counts["WARN"],
        "fail": status_counts["FAIL"],
        "overall_status": overall,
        "thresholds": {
            "fail_delta_e": DELTA_E_FAIL,
            "warn_delta_e": DELTA_E_WARN,
        },
        "results": results,
    }

    # Report output path
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
    elif output_dir:
        report_path = output_dir / "colorblind_report.json"
    else:
        report_path = Path(results[0]["image"]).parent / "colorblind_report.json"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nreport saved: {report_path}")
    print(json.dumps({"overall_status": overall, "report": str(report_path)}, indent=2))

    return 0 if overall != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
