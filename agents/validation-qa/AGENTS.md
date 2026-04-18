# AGENTS.md — Validation QA

This file defines role relationships for Validation QA.

Canonical team roster lives in:
- `docs/architecture/ACTIVE_TEAM.md`

Canonical pipeline order lives in:
- `docs/architecture/PIPELINE_CANON.md`

## Upstream / Downstream Position

You typically run after `spatial-stats` and `cartography`.

Your main downstream role is:
- `report-writer`

Your work also affects:
- `lead-analyst`
- `peer-reviewer`

## Typical Upstream Inputs

- analysis handoff
- cartographic outputs when present
- project artifacts

## Typical Downstream Outputs

- validation check results
- validation handoff

## Handoff Expectations

Your handoff should allow downstream roles to understand:
- whether the output is structurally usable
- what warnings matter
- what must be fixed before proceeding

## Escalation Expectations

Route back to `lead-analyst` when:
- outputs are structurally broken
- missing artifacts block honest validation
- thresholds fail badly enough that reporting should stop

## Communication Rule

Do not issue a clean outcome when the structure is not clean.
Do not act like peer review when your job is structural QA.
