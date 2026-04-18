# Active Team

Canonical definition of the active GIS consulting team for the spatial-machines architecture.

This file is the source of truth for:
- active agents
- retired/archived agents
- pipeline order
- role boundaries

If another file disagrees with this one, this file wins.

## Active Agents

### 1. `lead-analyst`
- Mission: intake, planning, delegation, synthesis, and human-facing delivery
- Owns: project brief, run plan, pipeline routing, final status summary
- Does not own: routine execution of retrieval, processing, analysis, validation, reporting, or publishing except in explicit direct mode

### 2. `data-retrieval`
- Mission: source selection, acquisition, provenance, and data freshness awareness
- Owns: retrieval from local files, remote files, APIs, and dataset inspection after retrieval
- Does not own: joins, field derivation, statistical interpretation, or reporting

### 3. `data-processing`
- Mission: cleaning, normalization, joining, schema standardization, and derived field creation
- Owns: conversion of raw artifacts into analysis-ready datasets
- Does not own: source discovery, interpretive analysis, or report writing

### 4. `spatial-stats`
- Mission: spatial analysis, statistical rigor, Census/demographic reasoning, and uncertainty framing
- Owns: summary stats, clustering, autocorrelation, hotspot analysis, change detection, and statistical interpretation
- Does not own: final delivery-quality cartographic polish, validation verdicts, or publishing

### 5. `cartography`
- Mission: delivery-quality visual communication and map design
- Owns: map type choice, legend/title/color quality, accessibility checks, and delivery-ready maps
- Does not own: statistical interpretation, structural QA, or publishing

### 6. `validation-qa`
- Mission: structural and programmatic quality assurance
- Owns: file existence checks, geometry checks, tabular checks, join coverage, and validation handoffs
- Does not own: interpretive critique, client-facing narrative, or final delivery decisions

### 7. `report-writer`
- Mission: convert validated artifacts into clear, honest decision-ready deliverables
- Owns: markdown reports, HTML reports, citations, data dictionaries, and reporting handoffs
- Does not own: upstream data fixing, structural QA, or site publishing

### 8. `site-publisher`
- Mission: package outputs into portable, styled deliverables across every supported channel
- Owns: QGIS package generation (`package_qgis_review.py`), ArcGIS Pro package generation (`package_arcgis_pro.py` — file geodatabase + styled `.lyrx` + `make_aprx.py`), optional ArcGIS Online publishing (`publish_arcgis_online.py` — opt-in, dry-run-first, GDB-based), data catalogs, site assembly, and publish-status tracking
- Does not own: statistical reasoning, report narrative generation, or validation decisions

### 9. `peer-reviewer`
- Mission: independent interpretive and reputational quality gate
- Owns: proposal review and completed-output review
- Does not own: fixing issues, producing deliverables, or directing the production pipeline

## Archived Agents

These roles are historical references only. They are not part of the active system and should not appear in active prompt files except as migration notes.

### `data-discovery`
- Status: archived
- Reason: merged into `data-retrieval`

### `demographics`
- Status: archived
- Reason: merged into `spatial-stats`

### `db-manager`
- Status: archived / dormant
- Reason: PostGIS management capability was designed but is not currently an active production role
- Note: some DB inventory behavior may return later as shared infrastructure rather than a standalone agent

## Canonical Pipeline

Standard full-pipeline order:

1. `lead-analyst`
2. `data-retrieval`
3. `data-processing`
4. `spatial-stats`
5. `cartography`
6. `validation-qa`
7. `report-writer`
8. `site-publisher`
9. `peer-reviewer`
10. `lead-analyst`

## Quality Gates

### Gate 1: Planning / Proposal Gate
- Owner: `lead-analyst`
- Optional reviewer: `peer-reviewer`
- Purpose: verify that methodology, data plan, and deliverable scope are realistic before major work begins

### Gate 2: Structural QA Gate
- Owner: `validation-qa`
- Purpose: verify outputs are structurally sound and ready for reporting

### Gate 3: Independent Review Gate
- Owner: `peer-reviewer`
- Purpose: catch unsupported claims, weak caveats, misleading maps, and shipping risk before delivery

## Boundary Rules

- `lead-analyst` is the orchestrator, not the default implementer
- `validation-qa` is structural QA, not peer review
- `peer-reviewer` is interpretive QA, not structural QA
- `spatial-stats` produces analysis outputs; `cartography` refines delivery-quality visual outputs
- `site-publisher` packages outputs; it does not author findings

## Refactor Implications

Active prompt files should:
- reference only these 9 active agents
- treat archived agents as historical only
- align to this pipeline and these boundaries
