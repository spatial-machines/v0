# HUD Housing Data Source Page

Source Summary:
HUD provides housing affordability data including Fair Market Rents (FMR), Income Limits, and Comprehensive Housing Affordability Strategy (CHAS) data. These datasets are essential for housing burden analysis, affordability studies, and equity work.

Owner / Publisher:
U.S. Department of Housing and Urban Development (HUD)

Geography Support:
County, metro area, state. CHAS data available at tract level.

Time Coverage:
FMR and Income Limits updated annually. CHAS data updated periodically (2-3 year cycle).

Access Method:
HUD User API for FMR and Income Limits. Direct download for CHAS. Use `fetch_hud_data.py` for retrieval.

Fetch Script:
`scripts/core/fetch_hud_data.py`

Example:
```bash
python scripts/core/fetch_hud_data.py --dataset fmr --state NE -o data/raw/ne_fmr.csv
python scripts/core/fetch_hud_data.py --dataset il --state KS --year 2024 -o data/raw/ks_income_limits.csv
```

Credentials:
Optional HUD API key (HUD_API_KEY in .env). Some endpoints may work without it. Free registration at https://www.huduser.gov/hudapi/public/register

Licensing / Usage Notes:
Public federal data.

Known Caveats:
- FMR represents the 40th percentile of gross rents — not average or median
- Income Limits define eligibility thresholds, not actual income distributions
- CHAS data is derived from ACS and carries the same estimate-based caveats
- Metro area definitions change over time, complicating trend analysis

Key Datasets:
- **Fair Market Rents (FMR):** Used for Section 8 voucher amounts. By bedroom count.
- **Income Limits (IL):** Very low, low, and moderate income thresholds by area.
- **CHAS:** Tabulations of housing problems (cost burden, overcrowding, inadequate facilities) by income/race/household type at tract level.

Best-Fit Workflows:
- domains/HOUSING.md
- domains/DEMOGRAPHIC_ANALYSIS.md
- workflows/TRACT_JOIN_AND_ENRICHMENT.md

Alternatives:
- ACS housing tables (B25070, B25106 for cost burden)
- Zillow/Redfin market data (commercial)

Sources:
- https://www.huduser.gov/portal/datasets/fmr.html
- https://www.huduser.gov/portal/datasets/il.html
- https://www.huduser.gov/portal/datasets/cp.html
- API: https://www.huduser.gov/hudapi/public/

Trust Level:
High — HUD is the authoritative source for U.S. housing program data.
