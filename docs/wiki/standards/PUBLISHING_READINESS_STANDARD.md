# Publishing Readiness Standard

This standard governs the publication gate. Use [Validation and QA Stage Workflow](../workflows/VALIDATION_AND_QA_STAGE.md) for the validation-stage sequence and [Reporting and Delivery Workflow](../workflows/REPORTING_AND_DELIVERY.md) for report assembly before publishing.

Purpose:
define when an analysis output is ready for client delivery or public-facing publication
prevent premature delivery of incomplete, unreviewed, or under-documented work
separate internal working outputs from client-grade deliverables
Use When
Use this standard before:
publishing to a review site or client-facing dashboard
delivering a data package, map set, or report to a client
releasing any output beyond the internal project team
Do Not Use When
Do not use this standard for internal scratch outputs, work-in-progress snapshots shared within the project team, or research-note drafts.
Approved Rule
An output is publishing-ready only when all of the following gates have been passed:
Gate 1: Structural QA
output has passed
qa-review/STRUCTURAL_QA_CHECKLIST.md
geometry is valid and CRS is documented
row counts, field presence, and null handling are confirmed
all required files exist
Gate 2: Methodology Documentation
output has provenance metadata per
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
methodology note exists in plain English
data sources are identified with vintages
known limitations are stated
aggregation methods are documented where applicable per
standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md
Gate 3: Interpretive Review
output has passed
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
narrative claims match the underlying data
framing follows applicable standards (trend, demographic shift, etc.)
no overclaiming
Gate 4: Domain-Specific Review
if output includes ZIP-aggregated data:
qa-review/ZIP_ROLLUP_REVIEW.md
has passed
if output includes trend claims:
qa-review/TREND_OUTPUT_REVIEW.md
has passed
if output includes maps:
qa-review/MAP_QA_CHECKLIST.md
has passed
if output includes POI data:
qa-review/POI_EXTRACTION_QA.md
has passed
Gate 5: Delivery Format
output is in the approved delivery format (GeoPackage, shapefile, PDF, web map, review site, etc.)
file names follow project or firm naming conventions
all required supplementary files are included (legends, data dictionaries, README)
sensitive or internal-only fields have been removed
licensing and attribution requirements are met (especially for OSM-derived data)
Gate 6: Human Sign-Off
a human has reviewed the final package before it reaches the client
agent-produced outputs have had at least one human review pass
the reviewer has confirmed that the output answers the question the client asked
Inputs
the output package to be evaluated
the QA results from each applicable checklist
the project brief (to confirm scope alignment)
Method Notes
Publishing readiness is a checklist, not a judgment call. If a gate has not been passed, the output is not ready.
For time-pressured deliveries, document which gates were deferred and why. Do not silently skip them.
Review-site publications and client-facing dashboards require the same rigor as static deliverables.
If a gate is not applicable (e.g., no maps in the deliverable), note that it was reviewed and deemed not applicable rather than leaving it blank.
Validation Rules
An output should fail publishing readiness if:
any required QA checklist has not been completed
the methodology note is missing or incomplete
no human has reviewed the final output
delivery format requirements have not been confirmed
attribution or licensing obligations have not been checked
Human Review Gates
Escalate when:
the client has legal or regulatory requirements for the deliverable
the output involves politically or commercially sensitive findings
the methodology note contains material caveats that the client should be explicitly warned about
the delivery is the first of its kind for the firm (new format, new platform, new client type)
Common Failure Modes
delivering before interpretive review because structural QA passed
treating agent-generated outputs as client-ready without human review
omitting the methodology note from the delivery package
leaving internal field names or debug columns in the client output
publishing OSM-derived data without ODbL attribution
delivering a map without checking classification, legend, and title accuracy
assuming that passing structural QA means the output is publishable
Related Workflows
workflows/REVIEW_SITE_PUBLISHING.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
qa-review/MAP_QA_CHECKLIST.md
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
Sources
firm delivery methodology notes
firm project review processes
Trust Level
Production Standard
