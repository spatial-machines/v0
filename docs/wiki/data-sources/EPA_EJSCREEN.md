# EPA EJScreen Source Page

Source Summary:
EPA's Environmental Justice Screening tool provides environmental and demographic indicators for any location in the United States. Includes pollution exposure (PM2.5, ozone, lead paint, proximity to hazardous waste), demographic vulnerability (low income, minority, limited English), and composite EJ indexes.

Owner / Publisher:
U.S. Environmental Protection Agency (EPA)

Geography Support:
Point + buffer query (returns indicators for the area around a lat/lon point), census block group level data.

Time Coverage:
Updated annually. Current version reflects the most recent ACS and environmental monitoring data.

Access Method:
REST API at ejscreen.epa.gov. Use `fetch_ejscreen.py` for point+buffer queries.

Fetch Script:
`scripts/core/fetch_ejscreen.py`

Example:
```bash
python scripts/core/fetch_ejscreen.py --lat 33.749 --lon -84.388 --distance 1 -o data/raw/ejscreen_atlanta.json
python scripts/core/fetch_ejscreen.py --lat 41.878 --lon -87.629 --distance 3 -o data/raw/ejscreen_chicago.json
```

Credentials:
None required.

Licensing / Usage Notes:
Public federal data. Intended for screening, not regulatory decisions.

Known Caveats:
- Screening tool only — not designed for site-specific regulatory assessment
- Buffer-based queries aggregate block group data, not precise pollution modeling
- Environmental indicators use proximity-based measures (distance to facilities), not direct exposure
- Some indicators may not be available in all areas

Key Indicators:
- Demographics: % low income, % minority, % limited English, % less than high school
- Pollution: PM2.5, ozone, diesel PM, air toxics cancer risk, lead paint, traffic proximity
- Proximity: to superfund sites, RMP facilities, hazardous waste, wastewater discharge
- EJ Indexes: composite scores combining demographic and environmental factors

Best-Fit Workflows:
- domains/ENVIRONMENTAL_JUSTICE.md
- domains/CLIMATE_RISK.md
- workflows/WITHIN_DISTANCE_ENRICHMENT.md

Alternatives:
- EPA ECHO (facility-level compliance data)
- CalEnviroScreen (California-specific, more detailed)

Sources:
- https://www.epa.gov/ejscreen
- API: https://ejscreen.epa.gov/mapper/

Trust Level:
High — EPA is the authoritative source for U.S. environmental data.
