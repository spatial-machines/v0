# Cartography Style Guide
## Making Maps That Look Like a Human Designed Them

> **Related guides:**
> - `cartography-advanced.md` — advanced techniques (layout design, visual hierarchy, color science)
> - `3d-visualization-guide.md` — when and how to use 3D terrain visualization
> - `cartography/qgis-review-conventions.md` — QGIS review package conventions (aspirational)
>
> **Start here** for the firm's core cartographic standards and script recipes.
> Read `cartography-advanced.md` after this for deeper design philosophy.

_Inspired by John Nelson's philosophy: "Maps are a communication device for a spatial phenomenon, not a list of ingredients."_

---

## The Core Problem

Our maps are technically correct but visually generic. They look like matplotlib defaults with data plotted on them. A consulting-quality map should feel intentional — every element earns its place, nothing is there by default.

**John Nelson's "Defend" test:** Point at every element on the map and say "defend." If you can't explain why it's there, remove it.

---

## Design Principles

### 1. Visual Hierarchy — The Most Important Thing

Every map has layers of importance. The viewer's eye should hit them in order:

1. **The data** (choropleth fill, point symbols) — this is why the map exists
2. **The legend** — so they can read the data
3. **The title** — what they're looking at
4. **Context** (borders, labels, basemap) — orientation without distraction
5. **Metadata** (source, date) — credibility, but quiet

**Rule:** Background elements should be visually quiet. Data should be visually loud.

### 2. Color With Intent

- **Sequential palettes** for single-variable choropleths: light → dark
  - Good: `YlOrRd`, `YlGnBu`, `RdPu`, `inferno`, `magma`
  - Avoid: rainbow, jet (perceptually uneven, colorblind-hostile)
