# Workflow Handbook — Analysis and Output Generation

## Purpose
Standardize how processed datasets are analyzed and turned into maps, tables, and structured analysis artifacts.

## Typical Inputs
- processed spatial/tabular datasets in `data/processed/`
- processing handoff artifact in `runs/` (documents upstream steps and warnings)
- analysis brief specifying metrics, fields, and geographic scope

## Typical Outputs
- summary statistics tables in `outputs/tables/` (CSV)
- choropleth map PNGs in `outputs/maps/`
- ranking tables in `outputs/tables/` (CSV)
- sidecar JSON logs for each analysis step
- analysis handoff artifact in `runs/`

## Steps
1. **Verify inputs** exist and the processing handoff is present. Do not proceed without knowing what upstream processing was done.
2. **Compute summary statistics** for numeric fields. Report null counts and coverage. If a filter is needed (e.g., only rows with demographic data), document the filter as an assumption.
3. **Generate maps** (choropleth) for selected spatial metrics. Use appropriate classification. Annotate missing/null features visually. Include legend and title.
4. **Rank features** (top/bottom N) for selected metrics. Exclude nulls from ranking and document exclusions.
5. **Write analysis handoff** summarizing all outputs, assumptions, warnings, and upstream references.

## Required QA
- all output files listed in the handoff actually exist
- null handling is documented in every analysis log
- choropleths include legend, title, and missing-data annotation
- summary stats include null counts and non-null counts
- ranking tables clearly label top vs. bottom entries
- analysis handoff references the upstream processing handoff
- partial coverage is explicitly noted, not hidden

## Common Pitfalls
- treating partial-coverage results as representative
- choosing classification schemes without considering data distribution
- forgetting to filter before computing demographic statistics on a mostly-null join
- not writing sidecar logs for analysis outputs
- generating maps with no legend or missing-data indication

## Example Tasks
- Compute summary stats for area and demographic fields, generate a water-percentage choropleth, rank tracts by median income, and write an analysis handoff.
- Generate a population density choropleth for counties with a natural breaks classification.

## Notes / Lessons
- Analysis is not complete until the handoff artifact exists in `runs/`.
- Always check the upstream processing handoff for unresolved warnings before starting analysis.
- When demographic data covers only a fraction of features, run both full-coverage stats (e.g., area fields) and filtered-subset stats (e.g., demographic fields) to give downstream agents an honest picture.
