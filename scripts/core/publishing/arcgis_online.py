"""ArcGIS Online (AGOL) publishing adapter — REST API implementation.

Talks to the documented AGOL REST endpoints directly via `requests`, no
`arcgis` Python API dependency. The `arcgis` package has a long history
of Python-version-sensitive bugs (distutils imports, internal-import
drift, session-deepcopy ssl_context); using the stable REST surface
avoids all of it.

Scope (intentionally narrow):
  - uploads ONE File Geodatabase (the one produced by package_arcgis_pro.py)
  - /publish turns it into ONE hosted Feature Service with N feature layers
  - `.style.json` sidecars drive per-layer renderers via
    `renderers.agol_renderer()` and `updateDefinition`
  - assembles a single Web Map referencing every layer in that service

Deliberately out of scope on AGOL:
  - map PNGs, chart PNGs, HTML report (these are local-only deliverables;
    AGOL's strength is hosted feature layers + Web Maps). The helper
    functions `_upload_image` and `_upload_report` are kept dormant below
    in case a future sharing mode wants them, but the main `publish()`
    flow no longer calls them.

Safety defaults:
  - sharing = PRIVATE unless the project brief sets `publish_sharing`
  - dry-run validates inputs and plans the payload without touching AGOL
  - credentials are never logged

Environment (one of these two auth modes):
    AGOL_URL        default: https://www.arcgis.com
    AGOL_API_KEY    API key — single-arg auth, preferred
    AGOL_USER       + AGOL_PASSWORD — token exchange auth

REST endpoints used (all under {AGOL_URL}/sharing/rest/):
    community/self                                   — resolve username from token
    content/users/{user}/addItem                     — create an item
    content/users/{user}/items/{id}/publish          — publish hosted FS from item
    content/users/{user}/items/{id}/share            — set sharing
    content/users/{user}/items/{id}/delete           — cleanup (used by teardown)
    {feature_service_url}?f=json                     — list service layers
    {feature_service_url}/{layer_idx}?f=json         — get layer fields
    {feature_service_url}/{layer_idx}/updateDefinition — apply renderer
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import requests

SCRIPTS_CORE = Path(__file__).resolve().parents[1]
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from renderers import agol_renderer  # shared sidecar->renderer translation

from .base import PublishAdapter, PublishRequest, PublishResult


SHARING_VALUES = ("PRIVATE", "ORG", "PUBLIC")
HTTP_TIMEOUT = 300        # seconds — big gpkg uploads can take a while
PUBLISH_POLL_SECS = 3
PUBLISH_MAX_WAIT = 300    # cap spent waiting for hosted FS to build


# ═════════════════════════════════════════════════════════════════════════
# HTTP client
# ═════════════════════════════════════════════════════════════════════════

class AGOLClient:
    """Minimal REST client. Holds the base URL, token, and username."""

    def __init__(self, base_url: str, token: str, username: str,
                 portal_id: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.username = username
        self.portal_id = portal_id
        self.session = requests.Session()

    # ── request helpers ────────────────────────────────────────────

    def _check_response(self, r: requests.Response, context: str) -> dict:
        """Raise on HTTP error or AGOL-embedded error; return parsed JSON."""
        r.raise_for_status()
        try:
            body = r.json()
        except ValueError as exc:
            raise RuntimeError(
                f"{context}: non-JSON response ({len(r.content)} bytes)"
            ) from exc
        if isinstance(body, dict) and body.get("error"):
            err = body["error"]
            msg = err.get("message") or err.get("messageCode") or str(err)
            raise RuntimeError(f"{context}: AGOL error {err.get('code')}: {msg}")
        return body

    def get(self, path: str, **params) -> dict:
        url = f"{self.base_url}{path}"
        params.setdefault("f", "json")
        params["token"] = self.token
        r = self.session.get(url, params=params, timeout=HTTP_TIMEOUT)
        return self._check_response(r, f"GET {path}")

    def post(self, path: str, *, data: dict | None = None,
             files: dict | None = None, **params) -> dict:
        url = f"{self.base_url}{path}"
        params.setdefault("f", "json")
        params["token"] = self.token
        post_data = {**(data or {}), **params}
        r = self.session.post(
            url, data=post_data, files=files, timeout=HTTP_TIMEOUT,
        )
        return self._check_response(r, f"POST {path}")

    def post_absolute(self, url: str, *, data: dict | None = None,
                      **params) -> dict:
        """For endpoints that return full URLs (feature service, etc.)."""
        params.setdefault("f", "json")
        params["token"] = self.token
        post_data = {**(data or {}), **params}
        r = self.session.post(url, data=post_data, timeout=HTTP_TIMEOUT)
        return self._check_response(r, f"POST {url}")

    # ── content operations ─────────────────────────────────────────

    def add_item(self, meta: dict, file_path: Path | None = None,
                 thumbnail: Path | None = None) -> dict:
        """POST /sharing/rest/content/users/{username}/addItem.

        Returns {'id': <item_id>, ...}. Raises on failure.
        """
        path = f"/sharing/rest/content/users/{self.username}/addItem"
        files: dict = {}
        if file_path and file_path.exists():
            mt = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            files["file"] = (file_path.name, file_path.open("rb"), mt)
        if thumbnail and thumbnail.exists():
            mt = mimetypes.guess_type(str(thumbnail))[0] or "image/png"
            files["thumbnail"] = (thumbnail.name, thumbnail.open("rb"), mt)
        try:
            body = self.post(path, data=meta, files=files or None)
        finally:
            for f in files.values():
                try:
                    f[1].close()  # close file handles
                except Exception:  # noqa: BLE001
                    pass
        item_id = body.get("id")
        if not item_id:
            raise RuntimeError(f"addItem returned no id: {body}")
        body["id"] = item_id
        return body

    def publish_item(self, item_id: str, publish_params: dict | None = None,
                     file_type: str = "geoPackage") -> dict:
        path = f"/sharing/rest/content/users/{self.username}/items/{item_id}/publish"
        data = {"fileType": file_type}
        if publish_params:
            data["publishParameters"] = json.dumps(publish_params)
        body = self.post(path, data=data)

        # AGOL has a quirk where /publish silently returns the item-info
        # response shape `{item: {...}, sharing: {...}}` (HTTP 200, no
        # `error` key) when the *subscription tier* doesn't support
        # publishing hosted feature services. Free "Location Platform"
        # developer accounts (the default at developers.arcgis.com) include
        # geocoding, routing, basemaps, etc. but NOT hosted feature service
        # publishing — even though the account role lists
        # `portal:publisher:publishFeatures` in its privileges. AGOL accepts
        # the upload (addItem succeeds) and accepts /analyze, but silently
        # no-ops /publish.
        #
        # This was reproduced with both AGOL_API_KEY and AGOL_USER+PASSWORD
        # auth on a Location Platform subscription; the body returned is
        # identical in both cases. The fix is on the AGOL side: upgrade to
        # an "ArcGIS Online" subscription that includes hosted feature
        # service publishing.
        if "item" in body and "sharing" in body and "services" not in body:
            raise RuntimeError(
                "publish silently returned item-info instead of services. "
                "Most common cause: your AGOL subscription is a Location "
                "Platform / Developer tier that doesn't include hosted "
                "feature service publishing (the upload succeeded, but "
                "AGOL won't create a Feature Service from it). Check at "
                "https://www.arcgis.com/home/organization.html -- if your "
                "subscription type is 'Location Platform', you need an "
                "ArcGIS Online subscription to use this adapter. "
                "If you DO have an ArcGIS Online subscription, this could "
                "also be an API key scope issue: switch to AGOL_USER + "
                "AGOL_PASSWORD auth in .env to bypass API key scopes."
            )

        services = body.get("services") or []
        if not services:
            raise RuntimeError(f"publish returned no services: {body}")
        service = services[0]
        if service.get("error"):
            err = service["error"]
            raise RuntimeError(
                f"publish service error: {err.get('message') or err}"
            )
        return service

    def delete_item(self, item_id: str) -> dict:
        """Best-effort delete; used to clean up orphans after publish failure."""
        path = f"/sharing/rest/content/users/{self.username}/items/{item_id}/delete"
        return self.post(path, data={})

    def wait_for_job(self, item_id: str, job_id: str) -> dict:
        """Poll an item's status job until success or timeout."""
        path = f"/sharing/rest/content/users/{self.username}/items/{item_id}/status"
        deadline = time.time() + PUBLISH_MAX_WAIT
        while time.time() < deadline:
            body = self.get(path, jobId=job_id)
            status = (body.get("status") or "").lower()
            if status in ("completed", "succeeded"):
                return body
            if status in ("failed", "error"):
                raise RuntimeError(f"publish job failed: {body}")
            time.sleep(PUBLISH_POLL_SECS)
        raise RuntimeError(
            f"publish job {job_id} did not complete in {PUBLISH_MAX_WAIT}s"
        )

    def share_item(self, item_id: str, sharing: str) -> dict:
        path = f"/sharing/rest/content/users/{self.username}/items/{item_id}/share"
        params = {
            "PRIVATE": {"everyone": "false", "org": "false"},
            "ORG":     {"everyone": "false", "org": "true"},
            "PUBLIC":  {"everyone": "true",  "org": "true"},
        }[sharing]
        return self.post(path, data=params)

    def item_home_url(self, item_id: str) -> str:
        return f"{self.base_url}/home/item.html?id={item_id}"

    def update_layer_renderer(self, service_url: str, layer_idx: int,
                              renderer: dict) -> dict:
        path = f"{service_url.rstrip('/')}/{layer_idx}/updateDefinition"
        return self.post_absolute(
            path,
            data={"updateDefinition": json.dumps({"drawingInfo":
                                                  {"renderer": renderer}})},
        )


