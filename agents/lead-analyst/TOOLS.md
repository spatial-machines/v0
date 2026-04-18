# TOOLS.md — Lead Analyst

Approved operational tools for the Lead Analyst role.

This file lists role-relevant tools only. Shared architecture and machine setup live elsewhere.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`
- `docs/architecture/DATA_REUSE_POLICY.md`

## Primary Tool Classes

- `intake`
- `project-management`
- `orchestration`
- `handoff synthesis`

## Approved Production Tools

### Intake and Planning
- `parse_task.py`
- `create_run_plan.py`

### Project and Status Tracking
- `list_projects.py`
- `project_status.py`
- `check_pipeline_status.py` — check which pipeline stages are complete for a project
- `check_data_freshness.py` — check if data sources need refreshing
- `check_reanalysis_needed.py` — identify analyses that should be re-run
- `search_project_inventory.py`
- `build_project_inventory.py` when a likely reuse candidate has no `inventory.json`

### Lead Synthesis
- `write_lead_handoff.py`
- `synthesize_run_summary.py` — build structured summary from all stage handoffs

### Read-Only Coordination Inputs
- upstream handoffs in `runs/`
- project metadata
- reports, QA outputs, and peer review outputs
- project inventories in `analyses/*/inventory.json`

## Experimental Tools

Escalate before relying on:
- experimental workflow branches not covered by the canonical pipeline
- specialist-owned tools as direct defaults
- ad hoc orchestration paths that are not reflected in project artifacts

## Allowed Secondary Tools

Use only when coordinating or validating routing decisions:
- `run_peer_review.py` for gate checks
- `compare_projects.py` for comparison-oriented synthesis

## Execution Notes

- prefer routing specialist work to the owning agent rather than directly invoking their workflow yourself
- use production tools by default
- experimental tools require explicit justification
- when invoking scripts through the runtime exec tool, use direct commands like `python scripts/core/file.py ...`
- do not use shell chaining like `cd ... && python ...`; set the working directory separately and run the script directly
- do not bundle multiple stage commands inside one shell script or `set -e` block; run each stage as its own direct exec call
- before authorizing new retrieval, query prior project inventories with `search_project_inventory.py`
- if a likely prior project has no inventory yet, build it with `build_project_inventory.py` before deciding that fresh retrieval is necessary

## Inputs You Depend On

- `project_brief.json`
- run plan artifacts
- stage handoffs
- review artifacts

## Outputs You Are Expected To Produce

- run plan
- delegation decision
- final synthesis
- lead handoff

## Not Your Default Tool Surface

These are not your default execution responsibilities:
- retrieval scripts
- processing scripts
- analysis scripts
- validation scripts
- publishing scripts

Use them directly only in explicit direct mode or when the specialist path is unavailable and the risk is acceptable.

For normal GIS pilots, completion requires:
- reporting handoff
- publishing handoff
- lead handoff

## Reuse-First Command Pattern

Use direct commands such as:
- `python scripts/core/search_project_inventory.py --analyses-dir analyses --query "cafes"`
- `python scripts/core/build_project_inventory.py --project-dir analyses/<project-id>`

Use these to support delegation and scope decisions. Do not treat fresh acquisition as the default if a compatible prior project already exists.
