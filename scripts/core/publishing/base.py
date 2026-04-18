"""Abstract publishing adapter interface.

Every concrete adapter (ArcGIS Online, Enterprise, GeoServer, S3, etc.)
subclasses `PublishAdapter` and implements:

    - `validate(request)` — check credentials and inputs without uploading
    - `publish(request)`  — perform the upload and return a PublishResult

The adapter is run from `scripts/core/publish_<target>.py` (a thin CLI
wrapper) or directly from `package_site_publisher` during the Delivery
Packaging stage when `publish_targets` is set in the project brief.

Outputs:

    analyses/<project>/outputs/arcgis/publish-status.json  (or the
    target-specific equivalent) with item IDs, URLs, sharing level, and
    timestamps — machine-readable so the site-publisher handoff can
    reference it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


@dataclass
class PublishRequest:
    """Input to an adapter's validate/publish."""
    analysis_dir: Path
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    sharing: str = "PRIVATE"            # PRIVATE | ORG | PUBLIC
    dry_run: bool = True                 # default off-by-default for safety
    # Artifacts the adapter may consume:
    gpkg_files: list[Path] = field(default_factory=list)
    map_pngs: list[Path] = field(default_factory=list)
    chart_pngs: list[Path] = field(default_factory=list)
    report_html: Path | None = None
    style_dir: Path | None = None       # for sidecar-driven symbology
    # Adapter-specific overrides:
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    """Normalised adapter output written to publish-status.json."""
    target: str                          # 'arcgis_online', 'geoserver', ...
    status: str                          # 'ok' | 'dry-run' | 'partial' | 'error'
    started_at: str = ""
    ended_at: str = ""
    items: list[dict] = field(default_factory=list)   # uploaded items
    web_map_url: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    request: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


class PublishAdapter:
    """Abstract base for publishing adapters."""

    target: str = ""     # subclasses set this (e.g. 'arcgis_online')

    def validate(self, request: PublishRequest) -> PublishResult:
        raise NotImplementedError

    def publish(self, request: PublishRequest) -> PublishResult:
        raise NotImplementedError

    # ── Shared helpers ────────────────────────────────────────────

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _write_status(analysis_dir: Path, target: str, result: PublishResult,
                      subdir: str = "arcgis") -> Path:
        out = analysis_dir / "outputs" / subdir / "publish-status.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result.to_json())
        return out

    @staticmethod
    def _collect_from_analysis(analysis_dir: Path) -> dict[str, list[Path]]:
        """Convenience: walk an analysis's outputs/ and group files for
        adapters that don't want to enumerate them themselves.
        """
        outputs = analysis_dir / "outputs"
        return {
            "gpkgs":   sorted((analysis_dir / "data" / "processed").glob("*.gpkg"))
                       if (analysis_dir / "data" / "processed").exists() else [],
            "maps":    sorted((outputs / "maps").glob("*.png"))
                       if (outputs / "maps").exists() else [],
            "charts":  sorted((outputs / "charts").glob("*.png"))
                       if (outputs / "charts").exists() else [],
            "reports": sorted((outputs / "reports").glob("*.html"))
                       if (outputs / "reports").exists() else [],
        }


class NotImplementedAdapter(PublishAdapter):
    """Shared stub for unimplemented targets. Points the user at the
    extension docs rather than silently failing.
    """

    how_to_extend: str = "docs/extending/PUBLISHING_ADAPTERS.md"

    def validate(self, request: PublishRequest) -> PublishResult:
        raise NotImplementedError(
            f"{self.target!r} adapter is not implemented yet. "
            f"See {self.how_to_extend} to contribute one."
        )

    def publish(self, request: PublishRequest) -> PublishResult:
        raise NotImplementedError(
            f"{self.target!r} adapter is not implemented yet. "
            f"See {self.how_to_extend} to contribute one."
        )