# ═════════════════════════════════════════════════════════════════════════
# Adapter
# ═════════════════════════════════════════════════════════════════════════

class ArcGISOnlineAdapter(PublishAdapter):
    target = "arcgis_online"

    def __init__(self) -> None:
        self._client: AGOLClient | None = None

    # ── public API ────────────────────────────────────────────────

    def validate(self, request: PublishRequest) -> PublishResult:
        result = PublishResult(
            target=self.target, status="dry-run",
            started_at=self._now(), request=_request_summary(request),
        )
        creds = _load_credentials(request, result.warnings, result.errors)
        gdb_path = _resolve_gdb_path(request, result.errors)
        if result.errors:
            result.status = "error"
            result.ended_at = self._now()
            return result
        planned = _plan_gdb_items(request, gdb_path, result.warnings)
        for p in planned:
            result.items.append(p)
        # Probe subscription tier so the dry-run flags non-publishing
        # accounts (Location Platform / Developer) before any upload happens.
        if creds:
            try:
                self._connect(creds)
                self._check_subscription_supports_hosting(result.warnings)
            except Exception as exc:  # noqa: BLE001
                result.warnings.append(f"subscription probe skipped: {exc}")
        result.ended_at = self._now()
        return result

    def publish(self, request: PublishRequest) -> PublishResult:
        if request.dry_run:
            return self.validate(request)

        result = PublishResult(
            target=self.target, status="ok",
            started_at=self._now(), request=_request_summary(request),
        )
        creds = _load_credentials(request, result.warnings, result.errors)
        gdb_path = _resolve_gdb_path(request, result.errors)
        if result.errors:
            result.status = "error"
            result.ended_at = self._now()
            return result

        try:
            client = self._connect(creds)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"AGOL connect failed: {exc}")
            result.status = "error"
            result.ended_at = self._now()
            return result

        sharing = request.sharing if request.sharing in SHARING_VALUES else "PRIVATE"

        # Pre-flight: warn (but don't block) if the subscription tier won't
        # support hosted publishing. /publish will fail loudly afterwards
        # via the item-info detection in publish_item; this just front-loads
        # the diagnosis so logs read more clearly.
        self._check_subscription_supports_hosting(result.warnings)

        # 1. Zip the .gdb and upload it as a File Geodatabase item
        try:
            gdb_zip = _zip_gdb(gdb_path)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"GDB zip failed: {exc}")
            result.status = "error"
            result.ended_at = self._now()
            return result

        try:
            gdb_rec = _upload_file_geodatabase(client, gdb_zip, request)
            result.items.append(gdb_rec)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"GDB upload failed: {exc}")
            result.status = "error"
            result.ended_at = self._now()
            _cleanup_zip(gdb_zip)
            return result
        finally:
            # Zip uploaded; local copy no longer needed.
            pass
        _cleanup_zip(gdb_zip)

        # 2. Publish GDB item → single hosted Feature Service with N layers
        try:
            fs_rec = _publish_gdb_to_service(client, gdb_rec["id"], request)
            result.items.append(fs_rec)
            fs_url = fs_rec["service_url"]
            fs_item_id = fs_rec["id"]
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"GDB publish failed: {exc}")
            # Clean up the orphan GDB item so re-runs don't pile up dead
            # source items in the user's AGOL content.
            try:
                client.delete_item(gdb_rec["id"])
                result.warnings.append(
                    f"cleaned up orphan GDB item {gdb_rec['id']}"
                )
            except Exception as del_exc:  # noqa: BLE001
                result.warnings.append(
                    f"could not clean up orphan GDB item {gdb_rec['id']}: "
                    f"{del_exc}"
                )
            result.status = "error"
            result.ended_at = self._now()
            return result

        # 3. Introspect service layers and apply renderers per-layer from sidecars
        try:
            layers = _fetch_service_layers(client, fs_url)
        except Exception as exc:  # noqa: BLE001
            result.warnings.append(f"layer introspection failed: {exc}")
            layers = []

        if layers and request.style_dir and request.style_dir.exists():
            plans, match_warnings = _match_layers_to_sidecars(
                layers, request.style_dir,
            )
            for w in match_warnings:
                result.warnings.append(w)
            for plan in plans:
                try:
                    renderer = agol_renderer(plan["data"])
                    if renderer:
                        client.update_layer_renderer(
                            fs_url, plan["layer_id"], renderer,
                        )
                        result.items.append({
                            "category": "renderer_applied",
                            "layer_id": plan["layer_id"],
                            "layer_name": plan["layer_name"],
                            "sidecar": plan["sidecar_name"],
                            "match_via": plan["match_via"],
                        })
                except Exception as exc:  # noqa: BLE001
                    result.warnings.append(
                        f"renderer failed for layer {plan['layer_name']}: {exc}"
                    )

        # 4. Build + upload a Web Map referencing every layer in the service
        try:
            wm_rec = _build_web_map_from_service(
                client, request, fs_url, fs_item_id, layers,
            )
            result.items.append(wm_rec)
            result.web_map_url = wm_rec.get("itemUrl")
        except Exception as exc:  # noqa: BLE001
            result.warnings.append(f"web map build failed: {exc}")

        # 5. Apply sharing. Filter out synthetic (non-item) records first.
        shareable = [r for r in result.items if r.get("id")]
        _apply_sharing(client, shareable, sharing, result.warnings)

        if result.errors:
            result.status = "error"
        elif result.warnings:
            result.status = "partial"
        result.ended_at = self._now()
        return result

    # ── auth ──────────────────────────────────────────────────────

    def _connect(self, creds: dict[str, str]) -> AGOLClient:
        """Resolve creds to an AGOLClient with token + username.

        Prefers user/password over api_key when both are present. API keys
        from developers.arcgis.com carry their own scope list separate from
        the user account; user/password tokens inherit the account's full
        privileges. Defaulting to user/password avoids an entire class of
        confusing "publish silently failed" errors.
        """
        base = creds["url"].rstrip("/")
        if creds.get("user") and creds.get("password"):
            token = _generate_token(base, creds["user"], creds["password"])
        elif creds.get("api_key"):
            token = creds["api_key"]
        else:
            raise RuntimeError("no AGOL credentials available")

        # Discover the logged-in username and org id by hitting community/self.
        # API-key tokens return a pseudo-user; username/password tokens return
        # the real account — both work for /content/users/{username}/addItem.
        self_body = _post(
            f"{base}/sharing/rest/community/self",
            data={"f": "json", "token": token},
        )
        username = self_body.get("username") or self_body.get("user", {}).get(
            "username")
        if not username:
            raise RuntimeError(
                f"could not determine AGOL username from community/self: "
                f"{self_body}"
            )
        self._client = AGOLClient(
            base, token, username, portal_id=self_body.get("orgId"),
        )
        return self._client

    def _check_subscription_supports_hosting(self, warnings: list) -> None:
        """Probe portals/self.subscriptionInfo and warn if the account is on
        a tier that doesn't support hosted feature service publishing.

        Location Platform / Developer subscriptions can geocode and route but
        cannot publish hosted feature services; AGOL accepts the upload then
        silently no-ops /publish. Surfacing this at validate-time saves a
        round-trip and a cleanup cycle.
        """
        try:
            body = self._client.post(
                "/sharing/rest/portals/self", data={},
            )
        except Exception:  # noqa: BLE001
            return
        sub = body.get("subscriptionInfo") or {}
        sub_type = sub.get("type") or ""
        if sub_type and "Location Platform" in sub_type:
            warnings.append(
                f"AGOL subscription type is '{sub_type}' which typically "
                "does NOT support hosted feature service publishing. The "
                "upload will succeed but /publish will silently no-op. "
                "Upgrade to an ArcGIS Online subscription to use this adapter."
            )


