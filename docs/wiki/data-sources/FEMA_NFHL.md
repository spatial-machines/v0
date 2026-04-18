# FEMA National Flood Hazard Layer (NFHL) Source Page

Source Summary:
The FEMA National Flood Hazard Layer (NFHL) is the official digital flood hazard dataset for the United States, containing flood zone boundaries, base flood elevations, and regulatory floodplain information from FEMA Flood Insurance Rate Maps (FIRMs).
The NFHL is the primary public-domain source for identifying which areas fall within Special Flood Hazard Areas (SFHAs) and for supporting flood risk screening, community planning, and environmental context work.
This is regulatory data — it defines the zones that trigger flood insurance requirements and local floodplain management regulations under the National Flood Insurance Program (NFIP).

Owner / Publisher:
Federal Emergency Management Agency (FEMA)

Geography Support:
national coverage, but completeness varies significantly
NFHL coverage depends on whether FEMA has completed a Flood Insurance Study (FIS) for the community — some rural areas and tribal lands have no or outdated coverage
data is organized by county and community; download by state or county
the S_FLD_HAZ_AR layer contains the primary flood zone polygons

Time Coverage:
NFHL reflects the most recently effective FIRM for each community
effective dates vary by community: some areas reflect studies from the 2020s, others from the 1980s or earlier
FEMA periodically issues Letters of Map Revision (LOMRs) and Letters of Map Amendment (LOMAs) that modify the effective map locally
preliminary (not yet effective) flood maps may exist for areas undergoing restudies — these are not in the NFHL until adoption
always check the effective date and study type for the specific community

Access Method:
FEMA NFHL web services (ArcGIS REST): https://hazards.fema.gov/gis/nfhl/rest/services
FEMA Map Service Center: https://msc.fema.gov/portal/home
bulk download by state or county from the NFHL download page
Fetch Script:
`scripts/core/fetch_fema_nfhl.py` — query flood zone polygons by bbox or county FIPS
FEMA's National Risk Index (NRI) provides pre-computed risk scores but is a separate product from the NFHL

File Formats:
geodatabase (GDB) — the primary distribution format
shapefile exports available through the web services
web map services (WMS/REST) for preview and light integration

Key Layers:
- **S_FLD_HAZ_AR:** flood hazard area polygons (Zone A, AE, AH, AO, V, VE, X, D, etc.) — the core layer for most screening work
- **S_BFE:** base flood elevation lines
- **S_XS:** cross-section lines from hydraulic studies
- **S_FIRM_PAN:** FIRM panel index
- **S_POL_AR:** political area boundaries associated with the FIS
- **S_PROFIL_BASLN:** stream profile baselines

Key Flood Zones:
- **Zone A, AE, AH, AO:** Special Flood Hazard Areas (1% annual-chance flood, the "100-year floodplain") — mandatory flood insurance for federally backed mortgages
- **Zone V, VE:** coastal high-hazard areas with wave action — also SFHAs
- **Zone X (shaded):** moderate flood hazard (0.2% annual-chance, the "500-year floodplain")
- **Zone X (unshaded):** minimal flood hazard — areas outside the SFHA
- **Zone D:** areas with possible but undetermined flood hazard — no analysis performed

Licensing / Usage Notes:
public federal data
no usage restrictions for the data itself
however: NFHL data carries regulatory weight — outputs that reference or interpret NFHL zones should note the effective date, study type, and the fact that NFHL is not a substitute for a formal flood determination
do not present NFHL-based screening as an official flood determination — those require a formal process through FEMA or an authorized determinations company

Known Caveats:
NFHL is regulatory data, not a physics-based flood model — zone boundaries reflect the study methodology and vintage, not real-time flood behavior
study vintage varies enormously: some areas have modern 2D hydraulic studies, others have 1970s-era approximate studies with no detailed hydraulic modeling
Zone A (approximate) areas have no base flood elevation and no detailed study — the boundary is based on approximate methods and should be treated with lower confidence than Zone AE
NFHL does not reflect recent development, land-use change, or infrastructure modifications unless FEMA has issued a LOMR
the NFHL does not model pluvial (rainfall-driven) flooding, only riverine and coastal flooding — urban flash flooding and stormwater backup are not captured
areas shown as Zone X may still flood — the NFHL reflects the studied hazard, not all possible flood scenarios
NFHL geometry can have topology issues (slivers, overlaps, gaps) especially at community boundaries
datum and vertical reference matter: base flood elevations are referenced to NAVD88 in modern studies but older studies may use NGVD29

Best-Fit Workflows:
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md (flood screening overlay)
workflows/TRACT_JOIN_AND_ENRICHMENT.md (demographic context for flood-exposed areas)
workflows/WITHIN_DISTANCE_ENRICHMENT.md (facility proximity to flood zones)

Best-Fit Domains:
domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md
domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md
domains/CLIMATE_RISK_AND_RESILIENCE.md
domains/CRITICAL_FACILITY_RESILIENCE.md
domains/DISASTER_RESPONSE_AND_RECOVERY_SUPPORT.md
domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md

Alternatives:
USGS StreamStats for watershed-based flood frequency estimates (not regulatory, but physics-based)
state or local floodplain data: some states maintain their own flood studies that may be more current than the NFHL
first-floor elevation surveys for site-specific flood risk assessment (much higher precision than zone-level screening)
private flood models (First Street Foundation, KatRisk, etc.) for forward-looking and pluvial flood risk (not regulatory)
National Water Model and NOAA flood forecasting services for real-time or near-real-time flood context (different purpose than regulatory floodplain)

Sources:
https://www.fema.gov/flood-maps/national-flood-hazard-layer
https://msc.fema.gov/portal/home
https://hazards.fema.gov/gis/nfhl/rest/services
FEMA Flood Map Modernization guidelines
FEMA Technical Reference documents for flood zone definitions

Trust Level:
Validated Source Page
