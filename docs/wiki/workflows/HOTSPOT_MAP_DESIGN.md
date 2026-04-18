# Hotspot Map Design Workflow

## Purpose

- design and produce a cartographic representation of a hotspot or cluster analysis result (Getis-Ord Gi* or Local Moran's I / LISA)
- inherit the firm's universal cartographic rules from `standards/CARTOGRAPHY_STANDARD.md` and apply them to the thematic categorical family
- own the **rendering** side of hotspot output; the **analytic** side is owned by `standards/SPATIAL_STATS_STANDARD.md`

## Map Family

This workflow produces a **thematic categorical** map. Per the family taxonomy in `standards/CARTOGRAPHY_STANDARD.md`:

- basemap: forbidden
- scale bar: forbidden
- north arrow: forbidden
- title, legend, attribution, dissolved outline: required

The thematic categorical family forbids chrome elements because the colored polygons are the visual story; chrome competes with the cluster pattern.

## Boundary with Spatial Stats Canon

This workflow does not run the analysis. It assumes the analysis is already complete and validated:

- `standards/SPATIAL_STATS_STANDARD.md` defines when hotspot analysis is appropriate, the Moran's I gate, the spatial weights rule, the multiple-comparisons-correction rule, and the required reporting template
- `workflows/SPATIAL_AUTOCORRELATION_TEST.md` is the gate procedure
- `workflows/HOTSPOT_ANALYSIS.md` is the analytic procedure for Gi*
- `workflows/LISA_CLUSTER_ANALYSIS.md` is the analytic procedure for LISA

This page covers what to do **after** those workflows produce a classified output. Do not redefine the analytic preconditions on this page; defer to the spatial stats standard.

## Typical Use Cases

- visualizing a Getis-Ord Gi* result (hot spots and cold spots at multiple confidence levels)
- visualizing a Local Moran's I (LISA) result (HH / LL / HL / LH cluster types)
- presenting clustering findings to a client or stakeholder
- producing a publication-ready hotspot map for a report or review site

## Inputs

- a GeoDataFrame with a per-feature significance classification produced by `compute_hotspots.py` or `compute_spatial_autocorrelation.py`
- the spatial stats handoff JSON documenting the Global Moran's I result, the weights type, the multiple-comparisons correction, and the corrected significant feature counts
- project brief specifying audience, geography, time period, and delivery format

## Preconditions

- the `standards/SPATIAL_STATS_STANDARD.md` Moran's I gate has passed (significant positive autocorrelation); if the gate failed, do not produce a hotspot map
- spatial weights are documented and consistent with the analysis (binary for Gi*, row-standardized for LISA)
- multiple-comparisons correction has been applied per the spatial stats standard
- the per-feature significance classification field exists in the input dataset
- CRS confirmed per `standards/CRS_SELECTION_STANDARD.md`
- structural QA passed per `standards/STRUCTURAL_QA_STANDARD.md`

## Preferred Tools

- GeoPandas + matplotlib for static output
- canonical core scripts under `scripts/core/` for production runs

## Execution Order

1. **Confirm the analytic preconditions are met.** Read the spatial stats handoff and verify the Moran's I gate passed and multiple-comparisons correction was applied. If either is missing, halt and return to the spatial stats canon for resolution.
2. **Confirm the family.** The map is a thematic categorical map. Apply the `CARTOGRAPHY_STANDARD.md` family rules (no basemap, no scale bar, no north arrow). Do not import chrome from other families.
3. **Choose the color taxonomy** based on the analysis type:
   - **Gi*** uses a diverging categorical scheme. Hot spots in red ramp (darkest red for 99% confidence, mid red for 95%, light red for 90%). Cold spots in blue ramp (darkest blue for 99%, mid blue for 95%, light blue for 90%). "Not significant" features in medium gray (#e0e0e0 or similar).
   - **LISA** uses four cluster categories plus a not-significant class. HH (true hot spot) in red. LL (true cold spot) in blue. HL (high outlier) in light red or pink. LH (low outlier) in light blue. "Not significant" in medium gray.
4. **Plot each significance class as a separate layer** for a clean legend. Iterating per class avoids matplotlib's auto-legend producing an inscrutable continuous color bar.
5. **Order the legend deliberately.** For Gi*: hot spot 99% → 95% → 90% → not significant → cold spot 90% → 95% → 99%. For LISA: HH → HL → not significant → LH → LL. The "not significant" class always appears in the middle, not at the top or bottom, so it does not visually anchor the reader's attention.
6. **Apply the standard's border rules.** Thin (0.2 mm) white tract borders. Add a dissolved outer outline (0.35 mm, medium gray) on top.
7. **Set title and attribution** per the standard. The title must name **both** the underlying metric and the analysis type, e.g., "Getis-Ord Gi* Hot Spot Analysis of Median Income, Tracts, ACS 5-Year 2018-2022". A title that names only the metric obscures that the map shows clusters, not raw values.
8. **Save at the family's numeric defaults.** DPI 200 preferred (150 minimum), figure size 14×10 for state-level or 12×10 for local-area framings.
9. **Run `qa-review/MAP_QA_CHECKLIST.md`** before declaring the map complete.

## Validation Checks

- the spatial stats Moran's I gate passed and is documented in the handoff this map references
- multiple-comparisons correction is documented and the corrected significant feature count is reported alongside the map
- the family is thematic categorical and the family rules are respected (no basemap, no scale bar, no north arrow)
- the color taxonomy uses diverging categorical (red/gray/blue or HH/LL outlier ramp), not sequential
- "not significant" features are styled with a clearly distinct gray (not the lightest hot or coldest blue)
- legend ordering follows the convention (Gi*: hot → not significant → cold; LISA: HH → HL → not significant → LH → LL)
- legend categories are labeled with their significance level or cluster type (not raw codes)
- title names both the underlying metric and the analysis type
- attribution cites the source data with vintage AND the spatial stats method (Gi* or LISA) with the weights type and correction method
- "not significant" features are visible on the map but visually subordinate to the significant clusters
- DPI and figure size meet the family defaults
- `MAP_QA_CHECKLIST.md` has been run

## Common Failure Modes

- producing a hotspot map for data that failed the Moran's I gate (the most consequential failure; the map will look meaningful but the underlying signal is noise)
- styling "not significant" tracts with a color that makes them look significant (e.g., light red rather than gray)
- using a sequential palette instead of a diverging categorical scheme (loses the hot/cold distinction)
- mixing Gi* significance levels with LISA cluster types in the same legend
- omitting the "not significant" class entirely, so the map shows only colored clusters with white gaps that the viewer cannot interpret
- adding a basemap or chrome despite the family rules
- title naming only the underlying metric, so the viewer thinks they are looking at a choropleth of values rather than a clustering result
- legend order that anchors the reader's eye on "not significant" (top or bottom of legend) instead of placing it in the middle
- using the cartography standard's choropleth border treatment without realizing this is a different family
- cherry-picking the significance threshold to produce a more visually compelling pattern (e.g., dropping from 95% to 90% to make more clusters appear)

## Escalate When

- the underlying spatial stats run does not have a documented Moran's I gate result
- the gate failed but the project brief still expects a clustering deliverable
- the topic is politically or commercially sensitive and the cluster pattern could mislead
- the corrected significant feature count is very small (single-digit) and a hotspot map may overstate the finding
- the audience is unfamiliar with hotspot analysis and an alternative visualization (filtered choropleth, ranked table) would communicate better
- the map will be used in a legal or regulatory context

## Outputs

- a static PNG hotspot or LISA map at the family's DPI and figure size
- the map's color taxonomy and significance threshold metadata recorded for reproducibility
- a reference to the spatial stats handoff that the map visualizes

## Related Standards

- `standards/CARTOGRAPHY_STANDARD.md` — universal design rules and the family taxonomy this workflow inherits from
- `standards/SPATIAL_STATS_STANDARD.md` — when to run hotspot or LISA analysis, the Moran's I gate, the weights rule, the FDR / Bonferroni rule, the required reporting template (the **analytic authority** for everything this workflow visualizes)
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — data integrity precondition

## Related Workflows

- `workflows/CHOROPLETH_DESIGN.md` — for cases where the Moran's I gate failed and a value choropleth is the appropriate fallback
- `workflows/SPATIAL_AUTOCORRELATION_TEST.md` — the Moran's I gate procedure
- `workflows/HOTSPOT_ANALYSIS.md` — the Gi* analytic procedure that produces the input dataset
- `workflows/LISA_CLUSTER_ANALYSIS.md` — the LISA analytic procedure that produces the input dataset

## Related QA

- `qa-review/MAP_QA_CHECKLIST.md` — operational cartographic checks
- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — analytic-side review for the underlying spatial stats output
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative-side review when the map is paired with prose claims

## Sources

- firm cartographic methodology
- the cartography standard's source list (Buckley, Nelson, Tufte, Brewer)
- the spatial stats standard's source list (Anselin, GeoDa, Esri Spatial Statistics)

## Trust Level

Validated Workflow — Needs Testing
