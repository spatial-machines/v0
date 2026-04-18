# Legal-Grade Analysis Standard

Purpose:
define the additional requirements that apply when a firm analysis may be used in legal, regulatory, or evidentiary contexts
prevent analysis produced to normal commercial standards from being silently treated as litigation-ready
make the distinction between commercial-grade and legal-grade work explicit at project intake
Use When
Use this standard when a project involves:
analysis that may be submitted to a court, regulatory body, or government agency
expert report or declaration support
environmental impact assessments with legal exposure
property or boundary disputes
water rights, drainage, or hydrology analyses with regulatory implications
any work where the methodology could be challenged under cross-examination or formal review
Do Not Use When
Do not use this standard for:
standard market analysis or demographic reporting for commercial clients
internal screening or exploratory analysis
research notes or preliminary findings
If unsure, escalate to a principal before proceeding.
Approved Rule
Legal-Grade Designation
The legal-grade designation must be assigned at project intake, not retroactively applied after analysis is complete.
A project is legal-grade if:
the client or project brief states the work may be used in litigation, regulation, or formal proceedings
the work involves a dispute where methodology may be formally challenged
the analysis supports an expert opinion or declaration
Additional Requirements Beyond Standard Workflows
When a project is designated legal-grade, the following additional requirements apply on top of normal firm standards:
1. Enhanced Provenance
all source data must be archived in its original form, not just processed outputs
every processing step must be logged with parameters, tool versions, and timestamps
chain of custody for data files must be documented (who received what, when, from whom)
the provenance record must be sufficient for a third party to reproduce the analysis independently
2. Method Defensibility
every methodological choice must be explicitly documented with a rationale
alternative methods that were considered and rejected must be noted with reasons
assumptions must be stated, not embedded silently in code
where professional judgment was exercised, the basis for the judgment must be recorded
the analysis must use methods consistent with accepted practice in the relevant domain
3. Enhanced QA
structural QA per
standards/STRUCTURAL_QA_STANDARD.md
with zero tolerance for unresolved issues
interpretive review per
standards/INTERPRETIVE_REVIEW_STANDARD.md
at Enhanced rigor level
domain-specific QA per the applicable checklist (hydrology, trend, map, etc.)
all QA results must be documented and archived
a second analyst must independently verify at least the key findings
4. Output Standards
all outputs must include full methodology notes, not abbreviated summaries
maps must include source citations, CRS documentation, and classification rationale
uncertainty and limitations must be stated prominently, not buried in footnotes
the output package must be self-contained: a reviewer should not need access to the firm's internal systems to evaluate the work
5. Review Gates
a principal or senior analyst must review and sign off on the final output
the reviewer must confirm that the methodology is defensible and the conclusions follow from the data
the review must occur before delivery, not after
Inputs
project brief or engagement letter specifying legal-grade requirements
all source data in original form
workflow logs and processing parameters
all QA results
relevant domain standards and guidelines
Method Notes
Legal-grade projects should use the firm's open execution stack to ensure reproducibility. Proprietary-only workflows are harder to defend because the opposing party cannot independently verify them.
When using open-source tools, record the tool version (e.g., WhiteboxTools 2.3.0, GDAL 3.8.4) so the analysis can be reproduced with the same software.
Do not use methods that cannot be explained in plain English to a non-technical audience. Legal-grade work may need to be explained to a judge or jury.
If client instructions conflict with defensible methodology, document the conflict and escalate to a principal. Do not silently follow client instructions that would undermine the analysis.
Keep all intermediate outputs. Do not delete intermediate files that might be needed to demonstrate the analytical chain.
Validation Rules
A legal-grade output should fail this standard if:
the legal-grade designation was not made at project intake
source data was not archived in original form
processing steps are not logged sufficiently for independent reproduction
alternative methods were not documented
QA was conducted at standard rather than enhanced rigor
a principal or senior analyst did not review and sign off
the output package is not self-contained
Human Review Gates
Escalate when:
the legal context is unclear or evolving
client instructions conflict with defensible methodology
a domain method has no established precedent in the relevant legal jurisdiction
the analysis is sensitive to small parameter changes
opposing parties are likely to produce a competing analysis
Common Failure Modes
retroactively designating standard-grade work as legal-grade without re-running with enhanced rigor
assuming that normal firm QA is sufficient for legal contexts
deleting intermediate files or processing logs
failing to record tool versions
using a method that is defensible technically but cannot be explained accessibly
producing a legal-grade watershed or hydrology analysis without consulting the relevant regulatory standards
allowing an agent to produce the final output without enhanced human review
Related Workflows
workflows/WATERSHED_DELINEATION.md
— common legal-grade workflow
workflows/TERRAIN_DERIVATIVES.md
— may support legal-grade hydrology
qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md
— the review checklist for legal-grade outputs
qa-review/HYDROLOGY_OUTPUT_QA.md
— domain-specific QA for hydrology
standards/STRUCTURAL_QA_STANDARD.md
— baseline QA required
standards/INTERPRETIVE_REVIEW_STANDARD.md
— enhanced rigor required
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
— enhanced provenance required
Sources
firm methodology notes for legal-grade projects
Federal Rules of Evidence (Daubert standard for expert testimony, as context)
relevant state and federal regulatory standards for environmental and hydrologic analysis
Trust Level
Production Standard Human Review Required
