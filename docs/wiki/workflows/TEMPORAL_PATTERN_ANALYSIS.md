# Temporal Pattern Analysis Workflow

Purpose:
define a repeatable process for analyzing time-based patterns in spatial event data
support time-of-day, day-of-week, monthly, and seasonal pattern detection for incident, activity, and usage datasets
produce temporal summaries and visualizations that complement spatial analysis without inventing forecasting or predictive methodology

Typical Use Cases
- when do crime incidents concentrate by hour, day, and season?
- which days or months show peak visitor or customer activity at a location?
- how does service demand vary across time periods for emergency or facility planning?
- do temporal patterns differ across geographic zones within the study area?
- how should temporal findings be combined with spatial hotspot or density results?

Inputs
- event or activity dataset with timestamp fields (date, time, or datetime)
- study area boundary or set of study geographies
- project-approved temporal groupings (hour of day, day of week, month, season, or custom periods)
- project-approved working CRS (when spatial joins are part of the workflow)

Preconditions
- the timestamp field is parsed and validated (consistent format, timezone documented, no null timestamps in analysis records)
- the distinction between "occurred date/time" and "reported date/time" is understood and the correct field is selected for the analysis question
- the data covers a sufficient time range for the temporal resolution requested (e.g., seasonal analysis requires at least one full year)
- reporting consistency across the time range is confirmed — gaps, changes in classification, or shifts in reporting practice are documented

Preferred Tools
- pandas for temporal grouping, aggregation, and summary statistics
- GeoPandas for spatial-temporal joins (`toolkits/GEOPANDAS_TOOLKIT.md`)
- PostGIS for scale and time-filtered spatial queries (`toolkits/POSTGIS_TOOLKIT.md`)
- matplotlib or similar for temporal visualization (bar charts, heatmaps, line charts)

Execution Order

## Phase 1: Timestamp Validation

1. Confirm the timestamp field name, format, and timezone.
2. Parse timestamps into a consistent datetime format.
3. Check for null, invalid, or out-of-range timestamps — document how they are handled (excluded, flagged, or corrected).
4. Confirm whether the field represents "occurred" or "reported" time and document the choice.
5. Summarize the time range: earliest record, latest record, total span.

## Phase 2: Temporal Grouping

1. Extract temporal components from the datetime field:
   - hour of day (0-23)
   - day of week (Monday-Sunday)
   - month (1-12)
   - season (winter/spring/summer/fall, or project-defined)
   - custom period if applicable (shift, school year, fiscal quarter)
2. Create grouping columns for each approved temporal resolution.
3. Document the grouping definitions (e.g., which months define "summer").

## Phase 3: Temporal Aggregation

1. Count events per temporal group (e.g., incidents per hour of day, per day of week).
2. Calculate rates or averages where appropriate:
   - mean daily count by day of week
   - mean hourly count by hour of day
   - monthly totals or monthly averages across years
3. If comparing across time periods of different lengths, normalize appropriately (e.g., per-day average rather than raw total for months with different day counts).
4. If the analysis requires cross-tabulation (hour-of-day by day-of-week heatmap), produce the pivot table.

## Phase 4: Spatial-Temporal Integration (when applicable)

1. If the question requires geographic variation in temporal patterns:
   - join events to study geographies using spatial joins per the event's point geometry
   - repeat the temporal aggregation for each geographic zone
2. Compare temporal patterns across zones to identify geographic variation.
3. If combining with spatial statistics (hotspot, clustering), document whether the spatial analysis was run on all time periods or a specific temporal subset.

## Phase 5: Validation

1. Validate that event counts per temporal group are plausible:
   - overnight hours should generally show lower counts for most activity types
   - weekend vs. weekday patterns should be consistent with the activity type
   - monthly patterns should not show implausible spikes unless explained by known events
2. Check for artifacts from reporting gaps or classification changes:
   - a sudden drop in monthly counts may indicate a reporting gap, not a real decline
   - a sudden spike may indicate a classification change or backlog processing
3. Validate structural integrity with `qa-review/STRUCTURAL_QA_CHECKLIST.md`.
4. Review interpretive claims with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`:
   - temporal patterns describe when events are recorded, not necessarily when they occur (for reported-date analysis)
   - seasonal patterns require sufficient data volume to distinguish real cycles from noise
   - correlation between temporal patterns and external factors (weather, events, policy changes) should not be presented as causation

## Phase 6: Output

1. Produce temporal summary tables (counts, rates, or averages per temporal group).
2. Produce temporal visualizations:
   - bar chart: event count by hour of day
   - bar chart: event count by day of week
   - line chart: monthly trend
   - heatmap: hour of day vs. day of week
3. If spatial-temporal integration was performed, produce zone-level temporal summaries and comparison tables.
4. Document: timestamp field used, temporal groupings, normalization method, time range, any exclusions.
5. Route maps and spatial products through `domains/CARTOGRAPHY_AND_DELIVERY.md`.

Validation Checks
- timestamp field and format are documented
- "occurred" vs. "reported" distinction is documented and the correct field is used
- temporal grouping definitions are documented
- event counts per group are plausible for the data type and time range
- reporting gaps or classification changes are identified and noted
- normalization is applied where periods have different lengths
- interpretive claims do not overstate the strength of temporal patterns from small samples

Common Failure Modes
- analyzing "reported date" when "occurred date" was the correct field (or vice versa)
- not documenting timezone or mixing events from different timezones
- seasonal analysis from less than one full year of data
- presenting raw monthly totals without normalizing for month length
- interpreting a reporting gap as a real decline in activity
- claiming seasonal or temporal significance from a small number of events
- not checking for classification or reporting-practice changes across the time range
- producing temporal visualizations without stating the time range they cover

Escalate When
- the client requires forecasting, prediction, or trend extrapolation (this workflow describes patterns, not predictions)
- the temporal pattern contradicts prior assumptions and could change a policy or operational recommendation
- the data has significant reporting gaps or known classification changes within the analysis period
- the temporal analysis will be used for staffing, resource allocation, or operational deployment decisions
- the data contains sensitive temporal information (incident timing that could identify individuals)

Outputs
- temporal summary tables
- temporal visualizations (bar charts, heatmaps, line charts)
- spatial-temporal comparison tables (if geographic variation was analyzed)
- methodology documentation (timestamp field, groupings, normalization, time range, exclusions)

Related Standards
- `standards/SOURCE_READINESS_STANDARD.md`
- `standards/INTERPRETIVE_REVIEW_STANDARD.md`
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`

Related Workflows
- `workflows/HOTSPOT_ANALYSIS.md` — spatial pattern analysis that complements temporal analysis
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md` — output packaging
- `workflows/DECADE_TREND_ANALYSIS.md` — long-horizon trend analysis (different purpose: year-over-year demographic change vs. within-period temporal patterns)

Related QA
- `qa-review/STRUCTURAL_QA_CHECKLIST.md`
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`

Best-Fit Domains
- `domains/CRIME_PUBLIC_SAFETY_AND_INCIDENT_MAPPING.md`
- `domains/TOURISM_HOSPITALITY_AND_VISITOR_ANALYSIS.md`
- `domains/EMERGENCY_OPERATIONS_AND_COVERAGE_PLANNING.md`
- `domains/TRANSPORTATION_SAFETY_AND_CRASH_ANALYSIS.md`

Trust Level
Draft Workflow Needs Testing
