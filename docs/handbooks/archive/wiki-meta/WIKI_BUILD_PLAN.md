# GIS Firm Wiki Build Plan

Purpose:
fill out the wiki rapidly without creating a contradictory mess
use multiple models efficiently
keep high-trust pages separated from rough notes
Build Strategy
Use a three-lane production system:
Lane 1: Architecture and Editorial Control
Owned by you plus the strongest model.
Responsibilities:
define page templates
define taxonomy
decide canonical page names
resolve conflicts
promote pages to higher trust levels
Lane 2: Research Extraction
Can be delegated to smaller models.
Responsibilities:
read official manuals and documentation
extract workflow patterns
extract source coverage facts
list failure modes and validation ideas
draft pages into
research-notes/
Lane 3: Standardization and Compression
Owned by a stronger model or human reviewer.
Responsibilities:
merge duplicates
remove tool-specific noise
convert notes into standardized pages
map workflows to standards and review gates
Rapid-Fill Plan
Sprint 1: Firm Core
Goal:
build the core pages that support real work this week
Pages:
tract-to-ZIP / ZCTA aggregation standard
decade trend analysis standard
demographic shift framing standard
ACS demographic inventory workflow
tract join and enrichment workflow
review-site publishing workflow
structural QA checklist
interpretive review checklist
Outcome:
enough shared logic to support demographic projects without improvising each time
Sprint 2: Near-Term Production Families
Goal:
cover the next common workflows
Pages:
POI retrieval from PostGIS
POI category normalization
service area / within-distance enrichment
watershed delineation workflow
terrain derivative workflow
geocoding workflow
Outcome:
enough workflow coverage for your current queue of projects
Sprint 3: Infrastructure and Source Pages
Goal:
make the wiki navigable and trustworthy
Pages:
Census / ACS source page
TIGER source page
ZCTA / ZIP note
local PostGIS source page
OSM source page
client-supplied DEM handling note
QA and trust-level policy
Outcome:
less source confusion, better traceability
Sprint 4: Hardening and Dedupe
Goal:
compress overlaps and promote tested pages
Tasks:
merge duplicate ideas
archive low-value notes
add cross-links
mark trust levels
add example outputs and review gates
Outcome:
a usable internal wiki instead of a pile of drafts
Page Production Workflow
For each new page:
Identify the workflow family.
Gather primary sources first.
Draft a
research-notes/
page.
Extract the reusable method.
Convert it to a standard or workflow page.
Add validation rules.
Add escalation rules.
Link to related standards and sources.
Assign trust level.
Test it on a real project before promoting.
Model Delegation Strategy
Use stronger models for:
taxonomy design
standard pages
conflict resolution
dedupe
methodology language
Use smaller models for:
extracting tool families from official docs
drafting source pages
generating first-pass workflow outlines
converting one source into a page template
Do not let multiple models write to the same canonical page at once.
Token Discipline
To avoid credit burn:
Batch research by workflow family.
Do not ask a model to "research all GIS."
Limit each extraction run to:
one workflow family
one source family
one page type
Use small models to draft.
Use stronger models only to normalize and promote.
Avoid live agent runs during wiki drafting.
Build standards locally first.
Let real client work validate pages.
Do not keep inventing synthetic tests.
Dedupe and Conflict Resolution
When multiple pages disagree:
Find the highest-trust source.
Convert conflicting claims into explicit notes.
Make one page canonical.
Add archive or redirect notes to the rest.
Never leave unresolved contradictions in production-standard pages.
Source Hierarchy
Preferred order:
Official product manuals and documentation
Official tutorials and training manuals
Agency or data-provider methodology docs
Mature open-source project docs
University / lab manuals
High-quality blogs or forums only as secondary support
Research Clustering
When mining workflows from sources, cluster them into:
data acquisition
data engineering
vector analysis
raster / surface analysis
hydrology
network / accessibility
demographics / market analysis
POI / business analysis
cartography / publication
QA / validation
automation / modeling
That lets you fill the wiki systematically instead of randomly.
Promotion Criteria
Promote a page to
Validated Workflow
when:
it has primary-source backing
it has a clear execution order
it has validation checks
it has been used or reviewed against a real task
Promote a page to
Production Standard
when:
it applies across projects
it defines a firm rule
it has survived at least one real project without causing confusion
What To Build First
Build the pages that have the highest combination of:
high reuse
high methodological risk
high token waste when undefined
That means:
ZIP / ZCTA aggregation
trend analysis
demographic shift framing
ACS / Census demographic retrieval
tract joins and enrichment
POI retrieval from PostGIS
watershed delineation QA
Expected Timeline
Strong first operating wiki:
2 to 4 weeks
Serious internal firm wiki:
2 to 3 months
Public-grade knowledge base:
6 months or more
The wiki should be built from real project pressure, not pure theory.
