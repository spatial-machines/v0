# Publishing Adapters

spatial-machines delivers analysis outputs to the local filesystem by default and can additionally push them to external platforms via publishing adapters. This guide covers the adapter architecture, the shipped ArcGIS Online adapter, and how to add one.

**Status:**

| Target | State | Entry point |
|---|---|---|
| **ArcGIS Online** | **Shipped (v1)** | `scripts/core/publish_arcgis_online.py` · `scripts/core/publishing/arcgis_online.py` |
| ArcGIS Enterprise | Stub — raises `NotImplementedError` | `scripts/core/publishing/enterprise.py` |
| GeoServer | Stub | `scripts/core/publishing/geoserver.py` |
| S3 / GitHub Pages / Netlify | Stub | `scripts/core/publishing/s3.py` |

The framework (`scripts/core/publishing/base.py`) is in place; adding a new adapter means implementing a subclass of `PublishAdapter` and registering a CLI wrapper next to `publish_arcgis_online.py`.

## Architecture

Publishing adapters sit at the end of the pipeline (Stage 7: Delivery Packaging). The delivery-packaging agent (site-publisher) organizes outputs into the standard directory structure, then an adapter pushes them to an external system — **only when the project brief opts in via `outputs.publish_targets`**.

```
Pipeline: ... → Reporting → Delivery Packaging → [Publishing Adapter] → External System
```

The adapter contract (see `scripts/core/publishing/base.py`):

```python
class PublishAdapter:
    target: str                                  # e.g. "arcgis_online"
    def validate(self, request: PublishRequest) -> PublishResult: ...   # dry-run
    def publish(self, request: PublishRequest) -> PublishResult: ...    # real upload
```

Steps every adapter follows:
1. Load credentials from `.env` (never log them).
2. Validate the request — build payloads, check cardinalities, short-circuit on error.
3. On `dry_run=True`, return the validated `PublishResult` without touching the target API.
4. On real publish: upload artifacts, record item IDs + URLs, apply sharing.
5. Write `publish-status.json` to the appropriate `outputs/<target>/` folder.

`PublishResult` fields:
- `target`, `status` (`ok` | `dry-run` | `partial` | `error`)
- `started_at`, `ended_at` (ISO8601 UTC)
- `items[]` — each uploaded/planned item with id, title, URL, category, source
- `web_map_url` (when applicable)
- `warnings[]`, `errors[]`
- `request` — echo of the request minus credentials, for audit trail

## Shipped reference: ArcGIS Online

Pure REST via `requests` — no `arcgis` Python package dependency. Scope is intentionally narrow: AGOL gets hosted layers + a Web Map; map PNGs, charts, and the HTML report stay local.

**What it does:**
- Resolves a File Geodatabase from `<analysis>/outputs/arcgis/data/project.gdb` (produced by `package_arcgis_pro.py`). Refuses to run with a clear error if the GDB doesn't exist.
- Zips the GDB, uploads as a `File Geodatabase` item.
- Calls `/publish` with `fileType=fileGeodatabase` → returns ONE hosted Feature Service with N feature layers (one per feature class).
- For each layer, introspects the service to get fields, matches to the corresponding `.style.json` sidecar using the same logic as `package_arcgis_pro._plan_lyrx_from_sidecars` (`source_gpkg` stem → field-presence → categorical fallback), and applies the renderer via `updateDefinition`.
- Assembles ONE Web Map referencing every layer in the service with a Light-Gray-Canvas basemap.
- Applies sharing (PRIVATE by default).
- Probes `portals/self.subscriptionInfo` in dry-run and warns if the account tier doesn't support hosted feature service publishing (Location Platform / Developer accounts can upload but `/publish` silently no-ops).
- On publish failure, auto-deletes the orphan GDB item so re-runs don't pile up dead source items.
- Writes `<analysis>/outputs/arcgis/publish-status.json`.

**Credentials** (in `.env`):

| Variable | Purpose |
|---|---|
| `AGOL_URL` | Default `https://www.arcgis.com`. Override for custom orgs. |
| `AGOL_USER` + `AGOL_PASSWORD` | **Preferred** — token-exchange auth inherits the account's full privileges. |
| `AGOL_API_KEY` | Alternative — API keys carry their own scope list separate from the user's privileges; may lack publish scope even when the user has it. |

**Prerequisite:** run `package_arcgis_pro.py` first to produce the GDB.

**CLI:**

```bash
# Always dry-run first (includes subscription-tier probe)
python scripts/core/publish_arcgis_online.py analyses/my-project/ \
    --title "My Project" --dry-run

# Real upload
python scripts/core/publish_arcgis_online.py analyses/my-project/ \
    --title "My Project" --tags equity demographics --sharing org

# Teardown everything the run created
python scripts/core/teardown_agol.py analyses/my-project/
```

See [ARCGIS_ONLINE_PUBLISHING.md](../wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md) for the full workflow, subscription-tier note, troubleshooting, and teardown loop.

### GeoServer

**What it would do:**
- Upload GeoPackage or Shapefile as a new layer
- Create a styled layer using SLD (Styled Layer Descriptor)
- Register the layer in a GeoServer workspace

