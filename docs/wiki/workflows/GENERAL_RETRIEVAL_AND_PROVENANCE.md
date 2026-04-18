# General Retrieval and Provenance Workflow

## Purpose

- define the general sequence every retrieval run follows regardless of source
- establish the firm's manifest, provenance, and handoff conventions for the front of the pipeline
- give source-specific pages (named providers like CENSUS_ACS, TIGER_GEOMETRY, USGS_ELEVATION, OSM, LOCAL_POSTGIS, CLIENT_SUPPLIED_DEMS, plus the category-level LOCAL_FILES and REMOTE_FILES) a single workflow to defer to for the steps that are universal across sources

This workflow is the front-of-pipeline counterpart to `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md`, `workflows/VALIDATION_AND_QA_STAGE.md`, and `workflows/REPORTING_AND_DELIVERY.md`. Together they define the firm's general pipeline canon: retrieval → processing → analysis → validation → reporting → orchestration.

## Relationship to Source Pages

This workflow describes the **general sequence** that applies to every retrieval. Source pages describe the **source-class details** that vary by where the data comes from.

| Belongs on this workflow page | Belongs on source pages |
|---|---|
| The 6-step retrieval sequence | Source-class access methods (path validation, HTTP GET, API call, database query) |
| Manifest writing rules and required fields | Source-class format quirks (sidecar files, ZIP nesting, encoding, sheet selection) |
| Run provenance structure and required fields | Source-class QA checks (file exists vs. HTTP 2xx vs. API status) |
| The retrieval handoff contract to processing | Source-class pitfalls (URL instability, vintage mismatch, license restrictions) |
| Source-selection logic (how to choose which source page applies) | Format-specific inspection guidance (CRS check for spatial files, sheet selection for Excel) |

When a retrieval task hits this workflow, the agent reads here for the general sequence and then reads the relevant source page for the source-class details. The source pages all carry a "Retrieval Contract" callout that points back to this workflow as the canonical sequence.

## Typical Use Cases

- acquiring any new dataset for a project, regardless of source
- documenting the provenance of data that arrived without a manifest
- copying or downloading source files into the project's `data/raw/` directory
- producing the retrieval handoff that the processing stage consumes

## Inputs

- a task request that names what to retrieve, the geographic scope, the time period, and the expected output format
- one or more source identifiers (a file path, a URL, an API endpoint, a database connection, or a known-source name)
- the project brief (so retrieval choices can be checked against scope)
- existing source readiness tier assignments per `standards/SOURCE_READINESS_STANDARD.md` if available

## Preconditions

- the project's `data/raw/`, `data/interim/`, `data/processed/`, and `runs/` directories exist
- the source class has been identified (named provider, local file, remote URL, database extract, or client-supplied)
- the relevant source page has been read for source-class details
- credentials are available where required (Census API key, database credentials), stored in environment variables and not hardcoded
- the working CRS has been confirmed per `standards/CRS_SELECTION_STANDARD.md` (so reprojection decisions can be deferred to processing without ambiguity)

## Preferred Tools

- Python `requests` or `httpx` for HTTP downloads
- GeoPandas / GDAL / OGR for spatial file inspection
- pandas for tabular file inspection
- canonical core scripts under `scripts/core/` for production runs (e.g., `fetch_acs_data.py` for Census ACS)
- Python `zipfile` and `shutil` for archive handling

The wiki workflow describes the method. The script implementation lives in the canonical core scripts.

## Execution Order

1. **Select the source.** Identify which source class applies and read the relevant source page for the source-class details:
   - named providers: `data-sources/CENSUS_ACS.md`, `data-sources/TIGER_GEOMETRY.md`, `data-sources/USGS_ELEVATION.md`, `data-sources/OSM.md`, `data-sources/LIVING_ATLAS.md`
   - firm spatial warehouse: `data-sources/LOCAL_POSTGIS.md`
   - client-supplied DEMs: `data-sources/CLIENT_SUPPLIED_DEMS.md`
   - any other file already on disk: `data-sources/LOCAL_FILES.md`
   - any other URL-downloadable file: `data-sources/REMOTE_FILES.md`
   The source page tells you the source-class access method, the formats to expect, the QA checks specific to the source class, and the known pitfalls.
