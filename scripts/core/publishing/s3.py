"""Static web publishing adapter (S3 / GitHub Pages / Netlify) — stub.

Planned for v1.1. Will assemble a static site from the analysis's HTML
report, maps, charts, and web map, then upload to S3 or write to a
directory suitable for `gh-pages` or Netlify deploys.
"""
from .base import NotImplementedAdapter


class S3StaticAdapter(NotImplementedAdapter):
    target = "s3_static"
