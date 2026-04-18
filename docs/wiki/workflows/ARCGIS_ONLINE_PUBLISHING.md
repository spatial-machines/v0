# Workflow — ArcGIS Online Publishing

How the optional AGOL adapter delivers an analysis as a hosted Feature Service plus a styled Web Map.

**Opt-in only.** The pipeline never auto-publishes. AGOL runs only when:
- the project brief sets `outputs.publish_targets: ["arcgis_online"]`, **or**
- the human explicitly runs `python scripts/core/publish_arcgis_online.py`.

## Scope (intentionally narrow)

| Goes to AGOL | Stays local only |
|---|---|
| One File Geodatabase (uploaded as item) | Map PNGs |
| One hosted Feature Service with N feature layers | Chart PNGs |
| Per-layer renderers from `.style.json` sidecars | HTML report |
| One Web Map referencing every layer | ArcGIS Pro `.lyrx` files |
|  | QGIS `.qgs` project |
|  | Source GeoPackages |

AGOL's strength is hosted feature layers + Web Maps. Maps, charts, and reports are first-class deliverables, but they live with the rest of the analysis (`outputs/maps/`, `outputs/charts/`, `outputs/reports/`) so reviewers always have the full kit. Anything published to AGOL is also available locally — not everything local is mirrored to AGOL.

## When to use this

- Stakeholder wants to pan/zoom the result in their browser without installing QGIS or ArcGIS Pro.
- Someone needs to embed layers in a dashboard, StoryMap, or Experience Builder app.
- You want a shareable URL you can drop into an email — not a ZIP to download.

If those don't apply, ship the local ArcGIS Pro package + QGIS package + HTML report instead. AGOL is extra surface, not required.

## Prerequisites

1. **No `arcgis` Python package required.** The adapter is REST-only — it talks to the documented AGOL REST endpoints via `requests`. Avoids a long history of bugs in the `arcgis` package (distutils imports, internal-import drift, ssl_context deepcopy).

2. **An AGOL subscription that supports hosted feature service publishing.** Read this first or you'll waste a debugging session: free **Location Platform** developer accounts (the default if you sign up at [developers.arcgis.com](https://developers.arcgis.com/)) include geocoding, routing, basemaps, and other platform services — but they **do not** support publishing hosted feature services. AGOL accepts the upload silently, accepts `/analyze` calls, and then silently no-ops `/publish` (no error, just an item-info response shape). Look up your subscription at [arcgis.com → My Organization](https://www.arcgis.com/home/organization.html); if `subscriptionInfo.type` is `"Location Platform"`, you need to upgrade.

   The adapter probes `subscriptionInfo` during `--dry-run` and emits a clear warning when the tier won't support hosting. A 21-day **ArcGIS Online** trial is enough to verify the full flow end-to-end.

3. **AGOL credentials in `.env`** (never committed, never logged):

   | Variable | Purpose |
   |---|---|
   | `AGOL_URL` | Default `https://www.arcgis.com`. Override for a custom AGOL instance. |
   | `AGOL_USER` | Your AGOL username. **Preferred.** |
   | `AGOL_PASSWORD` | Your AGOL password. |
   | `AGOL_API_KEY` | API key alternative. See scope note below. |

   The adapter prefers `AGOL_USER`+`AGOL_PASSWORD` when both are set, because user/password tokens inherit the full account privilege set. API keys from developers.arcgis.com carry their **own scope list** separate from user privileges; even with the right subscription, an API key may not include the publish-hosted-feature-layers scope. If you hit `publish silently returned item-info` and your subscription tier is correct, switch to user/password auth (it bypasses API-key scopes entirely).

4. **Build the ArcGIS Pro package first** (it produces the GDB the AGOL adapter uploads):

   ```bash
   python scripts/core/package_arcgis_pro.py analyses/<project>/ \
       --title "Project Title" \
       --data-files analyses/<project>/data/processed/*.gpkg \
       --style-dir  analyses/<project>/outputs/maps
   ```

   This writes `analyses/<project>/outputs/arcgis/data/project.gdb`. The AGOL adapter will refuse to run until it exists.

## Dry run first. Always.

`--dry-run` validates credentials, locates the GDB, introspects its feature classes, and lists the items that would be created — without making any AGOL API calls beyond credential validation.

```bash
python scripts/core/publish_arcgis_online.py analyses/<project>/ \
    --title "Project Title" --dry-run
```

Inspect the status file:

```
analyses/<project>/outputs/arcgis/publish-status.json
```

Each entry shows category (`source_gdb`, `feature_service`, `web_map`, `renderer_plan`), title, and the layer count / sidecar count it expects. If the layer count or sidecar count looks wrong, fix it before the real upload.

## Real upload

```bash
python scripts/core/publish_arcgis_online.py analyses/<project>/ \
    --title "Project Title" \
    --description "Quarterly equity snapshot for Cook County." \
    --tags demographics equity ACS
```

Default sharing is **PRIVATE**. To promote:

```bash
# Org-wide
python scripts/core/publish_arcgis_online.py analyses/<project>/ --title "..." --sharing org

# Public internet — use deliberately
python scripts/core/publish_arcgis_online.py analyses/<project>/ --title "..." --sharing public
```

