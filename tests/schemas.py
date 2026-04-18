"""Handoff schema definitions for validation.

Each schema is defined as a dict mapping field names to expected types
or validation callables. Used by test_handoff_contracts.py.
"""
from __future__ import annotations

# --- Common fields present in all handoff types (except provenance) ---
COMMON_HANDOFF_FIELDS = {
    "run_id": str,
    "summary": str,
    "created_at": str,
    "warnings": list,
    "ready_for": str,
    "notes": list,
}

# --- Provenance schema (no handoff_type field) ---
PROVENANCE_REQUIRED = {
    "run_id": str,
    "task_summary": str,
    "created_at": str,
    "sources": list,
    "artifacts": list,
    "notes": list,
}

PROVENANCE_SOURCE_REQUIRED = {
    "dataset_id": str,
    "retrieval_method": str,
    "source_name": str,
    "source_type": str,
    "stored_path": str,
    "format": str,
}

# --- Processing handoff ---
PROCESSING_HANDOFF_REQUIRED = {
    **COMMON_HANDOFF_FIELDS,
    "handoff_type": str,
    "output_files": list,
    "processing_steps": list,
    "processing_logs": list,
}

# --- Analysis handoff ---
ANALYSIS_HANDOFF_REQUIRED = {
    **COMMON_HANDOFF_FIELDS,
    "handoff_type": str,
    "output_files": list,
    "analysis_steps": list,
    "analysis_logs": list,
    "upstream_handoff": dict,
}

# --- Validation handoff ---
VALIDATION_HANDOFF_REQUIRED = {
    **COMMON_HANDOFF_FIELDS,
    "handoff_type": str,
    "overall_status": str,
    "check_summaries": list,
    "total_checks": int,
    "checks_pass": int,
    "checks_warn": int,
    "checks_fail": int,
    "upstream_handoff": dict,
}

VALID_VALIDATION_STATUSES = {"PASS", "PASS WITH WARNINGS", "REWORK NEEDED"}

# --- Reporting handoff ---
REPORTING_HANDOFF_REQUIRED = {
    **COMMON_HANDOFF_FIELDS,
    "handoff_type": str,
    "output_files": list,
    "report_files": list,
    "upstream_handoff": dict,
}

# --- Lead handoff ---
LEAD_HANDOFF_REQUIRED = {
    **COMMON_HANDOFF_FIELDS,
    "handoff_type": str,
    "run_plan": dict,
    "pipeline_status": dict,
    "validation_status": str,
    "upstream_handoffs": dict,
    "lead_summary": dict,
    "key_outputs": list,
}

# --- QGIS handoff ---
QGIS_HANDOFF_REQUIRED = {
    **COMMON_HANDOFF_FIELDS,
    "handoff_type": str,
    "package_dir": str,
    "validation_status": str,
    "package_files": list,
    "manifest": dict,
    "upstream_handoff": dict,
}

# Map handoff_type values to their schemas
HANDOFF_TYPE_SCHEMAS = {
    "processing": PROCESSING_HANDOFF_REQUIRED,
    "analysis": ANALYSIS_HANDOFF_REQUIRED,
    "validation": VALIDATION_HANDOFF_REQUIRED,
    "reporting": REPORTING_HANDOFF_REQUIRED,
    "lead-analyst": LEAD_HANDOFF_REQUIRED,
    "qgis-bridge": QGIS_HANDOFF_REQUIRED,
}

# Valid ready_for chain values
VALID_READY_FOR = {
    "processing",
    "analysis",
    "validation",
    "review",
    "reporting",
    "synthesis",
    "human-review",
    "qgis-review",
}
