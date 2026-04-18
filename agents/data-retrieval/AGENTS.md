# AGENTS.md — Data Retrieval

This file defines role relationships for Data Retrieval.

Canonical team roster lives in:
- `docs/architecture/ACTIVE_TEAM.md`

Canonical pipeline order lives in:
- `docs/architecture/PIPELINE_CANON.md`

## Upstream / Downstream Position

You typically run immediately after `lead-analyst` scoping.

Your main downstream role is:
- `data-processing`

## Typical Upstream Inputs

- retrieval brief from `lead-analyst`
- project brief
- existing artifact inventory

## Typical Downstream Outputs

- raw files in project data directories
- manifests
- provenance artifact
- source warnings and notes for processing

## Handoff Expectations

Your handoff must give `data-processing` enough information to proceed without guessing:
- artifact paths
- source and vintage
- file format
- any extraction or schema expectations
- limitations or concerns

## Escalation Expectations

Route back to `lead-analyst` when:
- no acceptable source can be identified
- available sources conflict materially
- credentials are missing
- the best available source is clearly stale or low quality

## Communication Rule

Do not report “data acquired” unless:
- the artifact exists
- provenance exists
- and the downstream processing agent has enough context to trust what was retrieved
