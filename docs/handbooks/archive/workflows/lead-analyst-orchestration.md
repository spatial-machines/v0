# Workflow Handbook — Lead Analyst Orchestration

## Purpose
Coordinate a GIS analysis run from task intake through final synthesis. The Lead Analyst creates a run plan, monitors pipeline status, synthesizes upstream results, and declares the run ready for human review.

## When to Use
When a GIS analysis task has progressed through some or all specialist stages (retrieval, processing, analysis, validation, reporting) and needs a coordinating synthesis before delivery.

## Workflow Steps

### Step 1: Create run plan
Run `create_run_plan.py` to define the task scope and expected pipeline stages.
- records the task description, geography, data sources, and expected outputs
- lists which pipeline stages are expected to run
- provides a structured task brief that downstream agents and reviewers can reference
- outputs a run plan JSON to `runs/`

### Step 2: Check pipeline status
Run `check_pipeline_status.py` to inspect which upstream handoff artifacts exist.
- looks for expected stage handoffs (provenance, processing, analysis, validation, reporting)
- reports which stages are complete vs missing
- reads validation status from the validation handoff if present
- outputs a pipeline status summary to stdout

### Step 3: Synthesize run summary
Run `synthesize_run_summary.py` to produce a structured summary from upstream handoffs.
- reads all available stage handoffs
- extracts key findings: sources, processing steps, analysis outputs, validation status, report artifacts
- surfaces warnings and caveats from every stage
- writes a lead summary markdown to `outputs/reports/`

### Step 4: Write lead handoff
Run `write_lead_handoff.py` to create the final lead analyst handoff artifact.
- references the run plan and all upstream handoffs
- includes the pipeline status and synthesis summary
- records the recommendation for human review
- declares `ready_for: "human-review"`
- outputs a lead handoff JSON to `runs/`

## Typical Inputs
- task request (what to analyze, what geography, what outputs needed)
- upstream handoff JSONs in `runs/`
- output files in `outputs/` referenced by upstream handoffs

## Typical Outputs
- run plan JSON in `runs/`
- lead summary markdown in `outputs/reports/`
- lead handoff JSON in `runs/`

## Required QA
- verify all expected pipeline stages have handoff artifacts before synthesizing
- check that validation status is surfaced accurately in the summary
- confirm that referenced output files actually exist
- ensure the summary does not overclaim or invent findings beyond what artifacts record

## Common Pitfalls
- synthesizing without first checking pipeline status (missing stages go unnoticed)
- presenting partial-coverage demo results as if they are production quality
- not surfacing validation warnings in the final summary
- writing a lead handoff without referencing specific upstream run IDs
- treating the lead handoff as an automatic approval rather than a review checkpoint

## Example Tasks
- "Synthesize the Nebraska tracts demo run and prepare it for human review"
- "Check which stages have completed for the flood risk analysis run"
- "Create a task brief for a new county-level demographic analysis"

## Notes / Lessons
- The lead analyst role is a coordination layer, not an autonomous reasoning engine. It reads artifacts, summarizes them, and flags issues — it does not generate new analysis.
- Pipeline status checking should happen before synthesis to avoid writing summaries based on incomplete data.
- The run plan serves as a contract for what was requested, making it easier to evaluate whether the outputs actually address the task.
