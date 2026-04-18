# Workflow Handbook — Validation and QA

## Purpose
Verify that upstream processing and analysis outputs are complete, structurally sound, and honestly described before they proceed to reporting.

## When to Use
After the Spatial Analysis Agent declares `ready_for: "validation"` in its analysis handoff.

## Workflow Steps

### Step 1: Review upstream handoff
Read the analysis handoff from `runs/`. Note:
- which output files are declared
- what warnings and assumptions were recorded
- what the upstream processing handoff says about join quality and coverage

This context prevents false alarms — e.g., 1.8% demographic coverage is expected when the demo table has 10 rows for 553 tracts.

### Step 2: Output existence check
Run `validate_outputs.py` with all files listed in the analysis handoff.
- PASS: all files exist and are non-empty
- WARN: file exists but is 0 bytes
- FAIL: file not found

### Step 3: Vector QA
Run `validate_vector.py` on spatial datasets (GeoPackage, Shapefile, GeoJSON).
- CRS present and matches expected authority code
- Feature count meets minimum
- Geometries are valid (no self-intersections, null geometries flagged)
- Geometry types are consistent

### Step 4: Tabular QA
Run `validate_tabular.py` on datasets with required field and null checks.
- Row count meets minimum
- Required fields are present
- Null coverage per field, with configurable warning threshold

### Step 5: Join coverage check
Run `validate_join_coverage.py` on joined datasets.
- Key field uniqueness
- How many features have non-null data from the join
- Per-field coverage breakdown
- Row count matches expected total

### Step 6: Write validation handoff
Run `write_validation_handoff.py` to aggregate all check results into a single structured handoff.
- Loads individual check JSONs
- Determines overall outcome: PASS / PASS WITH WARNINGS / REWORK NEEDED
- Writes recommendation text
- References upstream analysis handoff
- Sets `ready_for: "reporting"` or `ready_for: "review"`

## Outcome Levels

| Outcome | Meaning | Action |
|---|---|---|
| PASS | All checks passed, no warnings | Proceed to reporting |
| PASS WITH WARNINGS | All checks passed but warnings were raised | Review warnings; proceed if acceptable |
| REWORK NEEDED | One or more checks failed | Fix upstream issues before reporting |

## Required QA Artifacts
- `runs/validation/check_output_existence.json`
- `runs/validation/check_vector_qa.json`
- `runs/validation/check_tabular_qa.json`
- `runs/validation/check_join_coverage.json`
- `runs/<run_id>.validation-handoff.json`

## Key Lessons
- Validation is read-only. Never modify upstream data.
- Partial coverage is not a failure — it is a warning that must be visible.
- Thresholds should reflect the context (demo vs. production).
- The validation handoff is the contract between QA and reporting.
- If validation finds issues that upstream agents should have caught, note them for the learning loop (Milestone 9).

## Common Pitfalls
- Running validation without reading the upstream handoff first (leads to false alarms on expected partial coverage)
- Using production thresholds on a demo dataset
- Treating WARN as FAIL — warnings are informational, not blocking
- Not writing the validation handoff even when all checks pass
