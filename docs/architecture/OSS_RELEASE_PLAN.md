# OSS Release Plan

Forward-looking plan for turning the cleaned GIS agent system into a publishable open-source project.

This document is intentionally strategic.
It does not change the immediate migration and deployment priorities.

## v1 capabilities (shipped)

The following capabilities are in-tree, tested, and part of the v1 scope. All ship under the open-source license.

- **Nine-agent pipeline** — lead-analyst, data-retrieval, data-processing, spatial-stats, cartography (visualization), validation-qa, report-writer, site-publisher, peer-reviewer.
- **Twenty-plus built-in data sources** — Census ACS / Decennial / TIGER / LODES, CDC PLACES, EPA EJScreen, FEMA NFHL, NOAA Climate, OpenWeatherMap, BLS, FBI Crime, USDA Food Access, HUD, Overture Maps, OpenStreetMap, USGS DEM, GTFS, Socrata, generic URL / local file.
- **Maps** — choropleth, bivariate (Stevens 3×3), hotspot (Gi*), LISA clusters, point overlay, dot density, proportional symbols, small multiples, uncertainty panels. Auto-palette routing from field names; `.style.json` sidecar per map.
- **Statistical charts (new in v1)** — four families (distribution, comparison, relationship, time series) with 13 chart kinds. Paired with maps per the CHART_DESIGN_STANDARD pairing rule.
- **QGIS review package** — styled `.qgs` + graduated renderers + basemap + auto-zoom + print-layout template.
- **ArcGIS Pro review package (new in v1)** — file geodatabase via GDAL OpenFileGDB (no Esri license required), `.lyrx` per map from sidecars, `make_aprx.py` helper, optional arcpy-built `.aprx` with layout enhancement.
- **ArcGIS Online publishing adapter (new in v1)** — opt-in, dry-run-first, PRIVATE by default. Uploads ONE File Geodatabase, publishes a hosted Feature Service with N feature layers, applies sidecar-driven renderers via `updateDefinition`, and assembles a single Web Map. Map PNGs, chart PNGs, and the HTML report stay local — AGOL gets the interactive layers + map, not the static deliverables. Credentials via `.env`, never logged. Pure REST, no `arcgis` Python dependency. **This adapter stays open-source.**
- **Solution graph (new in v1)** — DAG of every input, operation, and output in an analysis, reconstructed from activity log + handoffs + sidecars. PNG + SVG + JSON + Mermaid. Inspired by the autonomous-GIS research from Ning et al. at Penn State / USC.
- **Combined HTML report (new in v1)** — self-contained demo report embeds map, charts, solution graph, and the interactive web map in a single file.
- **Observability** — JSONL activity log; `show_pipeline_progress.py` tails it live; `audit_delegation.py` verifies handoff / script / output integrity.
- **Validation / QA** — 30+ validators including `validate_cartography.py` (maps **and** charts, with optional colorblind gate), `validate_arcgis_package.py`, `validate_handoffs.py`, `validate_join_coverage.py`.
- **Renderer parity** — one `.style.json` sidecar produces matching QGIS, LYRX, and AGOL renderers; enforced by `tests/test_renderer_parity.py`.
- **Commitments made explicit in v1**: QGIS package, ArcGIS Pro package, and AGOL adapter are community features — they never move behind a paywall.

## Working Thesis

The project is strong enough to justify an open-source path, but not yet in its current operational form.

The right public release is not:
- a raw backup
- a private homelab snapshot
- a pile of prompts and scripts without installability

The right public release is:
- a clean, documented reference architecture
- a usable local deployment path
- a small set of excellent demos
- explicit feature maturity boundaries
- platform-agnostic guidance that is not tied to spatial-machines alone

## Release Goal

Publish a system that helps GIS analysts:
- learn agentic GIS workflows
- run a local multi-agent analysis pipeline
- understand handoffs, QA gates, and deliverable patterns
- adapt the framework to their own spatial-analysis work

Platform goal:
- the public framework should be portable across agentic runtimes such as spatial-machines, Codex-style environments, Claude-based setups, and other orchestration harnesses
- runtime-specific adapters should be separated from the framework core

## Recommended Release Shape

### Public Core

Open-source:
- active agent architecture
- handoff model
- tool governance model
- selected core scripts
- local deployment docs
- demo projects and sample datasets
- review-site pattern
- runtime-agnostic prompt and workflow contracts

### Private / Premium Layer

Keep private or commercialize:
- managed hosting
- premium deployment support
- enterprise auth and governance features
- advanced local-data connectors
- proprietary templates and curated methods
- benchmark packs and premium demos
- team operations / multi-client workflow layer
- runtime-specific enterprise adapters where appropriate

## Why This Split Makes Sense

It gives the GIS community real value while preserving room for:
- service revenue
- premium tooling
- hosted deployment
- enterprise support

