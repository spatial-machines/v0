# GIS Firm Wiki Architecture

Purpose:
create a reusable GIS operating system for the firm
reduce siloed specialist knowledge
give agents and humans a shared methodology layer
separate project-specific instructions from reusable workflow standards
This wiki is not a random collection of notes. It should function as:
a methods library
a workflow directory
a standards manual
a QA and escalation handbook
a training system for both humans and agents
Core Design Principles
Workflow first, tool second
Tool docs explain what a tool can do. The wiki should explain:
when to use it
in what order
with which prerequisites
how to validate the result
when to stop and ask questions
Separate universal standards from project decisions
Do not bury reusable methods inside one client folder. Put reusable logic in shared standards and playbooks.
Capture trust explicitly
Every page should make clear whether it is:
production standard
validated playbook
draft workflow
research note
Prefer repeatable procedures over prose essays
The wiki should be usable by:
humans under time pressure
agents with bounded context
reviewers checking whether work followed the standard
Build from recurring firm work
Do not attempt to document all of GIS at once. Prioritize the workflows that repeatedly matter to the firm.
Open execution by default
The firm's operational stack should prefer open, scriptable, portable tooling. Use proprietary platforms as delivery surfaces, reference sources, or optional adapters, not as hidden runtime dependencies.
Top-Level Structure
Recommended top-level sections:
1.
standards/
Firm-wide rules and methodological standards.
Use for:
open execution stack
ZIP / ZCTA aggregation
trend analysis
demographic shift framing
CRS selection
QA thresholds
provenance and handoff requirements
source readiness tiers
These pages answer:
what is the approved rule?
what is forbidden?
what needs human review?
2.
workflows/
Step-by-step operational playbooks.
Use for:
ACS demographic inventory
tract-to-ZIP rollup
decade trend analysis
POI retrieval and mapping
watershed delineation
geocode + buffer + enrichment
site suitability analysis
service area analysis
These pages answer:
how is this workflow executed end to end?
which tools are preferred?
how do we check our work?
3.
domains/
Domain-specific analytic logic.
Use for:
demographics and market analysis
hydrology and terrain
retail and POI analysis
environmental screening
transportation and accessibility
crime and public safety
land use and parcel analysis
These pages answer:
what kinds of questions do we answer in this domain?
which workflows are common?
which caveats are domain-specific?
4.
data-sources/
Source family documentation.
Use for:
Census / ACS
TIGER / Census geometry
Living Atlas
local PostGIS
OSM
client-provided DEMs
USGS elevation
agency crime data
These pages answer:
what does this source contain?
what geographies and years does it support?
what are the caveats?
which workflows depend on it?
5.
toolkits/
Operational tool references grouped by workflow use, not just software name.
Use for:
internal scripts
QGIS processing families
GDAL / OGR
PostGIS
GeoPandas
WhiteboxTools
ArcGIS / Business Analyst / Network Analyst as reference or delivery surfaces
These pages answer:
when is this toolkit the preferred engine?
what are the core commands or algorithms?
what workflows rely on it?
6.
qa-review/
Validation, review, and escalation pages.
Use for:
structural QA checklists
interpretive review checklists
map QA
legal-grade analysis review
client-delivery readiness checks
These pages answer:
what needs to be checked?
what is a failure?
when must the workflow escalate to a human?
7.
project-templates/
Reusable scaffolds for client work.
Use for:
market analysis kickoff
data inventory memo
methodology note
review-site publication template
QGIS handoff template
These pages answer:
how do we start a new project cleanly?
what should each project folder include?
8.
research-notes/
Temporary or exploratory pages not yet promoted.
Use for:
newly discovered workflows
source comparisons
unresolved methodology questions
notes extracted from manuals that are not yet standardized
These pages are intentionally lower trust and should not be silently treated as production truth.
Standards vs Workflows vs Projects
This distinction should be strict:
standard
: reusable rule or policy
workflow
: reusable sequence of steps
project doc
: client-specific decisions and scope
Examples:
"How to aggregate tract counts to ZIP / ZCTA" -> standard
"How to produce a 10-year ACS demographic inventory" -> workflow
"How we are handling LA County ZIP delivery for this client" -> project doc
Page Template Types
Standard Page Template
Required sections:
Purpose
Use When
Do Not Use When
Approved Rule
Inputs
Method Notes
Validation Rules
Human Review Gates
Common Failure Modes
Related Workflows
Sources
Trust Level
Workflow Page Template
Required sections:
Purpose
Typical Use Cases
Inputs
Preconditions
Preferred Tools
Execution Order
Validation Checks
Common Failure Modes
Escalate When
Outputs
Related Standards
Sources
Trust Level
Data Source Page Template
Required sections:
Source Summary
Owner / Publisher
Geography Support
Time Coverage
Access Method
Licensing / Usage Notes
Known Caveats
Best-Fit Workflows
Alternatives
Sources
Trust Level
Toolkit Page Template
Required sections:
Toolkit Summary
Best Uses
Avoid For
Core Operations
Workflow Fit
Validation Expectations
Related Workflows
Sources
Trust Level
Trust Levels
Every page should carry one of these:
Production Standard
Validated Workflow
Draft Workflow
Research Note
Archived
Optional additional flags:
Needs Testing
Needs Source Validation
Human Review Required
Workflow Families To Seed First
These are the highest-value initial workflow families based on common GIS ecosystems and your actual work.
Demographics and Market Analysis
ACS demographic inventory
tract / block-group retrieval and joins
tract-to-ZIP / ZCTA aggregation
decade trend analysis
demographic shift analysis
market ranking and peer geography comparison
trade area and penetration analysis
POI and Business Landscape
POI retrieval from PostGIS / OSM
category standardization
competitor landscape mapping
density and clustering
trade-area context enrichment
Hydrology and Terrain
DEM preparation
pour-point validation
flow direction and accumulation
watershed delineation
slope and aspect derivation
terrain QA for legal-grade analysis
Accessibility and Network Analysis
geocoding and point QA
service area analysis
route and drive-time analysis
within-distance enrichment
Cartography and Delivery
choropleth design
bivariate mapping
review-site publication
QGIS package handoff
client-ready memo and reporting
Data Engineering and QA
source inventory
schema normalization
CRS handling
geometry validation
handoff validation
publish validation
Cross-Cutting Standards
These should become the firm's reusable rules:
open execution stack standard
CRS and projection standard
count vs rate vs median aggregation standard
tract-to-ZIP / ZCTA aggregation standard
decade trend analysis standard
demographic shift framing standard
source readiness standard
structural QA standard
interpretive review standard
legal-grade analysis review standard
publishing readiness standard
Relationship To Agents
Agents should use the wiki in this order:
read the project brief
read the relevant standards
read the workflow playbook
execute using approved tools
validate against QA pages
escalate when a review gate is triggered
They should not jump straight from project brief to execution.
Relationship To Tools
The wiki should map workflows to tool families, for example:
Census demographic retrieval -> internal scripts + Census source pages
tract joins -> GeoPandas / QGIS / PostGIS
ZIP rollups -> tract-to-ZIP standard + aggregation workflow
watershed -> WhiteboxTools / GDAL / QGIS terrain tools
POI landscape -> PostGIS / OSM workflows
Preferred operational stack:
Python
GeoPandas
Shapely
Rasterio
GDAL / OGR
PostGIS
PyProj
WhiteboxTools
QGIS-compatible Python workflows
Esri products may still appear in:
source discovery
client delivery environments
comparative methodology references
But the wiki should avoid making ArcPy or other proprietary execution paths the default operational dependency.
This keeps the system workflow-led rather than software-led.
Dedupe Rules
When two pages overlap:
keep one as the canonical page
convert the other into a short reference or archive note
Do not let the same method live in five places.
Promotion Path
New knowledge should move through:
research-notes/
draft workflow
validated workflow
production standard
if it becomes firm-wide policy
This is how the wiki stays alive without becoming chaotic.
Minimum Viable Wiki
A strong first version does not need hundreds of pages. It needs:
8 to 12 standards
10 to 15 workflows
8 to 12 data source pages
5 to 10 QA / review pages
a consistent template system
That is enough to become the firm's operating system.
