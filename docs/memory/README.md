# Memory Layer

Per-fork institutional memory for the spatial-machines pipeline. Forks accumulate their own memory here as the team does more analyses; this content is **not** shipped from upstream.

## Why this folder exists

Agents improve when they can reference past decisions, past failures, and lessons a human operator wants them to carry forward. The memory layer gives agents four kinds of persistent context, each with its own file or subdir:

| Artifact | Purpose | Updated by |
|---|---|---|
| `PROJECT_MEMORY.md` | Human-maintained institutional summary — "read first on every engagement" | You (manually) |
| `lessons-learned.jsonl` | Append-only structured lessons from prior runs | `scripts/core/log_lesson.py` |
| `retrospectives/*.retro.md` | Per-run or per-milestone-chain retrospectives | `scripts/future/write_retrospective.py` (or by hand) |

The memory layer is referenced in [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) as Layer 2. It is not required — agents work fine without any memory content — but it's the mechanism by which your fork gets smarter over time.

## Why this README is the only tracked file

The contents of a memory folder are per-firm, per-fork, per-engagement. Shipping one person's memory as upstream content confuses every future fork. So:

- Upstream (this repo) ships **only this README**.
- The actual memory artifacts are in `.gitignore` so forks accumulate them locally without accidentally committing them back.
- When you fork and customize, your memory stays yours.

If you want to share institutional memory with your team, use your fork's own remote — don't send it upstream.

## File formats

### `PROJECT_MEMORY.md`

Free-form markdown. A practical starting template:

```markdown
# Project Memory — [Your Firm / Your Project]

_Last updated: YYYY-MM-DD_

## Current state
- Active version / release
- Live analyses
- Known open issues

## Standing conventions
- Preferred CRS per region
- Palette overrides
- QA thresholds your team uses

## Patterns that have worked
- [Domain] analyses benefit from [specific approach]
- [Data source] needs [specific handling]

## Patterns to avoid
- Don't [thing] because [reason]

## Escalation contacts
- [role] → [person or channel]
```

Read it before the engagement. Update it after significant changes. Treat it like your onboarding doc for your firm's next senior analyst.

### `lessons-learned.jsonl`

Append-only JSONL, one lesson per line. Schema:

```json
{
  "timestamp": "2026-04-16T13:42:30.313305+00:00",
  "category": "data-quality | process | qa | tooling | cartography | ...",
  "tags": ["retrieval", "census", "tiger"],
  "lesson": "one-sentence lesson",
  "run_id": "analysis-or-run-id-this-came-from",
  "detail": "optional longer context"
}
```

Use `scripts/core/log_lesson.py` to add entries — it creates the file if missing and validates the schema.

Lessons are agent-readable. When `data-retrieval` picks up a Census fetch, it can query the lessons log for tags like `["retrieval", "census"]` and surface prior gotchas.

### `retrospectives/<run-or-milestone-id>.retro.md`

Per-run retrospective. Produced after a significant pipeline run finishes. Suggested sections:

- **Pipeline summary** — stages covered, runtime
- **What worked** — good decisions, efficient patterns
- **What didn't** — friction, bugs, wrong turns
- **Lessons promoted** — which lessons were written to `lessons-learned.jsonl`
- **Follow-ups** — work to do later

Name by the run ID or analysis ID (e.g., `atl-equity-q2.retro.md`).

## Integration

- **`scripts/core/log_lesson.py`** — append a lesson to `lessons-learned.jsonl`
- **`scripts/core/check_memory_status.py`** — report staleness of memory files
- **`scripts/future/update_project_memory.py`** — auto-regenerate `PROJECT_MEMORY.md` from recent activity (experimental)
- **`scripts/future/write_retrospective.py`** — stub retrospective for a given run (experimental)

## When to refresh

- **`PROJECT_MEMORY.md`** — after major architectural changes, team changes, or when onboarding a new analyst
- **`lessons-learned.jsonl`** — whenever a run teaches you something worth remembering
- **`retrospectives/`** — after every substantive analysis
