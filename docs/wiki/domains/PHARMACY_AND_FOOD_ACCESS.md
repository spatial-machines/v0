# Pharmacy and Food Access Domain

Purpose:
provide a navigation and cross-linking page for pharmacy, grocery, and basic-needs access analysis built from facility context, demographic need, and accessibility workflows
help analysts and agents route recurring food-access and pharmacy-access questions into the correct reusable canon
define the current reusable canon coverage for access-to-resource questions without claiming a dedicated food-desert or pharmacy-equity methodology the firm has not yet formalized

## Domain Scope

This domain covers recurring analysis where the question is whether people can reach pharmacies, grocery stores, or other everyday resource locations.

It includes:
- pharmacy and grocery access baselines
- site and network access to essential-service locations
- demographic context for resource access questions
- POI extraction and normalization for pharmacy or food locations
- delivery and review routing for access findings

It does not include:
- formal public-health methodology ownership (see `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`)
- broader retail and competitor landscape ownership (see `domains/POI_AND_BUSINESS_LANDSCAPE.md`)
- transit-specific food access methodology
- nutrition, public-health outcomes, or food-system causal inference

## Common Questions

- how far are residents from pharmacies or grocery stores?
- which populations fall outside common access thresholds?
- how should pharmacy or food-service location inventories be cleaned before analysis?
- when is a simple buffer appropriate versus a network-based service area?
- how do demographic context and resource locations get combined into one defensible output?

## Common Workflow Sequences

### Sequence 1: pharmacy or grocery access baseline

1. retrieve or intake location data through `domains/POI_AND_BUSINESS_LANDSCAPE.md`
2. prepare demographic context through `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
3. use `workflows/SERVICE_AREA_ANALYSIS.md` or `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
4. validate with `qa-review/POI_EXTRACTION_QA.md` and `qa-review/STRUCTURAL_QA_CHECKLIST.md`

### Sequence 2: site-based access review

1. prepare anchor sites through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
2. retrieve pharmacy or food-service locations with `workflows/POSTGIS_POI_LANDSCAPE.md`
3. normalize categories through `workflows/POI_CATEGORY_NORMALIZATION.md` if needed
4. choose Euclidean or network access workflow based on the project question
5. review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

### Sequence 3: resource access delivery workflow

1. complete the access workflow and supporting demographic enrichment
2. validate structural and interpretive quality
3. use `domains/CARTOGRAPHY_AND_DELIVERY.md` for maps, review-site publishing, or package handoff

## Key Standards for This Domain

- `standards/SOURCE_READINESS_STANDARD.md` — readiness of pharmacy, grocery, and demographic inputs
- `standards/CRS_SELECTION_STANDARD.md` — projected CRS discipline for buffers and access analysis
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — summary handling when access outputs are aggregated
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred open-stack execution path

## Key Workflows for This Domain

- `workflows/POSTGIS_POI_LANDSCAPE.md` — pharmacy and grocery location extraction
- `workflows/POI_CATEGORY_NORMALIZATION.md` — category cleanup for essential-service locations
- `workflows/SERVICE_AREA_ANALYSIS.md` — network-based access workflow
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md` — Euclidean access workflow
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation and buffer-based enrichment
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — tract-level demographic context enrichment

## Key QA Pages for This Domain

- `qa-review/POI_EXTRACTION_QA.md` — extraction plausibility review
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural output checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — review of access claims and equity framing
- `qa-review/MAP_QA_CHECKLIST.md` — review for public-facing access maps

## Key Data Sources for This Domain

- `data-sources/LOCAL_POSTGIS.md` — local facility and resource extraction support
- `data-sources/OSM.md` — OSM-backed location context
- `data-sources/CENSUS_ACS.md` — demographic context and tract-level indicators
- `data-sources/TIGER_GEOMETRY.md` — tract and boundary geometry for enrichment and delivery
- `data-sources/LOCAL_FILES.md` — client-supplied pharmacy or grocery inventories
- `data-sources/REMOTE_FILES.md` — downloadable resource-location tables

## Key Toolkits for This Domain

- `toolkits/POSTGIS_TOOLKIT.md` — larger-scale extraction and spatial summaries
- `toolkits/GEOPANDAS_TOOLKIT.md` — joins, packaging, and lighter-weight enrichment
- `toolkits/GDAL_OGR_TOOLKIT.md` — conversion and output support

## Cartographic Composition for Food/Pharmacy Access Maps

When the cartography agent builds a delivery map for food or pharmacy
access, the reference layers shown must support the causal story, not
just decorate the map. Default overlay stack (top-to-bottom z-order):

1. **Primary facility overlay** — the supermarkets, pharmacies, or
   retailers themselves (from OSM, Overture, SNAP Retailer Locator, or
   client inventory). This is non-negotiable: you cannot visualize
   *access to a resource* without showing the resource. Use
   `scripts/core/layers/add_points_layer.py`.

2. **Transit overlay (optional but recommended for urban analyses)** —
   bus/rail lines and stations. A food-access map in a transit-rich
   city without transit shown is misleading because transit changes
   who is cut off. Use OSM `railway=subway|light_rail|tram|rail` or
   GTFS feeds via `scripts/core/fetch_gtfs.py`.

3. **Place labels** — neighborhoods/cities (`add_place_labels.py`).
   Readers need orientation.

4. **Callouts** — top-N tracts with multivariate context (poverty,
   income, score). Labels must use human-readable names (neighborhood,
   community area), not FIPS codes.

5. **Inset locator** — study area within state (margin, not overlap).

**Do NOT include by default:**

- **Hydrography/water features** — water is irrelevant to food access
  unless the analysis is about a coastal/island population cut off by
  water. The basemap's faint water rendering is sufficient context.
  Don't force blue lakes onto a food-desert map just to make it look
  "complete."
- **Parks and open space** — unless the analysis explicitly involves
  park food programs or farmers markets held there.
- **Administrative boundaries** (school districts, wards) — only if
  the narrative specifically uses them.

The principle: every reference layer must answer "what does this tell
the reader about *food access*?" If the answer is nothing, leave it off.

## Domain-Specific Caveats

- category normalization strongly affects what counts as a pharmacy, grocery, or food-access point
- access metrics can look objective while hiding important assumptions about travel mode, threshold, and source quality
- food-access and pharmacy-access narratives can drift into policy claims unless interpretation stays tethered to the actual workflow outputs
- open-source resource-location data often needs validation before being treated as a defensible inventory
- reference-layer selection for delivery maps is an analytical choice — adding water or terrain layers to a food-access map because "every map should have them" is amateur cartography

## Known Gaps in Current Canon

- there is no dedicated pharmacy-specific or food-access-specific standard yet
- no first-class transit-based food/pharmacy access workflow exists yet
- there is no dedicated review checklist for essential-service access beyond the general POI, structural, and interpretive layers
- branded-chain handling and specialized resource taxonomy rules remain a broader POI governance gap

## Adjacent Domains

- `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/CARTOGRAPHY_AND_DELIVERY.md`

## Trust Level

Validated Domain Page
