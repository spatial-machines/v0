"""Layer 2: Handoff Contract Tests.

Validate that all handoff JSON artifacts conform to expected schemas.
Tests run against completed analyses and skip gracefully when no
analysis data exists.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import (
    EXAMPLE_RUNS_DIR,
    PROJECT_ROOT,
    load_json,
)
from .schemas import (
    PROVENANCE_REQUIRED,
    PROVENANCE_SOURCE_REQUIRED,
    PROCESSING_HANDOFF_REQUIRED,
    ANALYSIS_HANDOFF_REQUIRED,
    VALIDATION_HANDOFF_REQUIRED,
    REPORTING_HANDOFF_REQUIRED,
    LEAD_HANDOFF_REQUIRED,
    QGIS_HANDOFF_REQUIRED,
    HANDOFF_TYPE_SCHEMAS,
    VALID_VALIDATION_STATUSES,
    VALID_READY_FOR,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_handoffs(*dirs: Path) -> list[Path]:
    """Collect all top-level handoff JSON files from the given directories."""
    files = []
    for d in dirs:
        if d.exists():
            files.extend(sorted(f for f in d.glob("*.json")))
    return files


def _validate_schema(data: dict, schema: dict[str, type], filename: str):
    """Assert that data contains all required keys with the expected types."""
    for key, expected_type in schema.items():
        assert key in data, f"{filename}: missing required field '{key}'"
        assert isinstance(data[key], expected_type), (
            f"{filename}: field '{key}' expected {expected_type.__name__}, "
            f"got {type(data[key]).__name__}"
        )


def _find_all_runs_dirs() -> list[Path]:
    """Find all runs/ directories across analyses."""
    analyses_dir = PROJECT_ROOT / "analyses"
    dirs = []
    if EXAMPLE_RUNS_DIR.exists():
        dirs.append(EXAMPLE_RUNS_DIR)
    for project_dir in analyses_dir.iterdir():
        if project_dir.is_dir():
            runs = project_dir / "runs"
            if runs.exists() and runs != EXAMPLE_RUNS_DIR:
                dirs.append(runs)
    return dirs


ALL_HANDOFF_FILES = _collect_handoffs(*_find_all_runs_dirs())

# Skip all tests if no handoff files found
pytestmark = pytest.mark.skipif(
    len(ALL_HANDOFF_FILES) == 0,
    reason="No handoff files found — run an analysis first"
)


# ---------------------------------------------------------------------------
# Provenance tests
# ---------------------------------------------------------------------------

class TestProvenanceSchema:
    """Validate *.provenance.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "provenance" in f.name
    ], ids=lambda f: f.name)
    def provenance_file(self, request):
        return request.param

    def test_required_fields(self, provenance_file):
        data = load_json(provenance_file)
        _validate_schema(data, PROVENANCE_REQUIRED, provenance_file.name)

    def test_sources_have_required_fields(self, provenance_file):
        data = load_json(provenance_file)
        for i, source in enumerate(data["sources"]):
            _validate_schema(
                source, PROVENANCE_SOURCE_REQUIRED,
                f"{provenance_file.name}.sources[{i}]"
            )

    def test_has_at_least_one_source(self, provenance_file):
        data = load_json(provenance_file)
        assert len(data["sources"]) >= 1, f"{provenance_file.name}: no sources"


# ---------------------------------------------------------------------------
# Processing handoff tests
# ---------------------------------------------------------------------------

