# Model Routing

Initial model-routing policy for the cleaned spatial-machines GIS architecture.

This document is intentionally provider-agnostic at the policy level. Specific spatial-machines config can map these tiers to concrete models later.

## Routing Principle

Assign models by cognition type, not by prestige.

Use stronger models for:
- planning under ambiguity
- statistical judgment
- interpretive critique
- client-facing synthesis where mistakes are expensive

Use cheaper models for:
- procedural execution
- deterministic transformation work
- packaging and structural checks

## Proposed Tiers

### Tier A: High Reasoning
Use for:
- planning
- decomposition
- ambiguity resolution
- statistical interpretation
- independent critique

Target roles:
- `lead-analyst`
- `spatial-stats`
- `peer-reviewer`

### Tier B: Medium-High Reasoning
Use for:
- narrative synthesis
- source evaluation when ambiguous
- complex design choices

Target roles:
- `report-writer`
- `data-retrieval` for ambiguous sourcing tasks
- `cartography` for high-judgment deliverables

### Tier C: Procedural Reliable
Use for:
- data transformation
- validation
- standard retrieval
- repeatable workflows

Target roles:
- `data-processing`
- `validation-qa`
- `data-retrieval` for routine acquisition

### Tier D: Low-Cost Utility
Use for:
- packaging
- publish/build operations
- low-ambiguity assembly work

Target roles:
- `site-publisher`

## Initial Per-Agent Recommendations

| Agent | Default Tier | Escalate To | Rationale |
|---|---|---|---|
| `lead-analyst` | Tier A | none by default | planning, orchestration, synthesis, escalation logic |
| `data-retrieval` | Tier C | Tier B | routine retrieval is procedural; source ambiguity raises reasoning demand |
| `data-processing` | Tier C | Tier B only if blocked | highly procedural and script-driven |
| `spatial-stats` | Tier A | none by default | statistical reasoning and uncertainty handling are high-value |
| `cartography` | Tier B | Tier A for unusually complex design or method selection | design and map-type judgment matter, but not every task needs frontier-level reasoning |
| `validation-qa` | Tier C | Tier B when thresholds or anomalies are ambiguous | mostly deterministic structural QA |
| `report-writer` | Tier B | Tier A for high-stakes client narrative | synthesis quality matters, but much of the structure can be standardized |
| `site-publisher` | Tier D | Tier C if templating/build issues become non-trivial | packaging and assembly are low-ambiguity |
| `peer-reviewer` | Tier A | none by default | interpretive and reputational critique is high-value |

## Concrete Initial Mapping Proposal

This is a policy suggestion, not yet a final spatial-machines config.

### Primary strong model
- Use for Tier A
- Initial use: `gpt-5.4`

### Mid-tier model
- Use for Tier B
- Initial use: `gpt-5.4-mini`

### Efficient baseline model
- Use for Tier C and Tier D
- Initial use: `gpt-5.4-mini`

## Escalation Policy

Escalate a task upward when any of the following is true:

- the role reports ambiguity it cannot resolve from artifacts
- the task affects client-facing claims or delivery risk
- the method is experimental or under-specified
- the role needs to reconcile conflicting evidence
- a review gate would otherwise be passed on weak reasoning

## De-Escalation Policy

Do not keep a strong model assigned when:

- the task is mostly file movement, packaging, or template rendering
- the task is deterministic script invocation with known parameters
- the task is repeated validation or status checking

## Open Questions

These should be finalized after more review and some live testing:

- whether `report-writer` should stay on `gpt-5.4-mini` or move to `gpt-5.4` for high-stakes client work
- whether `cartography` can stay on `gpt-5.4-mini` for most tasks
- whether `data-retrieval` should dynamically route by source complexity later
- whether `site-publisher` ever needs more than `gpt-5.4-mini` outside template debugging

## Configuration Intent

When this policy is translated into spatial-machines configuration:

- assign one default model per agent
- allow escalation paths for selected agents
- avoid paying Tier A costs for routine pipeline execution
- preserve high-end reasoning where it has the highest leverage

## Current Rebuild Decision

For the first rebuilt deployment:
- Tier A roles use `gpt-5.4`
- Tier B, Tier C, and Tier D roles use `gpt-5.4-mini`
- OpenAI is the primary hosted provider
- Ollama remains optional fallback infrastructure, not the default routing path