2. **Retrieve or copy the dataset into `data/raw/`.** Apply the source-class access method from step 1. Never modify files already in `data/raw/`. Never read directly from a remote URL in analysis scripts; always download first, then load locally. Record any redirects, HTTP status codes, or copy operations performed.
3. **Write a dataset manifest.** Each retrieved dataset gets a manifest sidecar in `data/raw/` recording the source identifier (URL, path, API call), the retrieval timestamp, the file size, the source-declared vintage and geographic scope (when available), the file format, and any source-class warnings raised during retrieval. The manifest is the first record of provenance and is what every downstream stage references.
4. **Inspect the retrieved artifact.** When feasible, open the file and record initial structure: row count and column list for tabular data; geometry type, CRS (EPSG code), and feature count for spatial data; archive contents for ZIPs. Inspection findings are recorded in the manifest, not in a separate file. If the artifact cannot be opened, record the failure and escalate per the escalation rules below.
5. **Write or update the run provenance.** The run provenance is a per-run JSON in `runs/` that lists every dataset retrieved during the run, with references to each manifest. The run provenance follows the schema in `ARCHITECTURE.md` and inherits its provenance fields from `standards/PROVENANCE_AND_HANDOFF_STANDARD.md`.
6. **Write the retrieval handoff to processing.** Write a structured handoff artifact to `runs/` that conveys: the list of retrieved datasets, references to each manifest, the source readiness tier per `standards/SOURCE_READINESS_STANDARD.md`, any warnings raised during retrieval, the run provenance reference, and the readiness state for the processing stage. The exact JSON schema is owned by `ARCHITECTURE.md` § Retrieval Handoff and the canonical core scripts; this workflow describes what the handoff conveys, not its on-disk shape.

## Validation Checks

- every retrieved dataset is under `data/raw/` (not under `data/interim/`, `data/processed/`, or any other location)
- every retrieved dataset has a manifest sidecar
- the manifest records the source identifier, retrieval timestamp, file format, file size, source-declared vintage, and geographic scope
- the source readiness tier is assigned per `standards/SOURCE_READINESS_STANDARD.md`
- the run provenance entry references each manifest
- spatial datasets have a documented CRS (EPSG code recorded) per `standards/CRS_SELECTION_STANDARD.md`
- archived files (ZIPs) extract cleanly and the contents are inventoried in the manifest
- no dataset arrived in `data/raw/` without a manifest (silent intake is a failure)
- the retrieval handoff to processing exists in `runs/`
- the handoff includes the source readiness tier, warnings, and the run provenance reference
- structural QA per `standards/STRUCTURAL_QA_STANDARD.md` is achievable from the manifest fields alone

## Common Failure Modes

- copying or downloading a file into a directory other than `data/raw/`
- modifying a file in `data/raw/` after intake
- reading directly from a remote URL in an analysis script instead of downloading first
- skipping the manifest because the file is "obviously" what it claims to be
- inferring the vintage from the filename instead of recording the source-declared vintage
- archiving the run provenance separately from the per-dataset manifests
- failing to record a redirect, content-disposition rename, or URL canonicalization
- treating credentials as part of the source identifier (credentials never appear in the manifest)
- producing a manifest with no source-class warnings recorded even though the source page named known pitfalls
- not assigning a source readiness tier and assuming Tier 1
- not writing the retrieval handoff because the processing stage has not started yet (the handoff is the precondition for processing, not the consequence of it)

## Escalate When

