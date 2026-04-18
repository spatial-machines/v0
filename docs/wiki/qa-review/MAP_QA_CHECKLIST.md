# Map QA Checklist

This checklist is one component of the broader [Validation and QA Stage Workflow](../workflows/VALIDATION_AND_QA_STAGE.md). Use that workflow for stage order, final readiness classification, and validation handoff expectations.

Purpose:
provide a dedicated review checklist for map outputs before client delivery or publication
catch cartographic, classification, and labeling errors that structural and interpretive checklists do not fully cover
ensure maps communicate accurately and do not mislead
Use When
Use this checklist when reviewing any map output, including:
choropleth or graduated-color maps
graduated-symbol maps
dot-density maps
bivariate maps
point maps (POI, facility locations, geocoded sites)
service-area or buffer overlay maps
any map destined for a client deliverable, review site, or publication
Do Not Use When
Do not use this checklist for:
quick internal reference maps used only for analyst orientation during a workflow
raw data previews that will not leave the project team
Core Cartographic Checks
Title and Subtitle
title accurately describes the metric, geography, and time period shown
subtitle provides additional context if the title alone is insufficient
the title does not editorialize or imply a conclusion
Legend
legend is present and legible
legend labels match the actual classification method used
units are shown (e.g., "Percent", "Persons", "Dollars (2022)")
legend color scale is appropriate:
sequential for magnitude (e.g., population count, income level)
diverging for change or deviation (e.g., growth rate, above/below a threshold)
qualitative for categorical data (e.g., land use types, POI categories)
number of legend classes is reasonable (typically 4 to 7 for choropleth maps)
class breaks are defensible: quantile, natural breaks, equal interval, or manually defined with rationale
"no data" or "not applicable" category is shown if relevant features exist
Classification Method
the classification method is documented (quantile, natural breaks, equal interval, standard deviation, manual)
the method is appropriate for the metric:
do not use equal interval for heavily skewed distributions without justification
do not use quantile if the class labels imply absolute thresholds
class breaks have been inspected for misleading splits (e.g., a natural-break boundary that separates nearly identical values)
Geometry and Extent
the map shows the correct study area
the map extent is appropriate: not zoomed out so far that detail is lost, not cropped so tightly that context is missing
features align correctly (no visible CRS mismatch artifacts)
water bodies, boundaries, or other context features are included where they aid interpretation
if the map is clipped to a study area, the clipping boundary is visually indicated
Labels and Annotations
feature labels (tract IDs, ZIP codes, place names) are legible and do not collide
annotations (callouts, highlight boxes) are accurate and point to the correct features
font sizes are readable at the expected display or print size
labels do not obscure the thematic data
Source and Metadata
data source is cited on the map (e.g., "Source: U.S. Census Bureau, ACS 5-Year Estimates, 2018-2022")
date or vintage of the data is shown
CRS or projection note is included if relevant for the audience
attribution requirements are met (e.g., OSM attribution for OSM-derived layers)
Basemap and Visual Hierarchy
the basemap does not overpower the thematic layer
the visual hierarchy guides the eye to the primary story layer
colors are distinguishable for common forms of color vision deficiency (avoid red-green-only palettes)
print maps have been checked in grayscale if the deliverable may be printed in black and white
Escalate When
the classification method materially changes the visual story
the map could be misread to support a conclusion the data does not support
the map involves sensitive topics (race, income, crime) where visual framing matters
class breaks or color scales have been chosen to emphasize or minimize a particular pattern
the map will be used in a legal or regulatory context
Common Failure Modes
using equal-interval classification on a highly skewed distribution, making most features fall in one class
diverging color scale for a non-divergent metric (or vice versa)
missing legend
title that does not match the metric actually mapped
wrong vintage in the source citation
CRS mismatch between thematic layer and basemap causing visual misalignment
illegible labels at the display size
no "no data" category when some features have null values
color palette that is indistinguishable for colorblind viewers
mapping a count (e.g., raw population) on a choropleth without normalizing by area, creating a population-density proxy that misleads
Relationship to Other QA Pages
qa-review/STRUCTURAL_QA_CHECKLIST.md
— run first for data integrity
qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md
— covers narrative alignment; this page covers cartographic craft
standards/CARTOGRAPHY_STANDARD.md
— the firm's cartographic design rules and map family taxonomy that this checklist enforces
standards/PUBLISHING_READINESS_STANDARD.md
— maps must pass this checklist before publishing
standards/CRS_SELECTION_STANDARD.md
— governs projection choices
Trust Level
Validated QA Page Needs Testing
