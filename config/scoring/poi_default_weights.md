# POI Site Selection — Default Scoring Weights

Adjust weights (must sum to 1.0) and direction (higher/lower = better).

| Factor | Weight | Direction | Notes |
|--------|--------|-----------|-------|
| median_income | 0.20 | higher | Household spending power |
| population_density | 0.20 | higher | People per sq km in trade area |
| pct_under_35 | 0.15 | higher | Target demographic for most QSR/retail |
| competitor_density | 0.25 | lower | Competitors per sq km in trade area |
| gap_to_nearest | 0.20 | higher | Distance (km) to nearest existing location |

## Notes
- competitor_density: define competitors in fetch_poi.py --competitors flag
- gap_to_nearest: computed from existing brand locations in trade area
- All factors normalized 0-1 before weighting
- Final score: 0 (worst) to 100 (best)
