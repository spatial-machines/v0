# Crime and Incident Data Source Page

Source Summary:
Crime and public safety incident data encompasses geocoded records of reported crimes, calls for service, traffic crashes, and other public safety events.
Unlike Census or FEMA data, there is no single national crime dataset with consistent geographic detail. Crime data is maintained by local law enforcement agencies, and availability, schema, geocoding quality, and release practices vary enormously across jurisdictions.
This source page covers the general source family and key caveats rather than a single authoritative dataset.

Owner / Publisher:
primary: local law enforcement agencies (police departments, sheriff's offices)
aggregated sources: FBI Uniform Crime Reporting (UCR) / National Incident-Based Reporting System (NIBRS), state crime reporting agencies, municipal open data portals

Geography Support:
point-level: individual incidents geocoded to an address or intersection (when available from local agencies)
aggregate: UCR/NIBRS data is published at the agency/jurisdiction level (no point-level geography)
coverage varies: some cities publish point-level open data with precise geocoding; others publish only aggregate counts or nothing at all
address-level geocoding quality varies — many agencies offset or fuzz locations for privacy, especially for sensitive crime types
some agencies snap incidents to the nearest block or intersection rather than the actual address

Time Coverage:
local agency data: update frequency ranges from daily (major metro open data portals) to annual or irregular
UCR/NIBRS: annual releases, typically 1-2 years behind current; transitional period as agencies move from UCR Summary to NIBRS
traffic crash data: typically maintained separately from crime data, often by state DOT or highway safety offices
always confirm the time range, reporting completeness, and whether the jurisdiction participated consistently across the analysis period

Access Method:
municipal and county open data portals: the best source for point-level incident data (e.g., Chicago, Los Angeles, Philadelphia, Denver, many others)
state crime reporting agencies: aggregate data, sometimes with limited geographic detail
FBI Crime Data Explorer: https://cde.ucr.cjis.gov/ — UCR/NIBRS aggregate data by agency
Fetch Scripts:
`scripts/core/fetch_fbi_crime.py` — FBI crime statistics by state/offense/year
`scripts/core/fetch_socrata.py` — city-level crime data from Socrata portals (Chicago, LA, etc.)
NHTSA FARS (Fatality Analysis Reporting System): https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars — traffic fatality data with geographic detail
state DOT crash databases: traffic crash data with location information (availability and access vary by state)
CrimeMapping.com, Crimereports.com: commercial aggregators of local agency data (limited analysis use)

File Formats:
CSV is the most common format from open data portals
some portals offer GeoJSON, shapefile, or API access
UCR/NIBRS data is published as fixed-width or CSV files
FARS data is available as SAS, CSV, or through the FARS Query System
many portals provide API endpoints (Socrata/SODA, ArcGIS Open Data, CKAN)

Key Data Fields (vary by agency):
- **Incident ID / case number:** unique identifier
- **Date and time:** reported or occurred date/time (distinction matters for analysis)
- **Crime type / UCR code / NIBRS offense code:** classification of the incident
- **Location:** address, intersection, block, or coordinates (precision varies)
- **Latitude / longitude:** geocoded coordinates (when available)
- **Beat / district / zone:** police administrative geography
- **Disposition / status:** case outcome (not always included in open data)

Licensing / Usage Notes:
municipal open data is generally free for use but check each portal's terms
some agencies restrict commercial use or require attribution
CJIS (Criminal Justice Information Services) data has strict access controls — raw CJIS data is not publicly available
privacy restrictions apply: victim-identifying information, juvenile records, and certain sensitive crime categories may be redacted or excluded
do not republish individual incident records with victim-identifying information
traffic crash data access varies by state: some states charge fees, some require data use agreements

Known Caveats:
crime data reflects reporting and recording practices, not objective crime occurrence — underreporting is significant for many crime types (sexual assault, domestic violence, property crime in some areas)
geocoding quality varies: some agencies geocode to the rooftop, others to the block centroid, nearest intersection, or a default location for the beat
some agencies deliberately offset or fuzz coordinates for privacy, especially for crimes at residential addresses — this affects point-pattern analysis
crime classification changes over time: UCR to NIBRS transition, local code changes, and reclassification practices all affect trend comparability
not all agencies participate in national reporting programs: UCR/NIBRS participation is voluntary, and some agencies have reporting gaps
the distinction between "reported date" and "occurred date" matters for temporal analysis — some incidents are reported days or weeks after occurrence
calls for service data (911/CAD records) is different from crime data: CFS includes non-crime events and may have very different geocoding and classification
crime data should never be correlated with demographic characteristics without extreme interpretive caution — apparent correlations may reflect patrol allocation, reporting bias, or structural factors rather than resident behavior
traffic crash data and crime data are usually maintained by different agencies with different schemas, geocoding methods, and reporting standards
seasonal, day-of-week, and time-of-day patterns are real but require sufficient data volume and consistent reporting to analyze reliably

Best-Fit Workflows:
workflows/HOTSPOT_ANALYSIS.md (point-pattern analysis of incident concentrations)
workflows/SPATIAL_AUTOCORRELATION_TEST.md (areal pattern testing)
workflows/LISA_CLUSTER_ANALYSIS.md (local cluster identification)
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md (incident context packaging)
workflows/TRACT_JOIN_AND_ENRICHMENT.md (demographic context for incident areas)
workflows/CHOROPLETH_DESIGN.md (rate-based areal presentation)

Best-Fit Domains:
domains/CRIME_PUBLIC_SAFETY_AND_INCIDENT_MAPPING.md
domains/TRANSPORTATION_SAFETY_AND_CRASH_ANALYSIS.md
domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md
domains/POLICY_SUPPORT_AND_PUBLIC_COMMUNICATION_MAPS.md

Alternatives:
FBI Crime Data Explorer for national agency-level aggregate data
NHTSA FARS for traffic fatality data with geographic detail
state DOT crash databases for traffic crash data
commercial crime data aggregators (LexisNexis, CAP Index) for standardized multi-jurisdiction data (licensing required)
community survey data for victimization rates (e.g., NCVS — National Crime Victimization Survey, not geocoded)

Sources:
FBI Crime Data Explorer: https://cde.ucr.cjis.gov/
NHTSA FARS: https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars
Municipal open data portals (varies by city)
State crime reporting agency websites (varies by state)
Bureau of Justice Statistics: https://bjs.ojp.gov/

Trust Level:
Validated Source Page
Needs Source Validation (quality, geocoding precision, completeness, and reporting consistency vary by jurisdiction)
