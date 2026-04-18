"""ArcGIS Enterprise publishing adapter — stub.

Planned for v1.1. Will re-use arcgis_online.py's feature-layer upload
logic via `arcgis.gis.GIS(url=<enterprise-url>, ...)`. The auth path is
more varied (PKI, SAML, token) so proper implementation warrants its
own module.
"""
from .base import NotImplementedAdapter


class ArcGISEnterpriseAdapter(NotImplementedAdapter):
    target = "arcgis_enterprise"
