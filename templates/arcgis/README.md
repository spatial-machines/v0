# templates/arcgis/

This folder holds the **ArcGIS Pro project template** that `scripts/core/package_arcgis_pro.py` clones when `arcpy` is available.

## What belongs here

- `project_template.aprx` — an empty-but-valid ArcGIS Pro project with one Map, one Layout, and named placeholder elements (Title, Attribution, Legend, Scale Bar, North Arrow).
- `bootstrap_template.py` — run this once from inside ArcGIS Pro's Python window to generate `project_template.aprx` automatically. It creates a Map, a Letter-landscape Layout, and inserts the named elements the packager expects.

`project_template.aprx` is **not** in the repo by default. It's a binary file that only ArcGIS Pro can create. Anyone wanting the upgraded `.aprx` delivery path runs `bootstrap_template.py` once.

## How `package_arcgis_pro.py` uses the template

When `arcpy` is importable on the machine producing a package:

1. `package_arcgis_pro.py` clones `project_template.aprx`.
2. Replaces the placeholder map with the analysis's layers (each `.lyrx`).
3. Zooms the main map frame to the combined extent of those layers.
4. Sets the Layout's `Title` text element to the analysis title.
5. Sets `Attribution` / `Source` text element to the first sidecar's attribution.
6. Warns (but does not fail) if Legend, Scale Bar, or North Arrow elements are missing.
7. Saves the result next to the helper script as `<slug>.aprx`.

When `arcpy` is **not** available (Linux CI, no Pro license), `package_arcgis_pro.py` skips the `.aprx` entirely. The OSS baseline (`.gdb` + `.lyrx` files + `make_aprx.py` helper) always ships.

## Named element conventions

For layout enhancement to find your elements, name them in the Pro UI (Contents pane → right-click element → Rename) using any of these case-insensitive fragments:

| Purpose | Name must contain |
|---|---|
| Analysis title | `Title` |
| Source attribution | `Attribution` or `Source` |
| Legend | — (any `LEGEND_ELEMENT`) |
| Scale bar | `Scale` in the element name |
| North arrow | `North` in the element name |

Missing elements just skip that enhancement step.
