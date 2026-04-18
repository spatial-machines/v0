# Extending spatial-machines

spatial-machines is designed to be extended. The framework ships with 20+ data sources, 9 specialist agents, and a battle-tested analysis pipeline — but your work will inevitably require something we haven't built yet.

This directory contains guides for the most common extension points.

## Guides

### [Adding Data Sources](ADDING_DATA_SOURCES.md)
Write a new fetch script, register it in the data source registry, add a wiki page, and update the data-retrieval agent's toolset. Follow the same pattern used by all 21 existing fetch scripts.

**When you need this:** You want to pull data from an API or download source that spatial-machines doesn't support yet.

### [Connecting Infrastructure](CONNECTING_INFRASTRUCTURE.md)
Connect your own PostGIS database, ArcGIS Online account, cloud storage, or enterprise data warehouse. Configure the system to use your infrastructure alongside (or instead of) the default public APIs.

**When you need this:** You have data in a database, portal, or internal system that isn't accessible via public APIs.

### [Customizing the Pipeline](CUSTOMIZING_PIPELINE.md)
Modify color palettes, QA thresholds, report templates, and agent behavior. Add new agent roles or adjust existing ones to match your team's workflow.

**When you need this:** You want the pipeline to produce outputs that match your organization's standards, branding, or workflow.

### [Publishing Adapters](PUBLISHING_ADAPTERS.md)
Deliver analysis outputs to external systems — ArcGIS Online, GeoServer, cloud portals, or custom web applications. This is the extension point for enterprise delivery.

**When you need this:** You need to push finished analyses somewhere beyond the local filesystem.

## Design Principles

When extending spatial-machines, follow these principles:

1. **Script-first.** New capabilities should be scripts in `scripts/core/` (or `scripts/future/` if experimental), not inline code in agent prompts.

2. **Manifest everything.** Every data retrieval should produce a `.manifest.json` sidecar documenting what was fetched, when, from where, and any caveats.

3. **Isolate by project.** All analysis data lives under `analyses/<project-id>/`. Extensions that produce data should respect this isolation.

4. **Don't break the handoff chain.** The pipeline passes JSON handoff artifacts between stages. If you add a new stage or modify an existing one, ensure the handoff contract is maintained.

5. **Document in the wiki.** New data sources get a wiki page in `docs/wiki/data-sources/`. New workflows get a page in `docs/wiki/workflows/`. This is how the agents learn about your extensions.

6. **Keep it stdlib where possible.** Fetch scripts use Python's standard library (urllib, json, csv) to minimize dependencies. Only add external packages when the stdlib genuinely can't do the job.
