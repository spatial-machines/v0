# ArcGIS Pro Package Standard

The ArcGIS Pro deliverable is the analogue of the QGIS package: a portable, self-describing folder a stakeholder can open and trust. It mirrors the QGIS package's structure, idempotency, and handoff contract.

Produced by `scripts/core/package_arcgis_pro.py`. Consumed by anyone with ArcGIS Pro 3.1+.

## Guarantee matrix

| Artifact | OSS path (no Esri license) | arcpy path (ArcGIS Pro installed) |
|---|---|---|
| `data/project.gdb` | ✅ via GDAL OpenFileGDB | ✅ |
| `layers/*.lyrx` | ✅ pure-Python CIM JSON | ✅ |
| `review-spec.json` | ✅ | ✅ |
| `review-notes.md` | ✅ | ✅ |
| `manifest.json` | ✅ | ✅ |
| `README.md` | ✅ | ✅ |
| `make_aprx.py` helper | ✅ | ✅ |
| Charts (`charts/`) | ✅ copied from cartography | ✅ |
| `<slug>.aprx` | ❌ use `make_aprx.py` inside Pro | ✅ built via arcpy.mp |

The OSS path is the baseline. The arcpy upgrade is a convenience layer — no consumer-side feature depends on whether the `.aprx` was pre-built or assembled via the helper script.

## Directory layout

```
analyses/<project>/outputs/arcgis/
├── data/
│   ├── project.gdb/          # file geodatabase, one feature class per processed layer
│   └── *.gpkg                 # source GeoPackages copied for reference (unless --no-gpkg-copies)
├── layers/
│   └── *.lyrx                 # one styled layer file per thematic map
├── charts/                    # copied from outputs/charts/ (PNG + SVG + sidecars)
├── make_aprx.py               # helper to build .aprx inside ArcGIS Pro
├── <slug>.aprx                # ONLY when arcpy was available at package time
├── manifest.json
├── review-spec.json
├── review-notes.md
└── README.md
```

## Non-negotiables

1. **`.gdb` is the canonical data container.** Source `.gpkg` files may be copied for provenance, but `.lyrx` renderers reference the `.gdb`.
2. **Every map with a `.style.json` sidecar produces one `.lyrx`.** Missing sidecar → no `.lyrx` for that layer; packager emits a warning but still succeeds.
3. **Feature-class names are sanitized.** File geodatabases disallow names starting with a digit or containing non-alphanumeric characters (except `_`). The packager converts `2020_tracts` → `fc_2020_tracts`, `census tracts` → `census_tracts`.
4. **Workspace references are relative.** `.lyrx` files use `DATABASE=../data/project.gdb` so the package moves as a unit.
5. **CIM schema version is pinned** to `3.1.0` in `scripts/core/lyrx_writer.py`. Bump only with a conscious ArcGIS Pro version bump — older Pro versions reject newer CIM documents.
6. **No arcpy imports at module top.** All arcpy usage goes through `aprx_scaffold.arcpy_available()` so the package generates cleanly on Linux CI.

## Renderer translation

Style sidecars → `.lyrx` via `scripts/core/renderers.py`:

| `map_family` | Renderer | Equivalent AGOL renderer |
|---|---|---|
| `thematic_choropleth` | `CIMClassBreaksRenderer` (`GraduatedColor`) | `classBreaks` |
| `thematic_categorical` | `CIMUniqueValueRenderer` | `uniqueValue` |
| `point_overlay` | `CIMSimpleRenderer` with point symbol | `simple` point |
| `reference`, other | `CIMSimpleRenderer` with polygon symbol | `simple` polygon |

The same `renderers.py` produces the AGOL equivalents, so the ArcGIS Online publishing adapter inherits identical styling (Workstream 3).

## Color ramps

RGB stops come from `config/map_styles.json.color_ramps_rgb` (the same 5-stop ramps the QGIS packager uses). When the sidecar's `k` differs from the ramp length, `renderers.ramp_colors(palette, k)` linearly interpolates between stops. This matches `mapclassify` + matplotlib behavior closely enough that the three packages render visually consistent results.

## Known limits

