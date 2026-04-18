# GIS Agent Benchmark Suite — 100 Questions

Version: 1.0
Date: 2026-04-10
Purpose: Evaluate the GIS agent system's ability to navigate the wiki, select the correct workflows, and produce real spatial analyses across all 40 domains.

## Scoring Framework

### Difficulty Tiers
- **Easy (E):** Single workflow, clear inputs, minimal judgment. Target: any agent should pass.
- **Medium (M):** Multi-workflow, requires domain routing, some judgment calls. Target: a competent agent with wiki access should pass.
- **Hard (H):** Multi-domain synthesis, judgment under ambiguity, gap recognition. Target: only an agent that deeply understands the wiki and knows its limits should pass.

### Scoring Per Question (0-5 points)
| Score | Meaning |
|-------|---------|
| 5 | Correct output, correct method, proper QA, limitations stated |
| 4 | Correct output, minor method or documentation gap |
| 3 | Partially correct, right approach but execution errors |
| 2 | Right domain but wrong workflow or significant errors |
| 1 | Attempted but fundamentally wrong approach |
| 0 | No attempt or completely wrong |

### Aggregate Scoring
- **Easy (40 questions):** 200 points possible
- **Medium (35 questions):** 175 points possible
- **Hard (25 questions):** 125 points possible
- **Total:** 500 points possible
- **Pass threshold:** 350/500 (70%)
- **Strong threshold:** 425/500 (85%)

