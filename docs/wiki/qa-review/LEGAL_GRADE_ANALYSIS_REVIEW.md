# Legal-Grade Analysis Review Checklist

Purpose:
provide a dedicated review checklist for outputs designated as legal-grade per
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
verify that the enhanced provenance, defensibility, and QA requirements are met
serve as the final quality gate before a legal-grade output is delivered
Use When
Use this checklist when reviewing any output where:
the project has been designated legal-grade at intake
the output may be submitted to a court, regulatory body, or government agency
the methodology could be challenged under formal review or cross-examination
the work supports an expert opinion, declaration, or regulatory filing
Do Not Use When
Do not use this checklist for:
standard commercial-grade deliverables (use the normal QA and publishing readiness process)
internal research or exploratory analysis
outputs that will not leave the firm
Core Legal-Grade Checks
Designation Verification
the project was designated legal-grade at intake, not retroactively
the engagement letter or project brief explicitly states the legal or regulatory context
the team understood the legal-grade requirements before analysis began
Enhanced Provenance
all source data is archived in its original, unmodified form
every processing step is logged: tool, version, parameters, timestamp
chain of custody is documented: who received the source data, when, from whom
intermediate outputs are preserved (not deleted after final outputs were produced)
a third party could locate and retrieve every input file from the documentation
Method Defensibility
every methodological choice has a documented rationale
alternative methods that were considered and rejected are noted with reasons
assumptions are explicitly stated in the methodology note, not embedded only in code
professional judgment calls are documented with the basis for the judgment
the methods are consistent with accepted practice in the relevant domain
the methodology note could withstand a challenge from an opposing expert
Independent Verification
a second analyst has independently verified the key findings
the verification is documented: who verified, what they checked, what they confirmed
any discrepancies between the primary and verification analyses are resolved and documented
Output Completeness
the output package is self-contained: a reviewer does not need firm internal systems to evaluate it
the full methodology note is included (not an abbreviated summary)
all source citations are specific (not "Census data" but "ACS 5-Year Estimates, Table B19013, 2018-2022")
uncertainty, limitations, and caveats are stated prominently
maps include full source citations, CRS documentation, and classification rationale
Domain-Specific QA
the applicable domain QA checklist has been completed at enhanced rigor:
hydrology outputs:
qa-review/HYDROLOGY_OUTPUT_QA.md
trend outputs:
qa-review/TREND_OUTPUT_REVIEW.md
ZIP rollup outputs:
qa-review/ZIP_ROLLUP_REVIEW.md
map outputs:
qa-review/MAP_QA_CHECKLIST.md
POI outputs:
qa-review/POI_EXTRACTION_QA.md
all QA results are documented and archived
Sign-Off
a principal or senior analyst has reviewed the final output
the reviewer has confirmed methodology defensibility and conclusion validity
the sign-off is documented with reviewer name and date
the review occurred before delivery, not after
Escalate When
the legal context is ambiguous or has changed since project intake
client instructions conflict with defensible methodology
the analysis is sensitive to parameter choices that are not clearly governed by accepted practice
opposing parties are likely to produce a competing analysis
the relevant regulatory standards are unclear or in dispute
the firm does not have prior experience with the specific legal or regulatory context
Common Failure Modes
retrofitting standard-grade work as legal-grade without re-running with enhanced rigor
assuming normal firm QA is sufficient for legal contexts
deleting intermediate files or processing logs
not recording tool versions (e.g., "used WhiteboxTools" without the version number)
methodology note that is too brief to withstand formal challenge
source citations that are too vague to locate the specific dataset used
single-analyst production with no independent verification
delivering before principal sign-off because of deadline pressure
Relationship to Other QA Pages
standards/LEGAL_GRADE_ANALYSIS_STANDARD.md
— the governing standard this review enforces
qa-review/STRUCTURAL_QA_CHECKLIST.md
— must pass with zero unresolved issues
qa-review/HYDROLOGY_OUTPUT_QA.md
— domain QA for hydrology outputs
standards/INTERPRETIVE_REVIEW_STANDARD.md
— enhanced rigor level required
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
— enhanced provenance required
standards/PUBLISHING_READINESS_STANDARD.md
— all gates must pass
Trust Level
Validated QA Page Human Review Required