- the source data arrives with no documented vintage and the retrieval method cannot infer one
- the source data arrives with no CRS or a suspected incorrect CRS (per `standards/CRS_SELECTION_STANDARD.md`'s escalation rule)
- the source returns a non-2xx HTTP status, an HTML error page masquerading as a download, or a partial / truncated file
- the source readiness tier is Tier 3 (Provisional) or Tier 4 (Unreviewed) and the project requires Tier 1 or 2
- the source has license restrictions that the project brief did not anticipate
- the credentials needed for retrieval are not available or have expired
- the retrieval would exceed reasonable file-size limits for the project's storage or delivery channel
- a source-specific pitfall named in the source page has occurred and cannot be resolved automatically
- the retrieval method cannot be reproduced (one-off scraping, manual download with no documented URL)

## Outputs

- raw dataset files in `data/raw/`
- a dataset manifest sidecar for each retrieved file
- a run provenance entry in `runs/` referencing every manifest
- a retrieval handoff artifact in `runs/` conveying the list of retrieved datasets, source readiness tiers, warnings, and the readiness state for the processing stage

For the exact JSON schema of the retrieval handoff and the run provenance, see `ARCHITECTURE.md` § Handoff Contracts and the canonical core scripts. This workflow describes what the artifacts convey, not their on-disk shape.

## Relationship to Source-Class Pages

The retrieval workflow assumes the agent has read the relevant source page in addition to this page. The source pages and their scope:

- `data-sources/CENSUS_ACS.md` — Census ACS retrieval (named provider)
- `data-sources/TIGER_GEOMETRY.md` — Census TIGER geometry retrieval (named provider)
- `data-sources/USGS_ELEVATION.md` — USGS 3DEP elevation retrieval (named provider)
- `data-sources/OSM.md` — OpenStreetMap retrieval (named provider)
- `data-sources/LIVING_ATLAS.md` — Esri Living Atlas as a discovery / reference source
- `data-sources/LOCAL_POSTGIS.md` — firm spatial warehouse extraction
- `data-sources/CLIENT_SUPPLIED_DEMS.md` — client-supplied DEM intake (specialized local-files variant)
- `data-sources/LOCAL_FILES.md` — category-level page for files already on disk
- `data-sources/REMOTE_FILES.md` — category-level page for ad hoc HTTP downloads with no dedicated source page
- `data-sources/ZCTA_AND_ZIP_NOTE.md` — reference note on ZCTA / ZIP boundary semantics

## Related Standards

- `standards/SOURCE_READINESS_STANDARD.md` — source tier assignment that the retrieval handoff must include
- `standards/PROVENANCE_AND_HANDOFF_STANDARD.md` — general provenance fields the manifest and handoff inherit
- `standards/CRS_SELECTION_STANDARD.md` — CRS verification rule applied at intake
- `standards/STRUCTURAL_QA_STANDARD.md` — downstream QA gate that the manifest must support

## Related Workflows

- `workflows/GENERAL_PROCESSING_AND_STANDARDIZATION.md` — the immediate downstream stage; consumes the retrieval handoff this workflow produces
- `workflows/ACS_DEMOGRAPHIC_INVENTORY.md` — domain-specific specialization for ACS retrieval
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md` — common downstream consumer of retrieved tract geometry plus tabular data
- `workflows/POSTGIS_POI_LANDSCAPE.md` — domain-specific retrieval pattern from the firm warehouse
- `workflows/VALIDATION_AND_QA_STAGE.md` — eventual downstream consumer of the manifest fields via the structural QA gate

## Related QA

- `qa-review/STRUCTURAL_QA_CHECKLIST.md` — structural integrity gate run downstream against the retrieved data
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md` — narrative-side review for any client-facing claim that derives from the retrieved data

## Sources

- firm retrieval methodology
- Census Bureau API and TIGER documentation
- HTTP standards for download semantics (status codes, content-disposition)
- OGC standards for spatial file format inspection

## Trust Level

Validated Workflow — Needs Testing
