# LEHD / LODES Source Page

Source Summary:
The Longitudinal Employer-Household Dynamics (LEHD) program produces the LODES (LEHD Origin-Destination Employment Statistics) dataset, which provides workplace and residential employment counts at the Census block level.
LODES is the primary public-domain source for understanding where workers live, where they work, and the spatial relationship between the two.
The dataset is derived from administrative records (unemployment insurance wage records and QCEW) linked with Census data, not from survey responses.

Owner / Publisher:
U.S. Census Bureau, Center for Economic Studies

Geography Support:
block-level: origin (residence) and destination (workplace) at Census block geography
state-level files: each state publishes its own LODES dataset; cross-state commute patterns require merging files from multiple states
aggregation: block-level data can be aggregated to tract, county, ZCTA, or custom study-area geographies using standard spatial joins
coverage: all 50 states plus DC and Puerto Rico, though availability year varies by state
federal employment is included in a separate file (federal jobs are not in the main state files)

Time Coverage:
annual releases, typically 2002 through the most recent available year (usually 2-3 years behind current)
vintage matters: LODES data is tied to a specific Census block geography vintage (2010 or 2020 blocks depending on the release)
the geographic crosswalk between 2010 and 2020 block vintages requires a LODES-provided crosswalk file or manual reblocking

Access Method:
bulk download from the LEHD website: https://lehd.ces.census.gov/data/
OnTheMap web application for visual exploration: https://onthemap.ces.census.gov/
direct HTTPS download by state, year, and file type
Fetch Script:
`scripts/core/fetch_lehd_lodes.py` — download WAC/RAC/OD CSV by state and year
file naming convention: `[state]_[filetype]_[segment]_[jobtype]_[year].csv.gz`

File Formats:
gzipped CSV files
no geometry included — block-level FIPS codes must be joined to Census block or tract geometry from TIGER

Key File Types:
- **OD (Origin-Destination):** pairs of residence block and workplace block with job counts — the core commute-flow file
- **RAC (Residence Area Characteristics):** job counts by worker residence block, broken out by age, earnings, industry (NAICS 2-digit)
- **WAC (Workplace Area Characteristics):** job counts by workplace block, broken out by age, earnings, industry (NAICS 2-digit)

Job Type Segments:
- JT00: all jobs
- JT01: primary jobs
- JT02: all private jobs
- JT03: primary private jobs
- JT04: all federal jobs
- JT05: primary federal jobs

Workforce Segments:
- S000: total count
- SA01: age 29 or younger
- SA02: age 30 to 54
- SA03: age 55 or older
- SE01: earning $1,250/month or less
- SE02: earning $1,251 to $3,333/month
- SE03: earning more than $3,333/month
- SI01: goods-producing industry
- SI02: trade, transportation, and utilities
- SI03: all other services

Licensing / Usage Notes:
public federal data
no usage restrictions
LEHD applies some noise infusion for confidentiality protection — small-cell counts at the block level are not exact

Known Caveats:
LODES is synthetic in part — the Census Bureau applies noise infusion and data swapping to protect employer and worker confidentiality; block-level counts are approximate
small-area estimates (individual blocks) should be treated as noisy; aggregation to tract or larger geography improves reliability
the OD file can be very large (tens of millions of rows per state); filter by geography or aggregate early in the pipeline
cross-state commuting requires merging multiple state OD files — a worker living in Kansas but commuting to Missouri appears in the Missouri OD file, not the Kansas file
LODES covers wage-and-salary employment; it does not cover self-employment, military, or most agricultural work
industry categories are broad (NAICS 2-digit sectors); occupation-level detail is not available
the geographic vintage (2010 vs 2020 blocks) matters for joins — confirm which vintage the LODES release uses before joining to TIGER geometry
federal employment is in a separate file and is sometimes excluded from state-level analyses by accident

Best-Fit Workflows:
workflows/TRACT_JOIN_AND_ENRICHMENT.md (after aggregating blocks to tracts)
workflows/ACS_DEMOGRAPHIC_INVENTORY.md (as a complement to ACS employment variables)
workflows/SERVICE_AREA_ANALYSIS.md (for labor-shed delineation)
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md (for commute-flow packaging)

Best-Fit Domains:
domains/WORKFORCE_AND_LABOR_SHED_ANALYSIS.md
domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md
domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md
domains/TRANSIT_ACCESS_AND_COVERAGE.md

Alternatives:
ACS commute variables (B08301, B08302, B08303): survey-based, tract-level, covers mode and travel time but not origin-destination pairs
ACS workplace geography tables (B08601, B08602): limited workplace geography detail
County-to-county commute flows from ACS: broader geography, less spatial precision than block-level LODES
proprietary sources (SafeGraph, Replica, StreetLight): mobile-device-derived commute data with higher temporal resolution but licensing and cost constraints

Sources:
https://lehd.ces.census.gov/data/
https://lehd.ces.census.gov/doc/technical/
https://onthemap.ces.census.gov/
LODES Technical Documentation: https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.0.pdf

Trust Level:
Validated Source Page
