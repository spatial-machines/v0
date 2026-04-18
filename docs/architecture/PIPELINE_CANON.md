# Pipeline Canon

Canonical definition of the cleaned GIS pipeline.

This file is the authoritative source for:
- stage order
- stage ownership
- handoff types
- readiness flags
- blocking vs advisory gates

If another file disagrees with this pipeline definition, this file wins.

## Core Principle

The pipeline is artifact-driven.

Each stage:
- reads explicit upstream artifacts
- writes explicit downstream artifacts
- does not rely on hidden conversational memory

No stage is complete until its handoff artifact exists and is valid.

## Standard Full Pipeline

### Stage 0: Intake and Scoping
- Owner: `lead-analyst`
- Inputs: human request, project context, prior project inventory if relevant
- Outputs:
  - `project_brief.json`
  - run plan artifact
- Ready flag: `ready_for: "retrieval"` or `ready_for: "direct-execution"`

### Stage 1: Retrieval
- Owner: `data-retrieval`
- Inputs:
  - project brief
  - data reuse lookup results
  - source handbooks
- Outputs:
  - raw data in `data/raw/`
  - dataset manifests
  - retrieval provenance artifact
- Ready flag: `ready_for: "processing"`

### Stage 2: Processing
- Owner: `data-processing`
- Inputs:
  - raw data
  - manifests
  - retrieval provenance
- Outputs:
  - interim datasets
  - processed datasets
  - processing logs
  - processing handoff
- Ready flag: `ready_for: "analysis"`

### Stage 3: Analysis
- Owner: `spatial-stats`
- Inputs:
  - processed datasets
  - processing handoff
  - project brief
- Outputs:
  - analysis tables
  - analysis maps
  - sidecar logs
  - analysis handoff
- Ready flag: `ready_for: "cartography"` or `ready_for: "validation"`

### Stage 4: Cartography (Visualization)
- Owner: `cartography`
- Inputs:
  - processed datasets
  - analysis outputs, including `recommended_charts[]` from the analysis handoff
  - analysis handoff
  - style standards (`config/map_styles.json`, `config/chart_styles.json`)
- Outputs:
  - delivery-quality maps (PNG + `.style.json` sidecar)
  - **statistical charts** (PNG + SVG + `.style.json` sidecar) — distribution / comparison / relationship / timeseries, produced per the pairing rule in `docs/wiki/standards/CHART_DESIGN_STANDARD.md`
  - optional interactive Folium maps
  - visual QA notes where applicable
  - cartography handoff (`write_cartography_handoff.py`) declaring both `maps[]` and `charts[]`
- Ready flag: `ready_for: "validation"`

### Stage 5: Validation
- Owner: `validation-qa`
- Inputs:
  - analysis outputs
  - cartography outputs if present
  - upstream handoffs
- Outputs:
  - validation check JSONs
  - validation handoff
- Ready flag:
  - `ready_for: "reporting"` when acceptable
  - `ready_for: "review"` when rework is needed or warnings are severe

### Stage 6: Reporting
- Owner: `report-writer`
- Inputs:
  - validation handoff
  - analysis handoff
  - processing handoff
  - retrieval provenance
  - output artifacts
- Outputs:
  - markdown report
  - HTML report
  - citations
  - data dictionary
  - reporting handoff
- Ready flag: `ready_for: "publishing"` or `ready_for: "synthesis"`

### Stage 7: Publishing / Delivery Packaging
- Owner: `site-publisher`
- Inputs:
  - reports
  - maps + charts + style sidecars
  - tables
  - validation status
  - registry/project metadata
  - project brief (reads `outputs.arcgis_package_required`, `outputs.publish_targets`, `outputs.qgis_package_required`)
- Outputs:
  - site build artifacts, catalogs
  - **QGIS review package** (`outputs/qgis/`) — default on
  - **ArcGIS Pro package** (`outputs/arcgis/`) — default on; file geodatabase + `.lyrx` per map + helper `make_aprx.py` + optional arcpy-built `.aprx`
  - **ArcGIS Online publishing** — opt-in via `outputs.publish_targets: ["arcgis_online"]`. Always dry-run first; PRIVATE by default. Writes `outputs/arcgis/publish-status.json`.
  - publishing handoff (`write_publishing_handoff.py`) — includes `arcgis_pro_package` and `arcgis_online_publish` blocks when applicable
- Ready flag: `ready_for: "peer-review"`

### Stage 8: Independent Review
- Owner: `peer-reviewer`
- Inputs:
  - outputs only
  - reports
  - QA outputs
- Outputs:
  - peer review artifact
- Ready flag:
  - `ready_for: "delivery"` when PASS
  - `ready_for: "revision"` when REVISE
  - `ready_for: "human-escalation"` when REJECT

### Stage 9: Final Synthesis and Delivery
- Owner: `lead-analyst`
- Inputs:
  - all relevant handoffs
  - peer review verdict
  - publishing status
- Outputs:
  - final synthesis
  - human-facing delivery/update
  - lead handoff or final status note
- Ready flag: `ready_for: "human-review"` or `ready_for: "delivered"`

## Allowed Pipeline Variants

### Direct Mode
- Owner: `lead-analyst`
- Use only for small tasks with low ambiguity
- Must still produce minimal artifacts if the task materially changes project state

### Partial Pipeline
- Use only the stages needed
- Skipped stages must be explicit, not implied
- Readiness flags still apply

### Full Pipeline
- Default for new or substantial analyses

## Quality Gates

### Gate A: Planning Gate
- Owner: `lead-analyst`
- Optional reviewer: `peer-reviewer`
- Blocking when:
  - scope is unclear
  - data plan is unrealistic
  - requested outputs are unsupported

### Gate B: Structural QA Gate
- Owner: `validation-qa`
- Blocking when:
  - required artifacts are missing
  - geometry or join integrity is broken
  - output completeness is below threshold

### Gate C: Independent Review Gate
- Owner: `peer-reviewer`
- Blocking when:
  - conclusions overshoot evidence
  - map choices are misleading
  - caveats are inadequate
  - shipping would create reputational risk

## Blocking vs Advisory Outcomes

### Blocking
- missing handoff
- missing required artifact
- validation outcome of `REWORK NEEDED`
- peer review outcome of `REJECT`

### Advisory
- validation outcome of `PASS WITH WARNINGS`
- peer review outcome of `REVISE`
- partial coverage where the limitation is explicitly disclosed

## Canonical Handoff Types

Minimum handoff families in the cleaned architecture:

- retrieval provenance
- processing handoff
- analysis handoff
- validation handoff
- reporting handoff
- peer review artifact
- lead handoff
- optional publishing handoff
- optional qgis handoff

## Shared Rules

- raw data is immutable
- processed data is never edited by downstream stages
- validation is read-only
- peer review reads outputs only
- lead analyst synthesizes and routes; it is not the default executor
- pilot or production analyses should not be implemented as a single monolithic `run_*.py` that hand-writes every stage artifact
- use the core stage scripts and handoff writers where they exist; custom wrapper scripts are acceptable only as thin orchestrators that call those stage tools explicitly
- do not orchestrate normal runs through multiline shell wrappers like `set -e` blocks, chained shell scripts, or `cd && python ...` command bundles; use one direct stage command per exec call
- publishing is not complete until the intended project URL is verified reachable
- when publishing to the live review site, write a publish-status artifact rather than assuming the site updated correctly

## Refactor Implications

The cleaned system should:
- standardize artifact names and schema fields
- support project-scoped execution directly
- make skipped stages explicit
- ensure every active agent prompt points back to this file