### Evaluation Dimensions
Each question is tagged with which capabilities it tests:
- **R** = Wiki routing (finding the right pages)
- **W** = Workflow execution (following the steps)
- **D** = Data source selection (choosing the right inputs)
- **T** = Tool selection (picking the right toolkit)
- **Q** = QA discipline (applying review checks)
- **I** = Interpretive judgment (framing claims correctly)
- **G** = Gap recognition (knowing what the canon can't do)

---

## Easy Tier (40 questions)

### Demographics and Census (E01-E08)

**E01.** Pull the total population by tract for Denver County, CO (FIPS 08031) using ACS 5-year data. Output a GeoPackage with GEOID, geometry, and total population.
Tags: R, W, D | Domain: demographics | Workflow: ACS_DEMOGRAPHIC_INVENTORY

**E02.** Create a choropleth map of median household income by tract for Sedgwick County, KS. Apply the firm's cartographic standard for thematic choropleths.
Tags: R, W, T | Domain: demographics, cartography | Workflow: ACS_DEMOGRAPHIC_INVENTORY, CHOROPLETH_DESIGN

**E03.** For Douglas County, NE (FIPS 31055), compute the poverty rate by tract (population below poverty / total population for whom poverty status is determined). Flag any tracts with high coefficient of variation.
Tags: R, W, D | Domain: demographics | Workflow: ACS_DEMOGRAPHIC_INVENTORY, TRACT_JOIN_AND_ENRICHMENT

**E04.** Join ACS demographic data to Census tract geometry for Fulton County, GA. Confirm CRS is appropriate per the CRS Selection Standard. Export as GeoPackage.
Tags: R, W, D, T | Domain: data engineering | Workflow: TRACT_JOIN_AND_ENRICHMENT

**E05.** Compute a decade trend for total population by tract in Hennepin County, MN from 2013 to 2023 ACS 5-year estimates. Identify which tracts gained or lost population.
Tags: R, W, D | Domain: demographics | Workflow: DECADE_TREND_ANALYSIS

**E06.** Roll up tract-level poverty data to ZIP/ZCTA geographies for Johnson County, KS. Document the allocation method used.
Tags: R, W, D | Domain: demographics | Workflow: TRACT_TO_ZIP_ZCTA_ROLLUP

**E07.** Retrieve Census tract geometry for the state of Wyoming from TIGER/Line. Confirm the geometry vintage matches the ACS data vintage.
Tags: R, D | Domain: data engineering | Data source: TIGER_GEOMETRY

**E08.** Compute the demographic shift between 2013 and 2023 for percent non-white population by tract in Davidson County, TN. Classify tracts as diversifying, stable, or becoming less diverse.
Tags: R, W, I | Domain: demographics | Workflow: DEMOGRAPHIC_SHIFT_ANALYSIS

### POI and Business Landscape (E09-E13)

**E09.** Extract all restaurants and cafes within Denver County from the local PostGIS database. Normalize the OSM categories into a clean taxonomy. Report the count by normalized category.
Tags: R, W, D, T | Domain: POI | Workflow: POSTGIS_POI_LANDSCAPE, POI_CATEGORY_NORMALIZATION

**E10.** Count pharmacies within 1 mile of a given address (e.g., "100 Main St, Omaha, NE"). Use Euclidean distance. Document the CRS used for buffering.
Tags: R, W, T | Domain: POI, accessibility | Workflow: GEOCODE_BUFFER_ENRICHMENT, WITHIN_DISTANCE_ENRICHMENT

**E11.** Extract grocery stores within a study area polygon and validate the extraction with the POI Extraction QA checklist. Report any concerns about completeness.
Tags: R, W, Q | Domain: POI | Workflow: POSTGIS_POI_LANDSCAPE, QA: POI_EXTRACTION_QA

**E12.** Produce a point overlay map showing library locations on top of a population density choropleth for a county. Apply the correct map family rules.
Tags: R, W, T | Domain: POI, cartography | Workflow: POINT_OVERLAY_DESIGN

**E13.** Normalize a raw OSM extract of "amenity" tags into firm-approved categories for a business landscape analysis. Document the tag-to-category mapping.
Tags: R, W | Domain: POI | Workflow: POI_CATEGORY_NORMALIZATION

### Terrain and Hydrology (E14-E17)

**E14.** Download a USGS DEM for a county and compute slope and aspect rasters. Document the CRS, resolution, and tool used.
Tags: R, W, D, T | Domain: hydrology/terrain | Workflow: TERRAIN_DERIVATIVES | Toolkit: GDAL_OGR or WHITEBOXTOOLS

**E15.** Delineate watersheds from a DEM for a study area. Document the preprocessing steps (breach/fill) and the tool used.
Tags: R, W, T | Domain: hydrology/terrain | Workflow: WATERSHED_DELINEATION | Toolkit: WHITEBOXTOOLS

**E16.** Clip a DEM to a study area boundary with 10% padding. Convert from IMG format to GeoTIFF. Confirm NoData handling.
Tags: R, W, T | Domain: data engineering | Toolkit: GDAL_OGR

**E17.** Create a hillshade visualization of a DEM and produce a raster surface map following the firm's cartographic standard for raster surfaces.
Tags: R, W, T | Domain: cartography, terrain | Toolkit: GDAL_OGR

### Spatial Statistics (E18-E22)

**E18.** Run Global Moran's I on poverty rate by tract for a county. Document the spatial weights type, row standardization, and gate result (clustered/dispersed/random).
Tags: R, W, Q | Domain: demographics | Workflow: SPATIAL_AUTOCORRELATION_TEST

**E19.** Run a Getis-Ord Gi* hotspot analysis on median income by tract. Apply FDR correction. Produce a hotspot map with correct legend ordering.
Tags: R, W, Q | Domain: demographics | Workflow: HOTSPOT_ANALYSIS, HOTSPOT_MAP_DESIGN

**E20.** Run LISA cluster analysis on percent uninsured by tract. Report the corrected count of significant HH, LL, HL, LH clusters. Answer all 5 interpretation questions from the standard.
Tags: R, W, Q, I | Domain: demographics | Workflow: LISA_CLUSTER_ANALYSIS

**E21.** Validate a spatial statistics output using the Spatial Stats Output Review checklist. Check for: gate documentation, weights documentation, correction documentation, interpretation template completeness.
Tags: R, Q | Domain: QA | QA: SPATIAL_STATS_OUTPUT_REVIEW

**E22.** Produce a bivariate choropleth of poverty rate vs. uninsured rate by tract. Apply the correct map family rules for thematic choropleths.
Tags: R, W, T | Domain: cartography | Workflow: BIVARIATE_CHOROPLETH_DESIGN

### Service Areas and Access (E23-E27)

**E23.** Generate a 10-minute drive-time isochrone around a single facility address using OSRM or Valhalla. Validate that the shape follows road corridors, not a circle.
Tags: R, W, T, Q | Domain: accessibility | Workflow: SERVICE_AREA_ANALYSIS

**E24.** Enrich a 1-mile Euclidean buffer around a site with tract-level demographic data. Document the allocation method for partial tract overlaps.
Tags: R, W | Domain: accessibility | Workflow: WITHIN_DISTANCE_ENRICHMENT, TRACT_JOIN_AND_ENRICHMENT

**E25.** Generate 5, 10, and 15-minute drive-time isochrones around a facility. Count the population within each ring. Validate with the Service Area and Travel-Time QA checklist.
Tags: R, W, Q | Domain: drive-time | Workflow: SERVICE_AREA_ANALYSIS | QA: SERVICE_AREA_AND_TRAVEL_TIME_QA

**E26.** Geocode an address, buffer it at 3 miles, and extract all POIs within the buffer. Report counts by category.
Tags: R, W, T | Domain: POI, accessibility | Workflow: GEOCODE_BUFFER_ENRICHMENT, WITHIN_DISTANCE_ENRICHMENT

**E27.** Produce a map showing overlapping service areas for 3 fire stations. Apply the correct map family for a reference/orientation map (basemap, scale bar, north arrow required).
Tags: R, W, T | Domain: emergency ops, cartography | Workflow: SERVICE_AREA_ANALYSIS

### Data Engineering and QA (E28-E32)

**E28.** Validate a joined GeoPackage using the Structural QA Checklist. Report: geometry validity, null geometry count, CRS, feature count, field types.
Tags: R, Q | Domain: data engineering | QA: STRUCTURAL_QA_CHECKLIST

**E29.** Convert a shapefile to GeoPackage, reproject from EPSG:4326 to EPSG:5070, and confirm the output CRS. Document the GDAL command used.
Tags: R, T | Domain: data engineering | Toolkit: GDAL_OGR

**E30.** Read a raster file using Rasterio. Report: CRS, bounds, resolution, NoData value, band count. Sample values at 3 coordinate locations.
Tags: R, T | Domain: data engineering | Toolkit: RASTERIO

**E31.** Write a provenance record for a data retrieval operation. Include: source URL, download date, format, limitations.
Tags: R, W | Domain: data engineering | Workflow: GENERAL_RETRIEVAL_AND_PROVENANCE

**E32.** Run the cartographic validator on a set of map PNGs. Report which passed and which failed, with reasons.
Tags: R, T | Domain: cartography | Tool: validate_cartography.py

### Delivery and Reporting (E33-E36)

**E33.** Package a completed analysis for QGIS review. Include: GeoPackage data layers, a .qgs project file, and a review-notes.md.
Tags: R, W | Domain: cartography | Workflow: QGIS_HANDOFF_PACKAGING

**E34.** Produce an analysis report following the Pyramid Principle structure. Lead with 3-5 key findings, then methodology, then detailed findings.
Tags: R, W | Domain: delivery | Workflow: REPORTING_AND_DELIVERY

**E35.** Build a Folium interactive web map with at least 2 toggle layers and a tooltip. Export as self-contained HTML.
Tags: R, W, T | Domain: cartography | Standard: OPEN_EXECUTION_STACK_STANDARD

**E36.** Run the full publishing readiness check on a completed analysis. Confirm maps, reports, data catalog, and QA scorecard all exist.
Tags: R, Q | Domain: delivery | Standard: PUBLISHING_READINESS_STANDARD

### Source Guidance (E37-E40)

**E37.** Identify the correct FEMA flood zone data source for a county in Nebraska. Document: where to download, what layers to use, what the zone codes mean.
Tags: R, D | Domain: flood risk | Data source: FEMA_NFHL

**E38.** Find and download LEHD/LODES origin-destination employment data for a state. Describe the OD, RAC, and WAC file types and which to use for commute analysis.
Tags: R, D | Domain: workforce | Data source: LEHD_LODES

**E39.** Locate a GTFS feed for a metro transit agency. Validate the feed using the MobilityData validator. Report: route count, stop count, feed date range.
Tags: R, D | Domain: transit | Data source: GTFS_TRANSIT

**E40.** Identify parcel data sources for a specific county. Document: what's available (open data vs. commercial), what attributes to expect, and the key caveats about parcel data quality.
Tags: R, D | Domain: land use | Data source: PARCEL_CADASTRAL

---

## Medium Tier (35 questions)

### Multi-Workflow Analysis (M01-M10)

**M01.** Delineate a 10-minute drive-time trade area around a proposed retail site. Enrich with demographics (population, households, median income) and business landscape (restaurants, retail). Produce a trade-area summary table and map.
Tags: R, W, D, T | Domains: retail, demographics, POI | Workflow: TRADE_AREA_DELINEATION

**M02.** Compare healthcare access across 3 candidate clinic locations. Generate service areas, count population within each, identify the site with the best coverage of underserved populations.
Tags: R, W, D, I | Domains: healthcare, accessibility, demographics | Workflow: SERVICE_AREA_ANALYSIS, MULTI_CRITERIA_CONTEXT_ASSEMBLY

**M03.** Screen a commercial corridor for economic development context. Produce: demographic profile, business landscape, trend analysis, and accessibility summary.
Tags: R, W, D | Domains: economic development, demographics, POI | Workflow: ACS_DEMOGRAPHIC_INVENTORY, POSTGIS_POI_LANDSCAPE, DECADE_TREND_ANALYSIS

**M04.** Conduct a competitor gap screening for coffee shops in a metro area. Identify zones with high population but low coffee shop density. Produce a density comparison map.
Tags: R, W, D, T | Domains: competitor, POI, demographics | Workflow: COMPETITOR_GAP_SCREENING

**M05.** Delineate labor sheds for 2 employer sites using 30-minute drive times. Compare workforce demographics between the two sites. Produce a comparison table.
Tags: R, W, D | Domains: workforce, drive-time, demographics | Workflow: SERVICE_AREA_ANALYSIS, TRADE_AREA_DELINEATION

**M06.** Screen a county for flood-exposed critical facilities. Overlay FEMA flood zones against facility locations. Count facilities in Zone A/AE vs. Zone X.
Tags: R, W, D | Domains: flood, critical facility | Data source: FEMA_NFHL

**M07.** Produce a demographic shift analysis showing neighborhood change over 10 years. Combine with a hotspot analysis of the shift variable. Map both the shift and the hotspot results.
Tags: R, W, I | Domains: demographics | Workflow: DEMOGRAPHIC_SHIFT_ANALYSIS, HOTSPOT_ANALYSIS

**M08.** Build a transit access analysis: identify which tracts have a transit stop within 0.25 miles. Calculate the percent of population with transit access vs. without. Produce an equity comparison.
Tags: R, W, D | Domains: transit, demographics, equity | Data source: GTFS_TRANSIT

**M09.** Assemble a site selection context for 4 candidate warehouse locations. Include: drive-time coverage, demographic context, highway proximity, and competitor presence. Present as a side-by-side comparison table.
Tags: R, W, D | Domains: site selection, freight, demographics | Workflow: MULTI_CRITERIA_CONTEXT_ASSEMBLY

**M10.** Produce a tourism district profile: hospitality POI inventory, demographic context, transit access, and pedestrian walkability assessment.
Tags: R, W, D | Domains: tourism, POI, transit, pedestrian | Multiple workflows

### Domain Routing and QA (M11-M20)

**M11.** A client asks: "Where should we put our next pharmacy in this county?" Route this question to the correct domain pages and recommend a workflow sequence. Do not execute — just produce the routing plan.
Tags: R, G | Domains: pharmacy, site selection, competitor | Test: wiki navigation

**M12.** Review a completed trade-area analysis using the Market and Trade-Area QA checklist. Check all sections: method, enrichment, competitor context, gap framing, claim framing.
Tags: R, Q | Domain: retail | QA: MARKET_AND_TRADE_AREA_QA

**M13.** Review a hazard screening output using the Hazard and Environmental Screening QA checklist. Check: layer quality, vulnerability context, screening vs. modeling distinction, exposure claims.
Tags: R, Q | Domain: hazard | QA: HAZARD_AND_ENVIRONMENTAL_SCREENING_QA

**M14.** Review a coverage analysis output using the Coverage and Access Analysis QA checklist. Check: facility inventory, coverage method, population estimation, gap identification.
Tags: R, Q | Domain: public asset | QA: COVERAGE_AND_ACCESS_ANALYSIS_QA

**M15.** A temporal pattern analysis of crime incidents shows a spike in reported incidents on Mondays. Review the finding and identify at least 2 reasons why this could be an artifact rather than a real pattern.
Tags: R, I, Q | Domain: crime | Workflow: TEMPORAL_PATTERN_ANALYSIS

**M16.** Produce an interpretive review of a corridor economic development output. Check whether trend claims, business landscape findings, and investment framing are grounded in the data.
Tags: R, Q, I | Domain: economic development | QA: INTERPRETIVE_REVIEW_CHECKLIST

**M17.** A client provides a CSV of customer addresses and asks for a trade area. Describe the three trade-area methods (distance, drive-time, customer-origin) and recommend which to use given the data. Justify.
Tags: R, I, G | Domain: retail | Workflow: TRADE_AREA_DELINEATION

**M18.** An analyst presents a LISA cluster map but has not documented the Global Moran's I gate result. Explain why this is a failure per the Spatial Stats Standard and what must be added.
Tags: R, Q | Domain: spatial stats | Standard: SPATIAL_STATS_STANDARD

**M19.** A broadband coverage map shows 95% of a rural county as "served." Review the finding and identify at least 3 caveats about FCC broadband data that could affect this claim.
Tags: R, D, I | Domain: broadband | Data source: FCC_BROADBAND

**M20.** An EJ screening overlays flood zones with poverty rate by tract. The narrative says "low-income communities face disproportionate flood risk." Review this claim. What additional checks are needed?
Tags: R, Q, I | Domain: EJ, flood | QA: HAZARD_AND_ENVIRONMENTAL_SCREENING_QA

### Cross-Domain Synthesis (M21-M30)

**M21.** Produce a public facility coverage analysis for libraries in a county. Map service areas, identify underserved populations, and frame equity findings.
Tags: R, W, D, I | Domains: public asset, accessibility, equity

**M22.** Analyze crime hotspots by time of day and day of week. Produce a heatmap visualization and map the spatial hotspot for the peak period.
Tags: R, W, T | Domains: crime, spatial stats | Workflow: HOTSPOT_ANALYSIS, TEMPORAL_PATTERN_ANALYSIS

**M23.** Screen a set of 5 proposed solar farm sites for terrain suitability. Compute slope for each site and flag any with average slope >15 degrees.
Tags: R, W, D, T | Domains: energy, terrain | Workflow: TERRAIN_DERIVATIVES

**M24.** Produce an emergency service coverage gap analysis for fire stations in a county. Map 5 and 10-minute response zones. Identify populations outside both thresholds.
Tags: R, W, D | Domains: emergency ops, drive-time, demographics

**M25.** Compare broadband access across income quartiles in a county. Use FCC availability data and ACS income data. Produce an equity comparison table.
Tags: R, W, D, I | Domains: broadband, demographics, equity

**M26.** Assemble a disaster response context map for a flooding event. Show: affected area boundary, population within the area, critical facilities in the zone, and demographic vulnerability context.
Tags: R, W, D | Domains: disaster, flood, critical facility, demographics

**M27.** Produce a policy-support map showing transit access vs. poverty rate by tract. Use a bivariate choropleth. Apply the correct cartographic standard and review for public-audience readiness.
Tags: R, W, T, Q | Domains: policy, transit, demographics, cartography

**M28.** Analyze pedestrian access to parks: what percent of the population lives within a 10-minute walk of a park? Produce a map and summary table.
Tags: R, W, D | Domains: pedestrian, parks, demographics

**M29.** Build a workforce profile for a proposed manufacturing site. Include: population within 30-minute drive, working-age demographics, industry sector breakdown from LODES data.
Tags: R, W, D | Domains: workforce, drive-time, demographics | Data source: LEHD_LODES

**M30.** Produce a utility infrastructure gap screening. Identify areas with high population growth but no broadband or no water/sewer infrastructure data available.
Tags: R, W, D, G | Domains: utilities, broadband, demographics

### Data Source Integration (M31-M35)

**M31.** Integrate FEMA NFHL flood zone data with parcel data for a county. Identify parcels in the 100-year floodplain (Zone A/AE). Report count and total assessed value.
Tags: R, W, D | Domains: flood, land use | Data sources: FEMA_NFHL, PARCEL_CADASTRAL

**M32.** Use LODES data to map commute flows into a downtown district. Show which tracts send the most workers. Produce a flow visualization or summary table.
Tags: R, W, D, T | Domains: workforce, economic development | Data source: LEHD_LODES

**M33.** Combine GTFS stop locations with ACS demographic data to produce a transit equity assessment. Map which demographic groups have the best and worst transit access.
Tags: R, W, D, I | Domains: transit, equity, demographics | Data source: GTFS_TRANSIT

**M34.** Use parcel data to identify vacant commercial parcels in a corridor. Cross-reference with zoning to confirm commercial zoning. Produce a vacancy map.
Tags: R, W, D | Domains: land use, zoning, economic development | Data source: PARCEL_CADASTRAL

**M35.** Assemble a multi-source context package for a trade area: ACS demographics, LODES employment, POI landscape, and FEMA flood zones. Document the source vintage for each layer.
Tags: R, W, D | Domains: retail, demographics, workforce, flood | Multiple data sources

---

## Hard Tier (25 questions)

### Complex Multi-Domain Analysis (H01-H10)

**H01.** A client asks: "Evaluate these 5 candidate sites for a grocery store in a food desert area." Design and execute the full analysis: trade-area delineation, demographic enrichment, competitor gap screening, transit access, flood risk screening, and a multi-criteria context assembly. Produce a comparison table and map set. State which site looks strongest and what gaps remain in the analysis.
Tags: R, W, D, T, Q, I, G | Domains: retail, competitor, demographics, transit, flood, site selection

**H02.** A county wants to know where to place a new emergency shelter. Produce a suitability context analysis considering: population density, existing shelter locations and coverage gaps, flood zone avoidance, transit access, and proximity to critical facilities. Do NOT produce a ranked score — present context side-by-side and explain why scoring is not yet supported by the canon.
Tags: R, W, D, I, G | Domains: emergency ops, site selection, flood, transit, critical facility

**H03.** An economic development agency asks for a corridor vitality assessment of a 3-mile commercial strip. Produce: demographic trends, business landscape change, vacancy indicators (if data supports), transit access, pedestrian access, and crime hotspot context. Frame findings for a planning audience.
Tags: R, W, D, T, I | Domains: economic development, demographics, POI, transit, pedestrian, crime

**H04.** Produce a comprehensive environmental justice screening for a county. Layer: flood exposure, heat vulnerability, demographic vulnerability, proximity to major roads, and access to healthcare. Apply the Hazard and Environmental Screening QA checklist. State clearly what the screening can and cannot conclude.
Tags: R, W, D, Q, I, G | Domains: EJ, flood, heat, demographics, healthcare, hazard

**H05.** A hospital system asks: "Which communities are most underserved by our provider network?" Analyze: service area coverage gaps, demographic vulnerability in gap areas, competitor provider presence, and transit access to existing locations. Produce a prioritized gap map and summary.
Tags: R, W, D, I | Domains: healthcare, provider network, competitor, transit, demographics

**H06.** Design a renewable energy siting screening for a rural county. Consider: slope and aspect from DEM, land use constraints, flood zone avoidance, proximity to transmission lines (if data available), and community impact context. State which layers are well-supported by the canon and which are data gaps.
Tags: R, W, D, T, G | Domains: energy, terrain, land use, flood, demographics

**H07.** A tourism board asks: "How does our hospitality infrastructure compare to peer resort communities?" Design the analysis approach, identify what data is available, produce whatever comparison the canon supports, and clearly state what it cannot support (visitor volume, spending, economic impact).
Tags: R, D, I, G | Domains: tourism, POI, demographics, economic development

**H08.** Produce a climate resilience screening for a coastal county. Layer: flood zones, heat vulnerability, critical facility exposure, demographic vulnerability, and infrastructure context. Frame as a resilience screening, NOT a climate model. Apply the hazard QA checklist.
Tags: R, W, D, Q, I, G | Domains: climate, flood, heat, critical facility, demographics, infrastructure

**H09.** A school district asks for an analysis of which schools are hardest to reach by families without cars. Combine: school locations, transit access, pedestrian access, and demographic data on vehicle availability. Produce an access equity assessment.
Tags: R, W, D, I | Domains: community facility, transit, pedestrian, demographics, equity

**H10.** Evaluate 3 candidate locations for a distribution center. Consider: highway access, labor shed (30 and 45-minute drive times), competitor warehouse presence, flood risk, and parcel/zoning compatibility. Produce a multi-criteria comparison.
Tags: R, W, D, T | Domains: freight, workforce, competitor, flood, land use, zoning, site selection

### Judgment and Gap Recognition (H11-H18)

**H11.** A client asks for a "market penetration analysis" for their retail chain. The wiki has a trade-area delineation workflow but no penetration formula. Explain what you can produce, what you cannot, and how to frame the gap for the client.
Tags: R, I, G | Domain: retail | Test: gap recognition

**H12.** An analyst produced a "suitability score" for candidate sites by averaging normalized demographic, access, and environmental values with equal weights. Review this approach and explain why the wiki does not support it. Recommend the correct alternative (multi-criteria context assembly without invented weights).
Tags: R, Q, I, G | Domain: site selection | Workflow: MULTI_CRITERIA_CONTEXT_ASSEMBLY

**H13.** A client asks: "What's the economic impact of this proposed development?" Explain what spatial analysis the wiki can support (demographic context, business landscape, accessibility) and what it cannot (multiplier analysis, fiscal impact, job creation estimates). Be specific about the boundary.
Tags: R, I, G | Domain: economic development | Test: gap recognition

**H14.** A disaster response team provides a preliminary flood boundary and asks for "damage estimates." Explain what you can produce (affected population, facilities in the zone, demographic vulnerability) and what you cannot (structural damage, dollar losses). Produce what the canon supports.
Tags: R, W, D, I, G | Domain: disaster | Test: gap recognition

**H15.** An analyst's crime hotspot map uses uncorrected p-values and shows 45 "significant" hotspots. After FDR correction, only 8 remain. The analyst wants to present the uncorrected results. Explain why this violates the Spatial Stats Standard and what the correct presentation should be.
Tags: R, Q, I | Domain: crime, spatial stats | Standard: SPATIAL_STATS_STANDARD

**H16.** A broadband equity analysis shows that low-income tracts have lower broadband availability. Before delivering to the client, identify at least 5 caveats that should accompany this finding (source limitations, definition issues, coverage vs. adoption, etc.).
Tags: R, D, I, Q | Domain: broadband, equity | Data source: FCC_BROADBAND

**H17.** A client asks for a "walkability score" for neighborhoods in their city. The wiki has pedestrian access analysis but no walkability index or scoring methodology. Explain what you can produce and what would need to be developed before a score can be assigned.
Tags: R, I, G | Domain: pedestrian | Test: gap recognition

**H18.** Review a multi-criteria site comparison where one dimension (flood risk) is from a 1980s-era approximate FEMA study (Zone A, no BFE) and another (demographics) is from 2023 ACS. Explain the trust-level mismatch and how it should be disclosed.
Tags: R, Q, I | Domain: site selection, flood | QA: HAZARD_AND_ENVIRONMENTAL_SCREENING_QA

### Full Pipeline Execution (H19-H25)

**H19.** Execute a full pipeline: retrieve ACS data for a county, join to tract geometry, compute hotspots on poverty rate, produce a choropleth and a hotspot map, validate outputs, write a report following the Pyramid Principle, and package for QGIS review. Every step should reference the correct wiki page.
Tags: R, W, D, T, Q | All dimensions | Full pipeline test

**H20.** Execute a healthcare access analysis from scratch: retrieve provider locations, generate service areas, enrich with demographics, identify underserved populations, apply the Coverage and Access QA checklist, produce maps and a summary report.
Tags: R, W, D, T, Q, I | Domains: healthcare, accessibility, demographics | Full pipeline test

**H21.** Execute a trade-area comparison for 3 candidate retail sites: delineate trade areas, enrich with demographics and competitor landscape, apply the Market and Trade-Area QA checklist, produce comparison table and maps, frame findings for an investment audience.
Tags: R, W, D, T, Q, I | Domains: retail, competitor, demographics | Full pipeline test

**H22.** Execute a corridor economic development profile: demographic baseline, decade trends, business landscape, transit access, pedestrian context, and policy-ready maps. Apply interpretive review. Frame for a city council audience.
Tags: R, W, D, T, Q, I | Domains: economic development, demographics, POI, transit, pedestrian, policy | Full pipeline test

**H23.** Execute a flood exposure + EJ screening: overlay FEMA flood zones with demographic vulnerability. Identify disproportionately exposed populations. Apply the Hazard and Environmental Screening QA checklist. Produce maps for a public audience.
Tags: R, W, D, Q, I | Domains: flood, EJ, demographics | Full pipeline test

**H24.** Execute a labor-shed analysis for an employer site: delineate 20 and 40-minute drive-time commute sheds, enrich with LODES employment data and ACS demographics, compare to a competing site, produce a workforce comparison report.
Tags: R, W, D, T, I | Domains: workforce, drive-time, demographics | Data source: LEHD_LODES | Full pipeline test

**H25.** Execute a critical facility resilience screening for a county: inventory hospitals, fire stations, and schools; overlay with FEMA flood zones and heat vulnerability; identify the most exposed facilities; produce a resilience screening report with proper framing (screening, not engineering assessment).
Tags: R, W, D, Q, I, G | Domains: critical facility, flood, heat, demographics | Full pipeline test

---

## Domain Coverage Matrix

| Domain | Easy | Medium | Hard | Total |
|--------|------|--------|------|-------|
| Demographics & Market | E01-E08, E18-E22 | M01, M03, M05, M07 | H01, H03-H05, H19 | 20+ |
| POI & Business | E09-E13 | M04 | H01, H03, H07 | 9 |
| Hydrology & Terrain | E14-E17 | M23 | H06 | 6 |
| Accessibility & Network | E23-E27 | M02, M09 | H02, H09 | 7 |
| Cartography & Delivery | E02, E12, E17, E22, E27, E32-E36 | M27 | H19 | 11 |
| Data Engineering & QA | E04, E07, E16, E28-E31 | — | — | 7 |
| Retail & Trade Area | — | M01, M04, M17 | H01, H11, H21 | 6 |
| Competitor & White Space | — | M04 | H01, H05 | 3 |
| Economic Development | — | M03 | H03, H13, H22 | 4 |
| Workforce & Labor Shed | — | M05, M29 | H10, H24 | 4 |
| Tourism & Hospitality | — | M10 | H07 | 2 |
| Healthcare & Access | — | M02 | H05, H20 | 3 |
| Emergency & Coverage | — | M24 | H02 | 2 |
| Environmental Justice | — | M20 | H04, H23 | 3 |
| Flood & Floodplain | E37 | M06, M31 | H06, H08, H23, H25 | 5 |
| Climate & Resilience | — | — | H08 | 1 |
| Critical Facility | — | M06, M26 | H25 | 3 |
| Crime & Public Safety | — | M15, M22 | H03, H15 | 4 |
| Broadband & Telecom | — | M19, M25 | H16 | 3 |
| Transit & Coverage | — | M08, M33 | H09 | 3 |
| Land Use & Parcel | E40 | M31, M34 | H10 | 3 |
| Energy & Renewable | — | M23 | H06 | 2 |
| Policy & Communication | — | M27 | H22 | 2 |
| Disaster Response | — | M26 | H14 | 2 |
| Utilities & Infrastructure | — | M30 | — | 1 |
| Pedestrian & Bicycle | — | M28 | H09 | 2 |
| Site Selection | — | M09 | H01, H02, H10, H12 | 4 |
| Spatial Statistics | E18-E22 | M15, M22 | H15 | 6 |

---

## Execution Notes

### Running the Benchmark

1. Each question should be attempted independently (no carryover between questions).
2. The agent has access to the full wiki, all scripts, and all data sources.
3. For questions requiring real data, use the existing analyses in the repo or fetch live data.
4. Time each question. Easy: target <10 min. Medium: target <30 min. Hard: target <60 min.
5. Score immediately after completion using the 0-5 rubric.
6. Before closing a batch, run `make benchmark-audit BENCHMARK_ROOT=<batch-root> SUMMARY_CSV=<summary-csv-relative-path>` so question-level score notes, summary CSV scores, and substantive artifacts are reconciled.
7. Do not treat a batch summary as final until the benchmark audit passes cleanly.

### What Counts as a Pass

For each question, the agent must:
- Reference the correct wiki pages (domain, workflow, standard, QA, data source, toolkit)
- Follow the workflow steps in the correct order
- Use the correct tools per the toolkit guidance
- Apply the relevant QA checklist
- Frame interpretive claims correctly
- Recognize gaps when the canon cannot support the requested analysis

### Batch Execution Recommendation

- **Day 1:** E01-E20 (easy, first 20) — calibrate scoring
- **Day 2:** E21-E40 (easy, remaining 20) — complete easy tier
- **Day 3:** M01-M15 (medium, first 15)
- **Day 4:** M16-M35 (medium, remaining 20)
- **Day 5:** H01-H12 (hard, analysis + judgment)
- **Day 6:** H13-H25 (hard, gap recognition + full pipeline)
