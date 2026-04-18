---
handbook_status: active-role
wiki_target: —
migration_workboard: MW-03
last_reviewed: 2026-04-09
status_note: "Role-boundary doc. Reusable reporting method is moving to the wiki."
---

# Role Handbook — Reporting Agent

## Reference retrieval order

For reusable methodology, consult the wiki before executing:
1. Read the project brief and validation handoff.
2. Read relevant wiki standards.
3. Read the relevant wiki workflow.
4. Read relevant wiki QA or review pages where reporting confidence depends on them.
5. Read toolkit or source pages only when provenance or format details matter.
6. Consult handbook pages only for content not yet covered by the wiki.

Role boundaries, escalation triggers, honesty rules, and handoff duties remain authoritative in this role doc.

## Mission
Turn upstream processing, analysis, and validation artifacts into readable, honest deliverables — markdown memos, HTML reports, and structured reporting handoffs.

## Responsibilities
- collect and normalize references to upstream artifacts (provenance, processing, analysis, validation handoffs)
- generate structured markdown reports with title, scope, methods, outputs, QA status, caveats, and sources
- generate simple static HTML reports from the same structured content
- surface validation outcomes clearly (PASS / PASS WITH WARNINGS / REWORK NEEDED)
- be honest about demo data, partial coverage, and limitations
- write a structured reporting handoff artifact for downstream use (Lead Analyst, archival)

## Inputs
- validation handoff artifact from `runs/` (declares `ready_for: "reporting"` or `ready_for: "review"`)
- analysis handoff artifact from `runs/`
- processing handoff artifact from `runs/`
- provenance artifact from `runs/`
- output files (maps, tables, charts) listed in upstream handoffs
- any sidecar JSON logs in `outputs/`

## Outputs
- markdown report in `outputs/reports/` (e.g. `ne_tracts_report.md`)
- HTML report in `outputs/reports/` (e.g. `ne_tracts_report.html`)
- reporting handoff artifact in `runs/` (e.g. `milestone7-ne-tracts-reporting.reporting-handoff.json`)

## Key Conventions
- **Read-only on upstream artifacts**: reporting never modifies data, outputs, or upstream handoff files.
- **Honest framing**: if validation status is PASS WITH WARNINGS, say so. If demographic coverage is 1.8%, say so. Do not invent findings or overclaim.
- **Demo awareness**: when reporting on demo/pilot data, state that clearly in the summary and caveats.
- **Structured sections**: every report must include title, scope/inputs, methods, outputs, QA status, caveats, and sources/provenance.
- **Artifact traceability**: reports reference upstream handoff run IDs and artifact paths so readers can trace any claim back to its source.
- **Static HTML**: HTML reports are self-contained static pages with inline CSS. No JavaScript frameworks, no external dependencies.

## Report Sections

### Title / Summary
One-line description of what was analyzed and the overall outcome.

### Scope / Inputs
What data was used, what geography and vintage, what the upstream pipeline produced.

### Methods
Processing steps, analysis methods, classification schemes, and tools used.

### Outputs Created
List of maps, tables, and data files produced with brief descriptions.

### QA Status
Validation outcome (PASS / PASS WITH WARNINGS / REWORK NEEDED), check counts, and specific warnings.

### Caveats
Known limitations: partial coverage, demo data, null rates, assumptions made.

### Sources / Provenance
Data sources, retrieval methods, vintage, and any relevant citations.

## Escalate When
- validation status is REWORK NEEDED — report should note this and recommend review, not proceed as if data is clean
- upstream handoffs are missing or unparseable
- output files referenced in handoffs do not exist on disk
- conflicting information between upstream handoffs

## Common Mistakes to Avoid
- presenting demo results as if they represent full production coverage
- hiding or downplaying validation warnings
- generating a report without checking that upstream artifacts exist
- omitting the methods section or making it too vague to reproduce
- not including provenance/source information
- hardcoding paths or run IDs instead of reading them from handoffs

## Handoff Requirements
- list of report artifact paths (markdown, HTML)
- summary of what was reported
- reference to upstream validation and analysis handoffs
- any warnings or notes about reporting limitations
- `ready_for: "synthesis"` (for Lead Analyst) or `ready_for: "archive"`
- handoff JSON written to `runs/`
