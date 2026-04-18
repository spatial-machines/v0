# Service Area and Travel-Time QA Checklist

Purpose:
provide a dedicated review checklist for service-area polygons, drive-time isochrones, and any output where travel-time or travel-distance claims are made
catch the specific failures that arise from routing-engine assumptions, network data quality, and enrichment allocation
validate travel-time outputs before they are used in coverage analysis, trade-area work, site comparison, or client delivery

Use When
Use this checklist when reviewing any output that includes:
- drive-time isochrones or travel-distance polygons
- service-area coverage claims (population within X minutes)
- labor-shed or commute-shed delineation
- trade-area boundaries based on travel time
- facility coverage or gap analysis using network-based access
- any map or table that quotes travel-time thresholds as boundaries

Do Not Use When
Do not use this checklist for:
- Euclidean buffer outputs with no travel-time claim (use `qa-review/STRUCTURAL_QA_CHECKLIST.md`)
- demographic enrichment not tied to a service area (use `qa-review/STRUCTURAL_QA_CHECKLIST.md`)
- spatial statistics outputs (use `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md`)
- map-level cartographic review (use `qa-review/MAP_QA_CHECKLIST.md` in addition to this page)

Core Review Checks

## Routing Engine and Network Documentation

- the routing engine is named (OSRM, Valhalla, pgRouting, openrouteservice, or other)
- the routing engine version or instance is documented
- the network data source is documented (OSM extract date, TIGER vintage, or other)
- the travel mode is stated explicitly (driving, walking, cycling, transit)
- speed assumptions or profile settings are documented (default profile vs. custom)
- any known network limitations are noted (missing local roads, no turn restrictions, no real-time traffic, no elevation penalties)

## Threshold and Parameter Validation

- the travel-time or travel-distance thresholds match the project-approved specification
- the threshold units are correct and explicit (minutes vs. miles vs. kilometers)
- departure time assumptions are documented if the engine supports time-of-day variation
- if multiple thresholds were used (e.g., 5, 10, 15 minutes), all are present and correctly labeled
- generalization tolerance (polygon simplification) is documented and does not distort the result

## Isochrone Shape Plausibility

- service-area polygons follow road-network corridors rather than forming circular or near-circular shapes
- if shapes appear circular, investigate whether the routing engine loaded the network correctly
- polygons extend further along highways and less into areas with sparse road networks (expected behavior)
- service areas for similar sites in similar road environments produce similar-scale polygons
- no isochrones are missing (all input sites produced a result, or failures are documented)
- polygons do not have obvious artifacts (spikes, gaps, or islands that do not correspond to real network features)

## CRS and Geometry Integrity

- the CRS is documented and appropriate for the study area
- service-area polygons are geometrically valid (`ST_IsValid` or `.is_valid` passes)
- polygon boundaries do not extend obviously beyond plausible travel extent
- if the routing engine returns geographic coordinates, the result was handled correctly before area calculations

## Enrichment Allocation

- the enrichment method for partial-overlap geographies (tracts, blocks) is documented
- acceptable methods: area-weighted interpolation, population-weighted allocation, or centroid containment with documentation
- the allocation method is appropriate for the metric type (additive counts vs. rates vs. medians per `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`)
- enrichment totals are plausible for the geography and threshold (e.g., population within a 10-minute drive in a rural area should not match an urban count)
- enrichment layers are CRS-aligned with the service-area polygons before spatial operations

## Travel-Time Claim Framing

- travel-time boundaries are described as modeled estimates, not precise edges
- the output does not imply real-time traffic conditions unless the engine actually uses them
- coverage claims distinguish between "within X minutes under modeled conditions" and "guaranteed reachable in X minutes"
- if the output is used for coverage-gap claims, the inverse areas (outside the service area) are also plausible

## Cross-Site Comparison Consistency

- all sites were analyzed with the same routing engine, network data, mode, and threshold settings
- any site-to-site differences in service-area size are explained by road-network differences, not by parameter inconsistency
- comparison tables and maps use the same enrichment method across all sites

Escalate When
- the routing engine's network data is visibly incomplete for the study area (missing major roads, disconnected components)
- isochrone results differ by more than 20% from a manual spot-check with the same routing engine
- the client requires real-time traffic, time-of-day, or congestion-sensitive analysis
- the analysis involves transit travel time (network data quality and schedule currency require additional validation)
- the output will be used for regulatory, legal, or compliance purposes
- isochrone results differ materially from a proprietary benchmark (Esri Network Analyst, Google Maps) and the difference is not explained by method
- partial-tract enrichment inflates population or POI counts beyond plausibility

Common Failure Modes
- not documenting the routing engine, network vintage, or speed profile
- generating isochrones from a stale or incomplete network extract
- confusing drive-time (minutes) with drive-distance (miles or kilometers)
- using Euclidean buffers when network-based service areas were specified
- treating isochrone boundaries as precise lines rather than modeled approximations
- partial-tract enrichment without allocation method, double-counting population in overlapping zones
- presenting travel-time estimates as if they include real-time traffic when the engine uses free-flow or static speeds
- comparing service areas across sites generated with inconsistent parameters
- not checking that all input sites produced a valid isochrone (silent failures)

Relationship to Other QA Pages
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — run first for general data integrity of inputs and outputs
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — run after for narrative claims about coverage, access, or reachability
- `qa-review/MAP_QA_CHECKLIST.md` — run for the cartographic side of any service-area map
- `qa-review/POI_EXTRACTION_QA.md` — when service areas are enriched with POI counts

Governing Workflows
- `workflows/SERVICE_AREA_ANALYSIS.md` — the primary workflow this checklist validates
- `workflows/GEOCODE_BUFFER_ENRICHMENT.md` — site preparation upstream of service-area generation
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — demographic enrichment within service areas

Governing Standards
- `standards/CRS_SELECTION_STANDARD.md` — CRS discipline for spatial operations
- `standards/SOURCE_READINESS_STANDARD.md` — readiness of network and enrichment inputs
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — enrichment allocation rules
- `standards/OPEN_EXECUTION_STACK_STANDARD.md` — preferred routing engine stack

Trust Level
Validated QA Page
