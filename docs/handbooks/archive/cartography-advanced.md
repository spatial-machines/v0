# Advanced Cartography Guide
## For the Cartography Agent

> **Read `cartography-style-guide.md` first** — that's the mandatory baseline.
> This guide provides deeper design philosophy and advanced techniques for complex or high-stakes maps.
### Sources: John Nelson (Esri), Aileen Buckley (Esri), Edward Tufte, QGIS Print Layout docs

---

## The Philosophy

**John Nelson:** "Maps are a communication device for a spatial phenomenon, not a list of ingredients. They are always better when the creation is an austere additive process rather than a blind acceptance of defaults."

**Aileen Buckley:** "Without the five design principles — legibility, visual contrast, figure-ground, hierarchical organization, and balance — map-based communication will fail."

**Edward Tufte:** "Maximize the data-ink ratio. Every mark on the page should serve the data."

---

## The Five Principles (Aileen Buckley / Esri)

### 1. Visual Contrast
- Features must contrast with their background — the more contrast, the more important
- For quantitative choropleths: enough tonal contrast between classes so readers can distinguish them
- For qualitative data: use hue variation, not just lightness variation
- **Application:** State borders should be dark against light tract fills. Tract borders should be white/light against colored fills.

### 2. Legibility
- Every symbol must be large enough to SEE and also to UNDERSTAND
- Geometric symbols are legible at smaller sizes; complex shapes need more space
- Text below 7pt is not legible on screen; 8-9pt is minimum for labels
- **Application:** Hospital points at 12px are not legible. 60-80px (about 0.8-1.0cm) is the minimum for state-level overlays.

### 3. Figure-Ground
- The map's subject (the data) should spontaneously separate from the background
- Tools for figure-ground: white wash, drop shadows, feathering, color contrast
- **Application:** A dissolved state outline drawn on top of tract fills creates strong figure-ground separation. Contextily basemap behind transparent choropleth adds geographic context without competing.

### 4. Hierarchical Organization
- For thematic maps: **the theme is more important than the base that provides geographic context**
- Layers should read in this order: data → legend → context → metadata
- Background features (roads, city names, grid) should be visually quiet
- **Application:** Never use an ostentatious basemap behind a choropleth. CartoDB.Positron or nothing.

### 5. Balance
- Visual weight is distributed across the page to create equilibrium
- Central figure slightly above center on the page
- Title + legend + map should be evaluated together
- **Application:** Title top-left/center, legend bottom-left, attribution bottom-right.

---

## Label Best Practices

### The Label Overlap Problem
Label collision is the #1 cartographic failure in our maps. Solution: `adjustText`.

```python
from adjustText import adjust_text

# Instead of ax.annotate() in a loop:
texts = []
for idx, row in hospitals.iterrows():
    texts.append(ax.annotate(
        row['name_short'],
        xy=(row.geometry.x, row.geometry.y),
        fontsize=7, fontweight='bold', color='#1a1a1a',
        ha='center', va='bottom'
    ))
    
# Adjust to prevent overlap
adjust_text(
    texts,
    ax=ax,
    force_text=0.5,
    force_points=0.3,
    arrowprops=dict(arrowstyle='-', color='#666', lw=0.8),
    expand_text=(1.2, 1.2),
    expand_points=(1.5, 1.5)
)
```

Add `adjustText` to Docker requirements.

### Label Hierarchy
- Primary features: 8-10pt, bold
- Secondary features: 7-8pt, regular  
- Reference only: 6-7pt, light or italic
- Never label everything — label the 5-10 most important features

### Label placement rules
- Point labels: offset to upper-right by default; avoid overlap with point symbol
- Never let labels overlap the state boundary
- Abbreviate when needed: "KU Med Center" not "The University of Kansas Medical Center"

---

## The QGIS Print Layout Advantage

For final deliverable-quality maps, QGIS Print Layout beats matplotlib because:
- Vector output (PDF, SVG) — no pixelation
- Proper cartographic elements (scalebar, north arrow, legend box)
- Fine-grained control over typography, spacing, margins
- Print-ready at any size

