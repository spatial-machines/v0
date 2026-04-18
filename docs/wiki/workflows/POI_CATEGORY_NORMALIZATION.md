# POI Category Normalization Workflow

Purpose:
convert raw source categories (OSM tags, PostGIS labels, vendor codes) into a consistent firm-approved category taxonomy
make POI outputs comparable across projects, sources, and time periods
produce the normalized category layer that
workflows/POSTGIS_POI_LANDSCAPE.md
and
qa-review/POI_EXTRACTION_QA.md
expect
Typical Use Cases
normalizing OSM amenity/shop/leisure tags into a client-facing business taxonomy
harmonizing POI categories from multiple sources into a single classification
building a reusable category lookup table for a study area or industry vertical
preparing POI data for enrichment, counting, or density analysis
Inputs
raw POI extraction (from
workflows/POSTGIS_POI_LANDSCAPE.md
or equivalent)
approved category specification from the project brief
existing firm category lookup tables if available
OSM tagging reference documentation
Preconditions
the raw POI extraction is complete and has passed initial geometry validation
the project has an explicit approved category list or the analyst has authority to propose one
the study area and source are confirmed
Preferred Tools
pandas / GeoPandas for tabular mapping
SQL (PostGIS) for database-native normalization
firm category lookup scripts if available
Execution Order
Phase 1: Source Category Inventory
Extract the distinct raw category values from the POI dataset.
for OSM: the relevant tag keys and value combinations (e.g., amenity=restaurant, shop=supermarket, cuisine=*)
for PostGIS firm tables: the existing category or type columns
for vendor data: the vendor's classification codes
Count the frequency of each raw category value.
Identify:
high-frequency categories that clearly map to the approved taxonomy
ambiguous categories that need judgment
rare categories that may be noise or special cases
missing categories that the project expects but the source does not contain
Phase 2: Mapping Table Construction
Build a mapping table with columns:
raw_category
: the source value exactly as it appears
normalized_category
: the firm-approved category label
mapping_rationale
: brief note on why this mapping was chosen (especially for ambiguous cases)
action
: one of: map, exclude, escalate
Map clear cases first (e.g., amenity=restaurant → Restaurant).
Resolve ambiguous cases:
if the project has guidance, follow it
if not, propose a mapping and flag for review
document the decision
Handle unmapped categories:
assign to a catchall category (e.g., "Other / Unclassified") if the project permits
exclude if the category is clearly outside scope
escalate if the category could materially affect the analysis
Save the mapping table as a reusable artifact (CSV, database table, or lookup within the processing script).
Phase 3: Application
Join or map the raw POI layer to the normalized categories using the mapping table.
Add the
normalized_category
field to the POI layer.
Retain the
raw_category
field so the normalization can be audited.
For features with multiple relevant tags (e.g., a gas station with a convenience store), apply the project's multi-tag resolution rule:
assign to the primary category
or create one record per category (document which approach is used)
Phase 4: Validation
Count features per normalized category and compare against the raw category counts.
Confirm that no features were silently dropped during normalization.
Confirm that excluded categories were intentional and documented.
Spot-check ambiguous mappings against the source data.
Run through
qa-review/POI_EXTRACTION_QA.md
category normalization checks.
Validation Checks
every raw category value has a documented mapping, exclusion, or escalation
the mapping table is saved as a reusable artifact
feature counts before and after normalization reconcile
ambiguous mappings are documented with rationale
the normalized category labels match the project-approved taxonomy
multi-tag features are handled consistently
Common Failure Modes
applying an old mapping table to a new study area where different OSM tags are common
silently excluding categories that contain relevant POIs
mapping ambiguous categories inconsistently within the same project
not preserving the raw category field, making the normalization non-auditable
treating OSM tags as stable when they can change between extracts
missing cuisine or sub-type tags that the project needs for finer classification
not documenting the multi-tag resolution rule
Escalate When
the approved category list does not cover a significant portion of the raw data
OSM tagging is too inconsistent for the required category granularity
the project requires a formal taxonomy (NAICS, SIC) but the source uses freeform tags
the mapping table from a prior project does not transfer cleanly to the new study area
more than 10% of features fall into "Other / Unclassified" after normalization
Outputs
normalized POI layer with both raw and normalized category fields
category mapping table (CSV or database table)
normalization summary: counts per category before and after
documentation of ambiguous mappings and exclusion decisions
Related Standards
standards/OPEN_EXECUTION_STACK_STANDARD.md
standards/SOURCE_READINESS_STANDARD.md
qa-review/POI_EXTRACTION_QA.md
workflows/POSTGIS_POI_LANDSCAPE.md
workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md
— general processing conventions this workflow specializes for POI category fields
data-sources/OSM.md
Sources
OSM Map Features wiki (https://wiki.openstreetmap.org/wiki/Map_features)
OSM Taginfo (https://taginfo.openstreetmap.org)
firm POI methodology notes and category lookup tables
Trust Level
Draft Workflow Needs Testing
