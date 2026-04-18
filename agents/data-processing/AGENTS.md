# AGENTS.md — Data Processing

This file defines role relationships for Data Processing.

Canonical team roster lives in:
- `docs/architecture/ACTIVE_TEAM.md`

Canonical pipeline order lives in:
- `docs/architecture/PIPELINE_CANON.md`

## Upstream / Downstream Position

You typically run after `data-retrieval`.

Your main downstream role is:
- `spatial-stats`

`cartography` may later consume outputs that were prepared here, but your direct handoff target is analysis.

## Typical Upstream Inputs

- raw data and manifests from retrieval
- retrieval provenance
- processing instructions from `lead-analyst`

## Typical Downstream Outputs

- analysis-ready datasets
- processing logs
- processing handoff

## Handoff Expectations

Your handoff must allow `spatial-stats` to understand:
- what data exists
- how it was transformed
- which joins are trustworthy
- what limitations remain

## Escalation Expectations

Route back to `lead-analyst` when:
- join diagnostics are unexpectedly poor
- CRS assignment is uncertain
- schema mismatch suggests the wrong dataset
- derived metrics would be misleading without policy clarification

## Communication Rule

Do not report a dataset as analysis-ready unless:
- it exists
- the transformation path is documented
- and downstream analysis will not have to guess how it was made