**What you'd need:**
- Running GeoServer instance with REST API enabled
- GeoServer admin credentials in `.env`
- `requests` package for the REST API (or use urllib)

**Implementation sketch:**
```python
# Create workspace
PUT /geoserver/rest/workspaces -d '{"workspace": {"name": "spatial-machines"}}'

# Upload data store
PUT /geoserver/rest/workspaces/spatial-machines/datastores/myproject/file.gpkg
Content-Type: application/x-sqlite3

# Publish layer
POST /geoserver/rest/workspaces/spatial-machines/datastores/myproject/featuretypes
```

### Static Web Publishing (S3 / GitHub Pages / Netlify)

**What it would do:**
- Build a static HTML site from analysis outputs (maps, reports, interactive maps)
- Upload to S3, GitHub Pages, Netlify, or any static hosting
- Generate an index page linking all project deliverables

**What you'd need:**
- Static site template (HTML/CSS — could be adapted from the existing site templates)
- Hosting credentials in `.env` or CI/CD environment
- AWS CLI, `gh-pages`, or Netlify CLI for deployment

**Implementation sketch:**
```bash
# Build static site
python scripts/core/build_static_site.py --project analyses/my-analysis/ --output site/build/

# Deploy to S3
aws s3 sync site/build/ s3://my-gis-reports/ --acl public-read

# Or deploy to GitHub Pages
npx gh-pages -d site/build/
```

### Cloud Storage (S3 / GCS / Azure Blob)

**What it would do:**
- Upload analysis outputs to cloud storage for team access
- Generate signed URLs for sharing specific deliverables
- Organize outputs in a consistent bucket structure

**Implementation sketch:**
```python
import boto3
s3 = boto3.client("s3")
for output_file in outputs_dir.rglob("*"):
    key = f"projects/{project_id}/{output_file.relative_to(outputs_dir)}"
    s3.upload_file(str(output_file), bucket, key)
```

### Email / Notification

**What it would do:**
- Send a summary email with key findings and map attachments
- Post to Slack/Teams with analysis results
- Trigger a webhook on analysis completion

## Building a Publishing Adapter

The reference implementation is `scripts/core/publishing/arcgis_online.py` — start there and mirror its shape.

### Step 1: Subclass `PublishAdapter`

Create `scripts/core/publishing/<target>.py`:

```python
from .base import PublishAdapter, PublishRequest, PublishResult

class MyAdapter(PublishAdapter):
    target = "my_target"

    def validate(self, request: PublishRequest) -> PublishResult:
        result = PublishResult(target=self.target, status="dry-run",
                               started_at=self._now(),
                               request=_request_summary(request))
        # Check credentials, build payload for each planned item.
        # Set result.status = "error" and populate result.errors on failure.
        result.ended_at = self._now()
        return result

    def publish(self, request: PublishRequest) -> PublishResult:
        if request.dry_run:
            return self.validate(request)
        # Real upload. Populate result.items with {id, title, itemUrl, category, source}.
        # Catch per-item failures into result.warnings; only fail the overall
        # request when nothing can proceed.
        ...
```

Use `PublishAdapter._write_status(analysis_dir, target, result, subdir="...")` to persist `publish-status.json`. Use `PublishAdapter._collect_from_analysis(analysis_dir)` if you want the default file enumeration.

### Step 2: Write a CLI wrapper

Add `scripts/core/publish_<target>.py` that:

1. Loads `.env` (see `_load_dotenv()` in `publish_arcgis_online.py`).
2. Builds a `PublishRequest` from CLI args + walked outputs.
3. Calls `adapter.publish(request)` (which delegates to `validate()` when `--dry-run`).
4. Prints a human-readable summary.

### Step 3: Register with the Site Publisher

Add to `agents/site-publisher/TOOLS.md` under the "External Publishing" section. Document credential env vars in `.env.example`. Add a workflow page under `docs/wiki/workflows/`.

### Step 4: Document it here

Add a table row at the top of this file and a short section covering what the adapter uploads, credentials needed, and sharing defaults.

## Design Principles for Adapters

1. **Never modify source outputs.** Adapters read from `outputs/` and push copies. The local deliverables remain intact.
2. **Dry-run must be cheap and informative.** `validate()` should exercise credential loading and payload construction without hitting the external API. Consumers rely on `--dry-run` for safety.
3. **Default sharing = PRIVATE.** Promotion to ORG/PUBLIC requires an explicit flag or brief field. Never auto-promote.
4. **Write a publish status artifact.** Record what was published (or planned), where, and when — including a `request` echo minus credentials for audit.
5. **Fail gracefully.** Per-item failures go into `result.warnings` and do not fail the whole request. Only top-level auth/connection failures fail the adapter.
6. **Credentials from .env only.** Never hardcode, never prompt interactively, never log. Use the same env-var pattern across adapters so `.env` discovery is consistent.
7. **Idempotent (best effort).** Running twice should update rather than duplicate; when the target API doesn't support upserts, document the teardown path.
8. **Lazy-import heavy / proprietary deps.** `import arcgis` happens inside `_connect()`, not at module top. That lets the module and its `--dry-run` path load on any machine.
