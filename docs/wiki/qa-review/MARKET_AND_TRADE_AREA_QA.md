# Market and Trade-Area QA Checklist

Purpose:
provide a dedicated review checklist for trade-area delineation, market penetration framing, competitor gap screening, and retail or commercial market analysis outputs
catch the specific failures that arise from trade-area method choice, competitive landscape claims, and market opportunity framing
validate market and trade-area outputs before they are used in site selection, investment support, or client delivery

This is a sector-family QA page that applies across retail trade-area, competitor, economic development, workforce, and tourism-related market analysis.

Use When
Use this checklist when reviewing any output that includes:
- trade-area boundaries (drive-time, distance, or customer-origin)
- market penetration or market-share framing
- competitor density, gap screening, or white-space identification
- trade-area demographic or business-landscape enrichment
- commercial corridor or economic development market context
- site comparison based on trade-area characteristics

Do Not Use When
Do not use this checklist for:
- general service-area coverage not framed as market analysis (use `qa-review/COVERAGE_AND_ACCESS_ANALYSIS_QA.md`)
- general POI extraction not in a market context (use `qa-review/POI_EXTRACTION_QA.md`)
- spatial statistics outputs (use `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md`)

Core Review Checks

## Trade-Area Method

- the trade-area method is documented (drive-time, distance, customer-origin, or manual boundary)
- the method was project-approved, not analyst-defaulted
- the thresholds are documented and project-approved (time, distance, or customer-coverage percentage)
- if drive-time method: the travel-time QA checklist (`qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md`) has been applied
- if customer-origin method: the boundary method (convex hull, concave hull, density-based) and coverage percentage are documented
- the trade-area boundary is described as a modeled estimate, not a natural market edge

## Demographic Enrichment

- the enrichment method for partial-geography overlap is documented (area-weighted, population-weighted, or centroid containment)
- the enrichment method is appropriate for the metric type per `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`
- demographic totals within the trade area are plausible for the geography and threshold
- if comparing trade areas, all use the same enrichment method and demographic variables

## Competitor and Business-Landscape Context

- the competitor category definition is documented and project-approved
- the POI source and extraction date are documented
- competitor extraction has passed `qa-review/POI_EXTRACTION_QA.md`
- competitor counts are plausible: not obviously too low (source coverage gap) or too high (over-inclusive category)
- if competitor density is calculated, the denominator (per capita, per household, per area) is documented
- the output distinguishes between "competitor count" and "competitive intensity" — raw counts alone do not measure market saturation

## Gap and Opportunity Framing

- if white-space or gap zones are identified, the definition of "gap" is documented and project-approved
- the output does not treat low competitor density as proof of market opportunity without examining demand indicators
- the output acknowledges that low competitor presence may reflect low demand rather than unmet demand
- if thresholds are used for gap classification, they are project-approved, not analyst-invented
- the output does not make investment recommendations based solely on spatial gap screening

## Market Penetration and Share Claims

- if penetration or share language is used, the calculation method is documented
- the output distinguishes between "potential market" (population within the trade area) and "captured market" (actual customers, if data exists)
- if no customer-origin data exists, penetration claims are described as potential-based framing, not measured penetration
- the output does not imply precision in market-share estimates that the data does not support

## Cross-Site Comparison

- all sites being compared use the same trade-area method, thresholds, and enrichment approach
- differences between sites are attributable to geography and context, not to parameter inconsistency
- comparison tables present all dimensions side by side rather than implying a single winner
- if the comparison supports a site recommendation, the limitations of each dimension are stated

## Source and Method Documentation

- trade-area method and thresholds are documented
- routing engine and network data vintage are documented (for drive-time trade areas)
- demographic source and vintage are documented
- POI source and extraction date are documented
- enrichment allocation method is documented
- any limitations or known source gaps are noted

Escalate When
- the client requires a specific market-analysis methodology (Huff model, gravity model, analog model) not yet in the wiki canon
- the output will support investment, franchise, or real estate decisions
- customer-origin data introduces privacy or confidentiality concerns
- competitor category definitions are ambiguous and the resolution could materially change results
- the POI source has obvious coverage gaps that could create false white-space signals
- market-share or penetration claims exceed what the underlying data can support

Common Failure Modes
- not documenting the trade-area method or why it was chosen
- comparing trade areas generated with different methods or thresholds
- treating modeled trade-area boundaries as natural or precise market edges
- using incomplete POI data and interpreting missing competitors as market gaps
- inventing gap or opportunity thresholds without project approval
- presenting potential market as if it were captured market
- enrichment without allocation for partial-geography overlaps
- not checking that competitor categories match the project-approved definition

Relationship to Other QA Pages
- `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md` — apply for drive-time trade areas
- `qa-review/POI_EXTRACTION_QA.md` — apply for competitor and business-landscape extraction
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — apply for general data integrity
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — apply for narrative claims about market opportunity
- `qa-review/MAP_QA_CHECKLIST.md` — apply for cartographic review
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — escalate for investment or franchise decisions

Best-Fit Domains
- `domains/RETAIL_TRADE_AREA_AND_PENETRATION.md`
- `domains/COMPETITOR_AND_WHITE_SPACE_ANALYSIS.md`
- `domains/ECONOMIC_DEVELOPMENT_AND_CORRIDOR_ANALYSIS.md`
- `domains/WORKFORCE_AND_LABOR_SHED_ANALYSIS.md`
- `domains/TOURISM_HOSPITALITY_AND_VISITOR_ANALYSIS.md`
- `domains/SITE_SELECTION_AND_SUITABILITY.md`
- `domains/POI_AND_BUSINESS_LANDSCAPE.md`
- `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md`

Trust Level
Validated QA Page
