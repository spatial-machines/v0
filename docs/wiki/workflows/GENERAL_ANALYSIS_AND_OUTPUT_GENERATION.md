# General Analysis and Output Generation Workflow

## Purpose

- define the general sequence for turning processed datasets into analysis outputs (summary statistics, classifications, rankings, derived analytical fields, and the analysis handoff to validation)
- establish shared conventions that domain-specific analysis workflows inherit (`workflows/DECADE_TREND_ANALYSIS.md`, `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md`, `workflows/ACS_DEMOGRAPHIC_INVENTORY.md`)
- ensure every analysis run has documented null handling, classification rationale, and a recorded handoff to validation

This workflow is the analysis-stage counterpart to `workflows/GENERAL_RETRIEVAL_AND_PROVENANCE.md`, `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`, `workflows/VALIDATION_AND_QA_STAGE.md`, `workflows/REPORTING_AND_DELIVERY.md`, and `workflows/LEAD_ANALYST_ORCHESTRATION.md`. Together they define the firm's general pipeline canon.

## Relationship to Other Canon

This workflow describes the **general analysis sequence**. Specialized methods live in dedicated canon and are referenced rather than restated here.

| Belongs on this workflow page | Belongs elsewhere |
|---|---|
| Summary statistics computation conventions | Cartographic rendering — see `standards/CARTOGRAPHY_STANDARD.md` and `workflows/CHOROPLETH_DESIGN.md`, `workflows/POINT_OVERLAY_DESIGN.md`, `workflows/HOTSPOT_MAP_DESIGN.md`, `workflows/BIVARIATE_CHOROPLETH_DESIGN.md` |
| Classification scheme selection (when to use natural breaks vs. quantile vs. equal interval vs. manual) | Spatial autocorrelation, hotspot, LISA — see `standards/SPATIAL_STATS_STANDARD.md` and `workflows/SPATIAL_AUTOCORRELATION_TEST.md`, `workflows/HOTSPOT_ANALYSIS.md`, `workflows/LISA_CLUSTER_ANALYSIS.md` |
| Ranking outputs (top-N selection, exclusion rules) | Time-series trend method — see `standards/TREND_ANALYSIS_STANDARD.md` and `workflows/DECADE_TREND_ANALYSIS.md` |
| Null handling and coverage rules | Demographic shift framing — see `standards/DEMOGRAPHIC_SHIFT_STANDARD.md` and `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md` |
| Derived analytical fields beyond processing-level rates and shares | Processing-level rates / shares / densities / area — see `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` step 9 |
| The analysis handoff to validation (informational fields it conveys) | Aggregation rules across geographies — see `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` and `standards/ZIP_ZCTA_AGGREGATION_STANDARD.md` |

The analysis handoff JSON schema is owned by `ARCHITECTURE.md` § Analysis Handoff and the canonical core scripts. This workflow describes what fields the handoff conveys, not the JSON shape.

## Typical Use Cases

- producing summary statistics, classifications, rankings, and the analysis handoff for any analytical task that does not match a domain-specific workflow
- preparing analytical outputs for cartographic rendering and validation
- coordinating partial-coverage analyses where some metrics apply to all features and others apply only to a filtered subset
- providing the upstream stage for `workflows/VALIDATION_AND_QA_STAGE.md`

## Inputs

- processed spatial / tabular datasets in `data/processed/` produced by `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` (or a domain-specific processing workflow)
- the processing handoff artifact in `runs/` (documents upstream processing steps and warnings; the analysis stage must read this before proceeding)
- the analysis brief specifying metrics, fields, and geographic scope
- the project brief constraints on audience, deliverables, and time period

## Preconditions

- structural QA on the processed dataset has passed per `standards/STRUCTURAL_QA_STANDARD.md`
- the processing handoff exists in `runs/` and has been read for unresolved warnings
- CRS is documented per `standards/CRS_SELECTION_STANDARD.md`
- the analysis brief specifies which metrics, classifications, and rankings are required
- when the analysis is a specialization (trend, demographic shift, ACS inventory), the relevant domain workflow has been read in addition to this page

## Preferred Tools

- pandas / GeoPandas for tabular and spatial computation
- numpy / scipy for statistical methods
- canonical core scripts under `scripts/core/` for production runs (e.g., `run_choropleth.py`, `run_hotspot.py`, `run_bivariate_choropleth.py`)

The wiki workflow describes the method. The script implementation lives in the canonical core scripts.

## Execution Order

