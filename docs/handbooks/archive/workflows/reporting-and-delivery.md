# Workflow Handbook — Reporting and Delivery

## Purpose
Transform upstream handoff artifacts into readable reports that honestly communicate findings, methods, limitations, and data provenance.

## When to Use
After the Validation Agent produces a validation handoff (with status PASS, PASS WITH WARNINGS, or REWORK NEEDED). Reports can be generated regardless of validation outcome, but the QA status must be surfaced honestly.

## Workflow Steps

### Step 1: Collect upstream artifacts
Run `collect_report_assets.py` to gather and normalize references from upstream handoffs.
- reads provenance, processing, analysis, and validation handoff JSONs
- resolves artifact paths and checks that referenced files exist
- outputs a consolidated asset manifest for the report generators

### Step 2: Generate markdown report
Run `write_markdown_report.py` with the asset manifest.
- produces a structured markdown document with all required sections
- title, scope, methods, outputs, QA status, caveats, sources
- written to `outputs/reports/`

### Step 3: Generate HTML report
Run `write_html_report.py` with the asset manifest.
- produces a self-contained static HTML page with inline CSS
- same content structure as the markdown report
- no external dependencies or JavaScript frameworks
- written to `outputs/reports/`

### Step 4: Write reporting handoff
Run `write_reporting_handoff.py` to create the structured handoff artifact.
- records `output_files` for downstream consistency
- keeps detailed `report_files` existence/size checks
- includes upstream handoff references
- summarizes the reporting outcome
- written to `runs/`

## Required Report Sections

| Section | Content |
|---|---|
| Title / Summary | One-line description and overall outcome |
| Scope / Inputs | Geography, vintage, data sources, upstream outputs used |
| Methods | Processing steps, analysis methods, classification schemes |
| Outputs Created | List of maps, tables, data files with descriptions |
| QA Status | Validation outcome, check counts, specific warnings |
| Caveats | Partial coverage, demo data, null rates, assumptions |
| Sources / Provenance | Data origins, retrieval methods, vintage, citations |

## Key Lessons
- Reporting is read-only. Never modify upstream data or artifacts.
- Validation warnings must appear in the report, not be filtered out.
- Demo data should be labeled as demo data in every report.
- The reporting handoff is the final artifact in the pipeline before Lead Analyst synthesis.
- HTML reports should render correctly when opened directly in a browser — no build step needed.

## Common Pitfalls
- Generating reports without first checking that upstream handoffs and output files exist
- Presenting partial-coverage analysis results as if they are comprehensive
- Omitting the methods section or using vague language that prevents reproducibility
- Not including provenance information for the data sources
- Making the HTML report depend on external CSS/JS that may not be available offline
