# GTFS Transit Schedule Data Source Page

Source Summary:
The General Transit Feed Specification (GTFS) is the standard format for public transit schedule and route data.
GTFS feeds are published by transit agencies and describe routes, stops, schedules, and (in GTFS Realtime) vehicle positions and service alerts.
GTFS is the primary data source for transit accessibility analysis, transit coverage mapping, and multimodal travel-time modeling.

Owner / Publisher:
individual transit agencies publish their own GTFS feeds
aggregated by: OpenMobilityData (Transitland), the Mobility Database (maintained by MobilityData), and some state DOTs
originally specified by Google; now maintained as an open standard by MobilityData

Geography Support:
coverage depends on which transit agencies publish feeds
most U.S. urban transit agencies publish GTFS; rural and demand-response services are less consistently available
each feed covers one agency's service area — multi-agency analysis requires merging feeds
stop locations provide point geometry; route shapes provide line geometry
no standard administrative boundary layer is included — join with Census or local geography as needed

Time Coverage:
GTFS feeds describe a specific service period (typically 3-6 months, sometimes up to a year)
feeds are updated periodically as schedules change (seasonal service, route modifications, fare changes)
the feed's `calendar.txt` and `calendar_dates.txt` define which service runs on which days
historical feeds are available from some aggregators for longitudinal analysis
always confirm the feed's effective date range before analysis — an expired feed describes service that no longer exists

Access Method:
direct download from transit agency websites (look for "developer resources" or "open data")
Transitland (https://www.transit.land/) — aggregated feed discovery and download
Mobility Database (https://database.mobilitydata.org/) — canonical feed registry
Fetch Script:
`scripts/core/fetch_gtfs.py` — download by URL or search Mobility Database by agency name
OpenMobilityData / GTFS Data Exchange (legacy aggregators, some still active)
some agencies provide API endpoints for GTFS and GTFS Realtime

File Formats:
GTFS Static: a ZIP archive containing multiple CSV (`.txt`) files
GTFS Realtime: Protocol Buffer (protobuf) feeds for live vehicle positions, trip updates, and alerts

Key Files in a GTFS Static Feed:
- **agency.txt:** transit agency information
- **routes.txt:** route definitions (route ID, name, type — bus, rail, ferry, etc.)
- **trips.txt:** individual trips on each route, linked to service calendar
- **stops.txt:** stop locations with latitude/longitude — the primary geometry layer
- **stop_times.txt:** arrival and departure times at each stop for each trip — the core schedule data (often the largest file)
- **calendar.txt:** service patterns by day of week
- **calendar_dates.txt:** service exceptions (holidays, special events)
- **shapes.txt:** (optional) route geometry as ordered point sequences — provides line geometry for route mapping
- **frequencies.txt:** (optional) frequency-based service description instead of exact times
- **fare_attributes.txt / fare_rules.txt:** (optional) fare structure

Licensing / Usage Notes:
most GTFS feeds are published as open data, but licensing varies by agency
some agencies use Creative Commons, some use custom open-data licenses, some have no explicit license
check each agency's terms before redistribution
GTFS Realtime data may have additional terms or rate limits
attribution to the transit agency is standard practice

Known Caveats:
GTFS describes scheduled service, not actual service — delays, cancellations, and reroutes are not reflected in GTFS Static
feed quality varies: some agencies publish meticulously validated feeds, others have missing shapes, incorrect stop locations, or schedule errors
stop_times.txt can be extremely large (millions of rows for a major metro agency) — filter by route, time window, or date before loading into memory
not all agencies include shapes.txt — without it, route geometry must be inferred from stop sequences
transfer rules between agencies are often informal or missing — multi-agency routing requires explicit transfer definitions or proximity-based transfer assumptions
frequency-based services (frequencies.txt) and exact-time services (stop_times.txt) require different handling in accessibility analysis
wheelchair accessibility, bike accommodation, and other service attributes are optional fields and may not be populated
demand-response and paratransit services are sometimes but not always represented in GTFS
feed expiration is a real risk: if the feed's service period has ended, the data describes service that may no longer exist
coordinate quality for stops is usually good in urban areas but may be imprecise in rural areas or for agencies with less GIS capacity

Best-Fit Workflows:
workflows/SERVICE_AREA_ANALYSIS.md (transit-mode service areas when the routing engine supports GTFS)
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md (transit context packaging)
workflows/WITHIN_DISTANCE_ENRICHMENT.md (stop proximity analysis)

Best-Fit Domains:
domains/TRANSIT_ACCESS_AND_COVERAGE.md
domains/ACCESSIBILITY_AND_NETWORK_ANALYSIS.md
domains/PEDESTRIAN_AND_BICYCLE_ACCESS.md (multimodal access)
domains/WORKFORCE_AND_LABOR_SHED_ANALYSIS.md (commute-mode context)
domains/COMMUNITY_FACILITY_PLANNING.md (transit access to facilities)
domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md (transit equity)

Preferred Tools for GTFS Analysis:
- **OpenTripPlanner (OTP):** open-source multimodal routing engine that consumes GTFS + OSM for transit travel-time analysis
- **r5 / Conveyal:** high-performance multimodal routing engine designed for accessibility analysis at scale
- **gtfs-kit, partridge, gtfslite:** Python libraries for reading, validating, and querying GTFS feeds
- **GTFS Validator (MobilityData):** canonical feed validator (https://gtfs-validator.mobilitydata.org/)
- **Valhalla:** supports multimodal routing with GTFS integration
- **QGIS GTFS plugins:** for visualization and basic stop/route mapping

Alternatives:
ACS commute-mode variables (B08301): survey-based mode share at tract level, no schedule or route detail
agency-published route maps (PDF or GIS): static geometry without schedule information
Google Maps / Transit Directions API: provides transit routing but is proprietary, rate-limited, and not suitable for bulk analysis
Apple Maps transit data: proprietary, not available for bulk download
UrbanAccess (UDOT tool): Python library for computing transit access metrics from GTFS and OSM

Sources:
GTFS specification: https://gtfs.org/
MobilityData GTFS reference: https://gtfs.org/schedule/reference/
Transitland: https://www.transit.land/
Mobility Database: https://database.mobilitydata.org/
OpenTripPlanner: https://www.opentripplanner.org/
GTFS Validator: https://gtfs-validator.mobilitydata.org/
GTFS Best Practices: https://gtfs.org/schedule/best-practices/

Trust Level
Validated Source Page
Needs Source Validation (feed quality and currency vary by agency)
