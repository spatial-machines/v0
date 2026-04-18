# Capability Roadmap

Deferred capability expansion plan for the spatial-machines GIS architecture.

This document is intentionally separate from the active agent prompts and runtime docs.
Its purpose is to preserve upgrade direction without teaching unimplemented capabilities as if they already exist.

## Roadmap Principle

Stability first, expansion second.

A capability should not be promoted into agent-local prompts until:
- the architecture is stable
- the deployment path is stable
- the capability is proven in the current runtime

## Priority Bands

### Band 1: Post-Migration Stabilization
Capabilities that improve reliability or reduce repeated work.

### Band 2: High-Leverage Expansion
Capabilities that materially improve analyst quality, data reuse, or tool selection.

### Band 3: Strategic Expansion
Capabilities that broaden the firm's reach but are not required for stable operation.

## Band 1: Post-Migration Stabilization

### 1. Tool Registry Integration Layer
Goal:
- make the 600+ tool registry usable without exposing agents directly to ungoverned method sprawl

Needed:
- one lightweight query layer that maps:
  - analysis need
  - approved execution route
  - production vs experimental status
- one policy that distinguishes:
  - reference method
  - approved operational tool

Why it matters:
- today the registry is a strong reference asset but not yet an operational routing layer

### 2. Data Inventory and Reuse Lookup
Goal:
- answer "what do we already have?" before retrieval begins

Needed:
- project inventory files
- shared reference inventory
- local infrastructure inventory
- a simple query mechanism usable by `lead-analyst` and `data-retrieval`

Why it matters:
- this replaces the best part of the old `db-manager` idea without reviving prompt drift

### 3. Handoff Schema Enforcement
Goal:
- convert handoff conventions into typed contracts

Needed:
- JSON Schema or typed models for each handoff family
- validation of handoff structure before downstream use

Why it matters:
- current architecture depends on handoffs, so they should be enforceable

## Band 2: High-Leverage Expansion

### 4. Stronger Source Automation
Goal:
- broaden production-grade retrieval beyond Census/TIGER

Candidates:
- CDC PLACES
- HRSA
- EPA EJScreen
- USDA
- FEMA
- local/local-cache-backed POI workflows

Constraint:
- do not expose these as guaranteed until each route is proven on the deployed instance

### 5. Better Local Data Discovery
Goal:
- use PostGIS/local OSM as first-class reusable sources

Needed:
- documented query patterns
- stable local data-access utilities
- clear ownership between retrieval and infrastructure

### 6. Workflow Recommendation Layer
Goal:
- teach agents patterns, not just individual tools

Examples:
- when to use choropleth vs proportional symbols
- when to stop after Moran's I fails
- when to use tract vs county vs block group
- when reuse is preferable to acquisition

Why it matters:
- GIS quality depends more on workflow choice than raw tool count

## Band 3: Strategic Expansion

### 7. Advanced Raster and Terrain Pipelines
Candidates:
- terrain derivatives
- zonal raster workflows
- contour generation
- interpolation
- KDE
- 3D terrain delivery

### 8. Larger Method Surface from the 679-Tool Registry
Goal:
- selectively promote external GIS methods into approved execution routes

Approach:
- choose high-value consulting workflows first
- map each to:
  - Python implementation path
  - dependency requirements
  - approved owner agent
  - maturity level

### 9. Cross-Project Comparison and Performance Intelligence
Goal:
- improve institutional memory and benchmarking across analyses

Candidates:
- comparison dashboards
- reanalysis triggers
- data freshness monitoring
- repeated failure pattern tracking

### 10. Open-Source Release Readiness
Goal:
- prepare a public-core release of the system once the runtime is stable and the best demos are ready

Needed:
- public repo structure
- release-safe docs
- demo-first onboarding
- test and smoke-check coverage
- clear public vs premium boundary

See:
- `OSS_RELEASE_PLAN.md`

## Promotion Rule

A capability should move from roadmap into production only when:
- it has a clear owner
- it has a clear tool route
- it has a place in the canonical pipeline
- it has been tested in the real runtime
- agent prompts can describe it honestly

## Near-Term Recommendation

After migration, the first expansion work should be:
1. tool registry integration layer
2. data inventory and reuse lookup
3. handoff schema enforcement

Those three changes will improve the system more than adding a large number of new analysis scripts immediately.

After those are in better shape, the next strategic planning track should be:
4. public-core OSS release planning
