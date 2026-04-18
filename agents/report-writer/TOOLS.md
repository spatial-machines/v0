# TOOLS.md — Report Writer

Approved operational tools for the Report Writer role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`

## Primary Tool Classes

- `reporting`

## Approved Production Tools

### Report Assembly
- `collect_report_assets.py`
- `write_markdown_report.py`
- `write_html_report.py`
- `write_reporting_handoff.py`

### Supporting Documentation
- `write_data_dictionary.py`
- `generate_citations.py`

## Conditional / Secondary Tools

Use when the workflow explicitly supports them:
- sensitivity or editorial-risk checks
- reproducibility packaging helpers

These support reporting, but they do not replace evidence judgment.

## Experimental Tools

Escalate before relying on:
- non-production report review helpers
- dashboard/performance tools as reporting authority
- automated editorial tools that overrule validated evidence

## Inputs You Depend On

- upstream handoffs (including the cartography handoff for maps **and** charts)
- maps (`outputs/maps/`) and their style sidecars
- charts (`outputs/charts/`) — PNG + SVG + `.style.json` sidecars. Group by `chart_family` (distribution / comparison / relationship / timeseries) for narrative placement. Use each chart's `pairs_with` to co-locate it with its companion map.
- tables (`outputs/tables/`)
- interactive maps (`outputs/web/`)
- project brief

## Outputs You Are Expected To Produce

- `outputs/reports/*`
- reporting handoff
- supporting report artifacts such as citations/data dictionaries

## Operational Rules

- narrative ownership is yours
- publishing ownership is not yours
- do not treat a script-generated sentence as sufficient evidence on its own
- for normal GIS pilots, reporting is not complete until `write_reporting_handoff.py` is written
- when invoking reporting tools through exec, call one script directly per command
