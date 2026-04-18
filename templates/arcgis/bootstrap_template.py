"""Bootstrap the spatial-machines ArcGIS Pro template.

Run this ONCE from inside ArcGIS Pro's Python window (or via `propy.bat`
with arcpy on PATH) to generate `project_template.aprx` in the same
folder as this script. After that, `scripts/core/package_arcgis_pro.py`
will use it automatically when arcpy is detected.

The generated template has:

  * One Map named "Template Map" with an empty TOC.
  * One Layout sized Letter (8.5 × 11 in) in landscape orientation.
  * A Map Frame filling most of the page.
  * Named placeholder elements the packager looks for:
        - "Title"         — text element, top-left
        - "Attribution"   — text element, bottom-right (small, gray)
        - "Legend 1"      — legend element, right side
        - "Scale Bar 1"   — scale bar, bottom-left
        - "North Arrow 1" — north arrow, top-right

Once generated, commit `project_template.aprx` to the repo (or keep it
local — teammates can re-run this script to regenerate their own copy).
"""
from pathlib import Path

import arcpy  # type: ignore


HERE = Path(__file__).resolve().parent
OUT = HERE / "project_template.aprx"


def main() -> None:
    # Start from an existing "blank" .aprx that Pro ships with. On a
    # default install that's under %ProgramFiles%\ArcGIS\Pro\Resources\...
    # Easiest reliable bootstrap: create a brand-new project from CURRENT
    # (the project Pro is currently running) and saveACopy.
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Rename or create a map
    maps = aprx.listMaps()
    if maps:
        m = maps[0]
    else:
        m = aprx.createMap("Template Map")
    m.name = "Template Map"

    # Ensure we have a Layout
    layouts = aprx.listLayouts()
    if layouts:
        layout = layouts[0]
    else:
        layout = aprx.createLayout(11.0, 8.5, "INCH", "Template Layout")
    layout.name = "Template Layout"

    # Map Frame
    frames = layout.listElements("MAPFRAME_ELEMENT")
    if frames:
        mf = frames[0]
    else:
        mf = layout.createMapFrame(
            arcpy.Extent(0.5, 1.0, 10.0, 8.0),
            m,
            "Map Frame",
        )
    mf.map = m

    # Name placeholders so the packager can find them ----------------
    # (arcpy's layout text/legend/mapsurround creation API varies across
    #  Pro versions; the safest path is: if an element of the right type
    #  already exists, rename it; otherwise log a note and let the user
    #  create it in the UI. This script prints guidance when it can't
    #  fully automate.)

    needed = {
        "Title":         ("TEXT_ELEMENT",       "title"),
        "Attribution":   ("TEXT_ELEMENT",       "attribution"),
        "Legend 1":      ("LEGEND_ELEMENT",     "legend"),
        "Scale Bar 1":   ("MAPSURROUND_ELEMENT", "scale"),
        "North Arrow 1": ("MAPSURROUND_ELEMENT", "north"),
    }

    renamed = []
    missing = []
    for want_name, (kind, fragment) in needed.items():
        candidates = [
            el for el in layout.listElements(kind)
            if fragment in (el.name or "").lower()
        ]
        if candidates:
            candidates[0].name = want_name
            renamed.append(want_name)
        else:
            missing.append(want_name)

    aprx.saveACopy(str(OUT))

    print(f"Wrote template: {OUT}")
    if renamed:
        print("Renamed existing elements:", ", ".join(renamed))
    if missing:
        print()
        print("The following elements were NOT found and must be added via the Pro UI:")
        for m_name in missing:
            print(f"  - {m_name}")
        print()
        print("Steps:")
        print("  1. Open the Layout tab.")
        print("  2. Insert the element (Insert menu → Text / Legend / Scale Bar / North Arrow).")
        print("  3. In the Contents pane, rename it to the exact name above.")
        print("  4. File → Save, then re-run this script to verify.")


# Intentionally no `if __name__ == "__main__"` guard — this script is a
# one-shot helper that should run whenever it's loaded (via drag-drop into
# Pro's Python window, `runpy.run_path` without run_name, or direct `python`).
main()
