# Toolkit — ArcGIS Python API (`arcgis`)

Short reference for when and how spatial-machines uses Esri's `arcgis` Python package (not to be confused with `arcpy`, which is a different library shipped with ArcGIS Pro).

## `arcgis` vs `arcpy` — which, when

| Library | What it is | When we use it | Install |
|---|---|---|---|
| `arcgis` | Free Python API for ArcGIS Online and ArcGIS Enterprise | AGOL publishing adapter (`scripts/core/publishing/arcgis_online.py`) | `pip install arcgis` |
| `arcpy` | Proprietary library shipped with ArcGIS Pro | Optional upgrade path for `package_arcgis_pro.py` (builds a polished `.aprx`) | ships with ArcGIS Pro; not pip-installable |

Rule of thumb: if the code talks to a **web portal**, it's `arcgis`. If the code talks to the **desktop app or a local geodatabase via Esri's APIs**, it's `arcpy`. Our OSS-first design means `arcpy` is always optional and guarded by `try: import arcpy` — never a hard dependency.

## Install

```bash
# Install as an optional extra so it never blocks non-Esri users
pip install spatial-machines[esri]

# Or directly
pip install arcgis
```

The `arcgis` package has a significant transitive dep footprint (~300 MB with scientific stack). That's why it's optional-extras instead of core.

## Credentials

All AGOL auth goes through `.env`. Never hardcode, never commit, never log:

```env
AGOL_URL=https://www.arcgis.com
AGOL_USER=you@your-org.example
AGOL_PASSWORD=...
# Or use an API key instead of user/password:
AGOL_API_KEY=...
```

Credentials are read by `scripts/core/publish_arcgis_online.py`'s `_load_dotenv()` helper. The CLI's `PublishRequest.options` lets callers override any value at runtime without touching the environment.

Free ArcGIS Developer accounts work for evaluation: <https://developers.arcgis.com/>.

## Common calls

### Connect

```python
from arcgis.gis import GIS

# Username / password
gis = GIS(os.environ["AGOL_URL"],
          os.environ["AGOL_USER"],
          os.environ["AGOL_PASSWORD"])

# API key (takes precedence in our adapter when set)
gis = GIS(os.environ["AGOL_URL"], api_key=os.environ["AGOL_API_KEY"])
```

### Upload a GeoPackage as a hosted feature layer

```python
gp_item = gis.content.add(
    {"type": "GeoPackage",
     "title": "Demo — tracts",
     "description": "Poverty analysis",
     "tags": "demographics,equity"},
    data="data/processed/tracts.gpkg",
)
fl_item = gp_item.publish()
```

### Apply our sidecar-derived symbology

```python
from renderers import agol_renderer  # scripts/core/renderers.py

sidecar = json.loads(Path("outputs/maps/poverty.style.json").read_text())
renderer = agol_renderer(sidecar)
fl_item.layers[0].manager.update_definition({
    "drawingInfo": {"renderer": renderer}
})
```

The same `agol_renderer()` function drives `.lyrx` generation (via `renderers.lyrx_renderer`) and QGIS styling (via `write_qgis_project.py` which reads the sidecar directly). One sidecar → three matching deliverables. Parity is verified by `tests/test_renderer_parity.py`.

### Share an item

```python
item.share(everyone=False, org=True)          # ORG level
item.share(everyone=True,  org=True)          # PUBLIC
item.share(everyone=False, org=False)         # PRIVATE (default)
```

Our adapter enforces PRIVATE by default and only promotes when the project brief's `outputs.publish_sharing` explicitly requests `ORG` or `PUBLIC`.

### Tear down items from a publish run

```python
import json
status = json.load(open("analyses/<project>/outputs/arcgis/publish-status.json"))
for rec in status["items"]:
    if rec.get("id"):
        gis.content.get(rec["id"]).delete()
```

No automatic teardown tool ships in v1. Use the snippet above when an AGOL publish needs rolling back.

## Version pin

We target `arcgis>=2.3`. Older versions lack the `FeatureLayerManager.update_definition()` method we use for renderer injection. If you must run against an older AGOL, fall back to publishing without custom symbology and apply it manually in the AGOL Web Map viewer.

## Gotchas

- **GeoPackage publish is slow.** A medium GPKG (hundreds of MB) can take minutes to publish; set a generous timeout if wrapping this in CI.
- **Feature service limits vary by AGOL plan.** Free developer accounts cap hosted feature layer record counts. For large analyses, tile the data first.
- **Organizations with MFA / SAML** need a different auth flow (`arcgis.gis.GIS(..., client_id=...)`). Our adapter's `_load_credentials()` is the extension point — open an issue if you hit this.
- **Popups need configuration.** AGOL auto-populates popup fields from the feature layer schema, but our adapter leaves the `popupInfo.description` empty so the map reader can customise per-project.
- **Never log tokens.** The adapter doesn't; if you extend it, keep it that way.

## Further reading

- `docs/wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md` — the full operational workflow (dry-run, real publish, teardown, failure modes)
- `docs/extending/PUBLISHING_ADAPTERS.md` — how to build an adapter for a new external system
- Esri docs: <https://developers.arcgis.com/python/>
