"""Layer 6: Acceptance Test Hardening.

Validates completed analysis artifacts. These tests skip gracefully when
no analysis data exists (e.g., on a fresh clone). Run an analysis first,
then use these tests to validate the outputs.

Usage:
    python -m pytest tests/test_acceptance.py -v
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from .conftest import (
    PROJECT_ROOT,
    EXAMPLE_PROJECT_DIR,
    EXAMPLE_RUNS_DIR,
    EXAMPLE_DATA_DIR,
    EXAMPLE_OUTPUTS_DIR,
    load_json,
)

# Skip all tests in this module if no analysis data exists
pytestmark = pytest.mark.skipif(
    not EXAMPLE_PROJECT_DIR.exists(),
    reason="No analysis data found — run an analysis first"
)


class TestAcceptance:
    """Content validation for completed analysis artifacts."""

    def test_joined_gpkg_exists_and_nonzero(self):
        gpkgs = list((EXAMPLE_DATA_DIR / "processed").glob("*.gpkg"))
        assert len(gpkgs) >= 1, "No processed GeoPackages found"
        for gpkg in gpkgs:
            assert gpkg.stat().st_size > 0, f"{gpkg.name} is empty"

    def test_choropleth_exists_and_nonzero(self):
        maps_dir = EXAMPLE_OUTPUTS_DIR / "maps"
        if not maps_dir.exists():
            pytest.skip("No maps directory")
        pngs = list(maps_dir.glob("*.png"))
        assert len(pngs) >= 1, "No map PNGs found"
        for png in pngs:
            assert png.stat().st_size > 1000, f"{png.name} suspiciously small"

    def test_report_html_is_valid(self):
        reports_dir = EXAMPLE_OUTPUTS_DIR / "reports"
        if not reports_dir.exists():
            pytest.skip("No reports directory")
        htmls = list(reports_dir.glob("*.html"))
        if not htmls:
            pytest.skip("No HTML reports found")
        for html in htmls:
            content = html.read_text()
            assert "<html" in content.lower() or "<!doctype" in content.lower(), (
                f"{html.name} doesn't contain HTML tags"
            )

    def test_report_md_is_valid(self):
        reports_dir = EXAMPLE_OUTPUTS_DIR / "reports"
        if not reports_dir.exists():
            pytest.skip("No reports directory")
        mds = list(reports_dir.glob("*.md"))
        if not mds:
            pytest.skip("No markdown reports found")
        for md in mds:
            content = md.read_text()
            assert len(content) > 100, f"{md.name} too short"
            assert "#" in content, f"{md.name} has no headings"

    def test_all_handoffs_parse_as_json(self):
        if not EXAMPLE_RUNS_DIR.exists():
            pytest.skip("No runs directory")
        jsons = list(EXAMPLE_RUNS_DIR.glob("*.json"))
        if not jsons:
            pytest.skip("No handoff files found")
        for f in jsons:
            data = load_json(f)
            assert isinstance(data, dict), f"{f.name} did not parse as dict"

    def test_provenance_exists(self):
        if not EXAMPLE_RUNS_DIR.exists():
            pytest.skip("No runs directory")
        prov_files = list(EXAMPLE_RUNS_DIR.glob("*.provenance.json"))
        assert len(prov_files) >= 1, "No provenance files found"

    def test_all_handoff_output_files_exist(self):
        """Every path listed in output_files should exist on disk."""
        if not EXAMPLE_RUNS_DIR.exists():
            pytest.skip("No runs directory")
        for f in EXAMPLE_RUNS_DIR.glob("*.json"):
            data = load_json(f)
            for rel_path in data.get("output_files", []):
                full = PROJECT_ROOT / rel_path
                assert full.exists(), (
                    f"{f.name}: output_files references missing file: "
                    f"{rel_path} (checked {full})"
                )
