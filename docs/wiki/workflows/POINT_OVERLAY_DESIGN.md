# Point Overlay Design Workflow

## Purpose

- design and produce a map with point features overlaid on a thematic or context base, where the points are the subject and the base provides interpretive context
- inherit the firm's universal cartographic rules from `standards/CARTOGRAPHY_STANDARD.md` and apply them to the point overlay family

## Map Family

This workflow produces a **point overlay**. Per the family taxonomy in `standards/CARTOGRAPHY_STANDARD.md`:

- basemap: required (CartoDB.Positron or equivalent light tile basemap)
- scale bar: optional
- north arrow: optional
- title, legend, attribution, dissolved outline: required

The point overlay family requires a basemap because the points need geographic context to interpret their positions; scale bar and north arrow are optional unless the project brief calls for them.

## Typical Use Cases

- facility locations on a demographic context layer (hospitals, clinics, schools, libraries)
- competitor locations on a market characterization layer
- geocoded addresses on a thematic base (housing units, complaints, incidents)
- POI overlay on a tract demographic background
- buffer-enriched points where the buffer interaction is part of the story

## Inputs

- analysis-ready GeoDataFrame of point features with at minimum a name field for the most important points
- a polygon base layer (typically a thematic choropleth or a context layer)
- optional: a hierarchy field that distinguishes important points from secondary points (e.g., "trauma center" vs. "clinic")
- project brief specifying which points warrant labels

## Preconditions

- CRS confirmed per `standards/CRS_SELECTION_STANDARD.md` and consistent across the point layer and the base layer
- structural QA passed per `standards/STRUCTURAL_QA_STANDARD.md`
- the point dataset has been validated upstream
- if the base layer is a thematic choropleth, the choropleth itself satisfies `workflows/CHOROPLETH_DESIGN.md`

## Preferred Tools

- GeoPandas + matplotlib for static output, with `contextily` for the basemap layer
- Folium for interactive web map output
- canonical core scripts under `scripts/core/` for production runs

## Execution Order

1. **Confirm the family.** The map is a point overlay. Apply the `CARTOGRAPHY_STANDARD.md` family rules: basemap is required; scale bar and north arrow are optional per project brief.
2. **Prepare the polygon base.** If the base is a thematic choropleth, follow `workflows/CHOROPLETH_DESIGN.md` for the base layer. Allow the base to be slightly desaturated (alpha around 0.85) so the basemap shows through faintly and the points are visually dominant.
3. **Add the basemap** using a light, low-contrast tile source (CartoDB.Positron is the firm default). Reproject to Web Mercator for the basemap layer if needed; reproject for display only, not for analysis.
4. **Choose point symbology** that contrasts with the base. White circles with a dark edge work on almost any background. Marker size must be large enough to be visible at the display size — 60–80 pixels is the minimum for state-level overlays per the standard's legibility principle. Add an edge color (1–2 px) so points do not bleed into the background.
5. **Apply hierarchy** if some points matter more than others. Differentiate by size (larger for important) or by shape. Do not differentiate by color alone unless the project brief explicitly defines a categorical color scheme for the points.
6. **Label the most important points only.** The 5–10 most important points get text labels per the standard. Do not label every point. Use offset labels and a leader line if a label would otherwise collide with the marker.
7. **Add the dissolved outer outline** per the standard's border rules.
8. **Set title and attribution** per the standard. Title names the point class, the base context, and the geography.
9. **Optional: scale bar and north arrow** if the project brief calls for them or if distance / orientation context is part of the message.
10. **Save at the family's numeric defaults.** DPI 200 preferred, figure size 14×10 for state-level or 12×10 for local-area framings.
11. **Run `qa-review/MAP_QA_CHECKLIST.md`** before declaring the map complete.

## Validation Checks

- the family is point overlay and the family rules are respected (basemap present; scale bar and north arrow only if the project brief calls for them)
- the basemap is a light tile source that does not compete with the data layers
- point markers are large enough to see at the display size (60–80 px minimum)
- point markers have an edge color that prevents bleeding into the base
- only the most important points are labeled (5–10 maximum)
- labels do not overlap each other or the most important map features
- the polygon base layer is correct per its own family rules
- title names the point class and the base context
- attribution cites both the point source and the base layer source with vintages
- DPI and figure size meet the family defaults
- `MAP_QA_CHECKLIST.md` has been run

## Common Failure Modes

- point markers too small to see (the firm has shipped 12 px markers in the past; the lower bound is 60 px for state-level overlays)
- no edge color on points, so points bleed into the base and become invisible
- labeling every point on the map, producing label clutter that obscures the data
- labels that collide and become unreadable
- a busy basemap (street labels, road network, city names) that competes with the point and base layers
- using color to differentiate point importance without an explicit categorical legend
- the polygon base layer breaking its own family rules (a thematic choropleth base with chrome it should not have)
- mismatched CRS between the point layer and the base layer, producing visible misalignment
- title that names only the points and forgets the context layer

## Escalate When

- the project brief requires hundreds of point markers and the map becomes illegible (consider point clustering, hexbin, or a different visualization)
- the points fall partly or wholly outside the base layer's extent
- the audience is unfamiliar with the base layer's metric and the overlay risks misreading
- distance or geographic orientation is operationally important and the map's optional chrome (scale bar, north arrow) needs project-brief-level decisions
- the topic is politically or commercially sensitive

## Outputs

- a static PNG point overlay at the family's DPI and figure size
- optionally an interactive Folium web map with point popups for a review site
- the map's basemap source and point symbology metadata recorded for reproducibility

## Related Standards

- `standards/CARTOGRAPHY_STANDARD.md` — universal design rules and the family taxonomy this workflow inherits from
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements; matters more here because the basemap is in Web Mercator while the analysis CRS may be different
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition

## Related Workflows

- `workflows/CHOROPLETH_DESIGN.md` — produces the polygon base layer when the base is a thematic choropleth
- `workflows/HOTSPOT_MAP_DESIGN.md` — when points are overlaid on a clustering result
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — common upstream stage producing geocoded points
- `workflows/SERVICE_AREA_ANALYSIS.md` — common upstream stage when the points represent service centers

## Related QA

- `qa-review/MAP_QA_CHECKLIST.md` — operational checks applied to the finished map
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative-side review

## Sources

- firm cartographic methodology
- the cartography standard's source list (Buckley, Nelson, Tufte, Brewer)
- contextily documentation for basemap providers

## Trust Level

Validated Workflow — Needs Testing
