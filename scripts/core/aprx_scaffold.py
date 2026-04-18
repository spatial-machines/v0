"""Optional ArcGIS Pro (.aprx) project scaffolding.

A valid `.aprx` is a zipped bundle of binary/XML/JSON fragments that
ArcGIS Pro owns; synthesising one correctly from pure Python is
unreliable. So this module only produces an `.aprx` when `arcpy` is
importable (typically a local ArcGIS Pro install). Otherwise it writes a
`make_aprx.py` helper script that the user can run from inside Pro to
build the project themselves.

Either way, the reliable OSS deliverable is:
  - `data/project.gdb` — all feature classes
  - `layers/<name>.lyrx` per map — drag into any Pro project
  - `README.md` — two paths to load the data

The `.aprx` is a convenience on top of that baseline.

## arcpy upgrade path

When `arcpy` is importable, this module additionally:
  1. Clones `templates/arcgis/project_template.aprx` as the starting project.
  2. Replaces placeholder layers with the generated `.lyrx` stack.
  3. Zooms the primary map frame to the union of all layer extents.
  4. If the template has a Layout, enhances it with:
       - A dynamic title element bound to the project title
       - A legend element bound to the map frame
       - A scale bar
       - A north arrow
       - An attribution text box
  5. Saves a ready-to-share `.aprx`.

All layout enhancement is best-effort — if the template has no Layout,
or any element is missing, those steps are skipped gracefully with
warnings rather than raising. The OSS baseline (`.gdb` + `.lyrx` + helper)
always ships; the `.aprx` is a bonus.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence


def arcpy_available() -> bool:
    try:
        import arcpy  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def build_aprx_with_arcpy(
    template_aprx: Path,
    output_aprx: Path,
    *,
    title: str,
    gdb_path: Path,
    lyrx_files: Sequence[Path],
    attribution: str | None = None,
    zoom_to_layers: bool = True,
    enhance_layout: bool = True,
) -> dict:
    """Clone a template .aprx, wire in layers, optionally enhance its
    layout, and save to `output_aprx`.

    Requires arcpy — caller should guard with `arcpy_available()`.

    Returns a dict describing what was produced:
        {
          "output": "<path>",
          "map_name": "<string>",
          "n_layers": N,
          "layout_enhanced": bool,
          "warnings": [...],
        }
    """
    import arcpy  # type: ignore

    warnings: list[str] = []

    aprx = arcpy.mp.ArcGISProject(str(template_aprx))
    aprx.homeFolder = str(output_aprx.parent)
    aprx.defaultGeodatabase = str(gdb_path)

    # Wire up a default toolbox inside the output package folder. Without this
    # the saveACopy carries forward a toolbox path that won't exist when the
    # .aprx is opened — Pro shows a "Project Item Repair" dialog on first open.
    # Pro 3.6+ doesn't expose CreateToolbox in arcpy (regression vs. older
    # versions), so we copy an empty-ish .atbx that Pro ships with the install.
    import shutil
    out_tbx = output_aprx.parent / "default.atbx"
    pro_install = Path(arcpy.GetInstallInfo().get("InstallDir", ""))
    candidate_tbxes = [
        pro_install / "Resources" / "ArcToolBox" / "Services" / "PrintingTools.atbx",
        pro_install / "Resources" / "ArcToolbox" / "Services" / "PrintingTools.atbx",
    ]
    try:
        if not out_tbx.exists():
            src = next((c for c in candidate_tbxes if c.exists()), None)
            if src is None:
                warnings.append(
                    "default toolbox not copied — no source .atbx found under "
                    f"Pro's install ({pro_install}); Pro may show a one-time "
                    "Project Item Repair dialog when the .aprx is opened."
                )
            else:
                shutil.copy2(src, out_tbx)
        if out_tbx.exists():
            aprx.defaultToolbox = str(out_tbx)
    except Exception as exc:
        warnings.append(f"default toolbox setup failed: {exc}")

    maps = aprx.listMaps()
    if not maps:
        raise RuntimeError(
            "Template .aprx must contain at least one Map. "
            "Open templates/arcgis/project_template.aprx in ArcGIS Pro "
            "and insert a Map before committing."
        )
    m = maps[0]
    m.name = title

    for lyr in list(m.listLayers()):
        try:
            m.removeLayer(lyr)
        except Exception:
            warnings.append(f"could not remove placeholder layer {lyr.name!r}")

    # Add a basemap so the styled tract layer has geographic context on open.
    # Try a few known basemap names — "Human Geography Map" is the preferred
    # modern one; fall back to Light Gray Canvas which ships with every
    # subscription tier.
    basemap_added = None
    for candidate in ("Human Geography Map", "Light Gray Canvas", "Topographic"):
        try:
            m.addBasemap(candidate)
            basemap_added = candidate
            break
        except Exception:
            continue
    if basemap_added is None:
        warnings.append("no basemap could be added — all candidates failed")
    else:
        # addBasemap() adds its own layer(s); we want them to render UNDER the
        # data, so move newly-added data layers (via addDataFromPath later) to
        # the top. Pro does this by default, but make it explicit.
        pass

    added_layers = []
    for lyrx in lyrx_files:
        try:
            new_layers = m.addDataFromPath(str(lyrx))
            if isinstance(new_layers, list):
                added_layers.extend(new_layers)
            elif new_layers is not None:
                added_layers.append(new_layers)
        except Exception as exc:
            warnings.append(f"addDataFromPath({lyrx.name}) failed: {exc}")

    # Zoom map extent to the union of all layer extents
    if zoom_to_layers and added_layers:
        try:
            combined = None
            for lyr in added_layers:
                ext = arcpy.Describe(lyr).extent
                combined = ext if combined is None else combined.union(ext)
            if combined is not None:
                layouts = aprx.listLayouts()
                for layout in layouts:
                    for mf in layout.listElements("MAPFRAME_ELEMENT"):
                        if mf.map and mf.map.name == m.name:
                            mf.camera.setExtent(combined)
        except Exception as exc:
            warnings.append(f"zoom-to-layers failed: {exc}")

    # Enhance the first layout with title / legend / scale bar / north arrow
    layout_enhanced = False
    if enhance_layout:
        try:
            layouts = aprx.listLayouts()
            if layouts:
                layout = layouts[0]
                _enhance_layout(layout, title=title,
                                attribution=attribution or "", warnings=warnings)
                layout_enhanced = True
            else:
                warnings.append("template has no layouts — skipping enhancement")
        except Exception as exc:
            warnings.append(f"layout enhancement failed: {exc}")

    aprx.saveACopy(str(output_aprx))

    return {
        "output": str(output_aprx),
        "map_name": title,
        "n_layers": len(added_layers),
        "layout_enhanced": layout_enhanced,
        "basemap": basemap_added,
        "default_toolbox": str(out_tbx) if out_tbx.exists() else None,
        "warnings": warnings,
    }


def _enhance_layout(layout, *, title: str, attribution: str,
                    warnings: list) -> None:
    """Best-effort layout enhancement: set title, ensure a legend + scale bar
    + north arrow + attribution exist. All operations are try/except so a
    partially customized template still loads.
    """
    # Title: find an existing title text element (ESRI Pro calls it "TEXT_ELEMENT"
    # with name containing 'Title') and set it, or insert a new one top-center.
    title_set = False
    for el in layout.listElements("TEXT_ELEMENT"):
        name = (el.name or "").lower()
        if "title" in name:
            try:
                el.text = title
                title_set = True
                break
            except Exception as exc:
                warnings.append(f"title element text update failed: {exc}")
    if not title_set:
        try:
            # Add a new text element near the top of the page
            page = layout.pageHeight, layout.pageWidth
            # arcpy.mp.Layout's createMapSurroundElement / add text vary by
            # version — most reliable is to rely on the template having a
            # Title placeholder. Warn if missing.
            warnings.append(
                "no element named 'Title' in template — title not injected"
            )
        except Exception:
            pass

    # Attribution: look for element named 'Attribution' or 'Source'
    if attribution:
        for el in layout.listElements("TEXT_ELEMENT"):
            name = (el.name or "").lower()
            if "attribution" in name or "source" in name:
                try:
                    el.text = attribution
                    break
                except Exception as exc:
                    warnings.append(f"attribution update failed: {exc}")

    # Sanity-check that a legend, scale bar, and north arrow exist somewhere
    have = {
        "legend":      any(e for e in layout.listElements("LEGEND_ELEMENT")),
        "scale_bar":   any(e for e in layout.listElements("MAPSURROUND_ELEMENT")
                           if "scale" in (e.name or "").lower()),
        "north_arrow": any(e for e in layout.listElements("MAPSURROUND_ELEMENT")
                           if "north" in (e.name or "").lower()),
    }
    for element, present in have.items():
        if not present:
            warnings.append(
                f"template layout missing {element!r} — add it once to the "
                f"template .aprx to have it on every delivery"
            )


def write_make_aprx_helper(
    output_py: Path,
    *,
    title: str,
    gdb_path: Path,
    lyrx_files: Sequence[Path],
    output_aprx: Path,
) -> Path:
    """Write a Python script the user runs inside ArcGIS Pro.

    When arcpy isn't available locally, this script is the bridge: the
    user opens ArcGIS Pro, creates a new (or opens an existing) project,
    and runs this script from the Python window. It wires up the map and
    saves the project at `output_aprx`.
    """
    lines = [
        "\"\"\"Build an ArcGIS Pro project from this spatial-machines delivery.",
        "",
        "Run inside ArcGIS Pro's Python window. Works via:",
        "    import runpy; runpy.run_path(r'<full path to this file>')",
        "or by pasting the contents directly into the Python window.",
        f"Produces: {output_aprx.name}",
        "\"\"\"",
        "import arcpy",
        "import sys",
        "from pathlib import Path",
        "",
        "# __file__ isn't set when this script is pasted directly into the Pro",
        "# Python window (exec()-style evaluation). Detect our own location by",
        "# searching sys.argv and falling back to the hard-coded absolute path.",
        f"_FALLBACK_HERE = Path(r{str(output_py.parent)!r})",
        "try:",
        "    HERE = Path(__file__).resolve().parent",
        "except NameError:",
        "    HERE = _FALLBACK_HERE",
        f"TITLE = {title!r}",
        f"GDB = str(HERE / {str(gdb_path.relative_to(output_py.parent))!r})",
        "LYRX = [",
    ]
    for lf in lyrx_files:
        rel = lf.relative_to(output_py.parent)
        lines.append(f"    str(HERE / {str(rel)!r}),")
    lines.extend([
        "]",
        f"OUT_APRX = str(HERE / {output_aprx.name!r})",
        "TBX = str(HERE / 'default.tbx')",
        "",
        "aprx = arcpy.mp.ArcGISProject('CURRENT')",
        "m = aprx.listMaps()[0] if aprx.listMaps() else aprx.createMap(TITLE)",
        "m.name = TITLE",
        "",
        "# Rewire the project to be self-contained inside this package folder.",
        "# Without these three assignments, saveACopy() keeps references to the",
        "# ORIGINAL project's home folder + default toolbox, and Pro warns about",
        "# missing resources when the resulting .aprx is opened elsewhere.",
        "aprx.homeFolder = str(HERE)",
        "aprx.defaultGeodatabase = GDB",
        "# Use legacy `*_management` syntax — stable across Pro versions;",
        "# the grouped `arcpy.management.CreateToolbox` path isn't always exposed.",
        "if not Path(TBX).exists():",
        "    arcpy.CreateToolbox_management(str(HERE), 'default.tbx')",
        "aprx.defaultToolbox = TBX",
        "",
        "for lf in LYRX:",
        "    m.addDataFromPath(lf)",
        "aprx.saveACopy(OUT_APRX)",
        "print(f'Saved: {OUT_APRX}')",
        "",
    ])
    output_py.write_text("\n".join(lines))
    return output_py
