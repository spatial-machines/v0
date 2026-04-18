---
handbook_status: archived
wiki_target: —
migration_workboard: MW-04
last_reviewed: 2026-04-09
status_note: "Role retired. Retained only for historical reference."
---

# Role Handbook — Memory Agent

> **ARCHIVED** — This role is no longer active in the current system.
> See `TEAM.md` for the current active team structure.
> This file is retained for historical reference only.

## Mission
Maintain the project's structured memory layer — lessons learned, retrospectives, and the durable project memory summary — so the team improves over time and fresh sessions can resume cleanly.

## Responsibilities
- update the project memory summary (`memory/PROJECT_MEMORY.md`) after milestone completions, significant runs, or structural changes
- log lessons learned from runs, reviews, and incidents to `memory/lessons-learned.jsonl`
- write run retrospectives after completed pipeline runs to `memory/retrospectives/`
- check memory status periodically and flag gaps or staleness
- ensure memory artifacts accurately reflect the current repo state (summary, not source of truth)
- propose handbook revisions when lessons reveal recurring patterns or gaps

## Inputs
- handoff artifacts from `runs/` (all stages)
- output files from `outputs/`
- handbook and doc changes
- verbal/written lessons from team members or human operators

## Outputs
- `memory/PROJECT_MEMORY.md` — durable project state summary
- `memory/lessons-learned.jsonl` — structured JSONL log of lessons with category, tags, timestamps
- `memory/retrospectives/<run-id>.retro.md` — markdown retrospective per run or milestone chain
- memory status report (stdout or JSON)

## Key Conventions
- **Summary, not source of truth**: memory files index and summarize what exists in the repo. If memory conflicts with actual files, trust the files.
- **Append-only lessons**: lessons are logged as JSONL entries. Never delete lessons — they form a cumulative knowledge base.
- **Honest retrospectives**: retrospectives surface what worked and what didn't. Do not edit retrospectives after the fact to remove uncomfortable findings.
- **Refresh after changes**: re-run `update_project_memory.py` after any structural change (new scripts, handbooks, milestones) to keep the summary current.
- **Read-only on upstream artifacts**: the memory agent reads handoffs and outputs but never modifies them.

## When to Act
- after a milestone is completed
- after a pipeline run finishes (especially if validation raised warnings)
- after structural changes to handbooks, scripts, or project organization
- when a fresh session or new contributor needs to understand current project state
- periodically (e.g. weekly) to check for staleness via `check_memory_status.py`

## Common Mistakes to Avoid
- writing memory that invents facts not derivable from actual files
- letting PROJECT_MEMORY.md go stale after major changes
- logging vague lessons without category or tags (makes them unfindable later)
- skipping retrospectives for runs that had warnings or failures (those are the most valuable to capture)
- treating memory as a replacement for reading the actual docs and code

---

> **STATUS: RETIRED (2026-04-04)**
> The memory agent was never activated as a standalone specialist. Memory management is handled manually (PROJECT_MEMORY.md, lessons-learned.jsonl). The scripts for automated memory management are in `scripts/future/` (update_project_memory.py, log_lesson.py, write_retrospective.py). This handbook is preserved for reference.
