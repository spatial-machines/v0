# FCC Broadband Availability Source Page

Source Summary:
The FCC publishes broadband availability and deployment data through the Broadband Data Collection (BDC), which replaced the older Form 477 program.
BDC data reports broadband serviceable locations and provider-reported availability at the address level (a major improvement over the block-level Form 477 data).
This is the primary public-domain source for mapping where broadband service is and is not available in the United States, and the authoritative dataset for federal broadband funding programs including BEAD (Broadband Equity, Access, and Deployment).

Owner / Publisher:
Federal Communications Commission (FCC)

Geography Support:
national coverage at the location (address) level for BDC data
Form 477 legacy data is at the Census block level
BDC uses a Broadband Serviceable Location (BSL) fabric — a list of locations where fixed broadband could be installed
state-level and county-level summaries are available
tribal lands are included but coverage reporting may be less complete

Time Coverage:
BDC: biannual filings starting June 2022, with ongoing challenge processes and updates
Form 477: semiannual filings from 2014 through 2020 (legacy, no longer updated)
the BDC fabric and availability data are updated on a rolling basis as challenges are resolved
always check the filing date — broadband availability changes as providers build out and as challenge processes resolve

Access Method:
FCC BDC Public Data: https://broadbandmap.fcc.gov/data-download
FCC National Broadband Map: https://broadbandmap.fcc.gov/
bulk download by state, technology, and filing period
API access for programmatic queries
Form 477 legacy data: https://www.fcc.gov/general/broadband-deployment-data-fcc-form-477

File Formats:
CSV files (primary bulk distribution)
the BSL fabric itself is restricted — only availability data linked to fabric IDs is publicly downloadable
GeoJSON and shapefile derivatives available through some state broadband offices
web map services for preview

Key Data Fields:
- **Technology codes:** 10 (DSL), 40 (cable/DOCSIS), 50 (fiber/FTTH), 60 (fixed wireless), 70 (satellite), others
- **Maximum advertised download/upload speeds:** reported by provider per technology per location
- **Business vs. residential service:** separate filings
- **Provider name and FRN:** Federal Registration Number for each reporting entity
- **Location ID (BSL fabric):** unique identifier for each serviceable location

Speed Tier Thresholds (commonly used):
- **25/3 Mbps:** legacy FCC broadband benchmark (download/upload)
- **100/20 Mbps:** current FCC broadband benchmark as of 2024
- **100/100 Mbps:** BEAD program threshold for "reliable broadband service"
- **1000/500 Mbps:** high-speed or gigabit-class threshold sometimes used in state programs

Licensing / Usage Notes:
public federal data for the availability dataset
the BSL fabric itself has restricted access — requires an FCC fabric license for direct location-level use
availability data can be used freely for analysis, mapping, and reporting
attribution to FCC is standard practice

Known Caveats:
provider-reported availability does not guarantee actual service delivery — a provider may report a location as serviceable without having served it or being willing to connect it at the advertised speed
the BDC challenge process is ongoing and has resulted in significant corrections to initial filings — earlier BDC vintages may overstate availability
Form 477 legacy data overstated availability because it reported at the block level: if one location in a block was served, the entire block was counted as served
satellite broadband (Starlink, etc.) may report broad availability that does not reflect latency, capacity, or practical usability
technology code matters: DSL, cable, fiber, fixed wireless, and satellite have very different performance characteristics even at the same advertised speed
maximum advertised speed is not the same as typical experienced speed — use advertised speeds as upper bounds, not guarantees
the BSL fabric may not include all locations, particularly in areas with non-standard addressing (rural, tribal, unincorporated)
state broadband offices often maintain their own supplementary data that may be more current or more thoroughly challenged than the federal BDC data

Best-Fit Workflows:
workflows/TRACT_JOIN_AND_ENRICHMENT.md (after aggregating location-level data to tract)
workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md (broadband screening and packaging)
workflows/ACS_DEMOGRAPHIC_INVENTORY.md (as demographic complement for digital-divide analysis)

Best-Fit Domains:
domains/BROADBAND_AND_TELECOMMUNICATIONS_ACCESS.md
domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md
domains/UTILITIES_AND_INFRASTRUCTURE_PLANNING.md
domains/POLICY_SUPPORT_AND_PUBLIC_COMMUNICATION_MAPS.md
domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md

Alternatives:
state broadband offices: many states maintain their own broadband availability maps and challenge processes that may be more current
Ookla / Speedtest data: crowd-sourced speed test results that reflect experienced performance rather than advertised availability (licensing required)
M-Lab (Measurement Lab): open speed test data with location information (less structured than FCC data)
Microsoft Airband data: estimated broadband usage based on application behavior (published periodically, not a complete availability map)
NTIA broadband data and Indicators of Broadband Need: federal companion datasets used for BEAD and other grant programs

Sources:
https://broadbandmap.fcc.gov/
https://broadbandmap.fcc.gov/data-download
https://www.fcc.gov/BroadbandData
BEAD program documentation: https://broadbandusa.ntia.doc.gov/
FCC BDC Technical Documentation and filing instructions

Trust Level:
Validated Source Page
