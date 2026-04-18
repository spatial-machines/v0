# Bivariate Choropleth Design Workflow

## Purpose

- design and produce a bivariate choropleth map that visualizes two related variables on the same polygons using a 2D color matrix
- inherit the firm's universal cartographic rules from `standards/CARTOGRAPHY_STANDARD.md` and apply them to the thematic choropleth family
- give the cartography agent a discipline for choosing when bivariate is the right tool and when small multiples or two single-variable choropleths would communicate better

## Map Family

This workflow produces a **thematic choropleth** (the bivariate variant). Per the family taxonomy in `standards/CARTOGRAPHY_STANDARD.md`:

- basemap: forbidden
- scale bar: forbidden
- north arrow: forbidden
- title, legend, attribution, dissolved outline: required

The bivariate variant inherits the thematic choropleth family rules. The legend is more demanding than a single-variable choropleth and is the most failure-prone part of the workflow.

## Typical Use Cases

- visualizing two related demographic indicators that interact (poverty rate × uninsured rate, vacancy rate × renter share)
- showing exposure × vulnerability for a risk analysis
- showing supply × demand for a market analysis
- showing two metrics whose joint distribution tells a story neither tells alone

## Inputs

- analysis-ready GeoDataFrame with both target variables on the same polygons
- both variables are rates, percentages, shares, or normalized metrics — NOT raw counts
- both variables share the same geography level (e.g., both at tract; do not mix tract with ZCTA)
- both variables share the same time period or vintage when interpretation depends on it
- project brief specifying audience and confirming bivariate is the appropriate tool for the audience

## Preconditions

- the two variables are conceptually related (the joint distribution must mean something)
- both variables passed structural QA per `standards/STRUCTURAL_QA_STANDARD.md`
- CRS confirmed per `standards/CRS_SELECTION_STANDARD.md`
- the audience is familiar enough with bivariate maps to interpret a 2D legend, OR the report carries enough explanatory text to guide first-time readers
- the analyst has considered whether small multiples or two side-by-side single-variable choropleths would communicate better; bivariate is chosen because the joint distribution is the story

## Preferred Tools

- GeoPandas + matplotlib for static output
- canonical core scripts under `scripts/core/` for production runs

## Execution Order

