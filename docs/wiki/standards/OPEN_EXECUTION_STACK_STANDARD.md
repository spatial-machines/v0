# Open Execution Stack Standard

Purpose:
keep the firm's GIS operating system portable
avoid hidden dependence on proprietary runtime code
make agent workflows reproducible across platforms
support future OSS release paths
Use When
Use this standard for every new workflow, tool decision, and method page.
Do Not Use When
Do not use this standard to ban all proprietary products from the business. The rule is about execution dependency, not ideological purity.
Approved Rule
The firm's default execution stack is open and scriptable.
Preferred operational stack:
Python
GeoPandas
Shapely
Rasterio
GDAL / OGR
PostGIS
PyProj
WhiteboxTools
QGIS-compatible Python workflows
Acceptable secondary roles for proprietary platforms:
source discovery
client delivery environment
comparative reference
optional downstream handoff environment
Avoid as default operational dependency:
ArcPy
proprietary execution chains that cannot run without Esri licensing
closed workflows that cannot be reproduced outside one licensed environment
Inputs
When designing or documenting a workflow, identify:
required data sources
required geometry operations
required raster or network operations
deliverable environment
any claimed proprietary dependency
Method Notes
Prefer open execution paths first.
If a proprietary tool is referenced, document:
why it is being used
whether an open alternative exists
whether the workflow remains portable without it
Treat ArcGIS Online, Living Atlas, and similar systems as delivery or reference layers unless the project explicitly requires otherwise.
Avoid writing workflow pages that implicitly require ArcPy.
Validation Rules
A workflow should fail this standard if:
the primary execution path depends on ArcPy and no open alternative is documented
the steps cannot be reproduced with the approved open stack
the page treats an Esri-specific path as universal
Human Review Gates
Escalate for human review when:
a workflow appears to require a proprietary engine for core analysis
an open alternative is unclear
the client deliverable environment pressures the team into a closed-only method
Common Failure Modes
using Esri docs as if they imply ArcPy is required
confusing delivery platform with analysis engine
letting one specialist's licensed environment become the hidden standard
documenting a workflow in GUI terms only, with no portable execution path
Related Workflows
workflows/ACS_DEMOGRAPHIC_INVENTORY.md
workflows/TRACT_TO_ZIP_ZCTA_ROLLUP.md
workflows/DECADE_TREND_ANALYSIS.md
workflows/POSTGIS_POI_LANDSCAPE.md
workflows/WATERSHED_DELINEATION.md
workflows/TRACT_JOIN_AND_ENRICHMENT.md
Sources
ArcGIS Pro analysis documentation
QGIS documentation and training manual
PostGIS documentation
GDAL documentation
WhiteboxTools documentation
Trust Level
Production Standard
