# Tool Governance

Canonical governance rules for operational tools in the cleaned architecture.

This file defines:
- tool categories
- maturity levels
- ownership model
- autonomy rules
- relationship between pipeline scripts and the external GIS method registry

## Core Principle

Agents should not improvise when a production workflow already exists.

Operational tools must be clearly classified so agents know:
- which tool to use
- whether it is stable
- whether they are allowed to use it autonomously

## Tool Layers

### Layer 1: Operational Pipeline Tools
- The actual scripts used by the GIS system
- These are the tools agents execute
- Example: `fetch_acs_data.py`, `process_vector.py`, `compute_hotspots.py`

### Layer 2: Experimental Tools
- Scripts that exist but are not yet guaranteed
- They may be useful, but they are not safe default choices

### Layer 3: Reference Method Registry
- External or research-oriented method knowledge
- Example: the 679-tool GIS registry
- This layer helps agents reason about methods, not default execution

### Layer 4: Infrastructure Tools
- Python venv, optional PostGIS (local OSM mirror only), optional QGIS / ArcGIS Pro for style rendering, optional AGOL publishing adapter
- Operationally necessary, but not part of the analysis methodology itself

## Canonical Categories

- `intake`
- `retrieval`
- `inspection`
- `processing`
- `derivation`
- `analysis`
- `cartography`
- `validation`
- `reporting`
- `publishing`
- `project-management`
- `memory`
- `infra`
- `reference-method`

## Maturity Levels

### `production`
- approved for routine autonomous use
- backed by current workflow docs
- expected to work in the current environment

### `experimental`
- available, but not guaranteed
- may require stronger reasoning, testing, or human approval
- should not be used by default

### `retired`
- no longer active
- historical reference only
- should not appear in active role instructions except migration notes

## Ownership Model

Each operational tool should have:
- `owner_agent`
- `secondary_agents`
- `category`
- `maturity`
- `reads`
- `writes`
- `requires`
- `autonomous_use`
- `notes`

## Autonomy Rules

### Autonomous Use: Yes
Allowed when:
- tool is `production`
- tool belongs to the agent or the agent is an approved secondary user
- required upstream artifacts exist
- task is within the role boundary

### Autonomous Use: Conditional
Allowed only when:
- tool is `experimental`, or
- task is ambiguous, or
- output is client-facing and failure risk is high

Requires:
- `lead-analyst` escalation
- and optionally human approval depending on task risk

### Autonomous Use: No
Applies when:
- tool is `retired`
- tool is infra-only and should be human-controlled
- tool is reference-only, not executable in current runtime

## Owner Matrix

### `lead-analyst`
Primary categories:
- `intake`
- `project-management`

Typical tools:
- task parsing
- run plan creation
- project listing/status
- lead handoff writing

### `data-retrieval`
Primary categories:
- `retrieval`
- `inspection`

Typical tools:
- local/remote retrieval
- Census/TIGER fetch
- dataset inspection after acquisition

### `data-processing`
Primary categories:
- `processing`
- `derivation`

Typical tools:
- vector/table processing
- joins
- field derivation
- rate computation

### `spatial-stats`
Primary categories:
- `analysis`

Typical tools:
- summary stats
- rankings
- autocorrelation
- hotspots
- change detection
- spatial regression where stable

### `cartography`
Primary categories:
- `cartography`

Typical tools:
- choropleths
- bivariate maps
- point overlays
- visual quality checks

### `validation-qa`
Primary categories:
- `validation`

Typical tools:
- output existence
- vector QA
- tabular QA
- join coverage
- validation handoff writing

### `report-writer`
Primary categories:
- `reporting`

Typical tools:
- report generation
- citation generation
- data dictionaries
- reporting handoff writing

### `site-publisher`
Primary categories:
- `publishing`

Typical tools:
- site build
- data catalogs
- QGIS review packaging

### `peer-reviewer`
Primary categories:
- review artifacts only

Typical tools:
- peer review runner
- read-only inspection helpers

## Boundary Rules

- `lead-analyst` may route work across categories but should not routinely execute other agents' production tools
- `validation-qa` owns structural QA, not interpretive review
- `peer-reviewer` owns interpretive review, not structural QA
- `cartography` owns delivery-quality map polish, not statistical interpretation
- `site-publisher` packages outputs, it does not author analysis

## Relationship to the 679-Tool GIS Registry

The external GIS method registry is valuable, but it is not the same thing as the operational pipeline tool set.

Use the registry for:
- method discovery
- workflow design
- future capability planning
- mapping conceptual GIS operations to Python/QGIS/GRASS routes

Do not use the registry as:
- default execution authority
- proof that a method is production-ready in this repo

## Recommended Machine-Readable Companion

The cleaned architecture should later add a machine-readable file such as:
- `config/tool_ownership.json`

Suggested fields:
- `script`
- `category`
- `maturity`
- `owner_agent`
- `secondary_agents`
- `reads`
- `writes`
- `requires`
- `autonomous_use`
- `notes`

## Refactor Implications

The cleaned system should:
- mark every script as production, experimental, or retired
- assign a primary owner to every operational script
- teach agents only their approved production tools by default
- move machine-specific infra notes out of role prompts into setup docs