**QGIS Print Layout key elements:**
1. Map frame — the actual map view
2. Title label — top center/left, 16-18pt, bold
3. Subtitle/description — 10pt, regular
4. Legend — structured, clean, outside map frame
5. Scale bar — only if distance context matters (healthcare access maps: yes; pure thematic: no)
6. North arrow — only if map is rotated or at local scale
7. Attribution/data source — bottom margin, 7-8pt, gray

**The north arrow rule:** A map of Kansas doesn't need a north arrow. Everyone knows north is up. Add one only when the map is rotated or covering an area unfamiliar to the audience.

---

## Color in Depth

### Sequential palettes (single variable, low → high)
```python
# Recommended
'YlOrRd'   # warm, intuitive for poverty/risk
'YlGnBu'   # cool, good for access/coverage
'PuBu'     # soft, works for rates
'RdPu'     # distinctive, good for health outcomes
'viridis'  # perceptually uniform, colorblind-safe
'magma'    # dark background variant of viridis
```

### Diverging palettes (deviation from midpoint)
```python
'RdBu'     # classic diverging
'BrBG'     # good for environmental data
'PuOr'     # high contrast
'RdGy'     # when one direction matters more
```

### Categorical (qualitative)
```python
'Set2'     # muted, works well together
'Paired'   # good for before/after comparisons
'Dark2'    # darker, higher contrast
```

### Color rules
- Never use raw `'jet'` or rainbow scales — perceptually distorted
- Test for colorblind accessibility (red-green discrimination: avoid pure red/green pairs)
- Light = low, dark = high for sequential data — the convention is universal
- Missing data = `'#d0d0d0'` (medium gray) — never white (implies zero)

---

## Map Type Decision Guide

| Data type | Map type | Why |
|---|---|---|
| Rate/percentage (poverty %) | Choropleth | Normalized data; comparable across areas |
| Raw count (population) | Proportional symbol | Raw count depends on area size |
| Categories (land use) | Qualitative choropleth | No implied order |
| Two related variables | Bivariate choropleth | Shows correlation spatially |
| Many variables | Small multiples | Consistent scale for comparison |
| Hotspot/cold spot | Diverging categorical | Red=hot, blue=cold, gray=insignificant |
| Change over time | Diverging choropleth | Positive change vs negative change |
| Points on thematic base | Choropleth + point overlay | Background = context, points = subject |

---

## Matplotlib/GeoPandas Recipes

### State outline on top (critical for polish)
```python
# After all other layers
state_outline = gdf.dissolve()  # merge all tracts into single state shape
state_outline.boundary.plot(ax=ax, edgecolor='#333333', linewidth=1.2, zorder=20)
```

### Custom legend (avoid ugly auto-legends)
```python
from matplotlib.patches import Patch

legend_elements = [
    Patch(facecolor='#d73027', edgecolor='white', label='Hot Spot (99%)'),
    Patch(facecolor='#fc8d59', edgecolor='white', label='Hot Spot (95%)'),
    Patch(facecolor='#e0e0e0', edgecolor='white', label='Not Significant'),
    Patch(facecolor='#91bfdb', edgecolor='white', label='Cold Spot (95%)'),
    Patch(facecolor='#4575b4', edgecolor='white', label='Cold Spot (99%)'),
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=8,
          title='Gi* Significance', title_fontsize=9,
          frameon=True, framealpha=0.92,
          edgecolor='#cccccc', fancybox=False)
```

### Consistent figure setup
```python
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
```

### Attribution (always include)
```python
ax.text(0.99, 0.01,
    'ACS 2022 5-Year Estimates • Census TIGER 2024',
    transform=ax.transAxes, ha='right', va='bottom',
    fontsize=7, color='#999999', style='italic')
```

---

## The "Would John Nelson Be Proud?" Test

Before saving any map:
1. What is the ONE thing this map communicates?
2. Does every element earn its place? (The "Defend" test)
3. Is the data the star, or is it competing with its own background?
4. Would a non-GIS person understand the key takeaway in 5 seconds?
5. Are the labels readable without overlap?
6. Is the state outline crisp and clean?
7. Does the legend use human-readable values, not raw decimal numbers?

If you're unsure, err toward simpler. Remove elements rather than add them.