class TestProcessingHandoffSchema:
    """Validate *.processing-handoff.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "processing-handoff" in f.name
    ], ids=lambda f: f.name)
    def processing_file(self, request):
        return request.param

    def test_required_fields(self, processing_file):
        data = load_json(processing_file)
        _validate_schema(data, PROCESSING_HANDOFF_REQUIRED, processing_file.name)

    def test_handoff_type_value(self, processing_file):
        data = load_json(processing_file)
        assert data["handoff_type"] == "processing"

    def test_ready_for_is_analysis(self, processing_file):
        data = load_json(processing_file)
        assert data["ready_for"] == "analysis"


# ---------------------------------------------------------------------------
# Analysis handoff tests
# ---------------------------------------------------------------------------

class TestAnalysisHandoffSchema:
    """Validate *.analysis-handoff.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "analysis-handoff" in f.name
    ], ids=lambda f: f.name)
    def analysis_file(self, request):
        return request.param

    def test_required_fields(self, analysis_file):
        data = load_json(analysis_file)
        _validate_schema(data, ANALYSIS_HANDOFF_REQUIRED, analysis_file.name)

    def test_handoff_type_value(self, analysis_file):
        data = load_json(analysis_file)
        assert data["handoff_type"] == "analysis"

    def test_ready_for_is_validation(self, analysis_file):
        data = load_json(analysis_file)
        assert data["ready_for"] == "validation"


# ---------------------------------------------------------------------------
# Validation handoff tests
# ---------------------------------------------------------------------------

class TestValidationHandoffSchema:
    """Validate *.validation-handoff.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "validation-handoff" in f.name
    ], ids=lambda f: f.name)
    def validation_file(self, request):
        return request.param

    def test_required_fields(self, validation_file):
        data = load_json(validation_file)
        _validate_schema(data, VALIDATION_HANDOFF_REQUIRED, validation_file.name)

    def test_overall_status_is_valid(self, validation_file):
        data = load_json(validation_file)
        assert data["overall_status"] in VALID_VALIDATION_STATUSES


# ---------------------------------------------------------------------------
# Reporting handoff tests
# ---------------------------------------------------------------------------

class TestReportingHandoffSchema:
    """Validate *.reporting-handoff.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "reporting-handoff" in f.name
    ], ids=lambda f: f.name)
    def reporting_file(self, request):
        return request.param

    def test_required_fields(self, reporting_file):
        data = load_json(reporting_file)
        _validate_schema(data, REPORTING_HANDOFF_REQUIRED, reporting_file.name)

    def test_handoff_type_value(self, reporting_file):
        data = load_json(reporting_file)
        assert data["handoff_type"] == "reporting"


# ---------------------------------------------------------------------------
# Lead handoff tests
# ---------------------------------------------------------------------------

class TestLeadHandoffSchema:
    """Validate *.lead-handoff.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "lead-handoff" in f.name
    ], ids=lambda f: f.name)
    def lead_file(self, request):
        return request.param

    def test_required_fields(self, lead_file):
        data = load_json(lead_file)
        _validate_schema(data, LEAD_HANDOFF_REQUIRED, lead_file.name)

    def test_handoff_type_value(self, lead_file):
        data = load_json(lead_file)
        assert data["handoff_type"] == "lead-analyst"


# ---------------------------------------------------------------------------
# QGIS handoff tests
# ---------------------------------------------------------------------------

class TestQgisHandoffSchema:
    """Validate *.qgis-handoff.json files."""

    @pytest.fixture(params=[
        f for f in ALL_HANDOFF_FILES if "qgis-handoff" in f.name
    ], ids=lambda f: f.name)
    def qgis_file(self, request):
        return request.param

    def test_required_fields(self, qgis_file):
        data = load_json(qgis_file)
        _validate_schema(data, QGIS_HANDOFF_REQUIRED, qgis_file.name)


# ---------------------------------------------------------------------------
# Cross-cutting contract tests
# ---------------------------------------------------------------------------

class TestReadyForChain:
    """Verify the ready_for chain is valid across all handoffs."""

    def test_all_ready_for_values_are_valid(self):
        for f in ALL_HANDOFF_FILES:
            data = load_json(f)
            if "ready_for" in data:
                assert data["ready_for"] in VALID_READY_FOR, (
                    f"{f.name}: invalid ready_for value '{data['ready_for']}'"
                )
