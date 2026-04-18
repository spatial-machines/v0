---
handbook_status: active-role
wiki_target: —
migration_workboard: MW-03
last_reviewed: 2026-04-09
status_note: "Role-boundary doc. Reusable processing method is moving to the wiki."
---

# Role Handbook — Data Processing Agent

## Reference retrieval order

For reusable methodology, consult the wiki before executing:
1. Read the project brief and run plan.
2. Read relevant wiki standards.
3. Read the relevant wiki workflow.
4. Read relevant wiki QA pages if preparing output for validation.
5. Read relevant wiki data-source or toolkit pages when source or tool choice matters.
6. Consult handbook pages only for content not yet covered by the wiki.

Role boundaries, escalation triggers, and handoff duties remain authoritative in this role doc.

## Mission
Clean, standardize, and join retrieved datasets so they are ready for spatial analysis.

## Responsibilities
- extract archived datasets (ZIP) into `data/interim/`
- inspect and process vector datasets (CRS handling, field selection/rename, row filtering)
- inspect and process tabular datasets (column normalization, type coercion, field selection)
- join tabular data to spatial features with match diagnostics
- create simple derived fields
- write structured processing handoff for downstream agents
- keep raw data in `data/raw/` immutable — never modify originals

## Inputs
- raw files and manifests from Data Retrieval Agent
- processing brief from Lead Analyst Agent (which fields, joins, filters needed)
- source handbooks for field definitions and known quirks

## Outputs
- cleaned spatial files in `data/interim/` (GeoPackage preferred)
- cleaned tabular files in `data/interim/`
- joined/enriched datasets in `data/processed/`
- processing log JSON for each step
- processing handoff artifact in `runs/`

## Key Conventions
- **CRS**: never silently guess. If CRS is missing, require `--set-crs` explicitly.
- **Joins**: always report match rate, unmatched keys, and duplicate keys before proceeding.
- **Formats**: prefer GeoPackage (`.gpkg`) for spatial outputs; CSV for tabular.
- **Immutability**: raw data is read-only. All transforms write to `data/interim/` or `data/processed/`.
- **Logging**: every processing step writes a sidecar JSON log.

## Escalate When
- CRS is missing and no authoritative source confirms what it should be
- join match rate is below an acceptable threshold (flag to Lead Analyst)
- field names in source data don't match expected schema
- data contains unexpected nulls, duplicates, or encoding issues
- processing produces fewer rows than expected

## Common Mistakes to Avoid
- silently assigning EPSG:4326 when CRS is unknown
- joining on mismatched key types (string vs. integer GEOID)
- dropping geometry column during field selection
- overwriting raw data with processed output
- ignoring join diagnostics warnings

## Handoff Requirements
- list of output file paths
- processing steps taken
- warnings and diagnostics
- join match quality summary (if joins were performed)
- ready-for-analysis flag
- handoff JSON written to `runs/`
