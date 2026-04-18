# AGENTS.md — Spatial Statistics

This file defines role relationships for Spatial Statistics.

Canonical team roster lives in:
- `docs/architecture/ACTIVE_TEAM.md`

Canonical pipeline order lives in:
- `docs/architecture/PIPELINE_CANON.md`

## Upstream / Downstream Position

You typically run after `data-processing`.

Your main downstream roles are:
- `cartography`
- `validation-qa`

In simpler runs, `validation-qa` may consume your outputs directly.

## Typical Upstream Inputs

- processed datasets
- processing handoff
- analysis instructions from `lead-analyst`

## Typical Downstream Outputs

- analysis tables
- analysis maps
- analysis logs
- analysis handoff

## Handoff Expectations

Your handoff must allow downstream roles to understand:
- what methods were used
- what outputs exist
- what findings are supported
- what limitations remain

## Escalation Expectations

Route back to `lead-analyst` when:
- the question asks for unsupported causal inference
- coverage is too weak for meaningful analysis
- processed data is missing fields the method requires
- the requested analysis path is experimental and high-risk

## Communication Rule

Do not hand off a result as analytically meaningful unless:
- the evidence standard is met
- the caveats are explicit
- and downstream roles can distinguish signal from limitation
