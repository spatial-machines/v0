# Hazard and Environmental Screening QA Checklist

Purpose:
provide a dedicated review checklist for hazard screening, environmental justice screening, flood exposure analysis, heat vulnerability assessment, and climate-risk framing outputs
catch the specific failures that arise from multi-layer burden or hazard assemblies, vulnerability overlay claims, and resilience-oriented framing
validate hazard and environmental outputs before they are used in planning, policy, grant applications, or public delivery

This is a sector-family QA page that applies across flood, heat, EJ, general hazard, climate resilience, and critical facility resilience domains.

Use When
Use this checklist when reviewing any output that includes:
- hazard exposure screening (flood zones, heat islands, industrial proximity, etc.)
- environmental justice or equity-burden overlay claims
- vulnerability context combining demographic and environmental layers
- climate-risk or resilience framing products
- critical facility exposure to hazard zones
- any map or table that identifies populations or assets at risk from environmental conditions

Do Not Use When
Do not use this checklist for:
- market or trade-area analysis (use `qa-review/MARKET_AND_TRADE_AREA_QA.md`)
- general coverage or access analysis (use `qa-review/COVERAGE_AND_ACCESS_ANALYSIS_QA.md`)
- spatial statistics outputs (use `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md`)
- terrain or hydrology outputs with no hazard or burden claim (use `qa-review/HYDROLOGY_OUTPUT_QA.md`)

Core Review Checks

## Hazard Layer Quality

- each hazard layer source is documented: publisher, vintage, methodology, and coverage
- the hazard layer's geographic coverage matches the study area — no uncovered areas are silently treated as "no hazard"
- the hazard layer's intended use is compatible with the analysis: regulatory data (FEMA NFHL) has different appropriate uses than modeled data or screening proxies
- for flood data: the FEMA zone type is documented (A, AE, AH, X shaded, etc.) and the study type vintage is noted per `data-sources/FEMA_NFHL.md`
- for heat data: the data source and methodology are documented (satellite-derived LST, modeled heat index, field measurements, or proxy)
- for other hazard layers: the source, resolution, and limitations are documented
- multiple hazard layers are not combined into a single score or index unless the weighting methodology is project-approved

## Vulnerability and Demographic Context

- demographic vulnerability variables are named, sourced, and documented
- the connection between the demographic variable and the vulnerability claim is stated (e.g., age >65 as heat vulnerability indicator)
- vulnerability indicators are not assumed to be universal — what constitutes vulnerability depends on the hazard type and context
- the output does not conflate spatial overlap between a hazard and a demographic characteristic with causation or inequity without proper framing
- the trust level of demographic data (ACS estimates with margins of error) is acknowledged when making population-level claims about hazard exposure

## Screening vs. Modeling Distinction

- the output clearly states whether it is a screening product or a detailed hazard model
- screening products identify spatial overlap between hazard layers and population or asset locations — they do not model physical processes, predict outcomes, or estimate losses
- if the output uses screening language ("areas that overlap with," "populations within," "facilities located in"), the language is consistent and does not drift into modeling claims
- the output does not imply predictive certainty or probability unless the underlying data actually provides it (e.g., FEMA's 1% annual-chance designation)

## Multi-Layer Assembly Integrity

- if multiple burden or hazard layers are combined, each layer passed its own QA gate before assembly
- the method for combining layers is documented: side-by-side presentation, union of hazard areas, intersection of burden and vulnerability, or other
- if a composite index or score is produced, the weighting methodology is project-approved (do not invent weights)
- layers with very different trust levels, resolutions, or vintages are not silently merged — differences are documented
- the assembly does not create artificial precision: combining two approximate layers does not produce a precise result

## Exposure and Impact Claims

- "exposure" is defined: population living within a hazard zone, facilities located in a flood zone, assets within proximity of a burden source, or other
- population exposure estimates use documented allocation methods for partial-geography overlaps per `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`
- the output distinguishes between exposure (being in the zone) and impact (experiencing harm) — spatial overlap is not the same as actual damage or health effect
- if the output quantifies exposed population or assets, the numbers are plausible for the geography
- the output does not use "at risk" language when "spatially overlapping with a hazard layer" is what was actually measured

## Environmental Justice Framing

- if the output uses EJ language, the burden-vulnerability framework is stated
- the output does not imply that demographic groups cause their own exposure
- disparities in exposure are presented as findings, not as policy conclusions
- if the output compares burden across demographic groups, the comparison method is documented
- the framing acknowledges that screening is a starting point for further investigation, not a final determination
- if the output references federal or state EJ screening tools (EJScreen, CalEnviroScreen, CEJST), the tool version and methodology are documented

## Regulatory and Legal Sensitivity

- if the output references regulatory data (FEMA flood zones, EPA facility locations), the regulatory context is stated
- the output does not present screening results as official regulatory determinations
- if the output could be used in legal, regulatory, or compliance contexts, `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` has been applied
- claims about flood risk, environmental burden, or community vulnerability carry high interpretive weight and should be reviewed accordingly

Escalate When
- the hazard layer has known gaps or limitations that could produce misleading exposure estimates
- the output combines layers with very different trust levels and the assembly could mislead
- the output will be used for regulatory compliance, grant applications, or legal proceedings
- EJ or vulnerability claims could stigmatize communities or be used to justify actions harmful to the identified populations
- the client requires a formal EJ index, risk score, or resilience index that is not yet in the wiki canon
- the output presents screening results in language that implies predictive certainty
- flood exposure claims are based on approximate (Zone A) FEMA studies rather than detailed (Zone AE) studies, and the distinction is not stated

Common Failure Modes
- using hazard layers with incomplete coverage and treating uncovered areas as "no hazard"
- combining layers with very different vintages or resolutions without documenting the mismatch
- inventing composite scores or indices without project-approved weighting
- using "at risk" language when "within the mapped hazard zone" is what was measured
- conflating spatial overlap with causation or impact
- not documenting the screening vs. modeling distinction
- EJ framing that implies communities are responsible for their own exposure
- population exposure estimates without documented allocation method for partial geographies
- presenting FEMA flood zone data without noting the study vintage or zone type
- not distinguishing between detailed (Zone AE) and approximate (Zone A) flood zone studies

Relationship to Other QA Pages
- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — apply first for general data integrity
- `qa-review/HYDROLOGY_OUTPUT_QA.md` — apply for terrain and hydrology-specific checks
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — apply for narrative claims about burden, vulnerability, and risk
- `qa-review/MAP_QA_CHECKLIST.md` — apply for cartographic review of hazard and EJ maps
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md` — escalate for regulatory, legal, or high-stakes outputs
- `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md` — when access to emergency services is part of the analysis

Best-Fit Domains
- `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md`
- `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md`
- `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md`
- `domains/URBAN_HEAT_AND_HEAT_VULNERABILITY.md`
- `domains/CLIMATE_RISK_AND_RESILIENCE.md`
- `domains/CRITICAL_FACILITY_RESILIENCE.md`
- `domains/DISASTER_RESPONSE_AND_RECOVERY_SUPPORT.md`

Trust Level
Validated QA Page
