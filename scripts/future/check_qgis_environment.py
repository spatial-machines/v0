"""Check and report whether QGIS is available in the current environment.

This is informational only — the QGIS bridge does NOT require QGIS to be
installed.  It generates plain XML .qgs files and copies data.  This script
simply tells the operator what is (or isn't) available locally so they know
whether they need a separate review PC.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path


def _check_binary(name: str) -> dict:
    """Check whether a binary is on PATH and capture its version."""
    path = shutil.which(name)
    if path is None:
        return {"found": False, "path": None, "version": None}
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        version = (result.stdout.strip() or result.stderr.strip()).split("\n")[0]
    except Exception:
        version = "unknown"
    return {"found": True, "path": path, "version": version}


def _check_python_module(name: str) -> dict:
    """Check whether a Python module is importable."""
    try:
        mod = __import__(name)
        version = getattr(mod, "__version__", getattr(mod, "QGIS_VERSION", "unknown"))
        return {"importable": True, "version": str(version)}
    except ImportError:
        return {"importable": False, "version": None}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Check whether QGIS is available in the current environment."
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Optional: write report as JSON to this path",
    )
    args = parser.parse_args()

    report: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "qgis_required": False,
        "checks": {},
    }

    # Check qgis binary
    report["checks"]["qgis"] = _check_binary("qgis")
    # Check qgis_process binary (headless tool)
    report["checks"]["qgis_process"] = _check_binary("qgis_process")
    # Check Python qgis module
    report["checks"]["qgis_python"] = _check_python_module("qgis.core")
    # Check ogr2ogr (useful for data conversion)
    report["checks"]["ogr2ogr"] = _check_binary("ogr2ogr")
    # Check ogrinfo
    report["checks"]["ogrinfo"] = _check_binary("ogrinfo")

    # Determine overall status
    qgis_available = (
        report["checks"]["qgis"]["found"]
        or report["checks"]["qgis_process"]["found"]
        or report["checks"]["qgis_python"]["importable"]
    )
    gdal_available = report["checks"]["ogr2ogr"]["found"]

    report["qgis_available"] = qgis_available
    report["gdal_available"] = gdal_available

    if qgis_available:
        report["recommendation"] = (
            "QGIS is available locally. You can open .qgs project files directly."
        )
    else:
        report["recommendation"] = (
            "QGIS is NOT installed in this environment. This is expected — the "
            "QGIS bridge generates portable review packages without QGIS. Copy "
            "the package to a PC with QGIS 3.x to review."
        )

    # Print report
    print("=== QGIS Environment Check ===")
    print(f"  qgis binary:      {'found' if report['checks']['qgis']['found'] else 'not found'}")
    print(f"  qgis_process:     {'found' if report['checks']['qgis_process']['found'] else 'not found'}")
    print(f"  qgis Python:      {'importable' if report['checks']['qgis_python']['importable'] else 'not available'}")
    print(f"  ogr2ogr (GDAL):   {'found' if report['checks']['ogr2ogr']['found'] else 'not found'}")
    print(f"  ogrinfo (GDAL):   {'found' if report['checks']['ogrinfo']['found'] else 'not found'}")
    print()
    print(f"  QGIS available:   {'YES' if qgis_available else 'NO'}")
    print(f"  GDAL available:   {'YES' if gdal_available else 'NO'}")
    print()
    print(f"  {report['recommendation']}")

    # Optionally write JSON
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        print(f"\nwrote environment report -> {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
