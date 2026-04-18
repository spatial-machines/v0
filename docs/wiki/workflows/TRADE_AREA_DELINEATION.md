# Trade-Area Delineation Workflow

Purpose:
define a repeatable process for delineating trade areas around retail, service, or facility locations
produce trade-area polygons enriched with demographic and business-landscape context
support trade-area comparison, penetration framing, and downstream site-selection or competitor analysis

Typical Use Cases
- what is the primary trade area for this retail location?
- how do trade areas compare across candidate sites?
- what demographic and competitive context exists within each trade area?
- how should a trade area be defined when customer-origin data is not available?

Inputs
- geocoded site or facility points (validated per `workflows/GEOCODE_BUFFER_ENRICHMENT.md`)
- approved trade-area method (drive-time, distance, or manual boundary)
- approved thresholds (e.g., 5/10/15-minute drive, 1/3/5-mile radius)
- approved enrichment layers (demographic, POI, competitor)
- project-approved working CRS
- customer-origin data if available (address list, transaction records, loyalty data)

Preconditions
- site points are geocoded and validated
- the CRS has been confirmed per `standards/CRS_SELECTION_STANDARD.md`
- the trade-area method is explicitly approved (do not default to a method without project guidance)
- if drive-time is the method, a routing engine is available and documented per `workflows/SERVICE_AREA_ANALYSIS.md`
- enrichment layers are confirmed available and source-ready per `standards/SOURCE_READINESS_STANDARD.md`

Preferred Tools
- OSRM, Valhalla, pgRouting, or openrouteservice for drive-time trade areas (per `standards/OPEN_EXECUTION_STACK_STANDARD.md`)
- GeoPandas for distance-based trade areas and enrichment (`toolkits/GEOPANDAS_TOOLKIT.md`)
- PostGIS for scale and spatial query work (`toolkits/POSTGIS_TOOLKIT.md`)

Execution Order

## Phase 1: Trade-Area Method Selection

Confirm the trade-area method with the project lead. The three common methods, in order of increasing data requirements:

**Method A — Distance-based (simplest)**
Use `workflows/WITHIN_DISTANCE_ENRICHMENT.md` to generate Euclidean buffers at approved radii.
Appropriate when: the road network is relatively uniform, the question is about nearby context rather than precise reachability, or the project scope does not justify routing-engine setup.

**Method B — Drive-time-based (most common)**
Use `workflows/SERVICE_AREA_ANALYSIS.md` to generate network-based isochrones at approved travel-time thresholds.
Appropriate when: the question is about how far customers will actually drive, the road network varies (urban vs. rural, highway vs. local), or the deliverable requires drive-time language.

**Method C — Customer-origin-based (strongest, requires data)**
Use customer address or transaction data to define the empirical trade area from observed behavior.
This method is not yet a first-class workflow — execute it as a project-level process using geocoding, spatial joins, and convex hull or density-based boundary methods, and document the approach.
Appropriate when: customer-origin data is available and the project requires an empirically grounded trade area rather than a modeled one.

Document the chosen method and the rationale.

## Phase 2: Trade-Area Generation

For Method A:
1. Reproject site points to the working CRS.
2. Generate buffers at each approved radius using `workflows/WITHIN_DISTANCE_ENRICHMENT.md`.
3. Confirm buffer geometry is valid and units are correct.

For Method B:
1. Follow `workflows/SERVICE_AREA_ANALYSIS.md` Phase 1 through Phase 2.
2. Generate isochrones at each approved threshold.
3. Validate isochrone shape plausibility (should follow road corridors, not circular).

For Method C:
1. Geocode customer addresses through `workflows/GEOCODE_BUFFER_ENRICHMENT.md`.
2. Assign customers to the nearest site.
3. Generate trade-area boundary (convex hull, concave hull, or density-based polygon encompassing a target percentage of customers, e.g., 70% or 80%).
4. Document the boundary method and the customer-coverage percentage.

## Phase 3: Demographic Enrichment