1. **Confirm both variables are normalized.** A bivariate choropleth on raw counts produces a population-density artifact for both axes. Both variables must be rates, percentages, or shares.
2. **Confirm bivariate is the right tool.** If the variables are weakly related, two side-by-side single-variable choropleths may communicate better. If the audience is unfamiliar with bivariate maps, small multiples may be safer. The "Defend test" from the cartography standard applies: defend the bivariate choice or use a different visualization.
3. **Confirm the family.** The map is a thematic choropleth (bivariate variant). Apply the `CARTOGRAPHY_STANDARD.md` family rules (no basemap, no scale bar, no north arrow).
4. **Choose the matrix size.** 2×2 is simplest and most accessible (4 cells; "low/low", "low/high", "high/low", "high/high"). 3×3 is the firm's standard (9 cells, with a meaningful middle category for each axis). 4×4 and larger are visually overwhelming and should not be used without strong justification.
5. **Choose the bivariate color scheme.** Standard bivariate palettes (purple-orange, teal-pink, blue-yellow) are the firm default. Avoid red-green pairs for colorblind accessibility per the cartography standard. Each axis must read as a sequential ramp on its own.
6. **Construct the bivariate classification.** Common methods: joint quantiles (each axis split at the same percentiles, typically tertiles for 3×3), joint natural breaks per variable, or manual classification when defending against thresholds. Document the method used. The classification breaks for each variable must be applied independently before joining into the bivariate cell.
7. **Apply the standard's border rules.** Thin (0.2 mm) white tract borders. Add a dissolved outer outline (0.35 mm, medium gray) on top.
8. **Construct the bivariate legend.** This is the most failure-prone part. The legend is a 2D color matrix (matching the matrix size from step 4) with both variable names labeled along the corresponding axes. Each axis is labeled with the variable name AND the unit ("Poverty Rate (%)" not "poverty"). Both axes are labeled with their direction (low → high). The legend size should be proportional to the map's other elements; a too-small bivariate legend is unreadable.
9. **Set title and attribution** per the standard. The title must name **both** variables, the geography, and the time period. Attribution cites both data sources with vintages.
10. **Add a "no data" category** for any features missing one or both variables. The bivariate cell for missing data is medium gray (#d0d0d0), distinct from any cell in the matrix.
11. **Save at the family's numeric defaults.** DPI 200 preferred (150 minimum), figure size 14×10 for state-level or 12×10 for local-area framings. Bivariate maps may need extra horizontal space for the legend.
12. **Run `qa-review/MAP_QA_CHECKLIST.md`** before declaring the map complete.

## Validation Checks

- both variables are normalized metrics, not raw counts
- both variables are at the same geography level and (where relevant) the same time period
- the family is thematic choropleth and the family rules are respected
- the matrix size is 2×2 or 3×3 (4×4+ requires explicit defense)
- the bivariate color scheme is sequential along each axis individually
- the colorblind accessibility check passes (no red-green-only pair)
- the classification method is documented and applied independently per variable before joining
- the legend is a 2D color matrix with both axes labeled with variable names AND units AND directions
- the legend is large enough to read at the display size
- a "no data" cell is shown when features have missing values for either variable
- the title names both variables, the geography, and the time period
- attribution cites both source datasets with vintages
- DPI and figure size meet the family defaults
- `MAP_QA_CHECKLIST.md` has been run

## Common Failure Modes

- mapping raw counts on either axis, producing a bivariate population-density artifact
- 4×4 or larger matrix that no first-time viewer can interpret
- bivariate scheme used for two unrelated variables; the joint distribution carries no meaning
- legend that does not label both axes with variable names, units, and direction
- legend too small to read; the 2D matrix becomes a colored square the viewer cannot interpret
- one variable visually dominates (the chosen color ramp for one axis is much higher contrast than the other)
- using a bivariate scheme that is hostile to colorblind viewers (red/green axes)
- classification method that is different per variable without justification
- no "no data" category when features have null values for either variable
- title naming only one variable
- presenting a bivariate as showing causation rather than joint distribution
- bivariate is used when small multiples or two side-by-side single-variable choropleths would have communicated more clearly to the actual audience

## Escalate When

- the project audience is unfamiliar with bivariate maps and the report cannot carry enough explanatory text
- the two variables are not actually related and the bivariate choice does not survive the "Defend test"
- one variable's distribution dominates the visual and the joint pattern cannot be read
- the analyst is considering a 4×4 or larger matrix
- the topic is politically or commercially sensitive and the joint visualization could mislead
- the reviewer asks for a side-by-side single-variable comparison instead

## Outputs

- a static PNG bivariate choropleth at the family's DPI and figure size
- the map's classification metadata for each variable AND the bivariate cell mapping recorded for reproducibility
- the legend as a discrete artifact in addition to its embedding in the map (so it can be reused in reports)

## Related Standards

- `standards/CARTOGRAPHY_STANDARD.md` — universal design rules and the family taxonomy this workflow inherits from
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition for both variables
- `standards/PUBLISHING_READINESS_STANDARD.md` — downstream gate before client delivery

## Related Workflows

- `workflows/CHOROPLETH_DESIGN.md` — single-variable alternative; consider this first
- `workflows/POINT_OVERLAY_DESIGN.md` — when one of the two variables is a point dataset rather than a polygon attribute
- `workflows/HOTSPOT_MAP_DESIGN.md` — when the relationship is about clustering rather than joint distribution
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — common upstream stage producing the joined two-variable dataset
- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — earlier upstream stage

## Related QA

- `qa-review/MAP_QA_CHECKLIST.md` — operational cartographic checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative-side review (especially relevant for bivariate maps because of the joint-distribution interpretation risk)

## Sources

- firm cartographic methodology
- the cartography standard's source list (Buckley, Nelson, Tufte, Brewer)
- Joshua Stevens — "Bivariate Choropleth Maps: A How-to Guide" (Brewer color schemes for bivariate)

## Trust Level

Validated Workflow — Needs Testing
