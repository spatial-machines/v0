# Lead Analyst Orchestration Workflow

Purpose:

- define the reusable orchestration method that produces a run plan, monitors pipeline status, synthesizes upstream handoffs, and writes the orchestration handoff at the end of a pipeline run
- describe the synthesis principles (artifact-driven, honest synthesis, traceability) that govern any role responsible for coordinating a multi-stage analysis
- give a stage-level playbook that can be followed by a human analyst, an orchestrating agent, or any future configuration of the team

## Relationship to Role Authority

This page describes the **method** of orchestration. It does not describe the **authority** of the lead analyst role.

Authority — including which specialists to activate, which operating mode the role uses for the run, when to escalate to human review, and the schema of the orchestration handoff artifact — remains with the orchestration role doc and supporting governance docs:

- `handbooks/roles/lead-analyst-agent.md` — mission, scope, operating modes, escalation triggers, non-negotiables, handoff requirements
- `TEAM.md` — team composition and full-pipeline sequence
- `ARCHITECTURE.md` — Orchestration Modes section, Lead Analyst Handoff section, Memory Layer section

This workflow assumes:

- The role authority for the orchestration role is defined elsewhere.
- An operating mode has already been selected for the run by the role that owns delegation authority.
- The handoff artifact's JSON schema is owned by the architecture documentation, not by this page.

## Typical Use Cases

- coordinating a full multi-stage analysis run from task intake through final synthesis
- preparing a structured task brief from an incoming request before delegating to specialists
- inspecting which upstream handoff artifacts exist for a partially-complete run
- producing a structured run summary from completed stage handoffs before declaring the run ready for human review
- writing the orchestration handoff that closes a run and records the recommendation for the human reviewer

## Inputs

- the incoming task request (geography, data sources, analysis goals, output format)
- upstream handoff artifacts written to `runs/` by each completed pipeline stage
- output files referenced by upstream handoffs (maps, tables, reports)
- the project brief and any project-specific constraints

## Preconditions

- the role's operating mode has been selected per the role doc
- the project brief is available (or the orchestration step is itself the brief-creation step)
- when synthesizing, all expected upstream handoff artifacts have been produced or their absence is known
- the orchestration role's read-only-on-upstream-artifacts non-negotiable (defined in the role doc) is respected throughout

## Preferred Tools

- structured handoff artifacts in `runs/` as the source of truth for stage state
- markdown for the human-readable run summary in `outputs/reports/`
- JSON for the handoff artifact, following the schema owned by the architecture documentation

## Execution Order

1. **Create the run plan.** Record the task description, the geographic scope, the data sources expected to be retrieved, the expected outputs, and the pipeline stages expected to run. The run plan is the contract for what was requested. It is referenced by every downstream stage and by the eventual orchestration handoff. The run plan is written to `runs/`.
2. **Check pipeline status.** Before any synthesis, inspect which upstream handoff artifacts exist in `runs/` and which expected artifacts are missing. Read the validation handoff if it is present and record its outcome (PASS / PASS WITH WARNINGS / REWORK NEEDED) per `workflows/VALIDATION_AND_QA_STAGE.md`. The status check is a precondition for synthesis: synthesizing without first checking status risks producing summaries based on incomplete data.
3. **Synthesize the run summary.** Read every available upstream handoff. Extract the key findings each stage produced — sources used, processing steps applied, analysis outputs, validation outcome, report artifacts. Surface warnings and caveats from every stage so they remain visible in the summary. Write a structured run summary in markdown to `outputs/reports/`. The summary is the human-readable artifact that explains what the run produced and what the reviewer should know.
4. **Write the orchestration handoff.** Produce the final handoff artifact for the run. The handoff conveys: a reference to the run plan, the pipeline status (which stages completed, which are missing), the synthesis summary (key findings, QA outcome, caveats), the list of key output artifacts, the recommendation for the next action, and the readiness state of the run. The handoff is written to `runs/`. **For the exact JSON schema, the field names, and the readiness vocabulary, see the role doc and `ARCHITECTURE.md` § Lead Analyst Handoff.** This workflow does not redefine the schema.

## Synthesis Principles

