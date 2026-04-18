# Workflow Handbook — Processing and Standardization

## Purpose
Standardize how retrieved datasets are cleaned, joined, and prepared for analysis.

## Typical Inputs
- raw data files in `data/raw/` with manifests
- processing brief specifying required fields, joins, and output format

## Typical Outputs
- cleaned spatial files in `data/interim/` (GeoPackage)
- cleaned tabular files in `data/interim/` (CSV)
- joined/enriched datasets in `data/processed/`
- processing log JSONs for each step
- processing handoff artifact in `runs/`

## Steps
1. **Extract** archived sources (ZIP) into `data/interim/`.
2. **Process vector** data: inspect CRS, select/rename fields, optionally filter rows, write to GeoPackage.
3. **Process tabular** data: normalize column names, select/rename fields, coerce types, write cleaned output.
4. **Join** tabular data to spatial features on a shared key. Review join diagnostics for match quality.
5. **Derive** any calculated fields needed for analysis.
6. **Write processing handoff** summarizing all steps, outputs, and warnings.

## Required QA
- raw data was not modified
- CRS is present and correct in spatial outputs (or explicitly flagged as missing)
- join match rate is documented and acceptable
- no unexpected row count changes
- processing logs exist for each step
- handoff artifact exists in `runs/`

## Common Pitfalls
- joining on GEOID with mismatched types (string "31001952200" vs. integer)
- assuming CRS when source doesn't declare one
- losing geometry column during field operations
- not checking for duplicate join keys in tabular data
- skipping column normalization and getting bitten by spaces/mixed case

## Example Tasks
- Extract Nebraska TIGER tracts, clean fields, join a demographic table, derive area percentages.
- Normalize a downloaded CSV, coerce numeric types, join to county boundaries.

## Notes / Lessons
- Processing is not complete until the handoff artifact exists.
- Always cast join keys to strings before joining Census data (GEOIDs are string identifiers, not numbers).
