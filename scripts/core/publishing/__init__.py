"""Publishing adapters for spatial-machines.

Each adapter pushes an organised analysis package from
`analyses/<project>/outputs/` to an external system (ArcGIS Online,
ArcGIS Enterprise, a GeoServer, a static hosting target, etc.) and
writes a publish-status artifact so the site-publisher handoff knows
what was published and where.

Current adapters:
    arcgis_online — AGOL hosted feature layers + web map (reference impl)

Stubs (raise NotImplementedError with a pointer):
    enterprise    — ArcGIS Enterprise portal (post-1.0)
    geoserver     — OGC-standards GeoServer instance (post-1.0)
    s3            — Static site to S3 / GitHub Pages / Netlify (post-1.0)

See docs/extending/PUBLISHING_ADAPTERS.md for the adapter contract.
"""
from .base import PublishAdapter, PublishRequest, PublishResult

__all__ = ["PublishAdapter", "PublishRequest", "PublishResult"]