1. **Read the upstream processing handoff.** Before computing anything, read the processing handoff from `runs/` and note: which datasets were processed, what join match rates were achieved, what warnings were raised, what the join coverage looks like, and whether any processing-level transformations affect the analytical question. Skipping this step is the most common source of false alarms (e.g., reporting low demographic coverage as a failure when the upstream join was intentionally limited).
2. **Compute summary statistics for numeric fields.** For each field that the analysis brief requires, compute count, non-null count, null count, min, max, mean, median, and quartiles. Document the null counts explicitly — they are not optional metadata. If the field has a meaningful zero or sentinel value, distinguish that from null.
3. **Decide null handling per metric.** A metric can be: full-coverage (computed across all features), filtered-subset (computed only across features that have non-null values for the inputs), or both. The analysis brief or the project brief drives this choice. Whichever is chosen, the choice is documented as an assumption in the analysis log. **Never silently exclude nulls.**
4. **Compute derived analytical fields** beyond the processing-level rates and shares. This is where statistical comparisons, normalized indices, ratios across vintages, and cross-field aggregations live. Processing-level fields (rates, shares, densities, areas) come pre-computed from the processing stage; the analysis stage adds analytical fields built on top of them. Document the formula for every derived field.
5. **Choose a classification scheme** for any field that will feed a categorical output (a choropleth, a ranking tier, a threshold-based filter). Match the scheme to the data:
   - **natural breaks** for skewed distributions
   - **quantile** when the project asks for rank framing
   - **equal interval** for uniform distributions
   - **standard deviation** for deviation framing
   - **manual** when defending against a known threshold (and the threshold is documented)
   The classification choice is recorded in the analysis log. Five classes is the firm's choropleth maximum per `standards/CARTOGRAPHY_STANDARD.md`.
6. **Generate analytical outputs.** Tables go to `outputs/tables/` (CSV with column headers, no abbreviations). Spatial analytical outputs that will be rendered as maps stay as GeoDataFrames or are written to `data/processed/` with a new analytical field. Map rendering itself is the cartography stage's responsibility, governed by `standards/CARTOGRAPHY_STANDARD.md` and the four cartography workflow pages — this analysis workflow does not render maps, it produces the analytical fields the map workflows consume.
7. **Rank features** for any metric the analysis brief calls for. Top-N or bottom-N selection. **Exclude nulls from ranking and document the exclusion in the analysis log.** Tie-breaking rules are explicit (alphabetical, secondary metric, or first-come). Ranking output tables clearly label whether they are top or bottom rankings, what the metric is, and what the time period and geography are.
8. **Write per-step analysis logs.** Each major step (summary stats, classification, derivation, ranking) gets a sidecar JSON in `runs/` or `outputs/qa/` recording the inputs, the parameters, the outputs, and any warnings. Logs are append-only and reference the upstream processing handoff.
9. **Write the analysis handoff to validation.** Produce the structured handoff artifact in `runs/` that conveys: the list of analytical outputs (file paths and field names), the upstream processing handoff reference, the classification choices, the null-handling decisions, the ranking exclusions, the warnings raised during analysis, and the readiness state for the validation stage. The exact JSON schema is owned by `ARCHITECTURE.md` § Analysis Handoff and the canonical core scripts; this workflow describes what the handoff conveys, not its on-disk shape.

## Validation Checks

- the upstream processing handoff was read before analysis began (the analysis log records the read)
- summary statistics include null counts for every numeric field
- null handling per metric is documented as an assumption
- partial-coverage results are explicitly labeled as such, not silently treated as full-coverage
- derived field formulas are documented
- classification scheme is documented per field; the choice is appropriate to the distribution
- ranking outputs document the exclusion of nulls and the tie-breaking rule
- per-step analysis logs exist for every major step
- the analysis handoff exists in `runs/` and references the upstream processing handoff
- the handoff conveys the analytical output paths, classification choices, null-handling decisions, warnings, and readiness state
- structural QA per `standards/STRUCTURAL_QA_STANDARD.md` is achievable from the analytical output fields
- no analytical claim made in the handoff is unsupported by an output file or log

## Common Failure Modes

- treating partial-coverage results as if they were representative of all features
- silently excluding nulls from a calculation and not documenting the exclusion
- choosing a classification scheme without considering the data distribution (e.g., equal interval on heavily skewed data)
- forgetting to filter before computing demographic statistics on a mostly-null join
- not writing per-step analysis logs (the analysis stage produces undocumented outputs)
- generating an analytical output without recording the formula or the inputs that produced it
- ranking features without excluding nulls, producing a top-N list with null-valued features at the top
- writing the analysis handoff before the per-step logs exist, so the handoff cannot be reconstructed
- producing a derived field that overlaps with a processing-level field and creating ambiguity about which value is canonical
- not reading the upstream processing handoff and reporting normal partial coverage as a failure
- claiming statistical significance without documenting the test or the threshold (and without consulting `standards/SPATIAL_STATS_STANDARD.md` when the question is spatial)
- attempting to render a map directly in this workflow instead of handing off to the cartography canon

