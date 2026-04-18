# CDC PLACES Source Page

Source Summary:
CDC PLACES provides small-area health outcome and risk factor estimates for census tracts, counties, and places across the United States. Covers 36 chronic disease measures including diabetes prevalence, obesity, high blood pressure, mental health, cancer screening, and healthcare access.

Owner / Publisher:
Centers for Disease Control and Prevention (CDC)

Geography Support:
Census tract, county, place (city/town)

Time Coverage:
Annual releases; most recent data reflects model-based estimates from BRFSS survey data with 1-2 year lag.

Access Method:
Socrata-powered API at data.cdc.gov. Use `fetch_cdc_places.py` for direct retrieval by state and measure.

Fetch Script:
`scripts/core/fetch_cdc_places.py`

Example:
```bash
python scripts/core/fetch_cdc_places.py 20 --measure DIABETES -o data/raw/ks_diabetes.csv
python scripts/core/fetch_cdc_places.py 13 --measure OBESITY --geo-level county -o data/raw/ga_obesity_county.csv
```

Credentials:
Optional Socrata app token (SOCRATA_APP_TOKEN in .env) increases rate limits. Works without it.

Licensing / Usage Notes:
Public federal data. Model-based estimates — not direct survey counts.

Known Caveats:
- Estimates are model-based, not direct observations — interpret with appropriate uncertainty
- Tract-level estimates have wider confidence intervals than county-level
- Not all measures are available at all geography levels
- Age-adjusted prevalence is the standard metric (data_value_type_id = AgeAdjPrv)

Available Measures (partial list):
DIABETES, OBESITY, BPHIGH, MHLTH, PHLTH, ACCESS2, CHECKUP, CHOLSCREEN, CSMOKING, BINGE, DENTAL, MAMMOUSE, CERVICAL, COLON_SCREEN, ARTHRITIS, KIDNEY, COPD, CHD, STROKE, CANCER, DEPRESSION, SLEEP, TEETHLOST

Best-Fit Workflows:
- workflows/DEMOGRAPHIC_INVENTORY.md (health dimension)
- domains/HEALTHCARE_ACCESS.md
- domains/ENVIRONMENTAL_JUSTICE.md

Alternatives:
- BRFSS direct survey microdata (more detail, less geography)
- County Health Rankings (Robert Wood Johnson Foundation)

Sources:
- https://www.cdc.gov/places/
- https://data.cdc.gov/browse?tags=places
- API: https://data.cdc.gov/resource/swc5-untb.json

Trust Level:
High — CDC is the authoritative source for U.S. population health estimates.
