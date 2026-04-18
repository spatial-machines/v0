# Workflow Handbook — Retrieval and Provenance

## Purpose
Standardize how datasets are acquired and documented before processing.

## Typical Inputs
- task request
- one or more source identifiers (path, URL, or known source)

## Typical Outputs
- raw data files in `data/raw/`
- dataset manifest(s)
- optional inspection summaries
- run provenance file

## Steps
1. Select source using the relevant source handbook.
2. Retrieve or copy the dataset into `data/raw/`.
3. Write a dataset manifest.
4. Inspect the retrieved artifact when feasible.
5. Write or update run provenance.
6. Handoff to processing with warnings and notes.

## Required QA
- source and timestamp recorded
- artifact exists
- format recorded
- warnings documented

## Common Pitfalls
- missing vintage
- unreadable zip archive contents
- confusing geography level
- failing to preserve original raw artifact

## Example Tasks
- Download 2024 Nebraska tract boundaries from TIGER and write provenance.
- Copy a local CSV into `data/raw/` and create its manifest.

## Notes / Lessons
- Retrieval is not complete until provenance exists.
