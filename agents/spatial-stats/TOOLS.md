# TOOLS.md — Spatial Statistics

Approved operational tools for the Spatial Statistics role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`

## Primary Tool Classes

- `analysis`

## Approved Production Tools

### Statistical Analysis
- `analyze_summary_stats.py`
- `analyze_top_n.py`
- `compute_spatial_autocorrelation.py`
- `compute_hotspots.py`
- `compute_change_detection.py`

### Supporting Analysis Inputs
- processed datasets
- processing handoffs
- demographic and ACS-derived fields prepared upstream

### Handoff
- `write_analysis_handoff.py`

## Conditional / Secondary Tools

Use when appropriate to the analysis design and project brief:
- `analyze_bivariate.py`
- `overlay_points.py`

These can support analysis outputs, but final delivery-quality visual refinement belongs to `cartography`.

## Experimental Tools

Escalate before relying on:
- spatial regression workflows not yet fully standardized
- raster-heavy methods
- KDE/interpolation methods outside current production norms

## Inputs You Depend On

- `data/processed/*`
- processing handoff
- project brief

## Outputs You Are Expected To Produce

- `outputs/tables/*`
- analysis maps
- sidecar logs
- analysis handoff

## Operational Rules

- do not use experimental methods as default substitutes for proven workflows
- distinguish analytic visualization from final cartographic presentation
- document classification and significance decisions clearly
