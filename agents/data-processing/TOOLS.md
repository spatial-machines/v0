# TOOLS.md — Data Processing

Approved operational tools for the Data Processing role.

Canonical references:
- `docs/architecture/ACTIVE_TEAM.md`
- `docs/architecture/PIPELINE_CANON.md`
- `docs/architecture/TOOL_GOVERNANCE.md`

## Primary Tool Classes

- `processing`
- `derivation`

## Approved Production Tools

### Processing
- `process_vector.py`
- `process_table.py`
- `extract_archive.py`
- `join_data.py`
- `batch_join.py`
- `spatial_join.py`

### Raster Processing
- `raster_clip.py` — clip raster to vector mask or bounding box
- `raster_calc.py` — raster calculator with spectral index presets
- `raster_mosaic.py` — merge/mosaic multiple raster tiles
- `raster_proximity.py` — compute proximity/distance raster from vector features
- `terrain_analysis.py` — compute terrain derivatives (slope, aspect, hillshade) from DEM

### Derivation
- `derive_fields.py`
- `compute_rate.py`
- `enrich_points.py`

### Handoff
- `write_processing_handoff.py`

## Experimental Tools

Escalate before relying on:
- raster-heavy processing paths not yet standardized
- unusual one-off transformations that bypass established logging patterns
- any workflow that would make processed outputs harder to audit

## Conditional / Secondary Tools

Use only when the workflow explicitly requires them:
- trade area or buffer preparation tools
- zonal/raster-support tools when the processing workflow is already approved

## Inputs You Depend On

- raw files
- manifests
- retrieval provenance
- processing instructions

## Outputs You Are Expected To Produce

- `data/interim/*`
- `data/processed/*`
- `.processing.json`, `.derivation.json`, `.join.json` sidecars
- processing handoff artifact

## Operational Rules

- prefer GeoPackage for spatial outputs
- preserve join diagnostics
- keep field names stable and explicit
- do not treat experimental raster workflows as default processing paths