The CLI mirrors the sharing decision into `publish-status.json` so the human review trail is preserved.

## What happens during a real upload

1. Locate the GDB at `outputs/arcgis/data/project.gdb` (or honour `--gdb /path/to/other.gdb`).
2. Zip it into a temporary `.zip` (root entry is the `.gdb/` folder, not its contents).
3. `addItem` with `type="File Geodatabase"` → returns the source item ID.
4. `/publish` with `fileType="fileGeodatabase"` → returns one Feature Service item with N layers (one per feature class).
5. Poll the publish job until the service is queryable.
6. Hit `{fs_url}?f=json` and `{fs_url}/{layer_idx}?f=json` to introspect the published layers and their fields.
7. Match each layer to its sidecar using the same logic as `package_arcgis_pro._plan_lyrx_from_sidecars` — by `source_gpkg` stem first, then `field` presence, then `categorical_map` fallback.
8. For each matched sidecar, build an AGOL renderer via `renderers.agol_renderer()` and call `{fs_url}/{layer_idx}/updateDefinition` to apply it.
9. Assemble a Web Map referencing every layer in the service, with a Light-Gray-Canvas basemap.
10. Apply sharing (PRIVATE / ORG / PUBLIC) to every item created.

If publish fails (for example, the API-key scope issue above), the adapter auto-deletes the orphan GDB item it just uploaded so re-runs don't pile up dead source items in your AGOL content.

## Symbology fidelity

Every layer's renderer is built from its matching `.style.json` sidecar by `scripts/core/renderers.agol_renderer()`. The same function drives `.lyrx` generation in the ArcGIS Pro packager and QGIS symbol translation in the QGIS packager — three deliverables, one source of truth:

- `thematic_choropleth` → `classBreaks` renderer with breaks + colors from the sidecar
- `thematic_categorical` → `uniqueValue` renderer from `categorical_map`
- `point_overlay`, `reference`, others → `simple` renderer with palette-matched fill

## Sharing scopes — what they mean

| Scope | Who can see | Who can edit |
|---|---|---|
| `PRIVATE` (default) | You only | You only |
| `ORG` | Members of your AGOL org | You only |
| `PUBLIC` | Anyone with the URL | You only |

- `PUBLIC` items appear in public AGOL search. Don't publish sensitive demographics publicly without explicit go-ahead from whoever owns the underlying data.
- An AGOL admin can override item sharing after you publish.
- `publish-status.json` records the sharing scope applied — use it as your audit trail.

## Teardown

```bash
python scripts/core/teardown_agol.py analyses/<project>/
```

Reads `publish-status.json` and deletes every item it references (Feature Service, source GDB item, Web Map). Idempotent — safe to re-run after you've already deleted some items by hand.

A typical iteration loop while validating a new analysis:

```bash
# 1. Build local Pro package (produces the GDB)
python scripts/core/package_arcgis_pro.py analyses/<project>/ --title "..." \
    --data-files analyses/<project>/data/processed/*.gpkg \
    --style-dir  analyses/<project>/outputs/maps

# 2. Dry run AGOL
python scripts/core/publish_arcgis_online.py analyses/<project>/ --title "..." --dry-run

# 3. Real upload (PRIVATE)
python scripts/core/publish_arcgis_online.py analyses/<project>/ --title "..."

# 4. Spot-check at https://www.arcgis.com/home/content.html

# 5. Tear down
python scripts/core/teardown_agol.py analyses/<project>/
```

## Failure modes & troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `AGOL credentials missing` | Env vars not set | Copy `.env.example` to `.env`, set `AGOL_USER`+`AGOL_PASSWORD` (preferred) or `AGOL_API_KEY`. |
| `No File Geodatabase found at ...` | You haven't run the ArcGIS Pro packager yet | Run `package_arcgis_pro.py` first; it produces the GDB. |
| WARN: `subscription type is 'Location Platform'...` | Account tier doesn't include hosted feature service publishing | Upgrade to an ArcGIS Online subscription. The 21-day trial covers full publishing for testing. |
| `publish silently returned item-info instead of services` | Either the subscription tier issue above, OR an API key without the publish scope | First check the subscription type at arcgis.com → My Organization. If it's already ArcGIS Online, switch from `AGOL_API_KEY` to `AGOL_USER`+`AGOL_PASSWORD` to bypass API-key scopes. |
| `AGOL connect failed: ...` | Wrong password, MFA required, IP-restricted org | Verify in a browser first. Organisations with SAML may need additional auth flow — extend `_load_credentials()`. |
| `renderer failed for layer ...` | Sidecar field absent on the published layer | Check the layer's `fields` via `{fs_url}/{idx}?f=json`; the sidecar's `field` must be a real column. |

## Roadmap (v1.1+)

- Enterprise publishing (SAML, PKI auth)
- GeoServer adapter (SLD from sidecar)
- Static-site adapter (S3 / GitHub Pages / Netlify)
- StoryMap / Dashboard authoring (planned — out of scope for v1)

See `docs/extending/PUBLISHING_ADAPTERS.md` for the adapter contract and how to contribute one.
