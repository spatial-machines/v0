# ACS Demographic Inventory Workflow

Purpose:
produce a defendable demographic inventory and first-wave retrieval plan for a market-analysis project
Typical Use Cases
market analysis kickoff
client data inventory memo
tract-level demographic foundation for later ZIP-oriented delivery
Inputs
project brief
approved geography scope
approved variable package or draft package
relevant source pages and standards
Preconditions
project scope has been decomposed into current snapshot, trend-ready, and unresolved lanes
the team has identified whether the final delivery is tract, ZIP, or another geography
Preferred Tools
internal ACS retrieval scripts
TIGER geometry retrieval
GeoPandas or PostGIS for joins and shaping
Execution Order
Read the project brief.
Read the trend-analysis standard.
Read the ZIP / ZCTA aggregation standard if delivery is ZIP-oriented.
Confirm the first-wave variable package.
Classify variables as:
current snapshot only
10-year trend-ready
selective extended-history
Confirm source families and likely year coverage.
Produce a spreadsheet-style inventory.
Produce a short methodology note or client memo.
Validation Checks
every variable has a source family
every variable has a geography assumption
trend claims are bounded
unresolved lanes are labeled clearly
Common Failure Modes
turning the inventory into a full analysis
overpromising 20-year comparability
treating ZIP as the native source geography when tract is the real working level
Escalate When
crime is being promoted beyond provisional status
non-additive metrics are being promised at ZIP level without a method
the first-wave package expands materially
Outputs
client-ready inventory table
methodology memo
first-wave retrieval plan
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/TREND_ANALYSIS_STANDARD.md
standards/ZIP_ZCTA_AGGREGATION_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md
— general analysis conventions this workflow specializes for first-wave demographic inventory at project intake
data-sources/CENSUS_ACS.md
data-sources/TIGER_GEOMETRY.md
Sources
Census ACS documentation
firm LA planning docs
Trust Level
Validated Workflow Needs Testing
