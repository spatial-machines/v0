# Data Reuse Policy

Canonical policy for data discovery, reuse, acquisition, and transformation in the cleaned GIS architecture.

This file defines the search order agents should follow before retrieving new data.

## Core Principle

Do not fetch new data until you have checked whether equivalent or authoritative data already exists locally.

The system should prefer:
- reuse
- provenance continuity
- local authority
- minimal duplication

over repeated downloading or rediscovery.

## Search Order

Before retrieving new data, agents should search in this order:

### 1. Current Project Artifacts
Check whether the needed data already exists in the current project:
- `data/raw/`
- `data/interim/`
- `data/processed/`
- project manifests and inventories

Use when:
- the same project is being rerun
- an upstream stage already acquired the data
- a derived dataset already exists and remains valid for the task

### 2. Shared Reference Data
Check whether a reusable reference layer already exists:
- canonical tract/county/state boundaries
- curated reference tables
- reusable project-independent base layers

Use when:
- the needed data is foundational and stable
- duplicating the data per project adds no value

### 3. Local Infrastructure Sources
Check local infrastructure-backed sources:
- local PostGIS databases
- local OSM/POI stores
- cached rasters
- known machine-local data services

Use when:
- local copies are more complete or faster than remote APIs
- the local source is already maintained and authoritative for the environment

### 4. Prior Analyses
Check completed or active prior analyses for reusable raw or processed artifacts.

Use when:
- the same geography and vintage have already been processed
- the same source was already retrieved recently
- a reusable intermediate exists

Do not reuse blindly:
- verify geography, vintage, schema, and suitability
- document reuse in provenance

### 5. Authoritative Remote Sources
Only after local checks fail should agents retrieve from:
- official APIs
- official bulk downloads
- authoritative open-data portals

Examples:
- Census
- TIGER/Line
- CDC
- HRSA
- USDA
- EPA
- FEMA

### 6. Fallback / Research-Only Sources
Use only when authoritative sources are unavailable or insufficient:
- secondary portals
- less formal open-data sites
- manual download links discovered through research

These require stronger caveats and usually escalation to `lead-analyst`.

## Reuse Rules

### Reuse Is Preferred When
- geography matches
- vintage matches or is acceptable for the task
- schema is suitable
- provenance is available
- the artifact is easier to trust than a fresh, ad hoc fetch

### Reuse Is Not Preferred When
- source vintage is stale for the task
- schema has drifted in ways that would mislead downstream work
- provenance is missing or unreliable
- the artifact was clearly demo-only or partial coverage
- the task requires a fresh authoritative pull

## Retrieval Decision Rules

### `data-retrieval` must answer these questions before external fetch:
1. Do we already have this in the current project?
2. Do we already have this as shared reference data?
3. Do we already have it in local infra or cached stores?
4. Do prior analyses contain a compatible version?
5. If not, what is the authoritative external source?

### `lead-analyst` must ask:
- is this a new acquisition problem, or a reuse and adaptation problem?

## Provenance Rules for Reuse

Reused data still needs provenance.

When reusing an existing artifact, record:
- original source
- original retrieval date if known
- original project if reused from another analysis
- reason reuse was chosen
- known caveats

## Recommended Artifact Types

The cleaned architecture should support:

### Project Inventory
Per project, track:
- raw sources
- processed datasets
- derived fields
- output artifacts
- vintages
- reuse candidates

### Shared Reference Inventory
Track:
- reference layer name
- authority
- vintage
- schema summary
- storage location

### Local Source Inventory
Track:
- PostGIS tables
- OSM/POI coverage
- local services and caches

## Policy Implications for Retired `db-manager`

The old `db-manager` role should not remain half-alive in prompts.

But the behavior it was trying to provide is still needed:
- "what do we already have?"
- "what is reusable?"
- "what is authoritative locally?"

The cleaned architecture should reintroduce this as:
- shared inventory and lookup behavior
- not necessarily as a standalone active agent

## Escalation Rules

Escalate to `lead-analyst` when:
- multiple candidate sources disagree
- reused data may be too stale
- remote authoritative source conflicts with local reused source
- provenance is incomplete
- local infra source is operationally unavailable

## Refactor Implications

The cleaned system should:
- make reuse lookup a mandatory pre-retrieval step
- define project and shared data inventories
- document local authoritative sources separately from prompts
- stop treating every task as a fresh retrieval problem
