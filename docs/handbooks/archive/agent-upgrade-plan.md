# Agent Upgrade Plan
## Research Sprint — Making Each Agent Best-in-Class

_Goal: Close the gap between "impressive for AI" and "impressive, period."_

---

## Agent-by-Agent Upgrade Plan

### 1. 🗺️ Cartography Agent — HIGHEST PRIORITY

**Inspiration:** John Nelson (Esri), Aileen Buckley (Esri), Edward Tufte
**Current gap:** Maps are technically correct but visually generic. Label overlap, invisible points, default styling.

**Upgrades needed:**

#### A. Label collision avoidance
- **Tool:** `adjustText` library (pip install adjustText)
- Add to Docker requirements
- When labeling points on maps, use `adjust_text()` to automatically push labels away from each other
- This single fix would have prevented the KC metro hospital label pileup

#### B. Visual hierarchy training (from Aileen Buckley / Esri)
Five principles to embed in SOUL.md:
1. **Visual contrast** — data features must contrast sharply with background; higher contrast = more important
2. **Legibility** — symbols must be large enough to see AND understood (geometric > complex at small sizes)
3. **Figure-ground** — spontaneous separation of foreground from background; use drop shadows, halos, white washes
4. **Hierarchical organization** — theme > base; the data layer dominates, context recedes
5. **Balance** — visual weight distribution on the page; central figure slightly above center

#### C. The Tufte principles
- **Data-ink ratio** — maximize the share of ink devoted to data; remove every non-data element you can
- **Chartjunk** — decorations that don't convey information; gridlines, heavy borders, 3D effects, gradient fills
- **Small multiples** — when comparing across categories, use repeated small maps with identical scales rather than one complex map
- **Micro/macro readings** — good design provides both an immediate overall impression AND rewards detailed examination

#### D. Practical matplotlib/geopandas improvements
- State outline as dissolved boundary on top layer (already in style guide)
- `constrained_layout=True` instead of `tight_layout` for better legend handling
- Custom legend creation (matplotlib patches) instead of relying on auto-legends which are often ugly
- Font: use `'Helvetica Neue'` or `'DejaVu Sans'` explicitly — don't rely on system default
- Consider `matplotlib.style.use('seaborn-v0_8-whitegrid')` as a starting point, then customize

#### E. Map type decision framework
Add to SOUL.md:
```
BEFORE making any map, answer:
1. Is a map the right choice? (sometimes a bar chart is better)
2. What's the ONE thing the viewer should take away?
3. What classification best reveals the pattern? (run all 3, compare)
4. Will this be readable on a phone?
5. Would John Nelson be proud of this?
```

---

### 2. 🎯 Lead Analyst — CRITICAL (Decision-Making)

**Inspiration:** Luc Anselin (GeoDa/PySAL creator), McKinsey's analytical frameworks
**Current gap:** Delegates tasks correctly but doesn't evaluate whether the analytical approach is appropriate for the data. The "run hotspots on everything" problem.

**Upgrades needed:**

#### A. Spatial analysis decision framework
Add to SOUL.md — a decision tree for choosing analytical methods:

```
QUESTION: "Is there spatial clustering?"
├── First: Run Global Moran's I
│   ├── Significant positive I → Yes, clustering exists → proceed to local analysis
│   ├── Significant negative I → Dispersion pattern → different story to tell
│   └── Not significant → Data is spatially random → DON'T run hotspots (they won't find anything)
│
├── If clustering exists, WHICH local method?
│   ├── Getis-Ord Gi* → Best for: finding where HIGH values cluster (hot spots) or LOW values cluster (cold spots)
│   │   └── Good when: you care about intensity, not outliers
│   ├── Local Moran's I (LISA) → Best for: finding clusters AND outliers (high value surrounded by low, or vice versa)
│   │   └── Good when: you want to find both hot spots AND spatial outliers
│   └── Both are local → ALWAYS run Global Moran's I first to confirm clustering exists
│
├── If data is NOT clustered:
│   ├── Consider: Is the data gradually varying (smooth gradient)?
│   │   └── Spatial interpolation or regression might be more appropriate
│   ├── Consider: Are there known explanatory variables?
│   │   └── Spatial regression (OLS → check residuals → spatial lag/error if autocorrelated)
│   └── Consider: Is the interesting story about the LACK of clustering?
│       └── "Uniformly distributed" IS a finding worth reporting
```