## Required Work Before Public OSS Release

### 1. Productize the Repo

The public repo should feel like a product, not a live machine image.

Needed:
- clear top-level structure
- public README with install path
- one-command or low-friction setup flow
- explicit runtime prerequisites
- separation between framework core and runtime adapters

### 2. Define Supported Scope

Needed:
- what is production
- what is experimental
- what is archived
- what is reference-only

Without this, users will over-trust unstable features.

### 3. Add Demo-First Onboarding

Needed:
- 1-2 polished demo analyses
- sample data
- expected outputs
- screenshots or short walkthroughs

The first public experience should prove value quickly.

### 4. Add Tests and Smoke Checks

Minimum bar:
- config validation
- handoff validation
- one pipeline smoke test
- one site build test
- one read-only retrieval test

### 5. Separate Framework from Private Identity

Needed:
- no personal-memory assumptions
- no private domains or infra examples
- no user-specific persona leakage
- no private ops conventions presented as universal truth
- no hard dependency on a single agent harness unless it is presented as one adapter among several

### 6. Make the Framework Platform-Agnostic

Needed:
- one canonical framework spec for:
  - agent roles
  - handoffs
  - tool governance
  - data flow
  - review gates
- adapter docs for:
  - spatial-machines
  - Codex-style environments
  - Claude-based agent environments
  - other compatible harnesses later

The architecture should be portable even when the runtime is not.

### 7. Clarify Licensing Strategy

This is not just a legal detail. It defines your leverage.

Questions:
- permissive license?
- copyleft?
- dual licensing?
- trademark restrictions for brand protection?

## Suggested Licensing Direction

You are worried about large vendors extracting value without returning value.

That points away from a fully permissive license.

Options worth considering with counsel later:
- GPL / AGPL style copyleft for the core
- dual licensing for commercial embedding
- open core with protected premium modules

This is a business decision as much as a community one.

## Commercialization Strategy Ideas

### Strategy A: Open Core + Paid Deployment

Open-source:
- architecture
- core agents
- core scripts
- local deployment

Paid:
- managed hosting
- deployment help
- premium templates
- premium connectors
- support contracts

### Strategy B: OSS Reference Architecture + Consulting Product

Open-source:
- the framework and demos

Paid:
- implementation
- custom workflows
- client deployments
- analysis-as-a-service

### Strategy C: Community Edition + Pro Edition

Community:
- local, self-hosted, limited integrations

Pro:
- better governance
- polished deployment
- premium review/publishing
- multi-client workspace support

## Potential Moats

Your moat is probably not "agents exist."

Stronger moats:
- real workflow quality
- excellent demos and outcomes
- disciplined handoff architecture
- strong QA and peer-review layer
- curated GIS workflow standards
- deployment knowledge
- tuned prompt/tool contracts based on real use
- trust from practitioners

Weak moats:
- generic prompt text alone
- public descriptions of agent roles
- basic script wrappers

## Competitive Risk

Yes, a larger vendor could copy ideas from an OSS release.

That risk is real.

Mitigations:
- release the right layer, not every layer
- keep premium deployment/support/IP where it matters
- build brand and community trust
- move faster on demos, usability, and quality than large vendors move on openness

## Ethical Considerations

### Why Open Source Helps

- broadens access to advanced GIS workflows
- helps researchers, nonprofits, students, and local governments
- creates a learning tool for agentic GIS
- improves transparency around automated geospatial analysis

### Why Purely Closed Commercialization Is Risky

- reduces accessibility
- makes methodology less inspectable
- can concentrate power in already dominant institutions

### Balanced Path

Open the core ideas and safe tooling.
Charge for reliability, deployment, support, and advanced enterprise value.

That is ethically defensible and commercially realistic.

## Release Readiness Milestones

### Milestone 1: Internal Stability
- migration complete
- Pi runtime stable
- site stable
- PostGIS restore stable

### Milestone 2: Public-Core Hardening
- repo restructuring complete
- docs rewritten for public users
- demos finalized
- sensitive content fully scrubbed
- tests and smoke checks added

### Milestone 3: Public Launch Candidate
- license chosen
- contribution/security docs added
- branding and positioning decided
- first release package prepared

### Milestone 4: Commercial Layer Decision
- decide open-core vs consulting vs pro edition
- identify premium modules
- define support and pricing model

## Near-Term Recommendation

Do not optimize for public release yet.

First:
1. complete migration
2. stabilize the cleaned runtime
3. expand the highest-value capabilities
4. build 1-2 exceptional demos
5. then shape the public-core release

## Immediate Follow-On Work

When the migration track is done, the first OSS-planning tasks should be:

1. public repo structure proposal
2. candidate licensing analysis
3. demo-selection plan
4. public-vs-private module split
5. minimum testing matrix for public release
6. framework-core vs runtime-adapter split
