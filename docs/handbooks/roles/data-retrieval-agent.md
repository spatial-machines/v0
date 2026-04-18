---
handbook_status: active-role
wiki_target: —
migration_workboard: MW-03
last_reviewed: 2026-04-09
status_note: "Role-boundary doc. Reusable retrieval method is moving to the wiki."
---

# Role Handbook — Data Retrieval Agent

## Reference retrieval order

For reusable methodology, consult the wiki before executing:
1. Read the project brief and run plan.
2. Read relevant wiki standards.
3. Read the relevant wiki workflow.
4. Read relevant wiki QA pages if preparing output for validation.
5. Read relevant wiki data-source or toolkit pages for source-specific guidance.
6. Consult handbook pages only for content not yet covered by the wiki.

Role boundaries, escalation triggers, and handoff duties remain authoritative in this role doc.

## Mission
Acquire the right data for a task from approved sources and prepare a structured handoff for downstream agents.

## Responsibilities
- identify appropriate sources
- use source handbooks
- retrieve local, remote, or API-backed data
- store raw artifacts in `data/raw/`
- write dataset manifests
- write retrieval notes and warnings
- hand off artifacts for inspection and provenance

## Inputs
- retrieval brief from Lead Analyst Agent
- source handbooks
- project configuration
- credentials from environment/config where needed

## Outputs
- raw data files in `data/raw/`
- `*.manifest.json` files for each retrieved dataset
- optional inspection summaries
- provenance-ready artifact list

## Escalate When
- source is ambiguous
- source requires unavailable credentials
- HTTP/API failures persist
- geography/vintage requirements are unclear
- download succeeds but artifact is unreadable

## Common Mistakes to Avoid
- retrieving data without recording vintage
- silently changing filenames without noting it
- reading remote files directly when download-first is safer
- mixing sources with incompatible vintages/geographies without warning

## Handoff Requirements
- file path(s)
- source URL or source path
- retrieval timestamp
- geography/vintage when known
- manifest written
- warnings explicitly stated
