# Socrata Open Data Source Page

Source Summary:
Socrata powers thousands of open data portals for cities, counties, states, and federal agencies. The generic Socrata client (`fetch_socrata.py`) can query any of these portals using the same SODA API interface.

Owner / Publisher:
Various — Tyler Technologies (Socrata platform), used by 2000+ government agencies

Geography Support:
Varies by dataset. Many datasets include lat/lon point columns or are joinable to geographic identifiers.

Time Coverage:
Varies by dataset. Some are real-time, others are historical archives.

Access Method:
SODA (Socrata Open Data API) — consistent JSON/CSV API across all portals. Use `fetch_socrata.py` for retrieval from any Socrata portal.

Fetch Script:
`scripts/core/fetch_socrata.py`

Example:
```bash
# Chicago crime data
python scripts/core/fetch_socrata.py --domain data.cityofchicago.org \
    --dataset ijzp-q8t2 --where "year=2023" --limit 10000 \
    -o data/raw/chicago_crimes_2023.csv

# NYC 311 complaints
python scripts/core/fetch_socrata.py --domain data.cityofnewyork.us \
    --dataset erm2-nwe9 --where "created_date>'2023-01-01'" \
    --select "created_date,complaint_type,borough,latitude,longitude" \
    --limit 50000 -o data/raw/nyc_311_2023.csv

# CDC PLACES (also Socrata-powered)
python scripts/core/fetch_socrata.py --domain data.cdc.gov \
    --dataset swc5-untb --where "stateabbr='NE'" --limit 5000 \
    -o data/raw/ne_cdc_places.csv
```

Credentials:
Optional app token (SOCRATA_APP_TOKEN in .env). Works without it but may be rate-limited for large queries.

Licensing / Usage Notes:
Varies by portal and dataset. Most government datasets are public domain. Check the dataset metadata page on the portal.

Known Caveats:
- Dataset identifiers are 4-character codes (e.g., ijzp-q8t2) — find them on the portal website
- SoQL query language is similar to SQL but not identical — see Socrata docs for syntax
- Some portals throttle unauthenticated requests
- Data quality varies widely across portals — always inspect before analysis
- Large datasets may require pagination ($offset parameter)

Common Portal Domains:
- `data.cityofchicago.org` — Chicago
- `data.cityofnewyork.us` — New York City
- `data.lacity.org` — Los Angeles
- `data.sfgov.org` — San Francisco
- `data.cdc.gov` — CDC
- `data.cms.gov` — CMS Medicare/Medicaid
- `data.ny.gov` — New York State
- `data.texas.gov` — Texas
- `data.illinois.gov` — Illinois
- `datahub.transportation.gov` — U.S. DOT

Discovering Datasets:
- Browse the portal's catalog page (e.g., https://data.cityofchicago.org/browse)
- Use the Socrata Discovery API: `https://api.us.socrata.com/api/catalog/v1?q=your+search+terms`
- Look for the 4-character dataset ID in the URL when viewing a dataset on the portal

Best-Fit Workflows:
- Any domain where the relevant data lives on a Socrata portal
- domains/CRIME.md (city crime portals)
- domains/PARKS.md (city parks/recreation portals)
- domains/EMS.md (city 911/dispatch portals)

Alternatives:
- Direct API access to the source agency (if they have their own API)
- ArcGIS Hub/Open Data portals (similar concept, different platform)
- CKAN-powered portals (data.gov, some international portals)

Sources:
- https://dev.socrata.com/ (developer docs)
- https://dev.socrata.com/docs/queries/ (SoQL query reference)
- Portal discovery: https://www.opendatanetwork.com/

Trust Level:
Varies — the platform is reliable, but data quality depends on the publishing agency.