- **Diverging palettes** for above/below a midpoint: `RdBu`, `BrBG`, `coolwarm`
- **5 classes max** for choropleth — 3 is too coarse, 7+ overwhelms
- **Missing data = medium gray (#d0d0d0)**, never white (white reads as zero)
- **Color intensity should match data intensity** — the darkest color = the most extreme value

### 3. Point Symbols That Actually Show Up

When overlaying points on a choropleth:

- **Size matters:** minimum 30-40px marker size for state-level maps. Our hospital dots at 12px are invisible.
- **Contrast:** Use a color that contrasts with the choropleth palette. White circles with dark outlines work on almost any background.
- **Hierarchy:** If some points matter more (e.g., trauma centers vs clinics), use size or shape to differentiate.
- **Glow/halo:** Add a white or dark edgecolor (linewidth 1-2px) so points don't bleed into the background.
- **Labels for key points:** The top 5-10 most important facilities should have text labels.

**Recipe for visible point overlay:**
```python
points.plot(ax=ax, color='white', edgecolor='#333333', 
            markersize=60, linewidth=1.5, zorder=10, alpha=0.9)
```

### 4. Legends That Inform

- **Legend title = variable name + unit.** "Poverty Rate (%)" not "poverty_rate"
- **Break values should be rounded.** Show "0-5%, 5-10%, 10-20%, 20-40%, 40%+" not "0-4.53, 4.53-8.16..."
- **Position:** Lower-left or lower-right, inside a subtle box with slight transparency
- **Font size:** Readable on mobile (9-10pt minimum)
- **For hotspot maps:** Label each category clearly: "Hot Spot (99% confidence)", "Cold Spot (95%)", "Not Significant"

### 5. Basemaps — Use Them Sparingly

We have `contextily` in the Docker image. Use it for:
- **Point overlay maps** — a light basemap (CartoDB.Positron) gives geographic context without competing with the data
- **Healthcare access maps** — seeing roads/cities helps interpret distance patterns

Do NOT use basemaps for:
- Pure choropleth maps (the polygon fills ARE the visual — a basemap underneath just muddles it)
- Hotspot maps (same reason)

**When using a basemap:**
```python
import contextily as cx
# Reproject to Web Mercator first
gdf_wm = gdf.to_crs(epsg=3857)
gdf_wm.plot(ax=ax, alpha=0.7, ...)  # slightly transparent so basemap peeks through
cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
```

### 6. Layout Composition

- **Title:** Top-left or top-center, 14-16pt bold. One line. Subtitle in lighter weight below if needed.
- **No north arrow** unless the map is rotated or at a scale where direction is ambiguous. State-level thematic maps don't need one.
- **No scale bar** for thematic choropleths. The viewer cares about "which tracts are high" not "how many miles across."
- **Attribution line:** Small, bottom-right, gray text. "ACS 2022 5-Year • Table B17001 • Census TIGER 2024"
- **Figure size:** 14x10 for landscape state maps (gives room for legend + title)
- **DPI:** 200 for final output (150 minimum)
- **Background:** `facecolor='white'` or `facecolor='#f8f8f8'` — not the matplotlib default gray

### 7. Border and Edge Styling

- **Tract borders:** Very thin (0.15-0.3px), white or light gray. They define shapes without competing with fill color.
- **State outline:** Slightly thicker (1-2px), dark gray, drawn on top as a separate layer for a clean boundary
- **No thick black borders** — they make the map look like a coloring book

### 8. The "Defend" Checklist

Before finalizing any map, check every element:

- [ ] **Title** — Does it tell the viewer what they're looking at in plain language?
- [ ] **Legend** — Can a non-GIS person read it? Are breaks meaningful?
- [ ] **Color** — Does the palette match the data type? Is it colorblind-safe?
- [ ] **Points** — Can you actually see them? Are the most important ones labeled?
- [ ] **Borders** — Are they thin enough to not distract?
- [ ] **Basemap** — Does it add context or just noise? (If noise, remove it)
- [ ] **Source** — Is the data vintage and table cited?
- [ ] **Empty space** — Is there dead space that should be cropped?
- [ ] **Mobile test** — Will this be readable on a phone screen?

---

## Specific Map Type Recipes

### Choropleth (single variable)
```python
fig, ax = plt.subplots(1, 1, figsize=(14, 10), facecolor='white')
gdf.plot(ax=ax, column='poverty_rate', cmap='YlOrRd',
         scheme='natural_breaks', k=5,
         edgecolor='white', linewidth=0.2,
         legend=True,
         legend_kwds={'loc': 'lower left', 'fontsize': 9,
                      'title': 'Poverty Rate (%)', 'title_fontsize': 10,
                      'frameon': True, 'framealpha': 0.9,
                      'edgecolor': '#ccc'})
# State outline on top
gdf.dissolve().boundary.plot(ax=ax, edgecolor='#333', linewidth=1.2)
ax.set_title('Poverty Rate by Census Tract\nKansas — ACS 2022 5-Year Estimates',
             fontsize=14, fontweight='bold', loc='left', pad=12)
ax.text(0.99, 0.01, 'Source: ACS 2022 5-Year, Table B17001',
        transform=ax.transAxes, ha='right', va='bottom',
        fontsize=7, color='#999')
ax.set_axis_off()
fig.savefig(output, dpi=200, bbox_inches='tight', facecolor='white')
```

### Point Overlay on Choropleth
```python
fig, ax = plt.subplots(1, 1, figsize=(14, 10), facecolor='white')
# Background choropleth — slightly desaturated
gdf.plot(ax=ax, column='uninsured_rate', cmap='YlOrRd',
         scheme='natural_breaks', k=5,
         edgecolor='white', linewidth=0.15, alpha=0.85,
         legend=True, legend_kwds={...})
# State outline
gdf.dissolve().boundary.plot(ax=ax, edgecolor='#333', linewidth=1.2)
# Points — BIG, with contrast
pts.plot(ax=ax, color='white', edgecolor='#1a1a1a',
         markersize=80, linewidth=1.5, zorder=10)
# Label top facilities
for idx, row in pts.iterrows():
    ax.annotate(row['name'], xy=(row.geometry.x, row.geometry.y),
                fontsize=6, fontweight='bold', color='#333',
                xytext=(5, 5), textcoords='offset points')
```

### Hotspot Map (Getis-Ord Gi*)
```python
colors = {
    'Hot Spot (99%)': '#d73027',
    'Hot Spot (95%)': '#fc8d59', 
    'Hot Spot (90%)': '#fee08b',
    'Not Significant': '#e0e0e0',
    'Cold Spot (90%)': '#d1e5f0',
    'Cold Spot (95%)': '#91bfdb',
    'Cold Spot (99%)': '#4575b4',
}
# Plot each category separately for clean legend
for cls in order:
    subset = gdf[gdf['hotspot_class'] == cls]
    if len(subset) > 0:
        subset.plot(ax=ax, color=colors[cls], edgecolor='white',
                    linewidth=0.15, label=cls)
# Legend with all categories visible
ax.legend(loc='lower left', fontsize=8, title='Gi* Cluster Type',
          title_fontsize=9, frameon=True, framealpha=0.9,
          edgecolor='#ccc', fancybox=False)
```

---

## What "Good" Looks Like

Study these for inspiration:
- **John Nelson's Adventures in Mapping** (adventuresinmapping.com) — particularly his firefly style and thematic map layouts
- **r/MapPorn top posts** — sort by top/all-time for the best examples of clear, beautiful thematic maps
- **NYT graphics team** — their election maps, COVID maps, and demographic maps set the standard for data journalism cartography
- **Esri Map Gallery** (esri.com/en-us/maps-we-love) — curated professional examples

**Common thread in great maps:** restraint. The best maps show less, not more. Every element is intentional. White space is used deliberately. The data is the star.

---

_This guide should be read by the cartography agent before generating any map. The analyze_choropleth.py and related scripts should be updated to implement these defaults._
