# Review Site Publishing Workflow

Use [Reporting and Delivery Workflow](REPORTING_AND_DELIVERY.md) for report assembly, asset selection, and narrative packaging before entering the publishing stage.

Purpose:
define the firm's end-to-end process for building, validating, and publishing a review site or client-facing web dashboard
ensure that published outputs have passed all required QA gates before reaching the client
make review-site production repeatable across projects
Typical Use Cases
client review site for a market analysis project
interactive dashboard presenting demographic, POI, or trend outputs
internal review site for team QA before final client delivery
public-facing data explorer or story map
Inputs
approved analysis outputs (tables, layers, maps, charts)
project brief and approved scope
client delivery requirements (format, platform, branding)
QA results from all applicable checklists
methodology note and provenance metadata per
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
Preconditions
all analysis outputs have passed
qa-review/STRUCTURAL_QA_CHECKLIST.md
interpretive review has been completed per
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
domain-specific reviews have been completed where applicable:
qa-review/ZIP_ROLLUP_REVIEW.md
for ZIP-aggregated data
qa-review/TREND_OUTPUT_REVIEW.md
for trend data
qa-review/MAP_QA_CHECKLIST.md
for map outputs
qa-review/POI_EXTRACTION_QA.md
for POI outputs
the team has confirmed the review-site platform and hosting approach
the methodology note is complete
Preferred Tools
static site generators or review-site frameworks approved by the firm
QGIS for preparing map tiles or static map exports
GeoPandas for data preparation and export to web-friendly formats (GeoJSON, CSV)
Mapbox, Leaflet, or similar open mapping libraries for interactive maps
firm-approved hosting (internal server, cloud storage, or client-provided platform)
Execution Order
Phase 1: Content Assembly
Confirm the approved output inventory: which tables, maps, charts, and narrative sections will appear on the review site.
Prepare data for web consumption:
export layers to GeoJSON, CSV, or tile format as needed
simplify geometry if needed for web performance (document the simplification tolerance)
remove internal-only fields, debug columns, and sensitive data
Prepare map outputs:
finalize classification, color scales, and legends per
qa-review/MAP_QA_CHECKLIST.md
export static maps or configure interactive map layers
Prepare narrative content:
finalize text per
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
ensure all claims match the final data
Prepare the methodology note for inclusion or reference.
Phase 2: Site Build
Build the review site using the approved framework or template.
Place each output in the correct section of the site.
Confirm that interactive elements (filters, tooltips, zoom) work correctly.
Add source citations, vintage notes, and attribution (especially OSM ODbL where required).
Add the methodology note or a link to it.
Phase 3: Pre-Publish Validation
Run through the publishing readiness gates in
standards/PUBLISHING_READINESS_STANDARD.md
.
Check all links, downloads, and interactive features.
Check that the site displays correctly on the expected devices and browsers.
Have a human who was not the primary analyst review the site end-to-end.
Confirm that no internal-only or draft content is visible.
Confirm that file sizes are reasonable for web delivery.
Phase 4: Publication
Publish to the approved hosting environment.
Confirm the published URL is accessible to the intended audience.
Send the site link to the client or stakeholder with a brief cover note.
Archive the site source, data, and methodology note in the project folder.
Validation Checks
every data element on the site traces back to an approved, QA-passed output
source citations and vintages are present on every page or section
interactive features work and do not expose raw or internal data
the methodology note is accessible from the site
attribution requirements (OSM, Census, etc.) are met
the site does not contain draft watermarks, debug data, or placeholder content
the site displays correctly on the devices the client will use
Common Failure Modes
publishing before interpretive review is complete
leaving draft labels or placeholder text in the published site
exposing internal field names in tooltips or pop-ups
omitting source citations or vintage notes
publishing a map with a classification scheme that was not reviewed
not testing the site on mobile or tablet if the client will use those devices
archiving the site URL but not the site source or data, making future updates difficult
Escalate When
the client has specific accessibility requirements (WCAG, Section 508)
the review site will be shared beyond the direct client (public, regulatory, media)
the analysis contains sensitive findings that require controlled distribution
the platform or hosting environment is new to the firm
a human review of the final site has not occurred
Outputs
published review site at a confirmed URL
archived site source and data package
methodology note or link
cover note to the client
Related Standards
standards/PUBLISHING_READINESS_STANDARD.md
standards/PROVENANCE_AND_HANDOFF_STANDARD.md
standards/OPEN_EXECUTION_STACK_STANDARD.md
qa-review/STRUCTURAL_QA_CHECKLIST.md
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
qa-review/MAP_QA_CHECKLIST.md
Sources
firm review-site production notes
Leaflet documentation (https://leafletjs.com)
Mapbox documentation (https://docs.mapbox.com)
Trust Level
Draft Workflow Needs Testing
