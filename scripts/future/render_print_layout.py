#!/usr/bin/env python3
"""Headless QGIS Print Layout → PDF/PNG export.

Loads a .qgs project file, finds a named print layout (or the first one),
and exports it to PDF or PNG without opening the QGIS GUI.

Requirements:
  - QGIS must be installed with Python bindings (qgis.core)
  - Run with the QGIS Python environment:
      qgis_process run ... OR
      python3 /path/to/render_print_layout.py (with QGIS env vars set)

  On Debian/Ubuntu with QGIS installed:
      export PYTHONPATH=/usr/lib/python3/dist-packages:/usr/share/qgis/python
      export LD_LIBRARY_PATH=/usr/lib/qgis
      python3 render_print_layout.py --project analysis.qgs --output report.pdf

  In Docker (if qgis is installed):
      docker run --rm -v $PWD:/data qgis/qgis qgis_process run ...

Usage:
    python render_print_layout.py \\
        --project outputs/qgis/ks_poverty.qgs \\
        --output  outputs/reports/ks_poverty_map.pdf \\
        [--layout "Main Map"] \\
        [--dpi 200] \\
        [--format pdf|png]

If QGIS is not available, falls back to a matplotlib-based PDF assembler
that compiles all PNG maps from the analysis into a simple multi-page PDF.
"""
import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# QGIS headless export
# ---------------------------------------------------------------------------

def export_qgis_layout(project_path, output_path, layout_name=None, dpi=200, fmt="pdf"):
    """Try to export via QGIS Python bindings."""
    try:
        # Locate QGIS Python path if not already set
        qgis_python_paths = [
            "/usr/lib/python3/dist-packages",
            "/usr/share/qgis/python",
            "/usr/lib/qgis/python",
            "/Applications/QGIS.app/Contents/Resources/python",
        ]
        for p in qgis_python_paths:
            if Path(p).exists() and p not in sys.path:
                sys.path.insert(0, p)

        from qgis.core import (
            QgsApplication, QgsProject,
            QgsPrintLayout, QgsLayoutExporter,
            QgsLayoutItemMap,
        )
        from qgis.PyQt.QtCore import QSizeF

        # Init QGIS application (headless)
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QgsApplication([], False)
        app.initQgis()

        # Load project
        project = QgsProject.instance()
        if not project.read(str(project_path)):
            print(f"ERROR: Could not load QGIS project: {project_path}")
            app.exitQgis()
            return False

        # Find layout
        layout_manager = project.layoutManager()
        layouts = layout_manager.printLayouts()

        if not layouts:
            print("No print layouts found in project.")
            app.exitQgis()
            return False

        if layout_name:
            layout = next((l for l in layouts if l.name() == layout_name), None)
            if layout is None:
                print(f"Layout '{layout_name}' not found. Available: {[l.name() for l in layouts]}")
                layout = layouts[0]
                print(f"Using first layout: {layout.name()}")
        else:
            layout = layouts[0]
            print(f"Using layout: {layout.name()}")

        # Export
        exporter = QgsLayoutExporter(layout)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if fmt.lower() == "pdf":
            settings = QgsLayoutExporter.PdfExportSettings()
            settings.dpi = dpi
            result = exporter.exportToPdf(str(output_path), settings)
        else:
            settings = QgsLayoutExporter.ImageExportSettings()
            settings.dpi = dpi
            result = exporter.exportToImage(str(output_path), settings)

        app.exitQgis()

        if result == QgsLayoutExporter.Success:
            print(f"Exported via QGIS: {output_path}")
            return True
        else:
            print(f"QGIS export failed with result code: {result}")
            return False

    except ImportError as e:
        print(f"QGIS Python bindings not available ({e}). Falling back to matplotlib PDF assembler.")
        return False
    except Exception as e:
        print(f"QGIS export error: {e}. Falling back to matplotlib PDF assembler.")
        return False


