# Census / ACS Source Page

Source Summary:
U.S. Census Bureau data products, especially ACS 5-year Detailed Tables, are the firm's default source family for many demographic and socioeconomic workflows.
Owner / Publisher:
U.S. Census Bureau
Geography Support:
national to small-area geographies, including tract, block group, county, place, and many ZCTA-supported tables
Time Coverage:
ACS 5-year releases from 2009 onward
decennial anchors for 2000, 2010, and 2020 where relevant
Access Method:
Census API (recommended; an API key is recommended for any non-trivial use)
downloadable tables and supporting documentation
Fetch Scripts:
`scripts/core/fetch_acs_data.py` — ACS 5-year tables (B/S/DP) by tract/county
`scripts/core/fetch_census_population.py` — Decennial population counts
Credentials:
Census API key is recommended for tabular API access; without a key, the API is rate-limited and may reject requests
the firm convention is to store the key in the environment variable
CENSUS_API_KEY
never hardcode the key in retrieval scripts or commit it to the repo
Licensing / Usage Notes:
public federal data
Known Caveats:
ACS is estimate-based, not a full count
margins of error matter
rolling estimates complicate long-run comparison
not every table is equally suitable for trend work
Best-Fit Workflows:
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
workflows/DECADE_TREND_ANALYSIS.md
workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
Alternatives:
decennial Census for anchor metrics
Living Atlas as discovery/reference layer only
Sources:
https://www.census.gov/data/developers/data-sets/acs-5year.html
https://api.census.gov/data/2024/acs/acs5.html
Trust Level:
Production Source Page