# ═════════════════════════════════════════════════════════════════════════
# Credential loading + token exchange
# ═════════════════════════════════════════════════════════════════════════

def _load_credentials(request: PublishRequest, warnings: list,
                      errors: list) -> dict[str, str]:
    opts = request.options or {}
    url = (opts.get("agol_url")
           or os.environ.get("AGOL_URL", "https://www.arcgis.com"))
    api_key = opts.get("agol_api_key") or os.environ.get("AGOL_API_KEY")
    user = opts.get("agol_user") or os.environ.get("AGOL_USER")
    password = opts.get("agol_password") or os.environ.get("AGOL_PASSWORD")

    if not api_key and not (user and password):
        errors.append(
            "AGOL credentials missing. Set AGOL_API_KEY, "
            "or both AGOL_USER and AGOL_PASSWORD, in your .env."
        )
        return {}
    return {"url": url, "api_key": api_key or "",
            "user": user or "", "password": password or ""}


def _post(url: str, *, data: dict) -> dict:
    r = requests.post(url, data=data, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and body.get("error"):
        err = body["error"]
        msg = err.get("message") or str(err)
        raise RuntimeError(f"{url}: AGOL error: {msg}")
    return body


def _generate_token(base_url: str, username: str, password: str) -> str:
    """Exchange username+password for a short-lived token."""
    body = _post(
        f"{base_url}/sharing/rest/generateToken",
        data={
            "username": username, "password": password,
            "referer": base_url, "expiration": 60, "f": "json",
        },
    )
    tok = body.get("token")
    if not tok:
        raise RuntimeError(f"generateToken returned no token: {body}")
    return tok


# ═════════════════════════════════════════════════════════════════════════
# GDB resolution, zipping, upload, publish
# ═════════════════════════════════════════════════════════════════════════

def _resolve_gdb_path(request: PublishRequest, errors: list) -> Path | None:
    """Return the File Geodatabase path we should upload.

    Priority:
      1. `request.options["gdb_file"]` if present.
      2. `<analysis_dir>/outputs/arcgis/data/project.gdb` — the canonical
         location produced by `package_arcgis_pro.py`.
    """
    opts = request.options or {}
    override = opts.get("gdb_file")
    if override:
        p = Path(override)
        if not p.exists() or not p.is_dir():
            errors.append(
                f"options.gdb_file does not exist or is not a directory: {p}"
            )
            return None
        return p

    default_gdb = request.analysis_dir / "outputs" / "arcgis" / "data" / "project.gdb"
    if not default_gdb.exists():
        errors.append(
            f"No File Geodatabase found at {default_gdb}. "
            f"Run `python scripts/core/package_arcgis_pro.py {request.analysis_dir}` "
            f"first to produce it."
        )
        return None
    return default_gdb


def _zip_gdb(gdb_path: Path) -> Path:
    """Zip the `.gdb/` folder into a temp `.zip` that AGOL can ingest.

    AGOL expects the archive to contain the `.gdb/` directory at its root
    (the zip itself is named anything; inside it, the folder must end in
    `.gdb` and contain the gdbtable/gdbtablx files directly).
    """
    if not gdb_path.is_dir():
        raise RuntimeError(f"GDB path is not a directory: {gdb_path}")
    fd, zip_path_str = tempfile.mkstemp(prefix="agol_gdb_", suffix=".zip")
    os.close(fd)
    zip_path = Path(zip_path_str)
    gdb_name = gdb_path.name     # preserves "project.gdb"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in gdb_path.rglob("*"):
            if p.is_file():
                arcname = Path(gdb_name) / p.relative_to(gdb_path)
                zf.write(p, arcname.as_posix())
    return zip_path


def _cleanup_zip(zip_path: Path) -> None:
    try:
        if zip_path.exists():
            zip_path.unlink()
    except OSError:
        pass


def _upload_file_geodatabase(client: AGOLClient, gdb_zip: Path,
                             request: PublishRequest) -> dict:
    """Upload the zipped .gdb as a File Geodatabase item.

    Returns the item record (id, title, itemUrl).
    """
    meta = {
        "type": "File Geodatabase",
        "title": f"{request.title} \u2014 Data",
        "description": request.description or f"File Geodatabase for {request.title}",
        "tags": _comma_tags(
            request.tags + [request.title, "spatial-machines", "file-geodatabase"]
        ),
    }
    body = client.add_item(meta, file_path=gdb_zip)
    return {
        "id": body["id"],
        "title": meta["title"],
        "type": "File Geodatabase",
        "itemUrl": client.item_home_url(body["id"]),
        "category": "source_gdb",
        "source": str(gdb_zip.name),
    }


def _publish_gdb_to_service(client: AGOLClient, gdb_item_id: str,
                            request: PublishRequest) -> dict:
    """Publish a File Geodatabase item → hosted Feature Service with N layers.

    Returns the service record (id, service_url, title).
    """
    service_name = _sanitize_service_name(
        f"{_slugify(request.title)}_{gdb_item_id[:6]}"
    )
    publish_params = {
        "name": service_name,
        # targetSR default is 102100 (Web Mercator). Leave it unless the
        # caller overrides via options.
    }
    service_info = client.publish_item(
        gdb_item_id,
        publish_params=publish_params,
        file_type="fileGeodatabase",
    )
    fs_item_id = service_info["serviceItemId"]
    fs_url = service_info.get("serviceurl") or service_info.get("encServiceURL")
    job_id = service_info.get("jobId")
    if job_id:
        try:
            client.wait_for_job(gdb_item_id, job_id)
        except Exception:  # noqa: BLE001
            # Service may still be usable; surface as warning upstream if so.
            pass
    return {
        "id": fs_item_id,
        "source_item_id": gdb_item_id,
        "title": f"{request.title} \u2014 Feature Service",
        "type": "Feature Service",
        "itemUrl": client.item_home_url(fs_item_id),
        "service_url": fs_url,
        "category": "feature_service",
    }


def _fetch_service_layers(client: AGOLClient, fs_url: str) -> list[dict]:
    """Return [{id, name, fields: set[str]}, ...] for every layer in the
    hosted service. `id` is the integer layer index used by
    `updateDefinition`.
    """
    # Service-level listing gives us ids and names.
    body = client.post_absolute(fs_url, data={})
    layer_dicts = body.get("layers") or []
    layers: list[dict] = []
    for ld in layer_dicts:
        lid = ld.get("id")
        name = ld.get("name") or f"layer_{lid}"
        if lid is None:
            continue
        # Fetch fields from /{idx}. Costs an extra call but gives us the
        # authoritative column list used for sidecar field-match fallback.
        try:
            layer_body = client.post_absolute(
                f"{fs_url.rstrip('/')}/{lid}", data={},
            )
            fields = {f.get("name") for f in layer_body.get("fields") or []
                      if f.get("name")}
        except Exception:  # noqa: BLE001
            fields = set()
        layers.append({"id": int(lid), "name": name, "fields": fields})
    return layers


def _match_layers_to_sidecars(
    layers: list[dict],
    style_dir: Path,
) -> tuple[list[dict], list[str]]:
    """Pair each sidecar in `style_dir` with a service layer.

    Mirrors `package_arcgis_pro._plan_lyrx_from_sidecars` so the same
    matching rules drive both the local .lyrx production and the AGOL
    updateDefinition calls.

    Returns (plans, warnings) where each plan carries:
        layer_id:    int   — index used by updateDefinition
        layer_name:  str
        sidecar_name:str
        data:        dict  — parsed sidecar JSON
        match_via:   str
    """
    plans: list[dict] = []
    warnings: list[str] = []
    layer_by_name = {_normalize_layer_name(l["name"]): l for l in layers}
    layer_by_field: dict[str, list[dict]] = {}
    for l in layers:
        for f in l["fields"]:
            layer_by_field.setdefault(f, []).append(l)

    for sc in sorted(style_dir.glob("*.style.json")):
        try:
            data = json.loads(sc.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"sidecar unreadable: {sc.name} ({exc})")
            continue

        # 1. source_gpkg / source_layer → layer name
        src_stem = _sidecar_source_stem(data)
        if src_stem:
            norm = _normalize_layer_name(src_stem)
            if norm in layer_by_name:
                l = layer_by_name[norm]
                plans.append({
                    "layer_id": l["id"],
                    "layer_name": l["name"],
                    "sidecar_name": sc.name,
                    "data": data,
                    "match_via": "source_gpkg/source_layer",
                })
                continue

        # 2. Field presence — unambiguous only
        field = data.get("field")
        if field:
            hits = layer_by_field.get(field, [])
            if len(hits) == 1:
                l = hits[0]
                plans.append({
                    "layer_id": l["id"],
                    "layer_name": l["name"],
                    "sidecar_name": sc.name,
                    "data": data,
                    "match_via": f"field='{field}'",
                })
                continue
            elif len(hits) > 1:
                names = [h["name"] for h in hits]
                warnings.append(
                    f"sidecar {sc.name}: field '{field}' present on "
                    f"{len(hits)} layers ({names}); set 'source_gpkg' "
                    f"in the sidecar to disambiguate"
                )
                continue

        # 3. Categorical fallback — no field, categorical_map present
        cat_map = data.get("categorical_map") or data.get("categories")
        if cat_map and not field:
            category_cols = {"hotspot_class", "lisa_cluster", "cluster", "class"}
            match = next(
                ((l, next(iter(category_cols & l["fields"])))
                 for l in layers if category_cols & l["fields"]),
                None,
            )
            if match:
                l, col = match
                plans.append({
                    "layer_id": l["id"],
                    "layer_name": l["name"],
                    "sidecar_name": sc.name,
                    "data": data,
                    "match_via": f"category column '{col}'",
                })
                continue

        if field:
            warnings.append(
                f"sidecar {sc.name}: field '{field}' is not on any layer "
                f"in the feature service"
            )
        else:
            warnings.append(
                f"sidecar {sc.name}: no source_gpkg, no field, no "
                f"categorical_map \u2014 can't resolve a target layer"
            )
    return plans, warnings


def _sidecar_source_stem(data: dict) -> str | None:
    """Match `package_arcgis_pro._sidecar_source_stem` exactly."""
    for key in ("source_gpkg", "source_layer"):
        val = data.get(key)
        if val:
            return Path(str(val).replace("\\", "/")).stem
    return None


def _normalize_layer_name(name: str) -> str:
    """Normalize layer names for comparison: lowercased, non-alnum → _.

    AGOL service layers can get their names mangled during publish
    (dots replaced, case changed, etc.). Normalizing both sides lets
    `phila_tracts_enriched` from a sidecar match `Phila_Tracts_Enriched`
    from the service.
    """
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _slugify(text: str) -> str:
    """URL-/service-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "analysis"


def _build_web_map_from_service(
    client: AGOLClient,
    request: PublishRequest,
    fs_url: str,
    fs_item_id: str,
    layers: list[dict],
) -> dict:
    """Assemble a Web Map that references every layer in the single
    hosted Feature Service we just published.
    """
    operational_layers = []
    for l in layers:
        operational_layers.append({
            "id": f"{fs_item_id}_{l['id']}",
            "title": l["name"],
            "url": f"{fs_url.rstrip('/')}/{l['id']}",
            "itemId": fs_item_id,
            "layerType": "ArcGISFeatureLayer",
            "visibility": True,
            "opacity": 1,
            "popupInfo": {"title": l["name"], "description": ""},
        })

    web_map_json = {
        "operationalLayers": operational_layers,
        "baseMap": {
            "baseMapLayers": [{
                "id": "basemap",
                "layerType": "ArcGISTiledMapServiceLayer",
                "url": "https://services.arcgisonline.com/arcgis/rest/services/"
                       "World_Light_Gray_Base/MapServer",
                "title": "Light Gray Canvas",
            }],
            "title": "Light Gray Canvas",
        },
        "spatialReference": {"wkid": 102100},
        "version": "2.24",
    }

    meta = {
        "type": "Web Map",
        "title": f"{request.title} \u2014 Web Map",
        "description": request.description,
        "tags": _comma_tags(request.tags + [request.title, "web-map"]),
        "typeKeywords": "Web Map,Explorer Web Map,Map,Online Map",
        "text": json.dumps(web_map_json),
    }
    body = client.add_item(meta)
    return {
        "id": body["id"],
        "title": meta["title"],
        "type": "Web Map",
        "itemUrl": client.item_home_url(body["id"]),
        "category": "web_map",
        "source": f"web_map({len(operational_layers)} layers)",
    }


def _plan_gdb_items(request: PublishRequest, gdb_path: Path,
                    warnings: list) -> list[dict]:
    """Dry-run payload description. Introspects the .gdb to count feature
    classes so the user sees what a real publish would produce.
    """
    planned: list[dict] = []
    fc_names = _introspect_gdb_fcs(gdb_path, warnings)

    planned.append({
        "category": "source_gdb",
        "source": str(gdb_path),
        "title": f"{request.title} \u2014 Data",
        "type": "File Geodatabase",
        "feature_classes": fc_names,
    })
    planned.append({
        "category": "feature_service",
        "title": f"{request.title} \u2014 Feature Service",
        "type": "Feature Service",
        "layer_count": len(fc_names),
        "layer_names": fc_names,
    })
    planned.append({
        "category": "web_map",
        "title": f"{request.title} \u2014 Web Map",
        "layer_count": len(fc_names),
    })

    # Sidecar planning (how many renderers would be applied).
    if request.style_dir and request.style_dir.exists():
        sidecars = sorted(request.style_dir.glob("*.style.json"))
        planned.append({
            "category": "renderer_plan",
            "sidecars_found": len(sidecars),
            "note": "exact layer matching happens after publish",
        })
    else:
        warnings.append("no style_dir; layers will render with AGOL defaults")
    return planned


def _introspect_gdb_fcs(gdb_path: Path, warnings: list) -> list[str]:
    """Return feature class names inside a .gdb.

    Tries GDAL's OpenFileGDB first (authoritative). Falls back to
    enumerating gpkg copies that `package_arcgis_pro.py` placed beside
    the GDB (`<gdb>/../*.gpkg`) — same source data, same sanitized names.
    """
    try:
        from osgeo import ogr  # type: ignore
        ds = ogr.Open(str(gdb_path))
        if ds is None:
            warnings.append(f"GDAL couldn't open GDB: {gdb_path}")
            return _fcs_from_gpkg_copies(gdb_path.parent, warnings)
        names = [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
        ds = None
        return sorted(names)
    except ImportError:
        return _fcs_from_gpkg_copies(gdb_path.parent, warnings)


def _fcs_from_gpkg_copies(data_dir: Path, warnings: list) -> list[str]:
    """Best-effort FC enumeration by reading the gpkgs `package_arcgis_pro.py`
    copied into `<analysis>/outputs/arcgis/data/`.
    """
    out: list[str] = []
    for gpkg in sorted(data_dir.glob("*.gpkg")):
        try:
            conn = sqlite3.connect(str(gpkg))
            rows = conn.execute(
                "SELECT table_name FROM gpkg_contents WHERE data_type='features'"
            ).fetchall()
            conn.close()
            out.extend(r[0] for r in rows)
        except sqlite3.DatabaseError:
            continue
    if not out:
        warnings.append(
            "could not enumerate feature classes "
            "(install GDAL or keep gpkg copies in outputs/arcgis/data/)"
        )
    return sorted(set(out))


# ═════════════════════════════════════════════════════════════════════════
# Per-item upload helpers
# ═════════════════════════════════════════════════════════════════════════
#
# NOTE: `_upload_image`, `_upload_report`, `_upload_geopackage`,
# `_build_web_map`, `_plan_items`, and `_match_sidecar` below are DORMANT
# — retained in case a future sharing mode wants to mirror images/reports
# to AGOL. The live publish flow uses the GDB helpers above.
# ═════════════════════════════════════════════════════════════════════════

def _plan_items(request: PublishRequest, warnings: list) -> list[dict]:
    """Build the payload for every item we'd upload, without contacting AGOL."""
    planned: list[dict] = []
    for gpkg in request.gpkg_files:
        if not gpkg.exists():
            warnings.append(f"gpkg missing: {gpkg}")
            continue
        planned.append({
            "category": "feature_layer",
            "source": str(gpkg),
            "title": f"{request.title} \u2014 {gpkg.stem}",
            "tags": request.tags + [request.title, "spatial-machines"],
            "size_bytes": gpkg.stat().st_size,
        })
    for p in request.map_pngs:
        if not p.exists():
            continue
        planned.append({
            "category": "map", "source": str(p),
            "title": f"{request.title} \u2014 {p.stem}",
            "tags": request.tags + [request.title, "map"],
            "size_bytes": p.stat().st_size,
        })
    for p in request.chart_pngs:
        if not p.exists():
            continue
        planned.append({
            "category": "chart", "source": str(p),
            "title": f"{request.title} \u2014 {p.stem}",
            "tags": request.tags + [request.title, "chart"],
            "size_bytes": p.stat().st_size,
        })
    if request.report_html and request.report_html.exists():
        planned.append({
            "category": "report", "source": str(request.report_html),
            "title": f"{request.title} \u2014 Report",
            "tags": request.tags + [request.title, "report"],
            "size_bytes": request.report_html.stat().st_size,
        })
    if any(p["category"] == "feature_layer" for p in planned):
        planned.append({
            "category": "web_map",
            "title": f"{request.title} \u2014 Web Map",
            "tags": request.tags + [request.title, "web-map"],
            "layer_count": sum(1 for p in planned
                               if p["category"] == "feature_layer"),
        })
    return planned


def _match_sidecar(gpkg: Path, request: PublishRequest) -> Path | None:
    if not request.style_dir or not request.style_dir.exists():
        return None
    stem = gpkg.stem.lower()
    for sc in request.style_dir.glob("*.style.json"):
        try:
            data = json.loads(sc.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        src_gpkg = (data.get("source_gpkg") or "").lower()
        layer = (data.get("layer_name") or "").lower()
        if Path(src_gpkg).name.lower() == gpkg.name.lower() or stem == layer:
            return sc
    return None


def _comma_tags(tags: list[str]) -> str:
    return ",".join(t for t in tags if t)


def _upload_geopackage(client: AGOLClient, gpkg: Path,
                       request: PublishRequest, sidecar: Path | None) -> dict:
    """Upload a .gpkg → GeoPackage item, then publish → hosted FL item."""
    # 1. Create the source GeoPackage item
    meta = {
        "type": "GeoPackage",
        "title": f"{request.title} \u2014 {gpkg.stem}",
        "description": request.description,
        "tags": _comma_tags(request.tags + [request.title, "spatial-machines"]),
    }
    created = client.add_item(meta, file_path=gpkg)
    gp_item_id = created["id"]

    # 2. Publish → hosted feature service
    #    publishParameters.name defaults to the filename; override so the
    #    resulting service name is predictable and title-aligned.
    publish_params = {"name": _sanitize_service_name(gpkg.stem)}
    service_info = client.publish_item(
        gp_item_id, publish_params=publish_params, file_type="geoPackage",
    )
    fs_item_id = service_info["serviceItemId"]
    fs_url = service_info.get("serviceurl") or service_info.get("encServiceURL")
    job_id = service_info.get("jobId")
    if job_id:
        try:
            client.wait_for_job(gp_item_id, job_id)
        except Exception as exc:  # noqa: BLE001
            # Service was created; polling timed out but item may still be usable.
            # Surface as a non-fatal note on the returned record.
            pass

    record = {
        "id": fs_item_id,
        "source_item_id": gp_item_id,
        "title": meta["title"],
        "type": "Feature Service",
        "itemUrl": client.item_home_url(fs_item_id),
        "service_url": fs_url,
        "category": "feature_layer",
        "source": str(gpkg),
    }

    # 3. Apply renderer from the sidecar, if any
    if sidecar and sidecar.exists() and fs_url:
        try:
            sc_data = json.loads(sidecar.read_text(encoding="utf-8"))
            renderer = agol_renderer(sc_data)
            if renderer:
                client.update_layer_renderer(fs_url, 0, renderer)
                record["renderer_applied"] = True
        except Exception as exc:  # noqa: BLE001
            record["renderer_applied"] = False
            record["renderer_warning"] = str(exc)

    return record


def _upload_image(client: AGOLClient, path: Path, request: PublishRequest,
                  *, category: str) -> dict:
    meta = {
        "type": "Image",
        "title": f"{request.title} \u2014 {path.stem}",
        "description": request.description,
        "tags": _comma_tags(request.tags + [request.title, category]),
    }
    body = client.add_item(meta, file_path=path, thumbnail=path)
    return {
        "id": body["id"],
        "title": meta["title"],
        "type": "Image",
        "itemUrl": client.item_home_url(body["id"]),
        "category": category,
        "source": str(path),
    }


def _upload_report(client: AGOLClient, path: Path,
                   request: PublishRequest) -> dict:
    """Upload the HTML analysis report as an AGOL HTML item.

    AGOL 'Document Link' requires a remote URL (no file upload allowed).
    'HTML' is the correct type for a self-contained HTML file — it stores
    the file as a downloadable attachment and the AGOL viewer renders it
    inline via the item's iframe sandbox.
    """
    meta = {
        "type": "HTML",
        "title": f"{request.title} \u2014 Report",
        "description": request.description,
        "tags": _comma_tags(request.tags + [request.title, "report"]),
    }
    body = client.add_item(meta, file_path=path)
    return {
        "id": body["id"],
        "title": meta["title"],
        "type": meta["type"],
        "itemUrl": client.item_home_url(body["id"]),
        "category": "report",
        "source": str(path),
    }


def _build_web_map(client: AGOLClient, request: PublishRequest,
                   layer_items: list[dict]) -> dict:
    """Assemble a Web Map item referencing every uploaded feature layer."""
    operational_layers = []
    for li in layer_items:
        fs_url = li.get("service_url")
        if not fs_url:
            continue
        operational_layers.append({
            "id": li["id"],
            "title": li["title"],
            "url": f"{fs_url.rstrip('/')}/0",
            "itemId": li["id"],
            "layerType": "ArcGISFeatureLayer",
            "visibility": True,
            "opacity": 1,
            "popupInfo": {"title": li["title"], "description": ""},
        })

    web_map_json = {
        "operationalLayers": operational_layers,
        "baseMap": {
            "baseMapLayers": [{
                "id": "basemap",
                "layerType": "ArcGISTiledMapServiceLayer",
                "url": "https://services.arcgisonline.com/arcgis/rest/services/"
                       "World_Light_Gray_Base/MapServer",
                "title": "Light Gray Canvas",
            }],
            "title": "Light Gray Canvas",
        },
        "spatialReference": {"wkid": 4326},
        "version": "2.24",
    }

    meta = {
        "type": "Web Map",
        "title": f"{request.title} \u2014 Web Map",
        "description": request.description,
        "tags": _comma_tags(request.tags + [request.title, "web-map"]),
        "typeKeywords": "Web Map,Explorer Web Map,Map,Online Map",
        "text": json.dumps(web_map_json),
    }
    body = client.add_item(meta)
    return {
        "id": body["id"],
        "title": meta["title"],
        "type": "Web Map",
        "itemUrl": client.item_home_url(body["id"]),
        "category": "web_map",
        "source": "web_map.json",
    }


def _apply_sharing(client: AGOLClient, items: list[dict], sharing: str,
                   warnings: list) -> None:
    if sharing not in SHARING_VALUES:
        warnings.append(f"invalid sharing {sharing!r}; using PRIVATE")
        sharing = "PRIVATE"
    for rec in items:
        item_id = rec.get("id")
        if not item_id:
            continue
        try:
            client.share_item(item_id, sharing)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"share failed for {item_id}: {exc}")


def _sanitize_service_name(stem: str) -> str:
    """AGOL feature-service names must start with a letter and contain only
    letters, digits, and underscores.
    """
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in stem)
    if safe and not safe[0].isalpha():
        safe = "fl_" + safe
    return safe or "feature_layer"


def _request_summary(request: PublishRequest) -> dict:
    opts = request.options or {}
    gdb_override = opts.get("gdb_file")
    default_gdb = request.analysis_dir / "outputs" / "arcgis" / "data" / "project.gdb"
    return {
        "analysis_dir": str(request.analysis_dir),
        "title": request.title,
        "description": request.description,
        "tags": request.tags,
        "sharing": request.sharing,
        "dry_run": request.dry_run,
        "gdb_file": str(gdb_override or default_gdb),
        "style_dir": str(request.style_dir) if request.style_dir else None,
    }
