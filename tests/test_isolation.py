"""Layer 4: Isolation Property Tests.

Verify that isolated project artifacts are self-contained and don't leak
across boundaries. These tests run against completed analyses and skip
gracefully when no analysis data exists.
"""
from __future__ import annotations

import hashlib
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


def _checksum_file(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class TestProjectIsolation:
    """Completed analysis artifacts should be fully self-contained."""

    def test_handoffs_reference_project_paths(self):
        """All output_files in handoffs should be under the project directory."""
        if not EXAMPLE_RUNS_DIR.exists():
            pytest.skip("No runs directory")
        project_name = EXAMPLE_PROJECT_DIR.name
        for f in EXAMPLE_RUNS_DIR.glob("*.json"):
            data = load_json(f)
            for path_str in data.get("output_files", []):
                assert project_name in path_str or path_str.startswith("data/") or path_str.startswith("outputs/"), (
                    f"{f.name}: output_files references unexpected path: {path_str}"
                )

    def test_data_exists(self):
        """Key data files should exist."""
        processed = EXAMPLE_DATA_DIR / "processed"
        if not processed.exists():
            pytest.skip("No processed data directory")
        gpkgs = list(processed.glob("*.gpkg"))
        assert len(gpkgs) >= 1, "No processed GeoPackages found"

    def test_no_absolute_paths_in_handoffs(self):
        """Handoff files should not contain absolute paths."""
        if not EXAMPLE_RUNS_DIR.exists():
            pytest.skip("No runs directory")
        for f in EXAMPLE_RUNS_DIR.glob("*.json"):
            content = f.read_text()
            assert "/home/" not in content, (
                f"{f.name} contains absolute /home/ path"
            )


class TestRegistryConsistency:
    """The analyses registry (if present) should be valid."""

    def test_registry_entries_have_required_fields(self):
        registry_path = PROJECT_ROOT / "analyses" / "registry.json"
        if not registry_path.exists():
            pytest.skip("No registry.json — this is normal on a fresh repo")
        data = load_json(registry_path)
        for entry in data.get("analyses", []):
            assert "id" in entry
            assert "status" in entry
            assert entry["status"] in {"active", "paused", "archived", "failed"}
