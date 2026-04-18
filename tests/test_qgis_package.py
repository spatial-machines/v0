"""Layer 5: QGIS Package Tests.

Validate QGIS review package structure and portability.
Skips gracefully when no QGIS packages exist.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from .conftest import PROJECT_ROOT, load_json


def _find_qgis_packages() -> list[Path]:
    """Find all QGIS review packages across analyses."""
    packages = []
    analyses_dir = PROJECT_ROOT / "analyses"
    if not analyses_dir.exists():
        return packages
    for project_dir in analyses_dir.iterdir():
        if project_dir.is_dir():
            qgis_dir = project_dir / "outputs" / "qgis"
            if qgis_dir.exists():
                for pkg in qgis_dir.iterdir():
                    if pkg.is_dir() and (pkg / "project.qgs").exists():
                        packages.append(pkg)
    return packages


QGIS_PACKAGES = _find_qgis_packages()

# Skip all tests if no QGIS packages found
pytestmark = pytest.mark.skipif(
    len(QGIS_PACKAGES) == 0,
    reason="No QGIS packages found — run an analysis with QGIS packaging first"
)


@pytest.fixture(params=QGIS_PACKAGES, ids=[p.name for p in QGIS_PACKAGES])
def qgis_package(request):
    return request.param


class TestQgisPackageStructure:
    """Verify package contains required files."""

    def test_has_project_file(self, qgis_package):
        assert (qgis_package / "project.qgs").exists(), "Missing project.qgs"

    def test_has_data_directory(self, qgis_package):
        assert (qgis_package / "data").exists(), "Missing data/ directory"
        assert (qgis_package / "data").is_dir()

    def test_has_readme(self, qgis_package):
        assert (qgis_package / "README.md").exists(), "Missing README.md"

    def test_data_contains_gpkg(self, qgis_package):
        """At least one GeoPackage should be in the data/ directory."""
        gpkg_files = list((qgis_package / "data").glob("*.gpkg"))
        assert len(gpkg_files) >= 1, "No .gpkg files in data/"


class TestQgisProjectRelativePaths:
    """Parse .qgs XML and verify all datasource elements use relative paths."""

    def test_datasources_are_relative(self, qgis_package):
        project_file = qgis_package / "project.qgs"
        tree = ET.parse(project_file)
        root = tree.getroot()

        for ds in root.iter("datasource"):
            if ds.text and ds.text.strip():
                text = ds.text.strip()
                if "|" in text:
                    path_part = text.split("|")[0]
                else:
                    path_part = text

                if path_part and path_part != "None":
                    assert not path_part.startswith("/"), (
                        f"Absolute path in datasource: {text}"
                    )


class TestQgisProjectReferencesExist:
    """Verify every datasource path resolves to a file within the package."""

    def test_referenced_files_exist(self, qgis_package):
        project_file = qgis_package / "project.qgs"
        tree = ET.parse(project_file)
        root = tree.getroot()

        for ds in root.iter("datasource"):
            if ds.text and ds.text.strip():
                text = ds.text.strip()
                if text == "None":
                    continue

                if "|" in text:
                    path_part = text.split("|")[0]
                else:
                    path_part = text

                if path_part and path_part.startswith("./"):
                    resolved = qgis_package / path_part
                    assert resolved.exists(), (
                        f"Datasource references missing file: {path_part} "
                        f"(resolved to {resolved})"
                    )
