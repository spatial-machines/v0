"""Shared fixtures for the spatial-machines test suite."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# --- Script paths ---
SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "core"

# --- Analysis paths (for tests that validate completed analyses) ---
# Prefer a real analysis if one exists, otherwise use the test fixture.
_FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "sample-analysis"

def _find_example_project() -> Path:
    """Find the best example project for testing."""
    analyses_dir = PROJECT_ROOT / "analyses"
    # Check for any real completed analysis
    if analyses_dir.exists():
        for project_dir in sorted(analyses_dir.iterdir()):
            if project_dir.is_dir() and (project_dir / "runs").exists():
                runs = list((project_dir / "runs").glob("*.json"))
                if len(runs) >= 2:
                    return project_dir
    # Fall back to the test fixture
    return _FIXTURE_DIR

EXAMPLE_PROJECT_DIR = _find_example_project()
EXAMPLE_RUNS_DIR = EXAMPLE_PROJECT_DIR / "runs"
EXAMPLE_DATA_DIR = EXAMPLE_PROJECT_DIR / "data"
EXAMPLE_OUTPUTS_DIR = EXAMPLE_PROJECT_DIR / "outputs"
EXAMPLE_QGIS_PACKAGE = EXAMPLE_OUTPUTS_DIR / "qgis" / "sample-review"


@pytest.fixture
def project_root():
    return PROJECT_ROOT


@pytest.fixture
def scripts_dir():
    return SCRIPTS_DIR


@pytest.fixture
def example_runs_dir():
    return EXAMPLE_RUNS_DIR


@pytest.fixture
def example_qgis_package():
    return EXAMPLE_QGIS_PACKAGE


@pytest.fixture
def all_scripts():
    """Return sorted list of all Python scripts in scripts/core/."""
    return sorted(SCRIPTS_DIR.glob("*.py"))


@pytest.fixture
def example_handoff_files():
    """All example project handoff JSON files (if they exist)."""
    if not EXAMPLE_RUNS_DIR.exists():
        return []
    return sorted(EXAMPLE_RUNS_DIR.glob("*.json"))


def load_json(path: Path) -> dict:
    """Helper to load a JSON file."""
    return json.loads(path.read_text())
