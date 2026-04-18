# Source Readiness Standard

Purpose:
classify data sources by their readiness for firm workflows
prevent analysts and agents from treating every available dataset as production-ready
make source selection decisions explicit and reviewable
Use When
Use this standard when:
selecting or evaluating a data source for a new project
onboarding a client-supplied dataset
deciding whether a source is suitable for trend, enrichment, or delivery work
an agent is choosing between competing sources
Do Not Use When
Do not use this standard to reject sources outright. A source can be useful even if it is not production-ready, provided the limitations are documented.
Approved Rule
Every data source used in a project must be assigned a readiness tier before it enters analysis.
Tier 1: Production-Ready
The source is:
published by a known, authoritative provider
documented with metadata, geography, and time coverage
stable across releases
tested in at least one prior firm project
supported by a wiki data-source page
Examples:
ACS 5-year Detailed Tables
TIGER / Line shapefiles
firm local PostGIS / OSM extract
Tier 2: Validated but Caveated
The source is:
published and documented
usable for analysis with known limitations
not yet tested on a firm project, or has material caveats
Examples:
a new ACS table the firm has not used before
agency-published crime data with known reporting gaps
Living Atlas layers traced back to a known provider
Tier 3: Provisional
The source is:
available but not fully documented
potentially useful for context or screening
not suitable for client-facing analysis without human review
Examples:
client-supplied spreadsheets with no metadata
third-party scraped datasets
unverified open-data portals
Tier 4: Unreviewed
The source has not been evaluated. Do not use in production outputs without first promoting it to Tier 3 or higher.
Inputs
source name and provider
access method
geography and time coverage
any prior firm use
any known caveats
Method Notes
Assign the tier at project intake, not after analysis is complete.
Document the tier assignment in the project data inventory.
If a Tier 3 or Tier 4 source is the only option, note this in the methodology memo.
Tier assignment can be promoted after testing on a real project.
Agent workflows should check source readiness before beginning retrieval.
Validation Rules
A source assignment should fail validation if:
no tier is assigned
a Tier 3 or 4 source is used in client-facing outputs without a caveat note
the tier is assigned without checking the source's metadata or documentation
a source is promoted from Tier 4 to Tier 1 without intermediate testing
Human Review Gates
Escalate when:
a project relies on a Tier 3 source for a material finding
a client-supplied dataset has no metadata
two competing sources give materially different answers
an agent selects a source the firm has not used before
Common Failure Modes
treating all available data as equally trustworthy
skipping tier assignment during project intake
using a Tier 4 source in production because it was convenient
promoting a source to Tier 1 based on one successful use without documenting the decision
confusing data availability with data quality
Related Workflows
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/POSTGIS_POI_LANDSCAPE.md
Sources
U.S. Census Bureau data documentation
TIGER / Line documentation
firm project methodology notes
Trust Level
Production Standard
