# Agent Contract Template

Standard template for all active agent prompt folders.

Use this template for each active role so any frontier model can occupy the role without inheriting contradictory instructions. Each agent folder at `agents/<role>/` contains three files:

| File | Purpose |
|---|---|
| `SOUL.md` | Mission, non-negotiables, boundaries, escalation conditions |
| `TOOLS.md` | Approved scripts and execution rules |
| `AGENTS.md` | Upstream/downstream relationships, handoff expectations |

## File Responsibilities

### `SOUL.md`
Contains:
- mission
- non-negotiable rules
- role boundary
- escalation conditions
- can-do-now capabilities
- experimental / not-guaranteed capabilities
- decision heuristics

Should not contain:
- secrets
- machine-specific auth notes
- stale team references
- large script catalogs

### `TOOLS.md`
Contains:
- approved production tools for this role
- required inputs and outputs
- execution environment notes that are operationally necessary
- references to canonical docs for standards and workflow

Should not contain:
- aspirational capabilities presented as guaranteed
- local secrets or tokens
- broad architecture ownership that belongs in canonical docs

### `AGENTS.md`
Contains:
- upstream/downstream role relationships
- handoff expectations
- when to escalate back to `lead-analyst`

Should not contain:
- stale agent roster
- detailed tool catalogs
- duplicated workflow docs

## Standard Role Sections

Every active role should follow this shape.

### 1. Role Header
- agent id
- canonical role name
- short mission statement

### 2. Mission
- what this role exists to do
- what value it adds to the pipeline

### 3. Non-Negotiables
- 3 to 7 hard rules
- focused on behavior that protects quality

### 4. Owned Inputs
- which artifacts the agent reads
- where those artifacts come from

### 5. Owned Outputs
- which artifacts the agent writes
- where they go
- what downstream role depends on them

### 6. Role Boundary
- what the agent does own
- what the agent does not own

### 7. Can Do Now
- production-grade capabilities the role may rely on without approval

### 8. Experimental / Escalate First
- methods or tools that exist but are not yet guaranteed
- tasks that require stronger model routing or human confirmation

### 9. Escalate When
- ambiguity
- missing prerequisites
- quality thresholds violated
- task outside current production capability

### 10. Handoff Contract
- minimum required artifact fields
- downstream readiness flag

## Example Boundary Language

Use clear boundary statements like:

- "You own structural QA, not interpretive critique."
- "You may generate analysis maps, but final delivery-quality maps belong to cartography."
- "You package outputs; you do not author findings."

Avoid vague statements like:

- "Help wherever needed."
- "You can do the whole pipeline if necessary."

## Capability Labeling Rules

Every role should distinguish:

### Production
- stable
- approved for autonomous use
- backed by current scripts and workflow

### Experimental
- available but not guaranteed
- may require lead-analyst escalation
- may require human approval

### Historical
- not active
- archived reference only

## Model-Agnostic Writing Rules

To keep the prompts portable across GPT, Claude, and other frontier models:

- prefer explicit role boundaries over implied behavior
- prefer short rules over long motivational prose
- avoid relying on provider-specific prompt habits
- avoid teaching the model capabilities the system does not actually support
- encode decision patterns with concrete examples where ambiguity is high
- keep the source of truth small and consistent

## Required Canonical References

Each active agent should point back to:
- `ACTIVE_TEAM.md`
- `PIPELINE_CANON.md` once created
- `TOOL_GOVERNANCE.md` once created
- `DATA_REUSE_POLICY.md` once created

Those files should define shared truth. The agent files should only define role-local behavior.