# ---------------------------------------------------------------------------
# Matplotlib fallback: compile PNG maps into a PDF report
# ---------------------------------------------------------------------------

def assemble_pdf_from_maps(project_path, output_path, title=None, dpi=200):
    """
    Fallback: collect all PNG maps from the analysis outputs directory
    and compile them into a multi-page PDF using matplotlib.
    """
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages

    # Look for maps relative to the project .qgs file or PROJECT_ROOT
    search_dirs = [
        Path(project_path).parent / "outputs" / "maps",
        PROJECT_ROOT / "outputs" / "maps",
    ]

    png_files = []
    for d in search_dirs:
        if d.exists():
            # Match maps related to the project name
            stem = Path(project_path).stem
            png_files = sorted(d.glob(f"{stem}*.png"))
            if not png_files:
                png_files = sorted(d.glob("*.png"))
            if png_files:
                break

    if not png_files:
        print("No PNG maps found to assemble. Searched:")
        for d in search_dirs:
            print(f"  {d}")
        return False

    print(f"Assembling {len(png_files)} maps into PDF: {output_path}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    report_title = title or Path(project_path).stem.replace("_", " ").title()

    with PdfPages(str(output_path)) as pdf:
        # Title page
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor("white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.text(0.5, 0.6, report_title, transform=ax.transAxes,
                ha="center", va="center", fontsize=28, fontweight="bold", color="#222")
        ax.text(0.5, 0.48, f"GIS Analysis Report", transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="#666")
        ax.text(0.5, 0.38, f"{len(png_files)} maps", transform=ax.transAxes,
                ha="center", va="center", fontsize=11, color="#999")
        pdf.savefig(fig, dpi=dpi)
        plt.close(fig)

        # Map pages
        for i, png_path in enumerate(png_files):
            try:
                img = mpimg.imread(str(png_path))
            except Exception as e:
                print(f"  Skipping {png_path.name}: {e}")
                continue

            h, w = img.shape[:2]
            aspect = w / h
            fig_w = 11
            fig_h = fig_w / aspect
            fig_h = min(fig_h, 8.5)

            fig = plt.figure(figsize=(fig_w, fig_h))
            fig.patch.set_facecolor("white")
            ax = fig.add_axes([0.02, 0.06, 0.96, 0.90])
            ax.imshow(img)
            ax.set_axis_off()

            # Caption
            caption = png_path.stem.replace("_", " ").title()
            fig.text(0.5, 0.02, caption, ha="center", fontsize=9, color="#555")

            pdf.savefig(fig, dpi=dpi, bbox_inches="tight")
            plt.close(fig)
            print(f"  Added page {i+1}: {png_path.name}")

    print(f"PDF assembled: {output_path} ({len(png_files)} maps)")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Path to .qgs QGIS project file")
    parser.add_argument("-o", "--output", help="Output PDF or PNG path")
    parser.add_argument("--layout", help="Print layout name (default: first layout found)")
    parser.add_argument("--format", default="pdf", choices=["pdf", "png"],
                        help="Output format (default: pdf)")
    parser.add_argument("--dpi", type=int, default=200, help="Export DPI (default: 200)")
    parser.add_argument("--title", help="Report title (for fallback PDF assembler)")
    args = parser.parse_args()

    project_path = Path(args.project).expanduser().resolve()
    if not project_path.exists():
        print(f"Project not found: {project_path}")
        return 1

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "reports"
        out_path = out_dir / f"{project_path.stem}.{args.format}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Try QGIS first, fall back to matplotlib assembler
    success = export_qgis_layout(
        project_path, out_path, args.layout, args.dpi, args.format
    )

    if not success:
        success = assemble_pdf_from_maps(project_path, out_path, args.title, args.dpi)

    log = {
        "step": "render_print_layout",
        "project": str(project_path),
        "output": str(out_path),
        "format": args.format,
        "dpi": args.dpi,
        "method": "qgis" if success else "failed",
        "passed": success,
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
