"""Locate and invoke a PyQGIS-capable Python interpreter.

PyQGIS bindings ship with QGIS itself, not via pip. Our regular venv
(built from requirements.txt) cannot import `qgis.core`. This module
finds an installed QGIS on the system and exposes helpers to run
QGIS-dependent scripts as subprocesses under that interpreter.

Discovery order:
  1. $QGIS_PYTHON environment variable (explicit override)
  2. Current interpreter (works when already running under OSGeo4W python)
  3. Windows: QGIS standalone installer + OSGeo4W (system-wide and per-user)
  4. macOS: /Applications/QGIS*.app/Contents/MacOS/bin/python3
  5. Linux: /usr/bin/python3 if qgis.core is importable

Used by:
  - scripts/core/package_qgis_review.py (pipeline QGIS packager)
  - scripts/demo.py (the standalone demo; formerly had its own copy)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_qgis_python() -> str | None:
    """Return path to a Python that can `import qgis.core`, or None.

    Safe to call repeatedly; the probe of the current interpreter is
    cached via lru_cache-style memoization on `sys.executable` being
    stable for the process lifetime. (Not explicitly cached here — the
    probe is cheap.)
    """
    override = os.environ.get("QGIS_PYTHON")
    if override and Path(override).exists():
        return override

    # 1. Current interpreter — fastest path when user is already in OSGeo4W shell
    try:
        probe = subprocess.run(
            [sys.executable, "-c", "from qgis.core import QgsApplication"],
            capture_output=True, timeout=10,
        )
        if probe.returncode == 0:
            return sys.executable
    except (subprocess.TimeoutExpired, OSError):
        pass

    # 2. Windows — standalone installer + OSGeo4W (system-wide + per-user)
    if os.name == "nt":
        local_app = os.environ.get(
            "LOCALAPPDATA",
            rf"C:\Users\{os.environ.get('USERNAME', '')}\AppData\Local",
        )
        search_roots = [
            Path(r"C:\Program Files"),
            Path(r"C:\Program Files (x86)"),
            Path(r"C:\OSGeo4W"),
            Path(local_app) / "Programs" / "OSGeo4W",
            Path(local_app) / "Programs" / "OSGeo4W64",
        ]
        candidates: list[Path] = []
        for root in search_roots:
            if not root.exists():
                continue
            # Standalone installer: "QGIS 3.xx/bin/python-qgis*.bat"
            candidates.extend(root.glob("QGIS */bin/python-qgis.bat"))
            candidates.extend(root.glob("QGIS */bin/python-qgis-ltr.bat"))
            # OSGeo4W (system-wide + per-user): bin/python-qgis*.bat
            candidates.extend((root / "bin").glob("python-qgis*.bat"))
        if candidates:
            # Prefer LTR (more stable); newest version wins lexicographically
            ltr = [c for c in candidates if "ltr" in c.name.lower()]
            pool = ltr or candidates
            return str(sorted(pool)[-1])
        return None

    # 3. macOS — QGIS.app bundled python3
    if sys.platform == "darwin":
        macs = list(Path("/Applications").glob("QGIS*.app/Contents/MacOS/bin/python3"))
        if macs:
            return str(sorted(macs)[-1])
        return None

    # 4. Linux — system python3 with python3-qgis package installed
    try:
        probe = subprocess.run(
            ["python3", "-c", "from qgis.core import QgsApplication"],
            capture_output=True, timeout=10,
        )
        if probe.returncode == 0:
            return "python3"
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def run_write_qgs(
    gpkg_paths: list[str | Path],
    title: str,
    output_path: str | Path,
    *,
    layers: list[str] | None = None,
    crs_epsg: int = 4269,
    basemap: str = "carto-light",
    style_dir: str | Path | None = None,
    qgis_python: str | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    """Invoke scripts/core/write_qgis_project.py via a PyQGIS-capable Python.

    If `qgis_python` is None, calls `find_qgis_python()`. Raises
    `RuntimeError` if no PyQGIS interpreter can be located — the caller
    should catch and either degrade gracefully or surface the message.

    Returns the CompletedProcess; non-zero returncode means the subprocess
    failed and stderr will explain why. The caller is responsible for
    checking returncode.
    """
    py = qgis_python or find_qgis_python()
    if py is None:
        raise RuntimeError(
            "No PyQGIS-capable Python interpreter found. Install QGIS "
            "(https://qgis.org/download/) or set $QGIS_PYTHON to the full "
            "path of python-qgis-ltr.bat (OSGeo4W) or equivalent. On Windows "
            "the per-user OSGeo4W install typically lives at "
            r"%LOCALAPPDATA%\Programs\OSGeo4W\bin\python-qgis-ltr.bat."
        )

    script = Path(__file__).resolve().parent / "write_qgis_project.py"
    args: list[str] = [
        py,
        str(script),
        "--title", title,
        "-o", str(output_path),
        "--crs", str(crs_epsg),
        "--basemap", basemap,
        "--gpkg", *[str(p) for p in gpkg_paths],
    ]
    if layers:
        args.extend(["--layers", *layers])
    if style_dir:
        args.extend(["--style-dir", str(style_dir)])

    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def build_qgs_hybrid(
    gpkg_paths: list[str | Path],
    title: str,
    output_path: str | Path,
    *,
    layers: list[str] | None = None,
    crs_epsg: int = 4269,
    basemap: str = "carto-light",
    style_dir: str | Path | None = None,
) -> dict:
    """Build a styled .qgs, preferring in-process PyQGIS, else subprocess.

    Returns a dict with keys:
      - path: "in-process" | "subprocess" | "failed"
      - interpreter: str | None (the interpreter used, when subprocess)
      - output_path: Path (the .qgs written, if any)
      - stdout / stderr: str (subprocess output when that path ran)
      - error: str (exception message when generation failed)
    """
    # Try in-process first — works when the current interpreter has qgis.core
    try:
        import write_qgis_project  # noqa: F401 — side effect: triggers qgis.core import
        from write_qgis_project import build_qgs_from_gpkg

        build_qgs_from_gpkg(
            gpkg_paths=gpkg_paths,
            title=title,
            output_path=output_path,
            layer_names=layers,
            crs_epsg=crs_epsg,
            basemap=basemap,
            style_dir=style_dir,
        )
        return {"path": "in-process", "interpreter": sys.executable,
                "output_path": Path(output_path)}
    except ImportError:
        pass  # fall through to subprocess
    except Exception as e:
        return {"path": "failed", "interpreter": sys.executable,
                "error": f"in-process build failed: {e}"}

    # Subprocess fallback via external QGIS python
    try:
        py = find_qgis_python()
        if py is None:
            return {
                "path": "failed",
                "interpreter": None,
                "error": (
                    "No PyQGIS-capable Python interpreter found. Install "
                    "QGIS (https://qgis.org/download/) or set $QGIS_PYTHON "
                    "to the path of python-qgis-ltr.bat. See qgis_env.py."
                ),
            }

        result = run_write_qgs(
            gpkg_paths=gpkg_paths, title=title, output_path=output_path,
            layers=layers, crs_epsg=crs_epsg, basemap=basemap,
            style_dir=style_dir, qgis_python=py,
        )
        if result.returncode != 0:
            return {
                "path": "failed", "interpreter": py,
                "stdout": result.stdout, "stderr": result.stderr,
                "error": (
                    f"write_qgis_project.py exited with rc={result.returncode}. "
                    f"stderr tail: {result.stderr[-400:].strip()}"
                ),
            }
        return {
            "path": "subprocess", "interpreter": py,
            "output_path": Path(output_path),
            "stdout": result.stdout, "stderr": result.stderr,
        }
    except Exception as e:
        return {"path": "failed", "interpreter": None, "error": str(e)}