1. Load tract geometry and ACS data per `workflows/TRACT_JOIN_AND_ENRICHMENT.md`.
2. Intersect trade-area polygons with tract geometry.
3. For partial tract overlaps, apply area-weighted or population-weighted allocation per `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`.
4. Compile demographic summaries per trade area (population, households, income, age distribution, or other approved variables).

## Phase 4: Business-Landscape Enrichment

1. Extract POIs within each trade area using `workflows/POSTGIS_POI_LANDSCAPE.md`.
2. Normalize categories with `workflows/POI_CATEGORY_NORMALIZATION.md`.
3. Count and categorize relevant businesses, competitors, and amenities.
4. Validate with `qa-review/POI_EXTRACTION_QA.md`.

## Phase 5: Validation

1. Validate trade-area geometry with `qa-review/STRUCTURAL_QA_CHECKLIST.md`.
2. Validate travel-time outputs with `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md` (for Method B).
3. Review enrichment plausibility: are population counts, POI counts, and competitor counts reasonable for the geography and threshold?
4. Review interpretive framing with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — trade-area boundaries are modeled, not natural market edges.

## Phase 6: Output

1. Package trade-area polygons, demographic summaries, and business-landscape summaries.
2. If comparing trade areas across sites, produce a standardized comparison table.
3. Generate map-ready layers and route through `domains/CARTOGRAPHY_AND_DELIVERY.md`.
4. Document: method, thresholds, routing engine (if applicable), enrichment sources, allocation method, and any limitations.

Validation Checks
- trade-area method is documented and matches the project-approved approach
- thresholds match the approved specification (time, distance, or customer-coverage percentage)
- for drive-time trade areas, routing engine and network vintage are documented
- enrichment allocation method for partial tracts is documented
- demographic and POI counts are plausible for the geography
- trade-area boundaries are described as modeled estimates, not definitive market edges
- for customer-origin trade areas, the boundary method and coverage percentage are documented

Common Failure Modes
- defaulting to a trade-area method without explicit project approval
- using Euclidean buffers when drive-time was specified (or vice versa)
- not documenting the routing engine for drive-time trade areas
- partial-tract enrichment without allocation, inflating population counts
- presenting modeled trade-area boundaries as if they represent actual customer behavior
- comparing trade areas generated with different methods or thresholds as if they were equivalent
- not validating POI extraction within trade areas (double-counting, category errors)
- claiming market penetration or share without a signed-off penetration methodology

Escalate When
- the client requires a specific trade-area methodology (Huff model, gravity model, Reilly's law) that is not yet a wiki-standardized workflow
- customer-origin data introduces privacy or confidentiality concerns
- the trade-area output will be used for financial, investment, or legal purposes
- drive-time results differ materially from a proprietary benchmark
- the project requires penetration or market-share calculation (this workflow delineates the area; penetration methodology is a separate future gap)

Outputs
- trade-area polygons per site per threshold
- demographic enrichment summary per trade area
- business-landscape summary per trade area
- comparison table across sites if applicable
- methodology documentation (method, thresholds, engine, sources, allocation)
- map-ready layers

Related Standards
- `standards/CRS_SELECTION_STANDARD.md`
- `standards/SOURCE_READINESS_STANDARD.md`
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`
- `standards/OPEN_EXECUTION_STACK_STANDARD.md`

Related Workflows
- `workflows/SERVICE_AREA_ANALYSIS.md`
- `workflows/WITHIN_DISTANCE_ENRICHMENT.md`
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md`
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
- `workflows/POSTGIS_POI_LANDSCAPE.md`
- `workflows/POI_CATEGORY_NORMALIZATION.md`
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`

Related QA
- `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md`
- `qa-review/STRUCTURAL_QA_CHECKLIST.md`
- `qa-review/POI_EXTRACTION_QA.md`
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

Sources
- Huff model (gravity-based trade-area method): academic reference, not yet implemented in wiki canon
- Reilly's Law of Retail Gravitation: academic reference, not yet implemented
- OSRM documentation (https://project-osrm.org)
- Valhalla documentation (https://valhalla.github.io/valhalla/)

Trust Level
Draft Workflow Needs Testing
