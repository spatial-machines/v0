# Coverage and Access Analysis QA Checklist

Purpose:
provide a dedicated review checklist for outputs that make claims about service coverage, facility access, or population within reach of infrastructure, providers, or public assets
catch the specific failures that arise from coverage modeling, access measurement, and underserved-area identification
validate coverage and access outputs before they are used in planning recommendations, policy support, or client delivery

This is a sector-family QA page that applies across multiple domains including healthcare access, emergency service coverage, public asset coverage, broadband access, transit access, and community facility planning.

Use When
Use this checklist when reviewing any output that includes:
- population-within-reach or population-served estimates
- coverage-gap or underserved-area identification
- facility service-area comparison across sites
- access equity screening (who is and is not covered)
- coverage claims for infrastructure, providers, or public services

Do Not Use When
Do not use this checklist for:
- travel-time polygon validation without coverage claims (use `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md`)
- general structural data integrity (use `qa-review/STRUCTURAL_QA_CHECKLIST.md`)
- cartographic review of coverage maps (use `qa-review/MAP_QA_CHECKLIST.md` in addition)
- market trade-area and competitor analysis (use `qa-review/MARKET_AND_TRADE_AREA_QA.md`)

Core Review Checks

## Facility and Provider Inventory

- the facility or provider list is documented: source, vintage, and completeness
- the inventory covers the correct geography and does not exclude relevant facilities
- facility types and categories are defined and consistent
- facilities with null or invalid geometry have been identified and handled
- the inventory has been checked against a rough completeness expectation (known facilities, online directories, or client confirmation)
- if the inventory comes from open sources (OSM, PostGIS), coverage gaps for the study area are documented

## Coverage Method

- the coverage method is documented: drive-time, distance buffer, administrative boundary, or other
- the coverage threshold is documented and project-approved (e.g., 10 minutes, 3 miles, within-jurisdiction)
- for drive-time coverage: the travel-time QA checklist (`qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md`) has been applied
- for distance coverage: the CRS is projected and the distance units are correct
- the distinction between "coverage" and "capacity" is clear — being within geographic reach of a facility does not guarantee service availability

## Population Estimation

- the method for estimating population within coverage areas is documented
- for partial-geography overlap (tracts partially within a service area): the allocation method is documented (area-weighted, population-weighted, or centroid containment)
- the allocation method is appropriate for the metric type per `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`
- population estimates are plausible for the geography and threshold
- if multiple coverage zones overlap, population is not double-counted

## Gap and Underserved-Area Identification

- "underserved" is defined explicitly: outside all coverage zones, or outside the nearest facility's zone, or below a threshold population-to-facility ratio
- the underserved definition is project-approved (not analyst-invented)
- gap areas are checked for plausibility: do they correspond to real population centers or only to sparsely populated areas?
- the output distinguishes between "outside coverage" and "underserved" — an area outside a 10-minute drive-time may still have adequate service if the threshold is conservative
- if equity framing is applied, demographic characteristics of gap areas are compared against covered areas with proper interpretive discipline

## Access Equity Framing

- if the output compares coverage across demographic groups, the comparison method is documented
- demographic variables used as vulnerability or equity indicators are named and sourced
- the output does not imply causation between demographic characteristics and coverage gaps
- the framing distinguishes between geographic access (proximity) and effective access (service availability, capacity, affordability, cultural competence)

## Coverage Claim Framing

- coverage claims are described as estimates based on modeled access, not guarantees of service
- the output does not conflate geographic coverage with service adequacy, quality, or capacity
- limitations of the coverage method are stated (routing assumptions, source completeness, facility list currency)
- if the output supports policy recommendations, the uncertainty in coverage estimates is noted

Escalate When
- the facility inventory has obvious gaps that could produce misleading coverage estimates
- coverage claims will be used for regulatory compliance, funding applications, or network adequacy determinations
- the underserved-area identification will be used to justify facility placement, closure, or investment decisions
- the coverage method differs from an established industry standard for the sector (e.g., CMS network adequacy standards for healthcare)
- equity findings could be interpreted as blaming communities rather than identifying systemic access barriers
- population estimates for partial geographies produce implausible totals

Common Failure Modes
- using an incomplete facility inventory and interpreting missing data as coverage gaps
- not documenting the coverage threshold or coverage method
- double-counting population in overlapping service areas
- partial-tract allocation without documentation, inflating or deflating population estimates
- conflating geographic proximity with service availability or capacity
- presenting Euclidean distance coverage when drive-time coverage was specified
- gap identification using an analyst-invented threshold rather than a project-approved standard
- equity framing that implies causation or blames communities for access disparities

Relationship to Other QA Pages
- `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md` — apply first for travel-time polygon validation
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — apply first for general data integrity
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — apply after for narrative claims about coverage and equity
- `qa-review/MAP_QA_CHECKLIST.md` — apply for cartographic review of coverage maps
- `qa-review/POI_EXTRACTION_QA.md` — apply when facility data comes from POI extraction
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — escalate when outputs support consequential decisions

Best-Fit Domains
- `domains/PUBLIC_HEALTH_AND_HEALTHCARE_ACCESS.md`
- `domains/PROVIDER_NETWORK_AND_CLINIC_ACCESS.md`
- `domains/PHARMACY_AND_FOOD_ACCESS.md`
- `domains/EMERGENCY_MEDICAL_SERVICE_COVERAGE.md`
- `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`
- `domains/COMMUNITY_FACILITY_PLANNING.md`
- `domains/PUBLIC_ASSET_INVENTORY_AND_SERVICE_COVERAGE.md`
- `domains/BROADBAND_AND_TELECOMMUNICATIONS_ACCESS.md`
- `domains/TRANSIT_ACCESS_AND_COVERAGE.md`

Trust Level
Validated QA Page
