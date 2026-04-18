# BLS Employment Data Source Page

Source Summary:
The Bureau of Labor Statistics provides employment, unemployment, wages, and labor force time series data at national, state, metro, and county levels. Key source for economic analysis and workforce studies.

Owner / Publisher:
U.S. Department of Labor, Bureau of Labor Statistics (BLS)

Geography Support:
National, state, metro area (MSA), county

Time Coverage:
Monthly data available for most series. Historical data varies by series — LAUS (Local Area Unemployment Statistics) available from 1990+.

Access Method:
REST API (POST with JSON body). Use `fetch_bls_employment.py` for retrieval.

Fetch Script:
`scripts/core/fetch_bls_employment.py`

Example:
```bash
# State unemployment rate (series pattern: LAUST{FIPS}0000000000003)
python scripts/core/fetch_bls_employment.py \
    --series LAUST200000000000003,LAUST200000000000004 \
    --start-year 2019 --end-year 2023 -o data/raw/ks_employment.csv

# County unemployment rate (series pattern: LAUCN{FIPS}0000000003)
python scripts/core/fetch_bls_employment.py \
    --series LAUCN201730000000003 --start-year 2020 --end-year 2023 \
    -o data/raw/sedgwick_unemployment.csv
```

Credentials:
Optional BLS API key (BLS_API_KEY in .env). Without a key, limited to 25 requests/day and 10 years of data. Free registration at https://data.bls.gov/registrationEngine/

Licensing / Usage Notes:
Public federal data.

Known Caveats:
- Series IDs encode geography and measure type — must be constructed correctly
- LAUS data is model-based for small areas — not direct employer surveys
- Monthly data is seasonally adjusted for some series, not adjusted for others
- County-level data may have large revisions in annual benchmark updates

Key Series Patterns:
- `LAUST{state_fips}0000000000003` — State unemployment rate
- `LAUST{state_fips}0000000000004` — State unemployment count
- `LAUST{state_fips}0000000000005` — State employment count
- `LAUST{state_fips}0000000000006` — State labor force count
- `LAUCN{county_fips}0000000003` — County unemployment rate

Best-Fit Workflows:
- domains/WORKFORCE.md
- domains/DEMOGRAPHIC_ANALYSIS.md
- workflows/DECADE_TREND_ANALYSIS.md

Alternatives:
- LEHD/LODES (block-level, employer-based, 2-3 year lag)
- ACS employment tables (estimate-based, 1-year lag)

Sources:
- https://www.bls.gov/data/
- API: https://www.bls.gov/developers/
- Series finder: https://data.bls.gov/cgi-bin/srgate

Trust Level:
High — BLS is the authoritative source for U.S. labor market statistics.