## Escalate When

- the upstream processing handoff was not produced or cannot be located
- the processing handoff documents warnings that are severe enough to call the analysis into question (low join match rate, missing required fields, undocumented filters)
- the analysis brief requires a metric that the processed dataset does not support
- partial coverage is so severe that no honest summary statistic can be reported
- the field distribution is bimodal or otherwise resistant to standard classification methods
- a null-handling decision could materially change the analytical conclusion
- the question is spatial-statistical (clustering, hotspot, autocorrelation) and the firm's `standards/SPATIAL_STATS_STANDARD.md` rules apply — escalate to the relevant spatial stats workflow rather than improvising
- the question is a trend or shift question and the firm's `standards/TREND_ANALYSIS_STANDARD.md` or `standards/DEMOGRAPHIC_SHIFT_STANDARD.md` rules apply — escalate to the relevant domain workflow

## Outputs

- summary statistics tables in `outputs/tables/` (CSV)
- ranking tables in `outputs/tables/` (CSV)
- analytical fields added to the processed dataset (typically in `data/processed/` as a new GeoPackage layer or appended fields)
- per-step analysis logs (JSON) in `runs/` or `outputs/qa/`
- the analysis handoff artifact in `runs/`

For the exact JSON schema of the analysis handoff, see `ARCHITECTURE.md` § Analysis Handoff and the canonical core scripts. This workflow describes what the artifact conveys, not its on-disk shape. Map rendering is owned by the cartography canon and is performed downstream of this workflow.

## Relationship to Domain-Specific Analysis Workflows

This workflow defines the general analysis conventions. Domain-specific workflows inherit these conventions and add domain-specific steps:

- `workflows/DECADE_TREND_ANALYSIS.md` — specializes the analysis for 10-year trend windows. Adds endpoint integrity, vintage matching, and inflation handling per `standards/TREND_ANALYSIS_STANDARD.md`.
- `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md` — specializes the analysis for demographic change framing. Adds count vs. share distinction, category comparability, and the framing rules from `standards/DEMOGRAPHIC_SHIFT_STANDARD.md`.
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — specializes the analysis for first-wave demographic inventory at project intake. Adds variable classification (snapshot / 10-year / extended-history) and the inventory deliverable shape.

When a domain-specific analysis workflow exists for the analytical task, use it. Fall back to this general workflow for tasks not covered by a domain-specific page.

## Related Standards

- `standards/STRUCTURAL_QA_STANDARD.md` — quality precondition for the input data
- `standards/CRS_SELECTION_STANDARD.md` — projection requirements
- `standards/SOURCE_READINESS_STANDARD.md` — source tier that influences how confidently the analysis can be reported
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — general provenance fields the analysis handoff inherits
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md` — aggregation rules when analytical fields cross geographies
- `standards/CARTOGRAPHY_STANDARD.md` — governs the map rendering downstream of this workflow
- `standards/SPATIAL_STATS_STANDARD.md` — governs spatial autocorrelation and clustering when those are part of the analytical question
- `standards/TREND_ANALYSIS_STANDARD.md` — governs trend analyses
- `standards/DEMOGRAPHIC_SHIFT_STANDARD.md` — governs demographic shift framing

## Related Workflows

- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — the immediate upstream stage; produces the input dataset and the processing handoff
- `workflows/VALIDATION_AND_QA_STAGE.md` — the immediate downstream stage; consumes the analysis handoff
- `workflows/DECADE_TREND_ANALYSIS.md` — domain specialization
- `workflows/DEMOGRAPHIC_SHIFT_ANALYSIS.md` — domain specialization
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — domain specialization
- `workflows/CHOROPLETH_DESIGN.md` — the cartography workflow that consumes analytical fields and renders the map
- `workflows/POINT_OVERLAY_DESIGN.md` — cartography workflow when points are part of the deliverable
- `workflows/HOTSPOT_MAP_DESIGN.md` — cartography workflow when the analytical output is a clustering result

## Related QA

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity gate run upstream and re-run downstream
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative-side review for any client-facing claim derived from the analysis
- `qa-review/MAP_QA_CHECKLIST.md` — for the cartographic side of any rendered analytical output
- `qa-review/SPATIAL_STATS_OUTPUT_REVIEW.md` — when the analysis includes spatial autocorrelation or clustering
- `qa-review/TREND_OUTPUT_REVIEW.md` — when the analysis includes trend or change-over-time outputs

## Sources

- firm analysis methodology
- pandas and GeoPandas documentation
- numpy and scipy documentation

## Trust Level

Validated Workflow — Needs Testing
