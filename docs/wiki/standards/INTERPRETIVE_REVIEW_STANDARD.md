# Interpretive Review Standard

Purpose:
define the firm's policy on when and how interpretive review must occur
specify what interpretive review covers, who can perform it, and what rigor is required
provide the governing rules that the
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
operationalizes
This standard defines policy. The
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
is the operational tool that implements it.
Use When
Use this standard to determine:
whether an output requires interpretive review before delivery
what rigor level is expected
who is qualified to perform interpretive review
when interpretive review must escalate
Do Not Use When
Do not use this standard for:
structural validation of data integrity (use
standards/STRUCTURAL_QA_STANDARD.md
)
cartographic or map-specific review (use
qa-review/MAP_QA_CHECKLIST.md
)
legal-grade analysis (use
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
, which imposes additional requirements)
Approved Rule
When Interpretive Review Is Required
Interpretive review is mandatory before any output that contains:
narrative text, findings, or conclusions
maps or charts intended for a client or public audience
summary tables with interpretive labels (e.g., "high growth," "declining market")
agent-generated text of any kind that will reach a human audience outside the project team
What Interpretive Review Covers
Interpretive review validates that the output's meaning is accurate, defensible, and appropriately framed. It does not cover data integrity (structural QA) or cartographic craft (map QA).
Core areas:
claims match data: every assertion can be traced to a specific value in the output
context is present: geography, time period, source, and caveats are stated
overclaiming is flagged: no causal claims without evidence, no confidence beyond what the data supports
metric integrity: counts, rates, shares, and medians are correctly distinguished and described
sensitivity: framing of race, income, and community characteristics follows firm standards
Who Can Perform Interpretive Review
a human analyst who did not produce the output (preferred)
the producing analyst if no second reviewer is available (document this exception)
an agent may assist with interpretive checks but may not be the sole reviewer for client-facing outputs
Rigor Levels
Standard Review
required for all client-facing outputs
all checklist sections are checked
one human reviewer minimum
Enhanced Review
required when findings are politically or commercially sensitive
required when findings involve legal, regulatory, or equity claims
all checklist sections are checked plus domain-specific review
two human reviewers or one senior reviewer
Sequence
Interpretive review runs after:
structural QA has passed
domain-specific QA has passed (trend review, ZIP rollup review, POI QA, etc.)
Interpretive review runs before:
publishing readiness assessment
client delivery
Inputs
the output to be reviewed (tables, maps, charts, narrative text)
the structural QA result confirming data integrity
the project brief (to confirm scope and audience)
applicable standards (trend analysis, demographic shift, aggregation, etc.)
Method Notes
Interpretive review is a judgment task. It cannot be fully automated.
The reviewer must have access to the underlying data, not just the narrative or map.
For agent-generated text, the reviewer should compare the text against the data row by row for at least the key findings.
When multiple interpretations of the data are reasonable, the output should acknowledge alternatives or note that the presented interpretation was chosen for stated reasons.
If time pressure forces a reduced review, document which sections were deferred and why.
Validation Rules
The interpretive review process itself should fail if:
no review occurred before client delivery
the review was performed only by the producing analyst and no exception was documented
an agent was the sole reviewer for client-facing narrative
the reviewer did not have access to the underlying data
failures or concerns from the review were overridden without documentation
Human Review Gates
Escalate when:
a finding could affect client investment, policy, or legal decisions
demographic change framing could be politically sensitive
the output's audience includes media, regulators, or the public
the reviewer disagrees with the framing chosen by the producing analyst
margin-of-error overlap makes a key finding statistically weak
Common Failure Modes
treating structural QA as sufficient and skipping interpretive review
performing interpretive review on a draft version and not re-running after data changes
letting agent-generated narrative reach the client without human review
reviewing the narrative without checking it against the underlying data
deferring interpretive review to the client ("they'll catch any problems")
conflating interpretive review with proofreading
Related Workflows
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
— the operational checklist this standard governs
standards/STRUCTURAL_QA_STANDARD.md
— must pass first
standards/PUBLISHING_READINESS_STANDARD.md
— Gate 3 requires interpretive review
standards/DEMOGRAPHIC_SHIFT_STANDARD.md
— governs demographic framing within interpretive review
standards/TREND_ANALYSIS_STANDARD.md
— governs trend claims within interpretive review
Sources
firm project review processes
firm delivery methodology notes
Trust Level
Production Standard
