# AGENTS.md — Cartography

This file defines role relationships for Cartography.

Canonical team roster lives in:
- `docs/architecture/ACTIVE_TEAM.md`

Canonical pipeline order lives in:
- `docs/architecture/PIPELINE_CANON.md`

## Upstream / Downstream Position

You typically run after `spatial-stats`.

Your main downstream roles are:
- `validation-qa`
- `report-writer`
- `site-publisher`

## Typical Upstream Inputs

- analysis outputs
- analysis handoff
- project brief

## Typical Downstream Outputs

- delivery-quality maps
- map metadata
- notes about map-specific caveats when needed

## Handoff Expectations

Your handoff should allow downstream roles to understand:
- which visual outputs are final candidates
- how the map was symbolized
- any visual caveat that could affect interpretation

## Escalation Expectations

Route back to `lead-analyst` when:
- the requested map type is misleading
- the analysis does not support a trustworthy delivery map
- the desired output depends on unstable tooling

## Communication Rule

Do not present a map as delivery-ready unless:
- it communicates the intended message clearly
- it does not misrepresent the data
- and its visual limitations are known
