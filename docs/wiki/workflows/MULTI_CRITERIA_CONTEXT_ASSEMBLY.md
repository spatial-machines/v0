# Multi-Criteria Context Assembly Workflow

Purpose:
define a repeatable process for assembling context from multiple domain layers into a single comparison or screening output
support site selection, suitability screening, and corridor or district assessment where the question requires combining demographic, POI, access, environmental, and land-use context
provide a disciplined assembly pattern without inventing a weighting, scoring, or multi-criteria decision model

Typical Use Cases
- comparing candidate sites across demographic, access, competitive, and environmental dimensions
- assembling corridor or district profiles from multiple domain layers
- producing a multi-layer screening output for planning or investment audiences
- framing suitability context when a formal scoring model is not yet available

Inputs
- candidate sites, study areas, or comparison geographies (validated geometry)
- approved list of context dimensions and the domain or workflow that provides each one
- project-approved working CRS
- project guidance on how context should be organized (side-by-side comparison, overlay map, summary table, or narrative)

Preconditions
- each context layer has been produced by its own domain workflow and passed its own QA gate
- the CRS is consistent across all layers per `standards/CRS_SELECTION_STANDARD.md`
- the project lead has approved which dimensions to include (do not add dimensions without approval)
- source readiness has been confirmed for each input per `standards/SOURCE_READINESS_STANDARD.md`

Preferred Tools
- GeoPandas for in-memory assembly and tabular output (`toolkits/GEOPANDAS_TOOLKIT.md`)
- PostGIS for scale and multi-layer spatial queries (`toolkits/POSTGIS_TOOLKIT.md`)
- GDAL/OGR for format conversion (`toolkits/GDAL_OGR_TOOLKIT.md`)

Execution Order

## Phase 1: Dimension Inventory

Identify and document each context dimension. Common dimensions and their upstream sources:

| Dimension | Upstream Domain or Workflow |
|---|---|
| Demographics | `domains/DEMOGRAPHICS_AND_MARKET_ANALYSIS.md` → `workflows/TRACT_JOIN_AND_ENRICHMENT.md` |
| POI / business landscape | `domains/POI_AND_BUSINESS_LANDSCAPE.md` → `workflows/POSTGIS_POI_LANDSCAPE.md` |
| Competitor density | `domains/COMPETITOR_AND_WHITE_SPACE_ANALYSIS.md` → `workflows/COMPETITOR_GAP_SCREENING.md` |
| Drive-time access | `domains/DRIVE_TIME_AND_SERVICE_AREA_PLANNING.md` → `workflows/SERVICE_AREA_ANALYSIS.md` |
| Transit access | `domains/TRANSIT_ACCESS_AND_COVERAGE.md` |
| Flood / hazard exposure | `domains/FLOOD_RISK_AND_FLOODPLAIN_ANALYSIS.md` or `domains/HAZARD_EXPOSURE_AND_RISK_SCREENING.md` |
| Land use / parcels | `domains/LAND_USE_AND_PARCEL_ANALYSIS.md` |
| Zoning constraints | `domains/ZONING_AND_DEVELOPMENT_CONSTRAINTS.md` |
| Environmental justice | `domains/ENVIRONMENTAL_JUSTICE_AND_EQUITY_SCREENING.md` |
| Terrain / hydrology | `domains/HYDROLOGY_AND_TERRAIN.md` → `workflows/TERRAIN_DERIVATIVES.md` |

Record which dimensions are approved and which are not applicable.

## Phase 2: Layer Production

For each approved dimension:
1. Run the upstream domain workflow to produce the layer.
2. Pass the layer through its domain-specific QA gate.
3. Confirm CRS alignment with the assembly target geography.
4. Document the source, vintage, and any limitations.

Each layer should be independently valid before assembly. Do not use the assembly step to compensate for a layer that failed its own QA.

## Phase 3: Spatial Alignment

