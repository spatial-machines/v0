# USDA Food Access Research Atlas Source Page

Source Summary:
The USDA Food Access Research Atlas identifies census tracts that are food deserts — areas with limited access to affordable, nutritious food. Provides tract-level indicators for low access at various distance thresholds (0.5, 1, 10, 20 miles), combined with income and vehicle access data.

Owner / Publisher:
U.S. Department of Agriculture, Economic Research Service (USDA ERS)

Geography Support:
Census tract (national coverage)

Time Coverage:
Periodic updates. Most recent release uses 2019 data. Prior versions available for 2010, 2015.

Access Method:
Direct CSV download from USDA ERS. Use `fetch_usda_food_access.py` for retrieval with optional state filtering.

Fetch Script:
`scripts/core/fetch_usda_food_access.py`

Example:
```bash
python scripts/core/fetch_usda_food_access.py -o data/raw/food_access.csv
python scripts/core/fetch_usda_food_access.py --state-fips 20 -o data/raw/ks_food_access.csv
```

Credentials:
None required.

Licensing / Usage Notes:
Public federal data.

Known Caveats:
- "Food desert" definition varies by distance threshold and urban/rural classification
- Low access does not mean no access — it means distance to nearest supermarket exceeds threshold
- Vehicle access data from ACS has the usual estimate-based caveats
- Data may lag 2-4 years behind current conditions
- The full national file is ~50MB

Key Fields:
- LILATracts_1And10: low income and low access at 1 mile (urban) / 10 miles (rural)
- LILATracts_halfAnd10: low income and low access at 0.5 mile (urban) / 10 miles (rural)
- lapop1_10: population count with low access (1 mile urban / 10 mile rural)
- lalowi1_10: low income population count with low access
- lahunv1_10: households without vehicle with low access
- Urban: urban/rural flag
- GroupQuartersFlag: institutional population flag

Best-Fit Workflows:
- domains/FOOD_ACCESS.md
- workflows/TRACT_JOIN_AND_ENRICHMENT.md
- domains/ENVIRONMENTAL_JUSTICE.md

Alternatives:
- SNAP retailer data (USDA FNS)
- Grocery store POI from OpenStreetMap
- Nielsen / commercial food retail databases

Sources:
- https://www.ers.usda.gov/data-products/food-access-research-atlas/
- Documentation: https://www.ers.usda.gov/data-products/food-access-research-atlas/documentation/

Trust Level:
High — USDA ERS is the authoritative source for U.S. food access research.
