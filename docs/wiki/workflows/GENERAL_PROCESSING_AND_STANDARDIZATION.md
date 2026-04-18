# General Processing and Standardization Workflow

Purpose:

- define the general sequence for cleaning, normalizing, joining, and preparing retrieved datasets before analysis
- establish shared conventions that domain-specific processing workflows inherit
- ensure every processed dataset has documented CRS, join diagnostics, and a processing handoff artifact

## Typical Use Cases

- cleaning and standardizing any newly retrieved dataset before domain-specific analysis
- joining tabular data to spatial geometry when no domain-specific workflow applies
- preparing interim datasets for handoff between pipeline agents
- normalizing field names, types, and encodings across heterogeneous sources

## Inputs

- raw data files in `data/raw/` with retrieval manifests
- processing brief specifying required fields, joins, and output format
- working CRS confirmed per `standards/CRS_SELECTION_STANDARD.md`

## Preconditions

- retrieval is complete and validated — source files exist in `data/raw/` with manifests
- the working CRS has been confirmed per `standards/CRS_SELECTION_STANDARD.md`
- if a join is required, the join key mapping is specified in the processing brief

## Preferred Tools

- GeoPandas for spatial data
- pandas for tabular data
- GDAL / OGR for format conversion and CRS verification
- PostGIS for large-scale or database-backed processing
- Python zipfile / shutil for archive extraction

## Execution Order

1. **Extract** archived sources (ZIP, GDB) into `data/interim/`. Do not modify files in `data/raw/`.
2. **Inspect spatial data.** Verify the CRS is present and correct per `standards/CRS_SELECTION_STANDARD.md`. Reproject to the working CRS if needed. Log the source CRS and any reprojection.
3. **Inspect tabular data.** Check column names, types, encoding, and row counts. Log initial shape.
4. **Normalize column names.** Lowercase, strip whitespace, replace spaces with underscores. Rename fields per the processing brief.
5. **Select and filter fields.** Keep only the fields required by the processing brief. Optionally filter rows by geography or category.
6. **Coerce types.** Cast join keys to string. Cast numeric fields from string where needed. Log any coercion failures.
7. **Join tabular data to spatial features** on the shared key (left join from geometry to tabular data).
   - Normalize join key format on both sides: string type, zero-padded, trimmed whitespace.
   - For Census GEOIDs: always use the full FIPS string (e.g., 11-character tract GEOID). Never join on numeric GEOID.
8. **Review join diagnostics.**
   - Count matched rows, unmatched geometry rows, and unmatched tabular rows.
   - Investigate unmatched records. Water-only or zero-population tracts are expected gaps; mismatched vintages or FIPS codes are errors.
   - Document the join match rate.
9. **Derive calculated fields** needed for downstream analysis (rates, shares, densities, area). Compute derived fields from the joined result, not from pre-join sources.
10. **Write processed outputs.**
    - Spatial outputs: GeoPackage in `data/processed/` (or `data/interim/` if further processing is expected).
    - Tabular outputs: CSV in `data/processed/`.
11. **Write processing logs.** One JSON log per major step (extraction, normalization, join, derivation).
12. **Run structural QA, then write the processing handoff artifact** to `runs/`. Run `qa-review/STRUCTURAL_QA_CHECKLIST.md` against the outputs before the handoff is finalized. The handoff follows the provenance fields defined in `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` and adds a per-step summary covering extraction, normalization, join diagnostics (match rate and unmatched counts), derived fields, output paths, and any warnings raised during processing.

## Validation Checks

- raw data in `data/raw/` was not modified
- CRS is present and correct in all spatial outputs (or explicitly flagged as missing and escalated)
- join key types match on both sides (both string, both zero-padded)
- join match rate is documented and plausible
- unmatched records are explained, not silently dropped
- no unexpected row count changes between input and output
- no duplicate join keys in the output
- derived fields are computed from joined data, not separate pre-join sources
- processing logs exist for each major step
- structural QA checklist has been run against the outputs and its result recorded in the handoff
- processing handoff artifact exists in `runs/` and includes the provenance fields required by `standards/PROVENANCE_AND_HANDOFF_STANDARD.md`

## Common Failure Modes

- joining on GEOID with mismatched types (string `"31001952200"` vs. integer `31001952200`)
- assuming CRS when the source does not declare one — always verify, never assume
- losing the geometry column during field selection or pandas operations
- not checking for duplicate join keys in tabular data, causing row inflation
- skipping column normalization and getting bitten by mixed case or trailing spaces
- computing distances or areas in a geographic CRS (degrees) instead of a projected CRS
- vintage mismatch between geometry and tabular data (e.g., 2020 tracts joined to 2019 ACS)

## Escalate When

- the source data arrives with no CRS or a suspected incorrect CRS
- the join match rate drops below 90%
- unmatched records include populated tracts or areas that should have data
- the processing brief requires a join key that does not exist in the source data
- type coercion fails for more than a trivial number of records
- the source data contains unexpected duplicates that cannot be resolved automatically

## Outputs

- cleaned and standardized spatial files in `data/processed/` (GeoPackage)
- cleaned tabular files in `data/processed/` (CSV)
- joined / enriched datasets in `data/processed/` (GeoPackage or CSV)
- processing log JSONs for each major step
- processing handoff artifact in `runs/`

## Relationship to Domain-Specific Workflows

This workflow defines the general processing conventions. Domain-specific workflows inherit these conventions and add domain-specific steps:

- **Tract Join and Enrichment** (`workflows/TRACT_JOIN_AND_ENRICHMENT.md`) — specializes the join step for Census tract geometry with ACS tabular data. Adds vintage matching, GEOID-specific diagnostics, and tract-count validation.
- **POI Category Normalization** (`workflows/POI_CATEGORY_NORMALIZATION.md`) — specializes the normalization step for point-of-interest category fields. Adds category mapping, hierarchy flattening, and category QA.
- **Geocode, Buffer, and Enrichment** (`workflows/GEOCODE_BUFFER_ENRICHMENT.md`) — specializes extraction and enrichment for geocoded point data with buffer-based spatial joins.

When a domain-specific workflow exists for your processing task, use it. Fall back to this general workflow for tasks not covered by a domain-specific page.

## Related Standards

- `standards/CRS_SELECTION_STANDARD.md` — CRS selection and verification rules
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — handoff artifact structure and provenance requirements
- `standards/STRUCTURAL_QA_STANDARD.md` — structural quality checks for processed outputs
- `standards/SOURCE_READINESS_STANDARD.md` — source tier assignment for incoming data

## Related QA Pages

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural checks applied to processing outputs

## Sources

- GeoPandas documentation (merge, sjoin, to_file)
- GDAL / OGR documentation (ogrinfo, ogr2ogr)
- Census Bureau TIGER / Line technical documentation
- pandas documentation (read_csv, astype, merge)

## Trust Level

Validated Workflow — Needs Testing