- **Labels not carried into `.lyrx`** — ArcGIS Pro honors its own label classes; we don't pre-populate them. Users who want labels in Pro set them via the Pro UI.
- **No layouts in the OSS `.aprx`** — layouts are a Pro-side concern. The `make_aprx.py` helper only arranges the map layers. The **arcpy upgrade path** (below) fills this gap when an ArcGIS Pro license is available at package time.
- **No joins / relationship classes** — the `.gdb` contains only the feature classes as they existed in the processed GeoPackage; no derived joins.
- **CRS preserved** — whatever CRS the source `.gpkg` declared becomes the feature-class CRS. The packager does not reproject.

## arcpy upgrade path

When `package_arcgis_pro.py` runs on a machine where `import arcpy` succeeds
and `templates/arcgis/project_template.aprx` exists, it produces a
ready-to-share `.aprx` with:

1. **Populated Map** — placeholder layers swapped for the analysis's `.lyrx` stack.
2. **Auto-zoom** — the primary Map Frame zooms to the combined extent of all layers.
3. **Layout title** — the Layout's element named `Title` is set to the analysis title.
4. **Attribution** — the element named `Attribution` or `Source` is set from the first sidecar's `attribution` field.
5. **Legend / Scale Bar / North Arrow** — if present in the template, they auto-populate against the map frame. If missing, packaging warns but does not fail.

### Bootstrapping the template

`project_template.aprx` is a binary file that only ArcGIS Pro can produce.
It is **not** committed by default. To generate one:

```
# Inside ArcGIS Pro (any project), open the Python window:
exec(open(r"<repo>\templates\arcgis\bootstrap_template.py").read())
```

The bootstrap script creates a Landscape Letter layout and renames the
elements to the names the packager looks for. It prints guidance for
any elements you must insert manually (Insert menu → Text / Legend /
Scale Bar / North Arrow, then rename in the Contents pane).

Commit the resulting `.aprx` to the repo (or keep it local) — after that,
every arcpy-side package run gets a polished layout.

### Naming conventions used by the enhancer

| Element purpose | Case-insensitive name fragment |
|---|---|
| Analysis title | `Title` |
| Source attribution | `Attribution` or `Source` |
| Legend | any `LEGEND_ELEMENT` (no name match required) |
| Scale bar | `Scale` in the element name |
| North arrow | `North` in the element name |

Rename your template elements once using the Contents pane in Pro; the
packager picks them up on every future delivery. Missing elements skip
that enhancement step rather than failing the build.

### What still needs human touch

Even with the upgrade, a few things benefit from hand-polish in Pro:

- **Label classes** on individual layers (label field, halo size, placement)
- **Reference scale** if the layer is scale-sensitive
- **Page setup** for non-Letter paper sizes or portrait orientation
- **Extra map frames** for comparison layouts

These are one-time template edits. Commit the enhanced template back and
they apply to every future arcpy-built `.aprx`.

## Validation

```bash
python scripts/core/validate_arcgis_package.py analyses/<project>/
```

Passes when:
- `outputs/arcgis/` exists with all required top-level files
- `.gdb` opens and contains ≥1 feature class
- Every layer in `review-spec.json` exists in the `.gdb`
- Every `.lyrx` is a valid `CIMLayerDocument` and references a dataset present in the `.gdb`

Runs during Gate B (Structural QA).

## Loading into ArcGIS Pro

Two paths documented in the package README:

**Drag-and-drop.** User opens Pro, browses to `outputs/arcgis/` in the Catalog pane, drags each `.lyrx` onto a map. Single styled layer per drop. Safest, least error-prone.

**Helper script.** User opens the Python window inside Pro and runs `make_aprx.py`. It creates (or updates) the map, adds every layer, sets the default geodatabase, and saves `<slug>.aprx` next to the helper.

Neither path requires anything beyond stock ArcGIS Pro.

## Testing

- Unit: `validate_arcgis_package.py` against a generated fixture in CI.
- Integration: the synthetic test in `scripts/core/package_arcgis_pro.py`'s smoke block (Linux CI, no arcpy).
- Pro-side manual: drag one `.lyrx` into Pro 3.1, verify the symbology matches the paired static PNG. Do this before every release tag.
