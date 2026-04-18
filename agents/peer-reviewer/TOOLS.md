# TOOLS.md — Peer Reviewer

Approved operational tools for the Peer Reviewer role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`

## Primary Tool Classes

- `review`

## Approved Production Tools

### Primary Review Tool
- `run_peer_review.py`

### Read-Only Supporting Inputs
- output maps
- output reports
- QA outputs

### Optional Read-Only Support
- structural QA outputs when they are part of the visible review surface

## Conditional / Secondary Tools

Use only as support to deepen a review, not to become a production role:
- output existence checks
- color accessibility checks
- project comparisons

## Experimental Tools

Escalate before relying on:
- any workflow that expands review beyond the approved review surface
- any tool path that turns review into debugging or production work

## Inputs You Depend On

- proposal artifacts when in proposal review mode
- output maps
- output reports
- visible QA outputs

## Inputs You Are Allowed To Read By Default

### Allowed
- `outputs/maps/`
- `outputs/reports/`
- `outputs/qa/`
- proposal artifacts when in proposal review mode

### Not Allowed By Default
- `data/raw/`
- `data/processed/`
- `runs/`
- production scripts

If the evidence did not make it into the review surface, you should not assume it exists.

## Outputs You Are Expected To Produce

- peer review artifact
- verdict
- actionable findings

## Operational Rules

- you are a reviewer, not a fixer
- your authority is interpretive, not structural
- use visible evidence, not internal pipeline optimism
