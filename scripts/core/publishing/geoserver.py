"""GeoServer publishing adapter — stub.

Planned for v1.1. Will upload a GeoPackage to a GeoServer datastore via
its REST API and publish feature types with SLD styles translated from
our `.style.json` sidecars.

See docs/extending/PUBLISHING_ADAPTERS.md for the sketched API usage.
"""
from .base import NotImplementedAdapter


class GeoServerAdapter(NotImplementedAdapter):
    target = "geoserver"
