# Spatial Statistics Guide
## For the Spatial Stats Agent & Lead Analyst
### Sources: Luc Anselin (PySAL/GeoDa), Lauren Bennett (Esri), Esri Spatial Statistics Team

---

## The Golden Rule: Always Confirm Global Before Going Local

Before running ANY local statistic (hotspots, LISA, etc.), run **Global Moran's I** first.

- **Significant positive I** → Spatial clustering exists → proceed to local analysis
- **Significant negative I** → Spatial dispersion → different story entirely
- **Not significant (p > 0.05)** → Spatial randomness → **STOP. Do not run hotspots.** They will produce false-positive results.

This single check would have prevented the 95%-gray hotspot maps in Kansas. The uninsured rate in Kansas has weak global clustering (Moran's I likely ~0.15, not significant) — which means a hotspot map produces mostly noise.

---

## Choosing the Right Tool

### Decision Framework

```
Q: Is the data spatially random, or does it cluster?
   → Run Global Moran's I FIRST

If CLUSTERED (significant positive I):
   ├── "Where are the hot spots?" → Getis-Ord Gi*
   │      Best for: intensity clustering (high-high, low-low)
   │      Use when: you want to find concentrations
   │      Example: Finding where poverty is highest and surrounded by high-poverty neighbors
   │
   ├── "Are there outliers, not just clusters?" → Local Moran's I (LISA)  
   │      Best for: both clusters AND outliers (high surrounded by low, vice versa)
   │      Use when: spatial outliers are important (e.g., a wealthy tract surrounded by poor ones)
   │      Example: Finding Wyandotte tracts (high poverty) next to Johnson County (low poverty)
   │
   └── "How much of Y is explained by spatial location of X?" → Spatial Regression
          Start with OLS → check residual autocorrelation → if autocorrelated, use Spatial Lag/Error
          Use when: you want to model relationships, not just describe them

If DISPERSED (significant negative I):
   → Checkerboard pattern; rare in socioeconomic data
   → Report the finding: "Values are dispersed — no meaningful clustering"

If RANDOM (not significant):
   → Option A: Map individual tract values (choropleth) — clustering tools are wrong here
   → Option B: Filter + map high-value tracts directly (e.g., "tracts where poverty > 20%")
   → Option C: Tell the story of uniformity — "Kansas shows statewide moderate poverty without regional concentration"
```

### ArcGIS → Python/PySAL mapping (since our tools are Python-based)

| ArcGIS Tool | PySAL/Python Equivalent | When to Use |
|---|---|---|
| Spatial Autocorrelation (Moran's I) | `esda.moran.Moran` | Test if data clusters globally |
| Hot Spot Analysis (Getis-Ord Gi*) | `esda.getisord.G_Local` | Find high/low intensity clusters |
| Cluster and Outlier (LISA) | `esda.moran.Moran_Local` | Find clusters + outliers |
| OLS Regression | `spreg.OLS` | Model spatial relationships |
| Spatial Lag Model | `spreg.ML_Lag` | When residuals are autocorrelated |
| Spatial Error Model | `spreg.ML_Error` | Alternative spatial regression |
| Optimized Hot Spot | Not available — choose weights carefully | Adaptive scale |

### QGIS equivalents (for headless/scripted use via PyQGIS)
- Moran's I: `processing.run("qgis:spatialautocorrelation", {...})`
- Buffer: `processing.run("native:buffer", {...})`
- Dissolve: `processing.run("native:dissolve", {...})`
- Join attributes by location: `processing.run("native:joinattributesbylocation", {...})`
- Points in polygon: `processing.run("native:countpointsinpolygon", {...})`
- Statistics by category: `processing.run("qgis:statisticsbycategories", {...})`

---

## Interpreting Results — What to Report

### Global Moran's I
```
Moran's I = 0.47 (z = 12.3, p < 0.001)
→ "There is significant positive spatial autocorrelation in poverty rates. 
   Poverty clusters geographically — high-poverty tracts tend to be near 
   other high-poverty tracts."

Moran's I = 0.06 (z = 1.4, p = 0.16)
→ "Poverty rates show no significant spatial clustering. Individual tract 
   values are essentially random with respect to neighboring tracts. A 
   choropleth map is appropriate; hot spot analysis would not be meaningful."
```

### Hot Spots (Getis-Ord)
```
Hot Spot (99%) → Statistically significant cluster of HIGH values (Gi* z > 2.58)
Hot Spot (95%) → Statistically significant cluster of HIGH values (Gi* z > 1.96)
Cold Spot (99%) → Statistically significant cluster of LOW values (Gi* z < -2.58)
Not Significant → No clustering detected at this location
```

### LISA Cluster Types
```
High-High (HH) → High value surrounded by high values → True hot spot
Low-Low (LL)   → Low value surrounded by low values → True cold spot  
High-Low (HL)  → High value surrounded by low values → Spatial outlier
Low-High (LH)  → Low value surrounded by high values → Spatial outlier
```

---

## Multiple Comparisons Problem

With 829 Kansas tracts at p < 0.05, you'd expect **~41 significant results by chance alone**.

Always apply corrections:
- **Bonferroni bound**: α_corrected = α / n = 0.05 / 829 = 0.00006
- **False Discovery Rate (FDR)**: less conservative, more practical for exploratory work
- Report both: "19 tracts significant at p < 0.05; after FDR correction, 12 remain significant"

---

## Spatial Weights — Choosing the Right One

| Weight Type | Use When | Notes |
|---|---|---|
| Queen contiguity | Polygons sharing edges or corners | Default for census tracts |
| Rook contiguity | Polygons sharing edges only | More conservative |
| KNN (K=8) | Irregular polygons, or when contiguity has many islands | Good for rural tracts |
| Distance band | Point data or when specific distance matters | Need to choose threshold carefully |

**Row-standardize** weights (`w.transform = 'r'`) for Moran's I and LISA.
**Binary** weights (`w.transform = 'b'`) for Getis-Ord Gi*.

---

## The Interpretation Template

Every spatial stats output should answer these questions:
1. Is there statistically significant spatial structure? (Global Moran's I)
2. If yes, where does it cluster? (Local statistics)
3. What type of clustering? (HH, LL, outliers)
4. How many significant clusters after correction?
5. What does this mean for the analytical question?

---

## When Spatial Stats Is the Wrong Tool

- **Data is not area data** → Use point pattern analysis instead
- **N < 30** → Permutation tests unstable; report raw choropleth instead
- **All values identical** → Can't compute autocorrelation
- **Question is about individual tracts** → Use filtering/ranking, not spatial stats
- **Question is about change over time** → Use space-time analysis, not cross-sectional autocorrelation

---

## Reference
- Anselin, L. (1995). Local Indicators of Spatial Association — LISA. *Geographical Analysis*, 27(2), 93-115.
- GeoDa Workbook: geodacenter.github.io/workbook/6a_local_auto/lab6a.html
- Esri Spatial Statistics Resources: esri.com/arcgis-blog/products/product/analytics/spatial-statistics-resources
- Lauren Bennett / Lauren Scott, Esri: "Spatial Data Mining: A Deep Dive into Cluster Analysis"
