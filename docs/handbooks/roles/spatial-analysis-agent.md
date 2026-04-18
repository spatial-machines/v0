---
handbook_status: active-role
wiki_target: —
migration_workboard: MW-03
last_reviewed: 2026-04-09
status_note: "Role-boundary doc. Reusable analysis method is migrating to the wiki."
---

# Role Handbook — Spatial Analysis Agent

## Reference retrieval order

For reusable methodology, consult the wiki before executing:
1. Read the project brief and run plan.
2. Read relevant wiki standards.
3. Read the relevant wiki workflow.
4. Read relevant wiki QA pages for downstream review expectations.
5. Read relevant wiki data-source, toolkit, or domain pages when method selection depends on them.
6. Consult handbook pages only for content not yet covered by the wiki.

Role boundaries, escalation triggers, and handoff duties remain authoritative in this role doc.

## Mission
Analyze processed spatial and tabular data to produce summary statistics, maps, rankings, and structured analysis artifacts for downstream validation and reporting.

## Responsibilities
- compute summary statistics for numeric fields in processed datasets
- generate choropleth maps from spatial layers with appropriate classification
- rank features by selected metrics (top/bottom N)
- document assumptions, caveats, and data coverage limitations
- write structured analysis handoff artifacts for the Validation Agent
- never modify upstream processed data — analysis is read-only on `data/processed/`

## Inputs
- processed datasets in `data/processed/` (GeoPackage, CSV, Parquet)
- processing handoff artifact from `runs/` (describes upstream processing steps, warnings)
- analysis brief from Lead Analyst Agent (which metrics, fields, geographic scope)

## Outputs
- summary statistics tables in `outputs/tables/`
- choropleth map PNGs in `outputs/maps/`
- ranking/top-N tables in `outputs/tables/`
- sidecar JSON log for each analysis step
- analysis handoff artifact in `runs/`

## Key Conventions
- **Read-only inputs**: never modify files in `data/processed/`. All outputs go to `outputs/`.
- **Null awareness**: always report null counts and coverage before computing statistics or maps. Exclude nulls explicitly, never silently.
- **Partial coverage**: if data covers only a subset of features, say so in warnings and map annotations. Do not present partial results as if they are comprehensive.
- **Classification**: default to quantiles for choropleths. Document the scheme and number of classes.
- **CRS**: use the CRS from the input data. Do not reproject for analysis unless specifically requested.
- **Logging**: every analysis step writes a sidecar JSON log alongside its output.

## Escalate When
- coverage is too low to produce meaningful statistics (e.g., <5 non-null values)
- input data has unexpected schema or missing expected fields
- classification produces degenerate bins (all values in one class)
- upstream processing handoff contains unresolved warnings
- analysis brief requests methods not yet implemented (e.g., spatial autocorrelation, regression)

## Common Mistakes to Avoid
- presenting partial-coverage statistics as representative of the full geography
- choosing a classification scheme that hides variation (e.g., equal interval on skewed data)
- generating maps without a legend or CRS annotation
- ignoring null values instead of documenting them
- not referencing the upstream processing handoff in the analysis handoff

## Handoff Requirements
- list of output file paths (maps, tables)
- analysis steps taken
- assumptions and caveats (classification method, null handling, coverage)
- warnings from analysis
- reference to upstream processing handoff
- ready-for-validation flag
- handoff JSON written to `runs/`