These principles apply to step 3 (synthesis) but govern the orchestration role's behavior throughout the workflow.

- **Artifact-driven.** Every decision and every claim in the run summary is grounded in a recorded handoff artifact. The orchestrator does not invent findings, does not assume what may have happened, and does not summarize anything that is not visible in the artifacts.
- **Honest synthesis.** If validation produced PASS WITH WARNINGS, the warnings appear in the summary. If coverage is partial, the partiality is named. If a stage is missing, its absence is noted rather than papered over. The orchestrator never overclaims.
- **Traceability.** Every claim in the run summary references the specific upstream run identifier or artifact path that supports it. A reviewer should be able to walk from any sentence in the summary back to the artifact it came from.
- **Read-only on upstream artifacts.** The orchestration role's role doc declares this as a non-negotiable. The workflow inherits it: the orchestrator never modifies upstream handoff artifacts, output files, or processing data. The synthesis is a read-only summary.

These synthesis principles apply to the orchestrator's run summary, which reads upstream handoffs. For checks against client-facing outputs, see `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`.

## Validation Checks

Before the orchestration handoff is finalized, confirm:

- the run plan exists and has been referenced
- pipeline status has been checked; missing stages are documented or explained
- every expected upstream handoff has been read or its absence has been noted
- the validation outcome (per `workflows/VALIDATION_AND_QA_STAGE.md`) is surfaced accurately in the summary
- referenced output files actually exist on disk
- the run summary does not contain claims that go beyond what the artifacts record
- the run summary references specific upstream run identifiers, not generic "upstream" language
- warnings from every upstream stage are visible in the summary
- the orchestration handoff references the run plan, the upstream handoffs, the synthesis summary, the key outputs, and the recommendation

## Common Failure Modes

- synthesizing the run summary before checking pipeline status, then producing a summary based on incomplete data
- presenting partial-coverage or demo results as if they were production-quality
- losing validation warnings between the validation handoff and the orchestration handoff
- writing a run summary that does not reference any specific upstream run identifier
- treating the orchestration handoff as a rubber stamp rather than a substantive review checkpoint
- summarizing findings the upstream artifacts do not actually record
- modifying or restyling upstream artifacts to make the summary tidier

## Escalate When

The escalation triggers below are pattern-level — they describe situations the orchestration *method* hands back to the role that owns escalation authority. The role doc defines what to do when escalation fires.

- expected upstream handoff artifacts are missing and cannot be located
- upstream handoffs contain conflicting information that the orchestrator cannot reconcile from the artifacts alone
- the incoming task request is ambiguous or describes work outside the team's current capabilities
- data quality issues recorded in upstream handoffs are severe enough to call the usefulness of the outputs into question
- the validation outcome is REWORK NEEDED and the orchestrator cannot produce a useful summary without resolution

## Outputs

The orchestration workflow produces:

- a run plan artifact in `runs/`
- a run summary in markdown in `outputs/reports/`
- an orchestration handoff artifact in `runs/`

The orchestration handoff conveys (informational fields, not a JSON schema): the run plan reference, the pipeline status, the synthesis summary, the list of key output artifacts, the warning list, the recommendation, and the readiness state. The exact schema is owned by `ARCHITECTURE.md` § Lead Analyst Handoff.

## Related Standards

- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — provenance fields the orchestration handoff inherits from the firm's general handoff standard
- `standards/PUBLISHING_READINESS_STANDARD.md` — downstream gate that consumes the orchestration handoff for client-facing delivery

## Related Workflows

- `workflows/VALIDATION_AND_QA_STAGE.md` — the immediate upstream stage; the orchestration workflow consumes the validation handoff and surfaces its outcome
- `workflows/REPORTING_AND_DELIVERY.md` — runs after analysis and before orchestration synthesis in pipelines that produce a report
- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — earlier upstream stage whose handoff feeds the synthesis chain

## Related QA Pages

- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — applies to client-facing outputs; complements the orchestration workflow's synthesis principles
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — feeds the validation outcome that the orchestration workflow surfaces

## Sources

- firm orchestration methodology notes
- the existing handbook workflow that this page promotes (script execution detail remains in the handbook)

## Trust Level

Validated Workflow — Needs Testing