1. Confirm all layers share the same CRS.
2. Align all layers to the comparison geography (candidate sites, study zones, trade areas, or grid cells).
3. For areal layers: apply spatial joins, intersection, or enrichment per the appropriate workflow.
4. For point layers: aggregate to the comparison geography (count, density, nearest distance).
5. For raster layers: extract zonal statistics to the comparison geography.
6. Document the alignment method for each layer.

## Phase 4: Assembly

1. Join all dimension summaries to the comparison geography in a single table or GeoDataFrame.
2. Organize columns by dimension for readability.
3. Do not compute composite scores, weighted indices, or rankings unless the project has a signed-off weighting methodology.
4. If the project requests a composite score, escalate the weighting question — do not invent weights.
5. Present dimensions side by side so the reader can see the full context for each candidate or zone.

## Phase 5: Validation and Output

1. Validate structural integrity with `qa-review/STRUCTURAL_QA_CHECKLIST.md`.
2. Review interpretive framing with `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`:
   - Does the output imply a recommendation that the data does not support?
   - Are limitations of individual layers stated?
   - Is it clear that this is a context assembly, not a scored ranking?
3. If the output supports high-stakes decisions, escalate to `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md`.
4. Generate comparison tables, maps, and summary outputs.
5. Route maps and deliverables through `domains/CARTOGRAPHY_AND_DELIVERY.md`.

Validation Checks
- each input layer passed its own QA gate before assembly
- all layers are CRS-aligned
- the dimension list matches the project-approved scope
- no composite scores or rankings were computed without a signed-off weighting method
- the output clearly presents context rather than implying a definitive recommendation
- limitations of individual layers are documented and not hidden by the assembly
- the assembly method (join type, aggregation, alignment) is documented for each dimension

Common Failure Modes
- assembling layers that failed their individual QA gates
- inventing weights or composite scores without project-approved methodology
- presenting a multi-layer context assembly as if it were a definitive suitability ranking
- mixing layers with very different trust levels, vintages, or geographies without noting the differences
- losing track of which dimension came from which source and method
- CRS misalignment between layers causing silent spatial join errors
- adding dimensions beyond the approved scope without project guidance
- not documenting the assembly method, making the output non-reproducible

Escalate When
- the project requests a weighted composite score or formal multi-criteria decision model
- individual context layers have conflicting implications for the same candidate
- the trust level of one dimension is much lower than the others and could mislead
- the output will support investment, legal, or regulatory decisions
- the number of dimensions exceeds what can be clearly communicated in the deliverable format

Outputs
- multi-dimension comparison table per candidate site or zone
- individual dimension maps (one per layer)
- composite context map if appropriate (showing multiple dimensions together)
- methodology documentation: dimension list, upstream source for each, alignment method, limitations
- map-ready layers

Related Standards
- `standards/CRS_SELECTION_STANDARD.md`
- `standards/SOURCE_READINESS_STANDARD.md`
- `standards/COUNT_RATE_MEDIAN_AGGREGATION_STANDARD.md`
- `standards/INTERPRETIVE_REVIEW_STANDARD.md`
- `standards/LEGAL_GRADE_ANALYSIS_STANDARD.md`

Related Workflows
- `workflows/TRACT_JOIN_AND_ENRICHMENT.md`
- `workflows/POSTGIS_POI_LANDSCAPE.md`
- `workflows/SERVICE_AREA_ANALYSIS.md`
- `workflows/TRADE_AREA_DELINEATION.md`
- `workflows/COMPETITOR_GAP_SCREENING.md`
- `workflows/TERRAIN_DERIVATIVES.md`
- `workflows/GENERAL_ANALYSIS_AND_OUTPUT_GENERATION.md`

Related QA
- `qa-review/STRUCTURAL_QA_CHECKLIST.md`
- `qa-review/INTERPRETIVE_REVIEW_CHECKLIST.md`
- `qa-review/MAP_QA_CHECKLIST.md`
- `qa-review/LEGAL_GRADE_ANALYSIS_REVIEW.md`
- `qa-review/SERVICE_AREA_AND_TRAVEL_TIME_QA.md`

Trust Level
Draft Workflow Needs Testing
