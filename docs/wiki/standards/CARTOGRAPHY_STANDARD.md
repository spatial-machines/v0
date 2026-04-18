# Cartography Standard

Purpose:
define the firm's universal design rules for map production
preserve cartographic discipline across producers, tools, and map families
make every cartographic choice intentional and defensible
This standard governs map *design*. The map-type-specific *methods* live in workflow pages (choropleth, point overlay, hotspot, bivariate). The map *QA gate* lives in
qa-review/MAP_QA_CHECKLIST.md
.
Use When
Use this standard whenever a workflow produces:
a static or interactive map for any audience
a map for a client deliverable
a map for a review site, dashboard, or report
a map for internal QA review
Do Not Use When
Do not use this standard for:
quick scratch maps used only for analyst orientation during a workflow
raw data previews that will not leave the project team
non-cartographic visualizations (charts, tables) — those have their own conventions
Approved Rule — Defend Every Element
Every element on a map must earn its place. The "Defend test": point at every element and explain why it is there. If you cannot defend it, remove it.
This is the headline rule. Every other approved rule below is an operational expression of it.
Approved Rules
Visual hierarchy
The viewer's eye must hit elements in this order:
1. the data (choropleth fill, point symbols) — this is why the map exists
2. the legend — so the data can be read
3. the title — what the viewer is looking at
4. context (boundaries, labels, basemap) — orientation without distraction
5. metadata (source, date) — credibility, kept quiet
Background elements must be visually quiet. Data must be visually loud.
Color rules
Sequential palettes for single-variable choropleths (low → high):
warm (YlOrRd, RdPu, magma) for risk, poverty, intensity
cool (YlGnBu, PuBu, viridis) for access, coverage, neutral
Diverging palettes for above/below a midpoint or change metrics:
RdBu, BrBG, coolwarm, RdGy
Categorical palettes for unordered categories:
Set2, Paired, Dark2
Color rules:
never use raw rainbow or jet — perceptually uneven, colorblind-hostile
test for colorblind accessibility; avoid pure red/green pairs
light = low, dark = high for sequential data — universal convention
missing data = medium gray (#d0d0d0); never white (white reads as zero)
color intensity must match data intensity
Classification rules
Five classes maximum for choropleth — three is too coarse, seven or more overwhelms
The classification method must be documented:
natural breaks for skewed distributions
quantile for rank-based interpretation
equal interval for uniform distributions
standard deviation for deviation framing
manual when defending against a known threshold (and the threshold must be stated)
Method must be appropriate to the metric:
do not use equal interval on heavily skewed data without justification
do not use quantile if class labels imply absolute thresholds
class breaks must be inspected for misleading splits (e.g., a natural break that separates nearly identical values)
Legend rules
Legend title = variable name + unit ("Poverty Rate (%)" not "poverty_rate")
Break values must be rounded to readable numbers ("0–5%, 5–10%" not "0.00–4.53, 4.53–8.16")
Position: lower-left or lower-right, inside a subtle box with slight transparency
Font size: readable on the expected display size (9-10pt minimum for screen)
"No data" or "not applicable" category must be shown if features have null values
For categorical maps (hotspot, LISA): each category labeled clearly with its significance level or cluster type
Border and edge rules
Tract borders (or other interior subdivisions): thin (0.2 px / 0.2 mm), white or light gray. They define shapes without competing with the fill
Dissolved outer outline (state, county, study area boundary): slightly thicker (0.35 px / 0.35 mm), medium gray (#555555), drawn on top as a separate layer
Never use thick black borders — they make the map look like a coloring book
Title and attribution rules
Title: one line, 14-16pt bold, top-left or top-center; subtitle in lighter weight below if needed
Title must describe the metric, geography, and time period in plain language; never editorialize or imply a conclusion
Attribution: small (7-8pt), bottom-right, gray; cite the data source with vintage and table name where applicable
Attribution requirements: OSM-derived data requires ODbL attribution; Census-derived data cites the Census Bureau with vintage
Map family taxonomy
Different map families have different required elements. The basemap, scale bar, and north arrow are NOT universal — they apply to some families and not others. The taxonomy is the firm's resolution of the contradiction between the previously-mandatory cartography handbook (which forbade chrome on thematic maps) and PIPELINE_STANDARDS.md (which previously required chrome on every vector map). See
docs/CARTOGRAPHY_REQUIREMENT_RESOLUTION.md
for the resolution decision and rationale.
Five families:
1. Thematic choropleth — single-variable polygon fills; the data IS the visual
2. Thematic categorical — hotspot, LISA, qualitative categorical; the colored polygons are the visual
3. Point overlay on thematic base — points overlaid on a polygon base; context matters for the points
4. Reference / orientation — geographic context is itself the message
5. Raster surface — DEM, hillshade, slope, suitability; the raster IS the base
Required elements per family (Y = required, N = forbidden, O = optional):
| Element | Thematic choropleth | Thematic categorical | Point overlay | Reference / orientation | Raster surface |
|---|---|---|---|---|---|
| Basemap (CartoDB.Positron) | N | N | Y | Y | (raster IS base) |
| Scale bar | N | N | O | Y | Y |
| North arrow | N | N | O | Y | Y |
| Title | Y | Y | Y | Y | Y |
| Legend | Y | Y | Y | O | Y |
| Attribution | Y | Y | Y | Y | Y |
| Dissolved outline | Y | Y | Y | O | Y |
The thematic families forbid basemap, scale bar, and north arrow because the data is the visual and chrome competes with it. The reference / raster families require them because orientation and distance context are the point of those maps. Point overlay is in the middle: a basemap aids interpretation of point positions; scale bar and north arrow are optional unless the project brief calls for them.
Numeric defaults
DPI: 200 preferred for client-grade output; 150 minimum
Figure size: 14×10 (inches) for landscape state-level thematic maps; 12×10 for local-area or sub-region maps
Background: white or very light gray (#f8f8f8) — never the matplotlib default gray
Inputs
Required inputs for any workflow that invokes this standard:
analysis-ready data with documented CRS per
standards/CRS_SELECTION_STANDARD.md
project brief specifying audience, delivery format, and study area
the appropriate map family per the taxonomy above
output target (static PNG, web map, print)
Method Notes
The Aileen Buckley five principles
Cartographic design follows five principles that the rules above operationalize:
visual contrast — features must contrast with their background
legibility — every symbol must be large enough to see and to understand
figure-ground — the map's subject must spontaneously separate from the background
hierarchical organization — for thematic maps, the theme is more important than the base
balance — visual weight is distributed across the page for equilibrium
This standard's Approved Rules above are how the firm operationalizes those principles. See Sources for further reading.
Map type decision guide
Choosing the right map type for the data is part of the design. A common decision matrix:
| Data type | Map type | Family |
|---|---|---|
| Rate / percentage | Choropleth | Thematic choropleth |
| Raw count | Proportional symbol | Point overlay or thematic categorical |
| Categories (land use, POI category) | Qualitative choropleth | Thematic categorical |
| Two related variables | Bivariate choropleth | Thematic choropleth |
| Many variables | Small multiples | Thematic choropleth |
| Hotspot / cold spot | Diverging categorical | Thematic categorical |
| Change over time | Diverging choropleth | Thematic choropleth |
| Points on thematic base | Choropleth + point overlay | Point overlay |
| Geographic orientation | Reference map | Reference / orientation |
| Terrain / surface | Raster surface map | Raster surface |

## Reference layer selection (the narrative test)

Before adding any reference layer (water, roads, transit, parks,
boundaries, POIs), ask: **what does this layer tell the reader about
the analysis question?** If the answer is "nothing, it just makes
the map look complete," leave it off.

| Reference layer | Include when | Skip when |
|---|---|---|
| Hydrography / water | Analysis involves flooding, coastal risk, waterfront access, or the study area is genuinely bisected by water | Analysis is about demographics, health, food access, or anything else that doesn't cross water boundaries |
| Road network | Analysis involves driving distance, traffic safety, or road-dependent access | Choropleth of tract-level demographics; the basemap already carries enough road context |
| Transit lines / stops | Analysis involves transit access, equity in transit-rich cities, or mobility constraints of non-car populations | Rural analyses, or urban analyses where transit is not the causal mechanism |
| POIs (retailers, clinics, schools) | The analysis is specifically about access to those facilities | The facilities have no relationship to the analysis question |
| Parks / open space | Analysis involves heat, green space access, or environmental equity | Default maps; parks become visual clutter |
| Place labels | Always (readers need orientation) | Never — always include at least major cities/neighborhoods |

Consult the relevant `domains/*.md` page for the analysis question
before composing the reference stack. Domain wiki pages document the
standard reference-layer choices for that kind of analysis. Adding
layers that don't serve the narrative is a tell of amateur work.
Validation Rules
A map should fail this standard if:
any element on the map cannot be defended (it is there by default, not by intent)
the map family is unstated or the required elements for that family are missing
the color palette does not match the data type (sequential vs. diverging vs. categorical)
classification has more than five classes for a choropleth without explicit justification
the classification method is undocumented or inappropriate for the distribution
the legend title uses a raw field name instead of a human label with units
break values are unrounded
missing data is shown as white (not gray) or omitted entirely when present
borders are thick black or compete with the fill
the title editorializes or fails to name the metric, geography, and time period
the attribution is missing the data source with vintage
the DPI is below the family minimum
the map shows a count on a choropleth without normalizing by area
the map mixes families' chrome conventions (e.g., a thematic choropleth with a required scale bar)
Human Review Gates
Escalate when:
the map covers a politically or commercially sensitive topic where visual framing matters
the classification method materially changes the visual story
the map could be misread to support a conclusion the data does not support
the map will be used in a legal or regulatory context
the project brief requires a non-standard family or chrome configuration
the visual analysis suggests the data does not support the chosen map type
Common Failure Modes
using equal-interval classification on heavily skewed data, putting most features in one class
using a diverging palette for a non-divergent metric, or vice versa
mapping raw counts on a choropleth and producing a population-density proxy
showing missing data as white (it reads as zero)
illegible labels at the display size
class breaks chosen to emphasize or minimize a particular pattern (cherry-picking)
title that does not match the metric actually mapped
wrong vintage in the source citation
basemap behind a thematic choropleth, muddling the data layer
scale bar and north arrow on a thematic map where neither contributes interpretation
no "no data" category when some features have null values
color palette indistinguishable for colorblind viewers
Related Workflows
workflows/CHOROPLETH_DESIGN.md
workflows/POINT_OVERLAY_DESIGN.md
workflows/HOTSPOT_MAP_DESIGN.md
workflows/BIVARIATE_CHOROPLETH_DESIGN.md
workflows/QGIS_HANDOFF_PACKAGING.md
workflows/REVIEW_SITE_PUBLISHING.md
domains/CARTOGRAPHY_AND_DELIVERY.md
Related QA
qa-review/MAP_QA_CHECKLIST.md
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
standards/PUBLISHING_READINESS_STANDARD.md
standards/CRS_SELECTION_STANDARD.md
standards/STRUCTURAL_QA_STANDARD.md
## Style Registry and Sidecar System

### Style Registry
The unified style registry at `config/map_styles.json` defines complete visual profiles for every map family:
- Typography hierarchy (title, subtitle, legend, attribution font sizes and weights)
- Stroke styling (interior edges, boundary outlines)
- Label rules (threshold, font size, halo width and color)
- Legend formatting (position, frame alpha, separator)
- Chrome rules (basemap, scale bar, north arrow, inset locator)
- Figure dimensions (state-level vs local)

Cartography scripts read this registry before rendering. The registry ensures visual consistency across all maps in a project.

### Auto-Palette Resolution
The `domain_palette_map` in the style registry maps 50+ field name keywords to semantically appropriate palettes. When a cartography script receives a field name like `poverty_rate`, it auto-resolves to the `poverty` palette (YlOrRd, natural breaks, 5 classes).

Override auto-palette only when the context demands a different visual treatment. Document the override in the handoff.

### Style Sidecar
Every map PNG must have a companion `.style.json` sidecar recording:
- Map family
- Field name
- Palette name and colormap
- Classification method and class count
- Break values and RGB colors
- Title, legend title, attribution
- CRS and source GeoPackage

The QGIS packaging stage reads these sidecars to reproduce the same styling in the QGIS project file. This ensures the QGIS deliverable matches the static maps exactly.

### Enhanced Cartography Features
- **Label halos** (`--labels`): Feature labels with white halos for readability over dark fills. Auto-detects label field (NAME, NAMELSAD). Only applied when feature count is below the family's label threshold.
- **Inset locator map** (`--inset`): "You are here" context map in the upper-left corner. Shows the study area highlighted against a wider geographic context.
- **Pattern fills** (`--pattern`): Hatching patterns (///, xxx, ..., |||, etc.) for print accessibility and visual texture. Use when color alone is insufficient to distinguish classes.

Sources
Aileen Buckley (Esri) — five principles of cartographic design
John Nelson (Esri) — Adventures in Mapping; the "Defend" test
Edward Tufte — data-ink ratio principle
Cynthia Brewer — ColorBrewer palette guidance
Trust Level
Production Standard Human Review Required
