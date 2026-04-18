# TOOLS.md — Validation QA

Approved operational tools for the Validation QA role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`

## Primary Tool Classes

- `validation`

## Approved Production Tools

### Structural Validation
- `validate_outputs.py`
- `validate_vector.py`
- `validate_tabular.py`
- `validate_join_coverage.py`
- `validate_analysis.py`
- `validate_cartography.py` — map PNG quality gate
- `validate_handoffs.py` — handoff contract validation

### Content Review
- `check_report_sensitivity.py` — scan reports for political/editorial risks

### Handoff
- `write_validation_handoff.py`

## Conditional / Secondary Tools

Use only when the workflow explicitly supports them:
- map sanity checks that are structural in nature
- supporting smoke tests or environment checks

## Experimental Tools

Escalate before relying on:
- policy-sensitive report review tools
- freshness/performance dashboards as validation authority
- anything that turns validation into interpretive critique

## Inputs You Depend On

- analysis handoff
- processing context
- output artifacts

## Outputs You Are Expected To Produce

- validation check JSONs
- aggregated validation handoff

## Operational Rules

- structural QA is your core mission
- peer review is a separate gate
- visual checks here are for output sanity, not final communicative elegance
