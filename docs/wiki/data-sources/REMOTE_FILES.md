# Remote Files Source Page

Source Summary:
covers any dataset retrievable via direct HTTP / HTTPS download from a URL
this is a category-level source page for ad hoc remote downloads, not a named external data provider
use this page when the source does not have its own dedicated wiki source page (e.g., a one-off download from a state data portal, an open-data hub, or a GitHub raw URL)
prefer source-specific pages (CENSUS_ACS, TIGER_GEOMETRY, USGS_ELEVATION, OSM) when the URL belongs to a known provider

Owner / Publisher:
varies by URL; must be identified and recorded during retrieval
filenames and URL paths are not provenance — confirm the publisher from the page or portal that hosts the file

Geography Support:
determined per dataset after download and inspection
no assumptions about coverage or projection are valid until the file has been opened

Time Coverage:
determined per dataset
record the download date and any source-declared vintage; the two are not interchangeable

Access Method:
Fetch Script:
`scripts/core/retrieve_remote.py` — download any file by URL with manifest sidecar
Usage:
preferred: HTTP GET with streamed download into `data/raw/`
fallback: manual browser download and placement into `data/raw/`
do not read directly from remote URLs in analysis scripts; always download first, then load locally
record the resolved URL after redirects, not just the original URL
when the server provides Content-Length, record it; when the server provides ETag or Last-Modified, record those too

Supported Formats:
CSV
GeoJSON
JSON
ZIP (may contain shapefile, GeoPackage, or other formats; inspect after extraction)
GeoPackage (.gpkg)
Parquet
other formats on a case-by-case basis after toolchain confirmation

Licensing / Usage Notes:
varies by source; check and record any license terms at the time of download
open-data portals typically publish under permissive licenses but the specific terms must be documented
some sources restrict redistribution, commercial use, or derivative work; record any such restriction in the provenance
download the source's terms-of-use page (or capture a screenshot) when the license is not embedded in the dataset itself

QA Checks (source-specific):
1. HTTP response status is in the 2xx range
2. file saved successfully to `data/raw/` with the expected filename
3. content length recorded when the server provides it; size is plausible for the expected dataset
4. file is readable after download: not truncated, not corrupt, not an HTML error page masquerading as a download
5. if ZIP: archive extracts cleanly, contents are inventoried, and any nested directories are flattened or noted
6. provenance recorded: resolved URL, download timestamp, HTTP status, response headers when relevant
7. if spatial: CRS inspected after download and EPSG code recorded per `standards/CRS_SELECTION_STANDARD.md`

Known Pitfalls:
some servers block direct programmatic access via user-agent restrictions, CAPTCHA challenges, or HTTP redirects; manual download may be required
ZIP archives may contain nested directories or unexpected file structures; do not assume a flat layout
filename may need to be inferred from the URL or from a Content-Disposition header
remote sources can change, move, or disappear without notice; always save a local copy and never re-fetch silently in analysis scripts
large files may need streaming download to avoid memory issues
HTTPS certificate issues are common on government and state portals; record any verification overrides explicitly
servers sometimes return an HTML landing page or login form with HTTP 200; check Content-Type and the first few bytes before trusting the download
URLs that work today may be paywalled, geofenced, or rate-limited tomorrow; the firm assumes nothing about long-term availability

Source Readiness Tier Guidance:
government open-data portals with documented methodology and stable URLs: Tier 2 (Validated but Caveated)
ad hoc URLs with no documentation: Tier 3 (Provisional) at best
unknown or unverifiable sources: Tier 4 (Unreviewed); escalate before using
see `standards/SOURCE_READINESS_STANDARD.md` for tier definitions and their consequences

Retrieval Contract:
this page covers source-specific intake for remote file downloads
for the general retrieval workflow (manifest writing, run provenance, handoff to processing), see `workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md`
do not redefine manifest or provenance schema on this page

Best-Fit Workflows:
any workflow where input data is available as a direct download
`workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` for cleaning, normalization, and join preparation after download
`workflows/TRACT_JOIN_AND_ENRICHMENT.md` when supplementary tabular data is fetched from a URL
`workflows/GEOCODE_BUFFER_ENRICHMENT.md` when a reference dataset is downloaded for buffer enrichment

Alternatives:
if the URL points to Census data, prefer `data-sources/CENSUS_ACS.md` or `data-sources/TIGER_GEOMETRY.md` which have source-specific retrieval guidance
if the URL points to USGS elevation data, prefer `data-sources/USGS_ELEVATION.md`
if the URL points to an OSM extract, prefer `data-sources/OSM.md`
if the URL points to an Esri Living Atlas layer, prefer `data-sources/LIVING_ATLAS.md`
if the data is already downloaded and present locally, use `data-sources/LOCAL_FILES.md` instead

Sources:
firm intake methodology notes
GDAL / OGR HTTP and curl driver documentation (https://gdal.org/user/virtual_file_systems.html)
Python requests documentation (https://requests.readthedocs.io)

Trust Level:
Validated Source Page
Needs Source Validation (quality, licensing, and stability vary per source)
