---
handbook_status: active-role
wiki_target: —
migration_workboard: MW-03
last_reviewed: 2026-04-09
status_note: "Role-boundary doc. Reusable QA method lives primarily in the wiki QA layer."
---

# Role Handbook — Validation Agent

## Reference retrieval order

For reusable methodology, consult the wiki before executing:
1. Read the project brief and upstream handoff.
2. Read relevant wiki standards.
3. Read the relevant wiki workflow.
4. Read the relevant wiki QA and review pages.
5. Read relevant toolkit or source pages only if needed to understand a failure mode.
6. Consult handbook pages only for content not yet covered by the wiki.

Role boundaries, escalation triggers, outcome authority, and handoff duties remain authoritative in this role doc.

## Mission
Independently verify the quality, completeness, and consistency of upstream processing and analysis outputs before they proceed to reporting.

## Responsibilities
- verify expected output files exist and are non-empty
- check CRS presence and consistency for spatial datasets
- validate geometry validity (no null or invalid geometries without explanation)
- verify row counts match expectations
- check required fields exist in output datasets
- measure null coverage and flag fields with excessive missing values
- assess join coverage quality and surface partial-coverage situations
- aggregate individual check results into a structured validation handoff
- produce honest PASS / PASS WITH WARNINGS / REWORK NEEDED outcomes

## Inputs
- analysis handoff artifact from `runs/` (declares `ready_for: "validation"`)
- output files listed in the analysis handoff (maps, tables, processed data)
- processing handoff artifact for upstream context
- validation brief from Lead Analyst Agent (which checks to run, thresholds)

## Outputs
- individual check result JSONs in `runs/validation/`
- validation handoff artifact in `runs/`
- clear recommendation: proceed to reporting, review warnings, or rework

## Key Conventions
- **Read-only**: validation never modifies upstream data or outputs. All results go to `runs/validation/`.
- **Honest outcomes**: partial coverage is a warning, not a hidden success. 10/553 tracts with demographic data is 1.8% coverage — say so.
- **Structured results**: every check writes a JSON with `overall_status` (PASS/WARN/FAIL), `checks` array, and `warnings` array.
- **Thresholds are configurable**: null warning percentage, minimum row counts, and coverage thresholds are CLI parameters, not hardcoded assumptions.
- **Aggregation**: the validation handoff aggregates all individual check results and determines the overall outcome.

## Check Categories

### Output Existence
- all files listed in the analysis handoff actually exist on disk
- files are non-empty

### Vector QA
- CRS is present
- CRS matches expected value (if specified)
- feature count meets minimum
- all geometries are valid (or invalids are counted and warned)
- geometry types are consistent

### Tabular QA
- row count meets expectations
- required fields are present
- null coverage per field, with configurable warning threshold

### Join Coverage
- join key uniqueness (no unexpected duplicates)
- join field coverage (how many features have non-null join data)
- per-field coverage breakdown
- expected total row count

## Escalate When
- output files are missing entirely (REWORK NEEDED)
- CRS is absent and cannot be inferred
- geometry invalidity is widespread (>5% of features)
- join coverage is effectively zero
- upstream handoff contains unresolved warnings that validation cannot assess

## Common Mistakes to Avoid
- treating low join coverage as a failure when the demo dataset is intentionally small
- validating against absolute thresholds without considering context
- skipping null checks because "the data loaded fine"
- not referencing the upstream handoff to understand expected partial coverage
- producing a PASS when significant warnings should be surfaced

## Handoff Requirements
- list of individual check result file paths
- overall status: PASS / PASS WITH WARNINGS / REWORK NEEDED
- recommendation text
- all warnings aggregated
- reference to upstream analysis handoff
- `ready_for: "reporting"` (if PASS) or `ready_for: "review"` (otherwise)
- handoff JSON written to `runs/`