#### B. Pre-analysis checklist
Before delegating analysis to the spatial-stats agent:
1. What's the global Moran's I? (run this FIRST, always)
2. Is the variable's distribution normal or heavily skewed?
3. Are there enough features with non-null values? (< 30 = questionable)
4. What spatial weights make sense? (contiguity for polygons, KNN for points)
5. Will the results be visually meaningful? (95% gray maps waste everyone's time)

#### C. Interpretation templates
When receiving results back from the spatial-stats agent, the lead analyst should frame findings as:
- "The data shows significant spatial clustering (Moran's I = X, p < 0.001), concentrated in [region]"
- "While poverty is elevated in certain tracts, it does NOT cluster spatially — intervention targeting should be based on individual tract characteristics, not geographic proximity"
- "The hotspot analysis reveals [N] statistically significant clusters, primarily in [region], suggesting spatially-targeted intervention would be efficient"

---

### 3. 📈 Spatial Stats Agent

**Inspiration:** Luc Anselin (PySAL/GeoDa), Sergio Rey (PySAL), Esri spatial statistics documentation
**Current gap:** Runs the analysis correctly but doesn't interpret results or flag when an analysis is inappropriate.

**Upgrades needed:**

#### A. Always-run-first protocol
- Global Moran's I MUST be computed before any local statistic
- If global I is not significant, WARN the lead analyst that local statistics may not find meaningful patterns
- Include interpretation in the handoff: "Global Moran's I = 0.15, p = 0.23 — spatial autocorrelation is weak; local hot spot results should be interpreted cautiously"

#### B. Multiple comparisons awareness
From Anselin's GeoDa workbook:
- With 829 features and p < 0.05, you'd expect ~41 "significant" results by chance alone
- Always apply Bonferroni correction or FDR (False Discovery Rate)
- Report both raw and adjusted significance counts
- If most "significant" results disappear after correction, say so

#### C. Sensitivity analysis
- Run analysis with at least 2 different spatial weights (queen contiguity AND KNN-8)
- If results change dramatically, the findings are not robust — report this
- Always report the permutation count and method

#### D. Conditional maps
When Gi* shows mostly "not significant":
- Suggest conditional analysis: "Show me high-poverty tracts that are ALSO far from hospitals"
- This is a filter-then-map approach, not a statistical test, but often more useful for policy

---

### 4. ✍️ Report Writer

**Inspiration:** Edward Tufte (data communication), McKinsey reporting, Pyramid Principle (Barbara Minto)
**Current gap:** Writes decent narrative but could be sharper. Needs more structure for consulting-grade deliverables.

**Upgrades needed:**

#### A. The Pyramid Principle (Minto)
- **Lead with the answer.** The first sentence should be the key recommendation.
- **Group supporting arguments.** Three pillars maximum.
- **Each pillar has evidence.** Maps, stats, tables — in that order of visual impact.

#### B. Tufte's data presentation rules
- **Show the data.** Don't describe what the reader can see; add context they can't see.
- **Avoid data-free zones.** Every paragraph should reference a specific number, map, or comparison.
- **Causality claims require evidence.** "Poverty causes poor health outcomes" needs a citation; "Poverty and uninsured rates correlate (r=0.53)" is what we can say.

#### C. Consulting-grade structure
```
1. Executive Summary (1 page max)
   - The question we answered
   - 3 key findings (specific numbers)
   - Recommendation
   
2. Key Finding 1 — [strongest finding]
   - Hero map
   - Supporting statistics
   - What this means for the client
   
3. Key Finding 2 — [second finding]
   - Hero map
   - Supporting statistics
   
4. Key Finding 3 — [third finding]
   
5. Methodology (technical audience only)
   
6. Limitations & Caveats
   
7. Appendix: Data Sources, Full Statistics, Downloads
```

---

### 5. 📦 Data Retrieval & 🔧 Data Processing

**Inspiration:** FME/Safe Software best practices, USGS data quality standards
**Current gap:** Works correctly. Main upgrade is defensive programming.

**Upgrades needed:**
- Validate GEOID format BEFORE join (check string type, length, leading zeros)
- Log and report match rates prominently (not buried in JSON)
- When match rate < 95%, automatically diagnose: is it GEOID format? Missing tracts? Water-only tracts?
- Add CRS validation at every stage (don't assume — check)

---

### 6. 🔍 Data Discovery

**Current gap:** Has good reference tables but doesn't yet verify download URLs or check data freshness.

**Upgrades needed:**
- When recommending datasets, include: vintage, last updated date, known limitations
- Prioritize federal authoritative sources over aggregated/third-party
- When multiple sources exist for the same data (e.g., uninsured rate from ACS vs SAHIE), recommend the more granular one and explain why

---

### 7. 🌐 Site Publisher

**Current gap:** Build script works but doesn't handle non-standard directory structures (the ks-healthcare-access flat layout broke it).

**Upgrades needed:**
- Make build_site.py resilient to both `outputs/maps/` and `outputs/` flat layouts
- Add thumbnail generation (crop + resize hero map to standard card size)
- Add last-modified timestamp per project
- Mobile: test that maps aren't clipped on narrow screens

---

### 8. ✅ Validation QA

**Current gap:** Checks are technically sound. Missing: analytical validity checks.

**Upgrades needed:**
- Add analytical checks: "Is the choropleth column actually a rate (0-100) or raw count?"
- Flag when summary stats show extreme skew that might mislead choropleth classification
- Check that maps have legends, titles, and attribution (image metadata or file size heuristics)

---

## Cross-Cutting Upgrades

### Inter-agent communication
Currently: sequential delegation, no back-and-forth.
**Needed:** The lead analyst should be able to say to the cartography agent "the stats agent found weak clustering — make a conditional map instead of a hotspot map." This requires:
- Handoff JSONs that include analytical recommendations, not just file paths
- The lead analyst reading results from one agent before delegating to the next
- A "review and revise" loop where the lead analyst can send work back

### Tools to add to Docker
- `adjustText` — label collision avoidance (critical for cartography)
- Consider `cartopy` — better map projections than raw matplotlib

### Documentation gaps
- Each script needs a `--help` that explains not just args but WHEN to use the script
- The handbooks should include worked examples ("for this kind of question, use this pipeline")

---

## Priority Order

1. **Cartography** — biggest visible impact, specific fixes known
2. **Lead Analyst** — decision-making framework prevents wasted analysis
3. **Spatial Stats** — always-run-Global-Moran's-I-first protocol
4. **Report Writer** — Pyramid Principle + consulting structure
5. **Site Publisher** — resilience fixes
6. **Validation QA** — analytical validity checks
7. **Data Processing** — defensive GEOID handling
8. **Data Discovery** — freshness verification
9. **Data Retrieval** — already solid

---

_This plan should be executed in priority order. Each agent upgrade = rewrite SOUL.md + TOOLS.md + test with a real analysis._
