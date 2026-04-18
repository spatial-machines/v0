# Methodology Template Library

This directory contains pre-built methodology templates for common GIS consulting archetypes. Each template is a complete `project_brief.json`-compatible JSON file with the `analysis` section pre-filled with the known best-practice method stack for that problem type.

---

## How Agents Use These Templates

### 1. Select the right template at project kickoff

When a new project is started, the lead-analyst agent (or `create_run_plan.py`) should identify whether the engagement matches one of the methodology archetypes below. If it does, **copy the template** as the starting `project_brief.json` rather than starting from the blank template.

```bash
# Copy a template to start a new project
cp templates/methodologies/healthcare-access-gap.json \
   projects/my-project/project_brief.json
```

### 2. Fill in the blanks

The template pre-fills `analysis`, `data.primary_sources`, `outputs`, `report.scqa`, and `_methodology_caveats`. The agent still needs to fill in:

- `project_id`, `project_title`, `created_at`
- `client.*` — name, type, contact
- `audience.*` — who is reading and what they're deciding
- `engagement.hero_question` — refine from the template default
- `geography.*` — study area, bounding box, CRS
- `data.vintage` — confirm which ACS/FEMA/etc. vintage to use

### 3. Read caveats before writing the report

Every template includes a `_methodology_caveats` array. **Before writing the final report**, the reporting agent must read these caveats and check whether any apply to the current project. Common examples:

- Is the state Medicaid-expanded? (healthcare template)
- Did tract boundaries change between vintages? (poverty-change template)
- Is the NFHL complete for the study county? (hazard template)

### 4. Override analysis defaults deliberately

Templates set sensible defaults for `spatial_weights`, `classification_scheme`, and `k_classes`. Override these only when there is a specific reason:

| Default | When to change |
|---|---|
| `"queen"` weights | Switch to `"knn5"` for irregularly shaped tracts |
| `"natural_breaks"` | Switch to `"quantile"` for skewed distributions, or `"equal_interval"` for index comparisons |
| `k_classes: 5` | Use 3 for executive/simple maps, 7 for technical appendix detail |

---

## Available Templates

### `healthcare-access-gap.json`
**Use for:** Uninsured rate mapping, FQHC siting, HPSA analysis, preventive care gap

**Key methods:** Choropleth (uninsured rate) → Proportional symbols (uninsured count) → HPSA overlay → Drive-time service areas (10/20/30 min from FQHCs) → Spatial lag regression → Hotspot analysis

**Primary data:** ACS S2701, HRSA HPSA Designations, HRSA Health Center Finder, TIGER tracts

**Key caveats:**
- Medicaid expansion status materially affects baseline uninsurance rates — do not compare across expansion/non-expansion states without adjustment
- FQHCs serve uninsured patients regardless of designation — high FQHC count does not mean uninsurance is solved
- ACS uninsured MOEs are high in low-population tracts

---

### `environmental-justice-screening.json`
**Use for:** EJ burden mapping, pollution disparity analysis, regulatory comment support, grant documentation

**Key methods:** Bivariate choropleth (poverty × PM2.5) → EJ index choropleth → Hotspot analysis → Industrial facility overlay

**Primary data:** EPA EJScreen, ACS B17001/B03002, EPA Superfund NPL, EPA FRS facilities, TIGER tracts

**Key caveats:**
- EJScreen is a **screening tool**, not a regulatory determination — do not represent findings as legal findings of disproportionate impact
- PM2.5 values are modeled at ~1km resolution, not measured at the tract level
- Document exactly how the composite EJ index is constructed — different methods yield different rankings

---

### `food-access-analysis.json`
**Use for:** Food desert mapping, grocery access gap, nutrition program siting, food systems planning

**Key methods:** Food desert choropleth (LILA flag) → Drive-time service areas from grocery stores → Dot density (population in food deserts) → Spatial regression (obesity/diet outcome)

**Primary data:** USDA Food Access Research Atlas, ACS B08201/B17001, OSM grocery stores, CDC PLACES (optional), TIGER tracts

**Key caveats:**
- USDA Atlas is **2019 vintage** — grocery store landscape changed significantly post-COVID; validate with current OSM data
- `pct_no_vehicle` is a proxy for transit dependence; does not capture ride-share, delivery, or informal networks
- LILA flag thresholds are administrative, not evidence-based — consider custom distance thresholds for client needs

---

### `poverty-change-analysis.json`
**Use for:** Before/after poverty trend analysis, program evaluation, grant impact reporting, CDBG/ESG needs assessment

**Key methods:** Change detection diverging choropleth → Small multiples (poverty/unemployment/income/rent burden) → Persistent hotspot overlay → SCQA narrative framing

**Primary data:** ACS 5-year estimates (two vintages), Census Tract Relationship Files (for boundary crosswalk), TIGER tracts (both vintages)

**Key caveats:**
- ACS 5-year estimates have **overlapping years** between adjacent vintages — change estimates are not fully independent
- **COVID disruption**: 2020-2022 ACS data is noisy; any comparison crossing 2020 should be flagged
- Tract boundary changes between decennial censuses require a population-weighted crosswalk before change detection
- Declining poverty rate may reflect displacement rather than improvement — cross-check with rent burden change

---

### `natural-hazard-exposure.json`
**Use for:** Hazard mitigation planning, BRIC/HMGP grant applications, climate resilience prioritization, emergency management equity analysis

**Key methods:** Bivariate choropleth (hazard × SVI) → Zonal statistics of hazard rasters per tract → Proportional symbols (exposed population) → Hotspot analysis → Composite exposure index

**Primary data:** FEMA NFHL, USFS Wildfire Hazard Potential, CDC/ATSDR SVI, ACS B01003/B17001, TIGER tracts

**Key caveats:**
- **FEMA is US-only** — substitute UNDRR/JRC data for international work
- Modeled hazard zones represent historical conditions, not future climate projections — note this limitation explicitly
- SVI Theme 3 includes race/ethnicity — when presenting bivariate maps, frame as "vulnerability," not as demographic targeting
- Always pair choropleth maps with population-weighted symbols — sparsely populated high-hazard tracts look alarming on maps but represent few residents

---

## Template Schema Reference

All templates follow the `project_brief.json` schema (see `templates/project_brief.json`). Additional template-specific fields:

| Field | Description |
|---|---|
| `_methodology_id` | Unique identifier for the template (matches filename) |
| `_methodology_version` | Version number — increment when methods change |
| `_based_on` | Parent schema reference |
| `_methodology_caveats` | Array of known caveats — **agents must read before reporting** |
| `analysis.analysis_notes` | Detailed method notes beyond the `analysis_types_requested` list |
| `analysis.dependent_variable_alternatives` | Alternate dependent variables if the primary is unavailable |

---

## Adding New Templates

When a new consulting archetype recurs more than twice, create a new template:

1. Copy `templates/project_brief.json` as the base
2. Add `_methodology_id`, `_methodology_version`, `_based_on`, `_methodology_caveats`
3. Pre-fill `analysis`, `data.primary_sources`, `outputs`, and `report.scqa` with best-practice defaults
4. Add to this README
5. Test on a real project before treating as canonical

---

## Maintenance

- Review templates annually against current data vintages (USDA, EJScreen, SVI release cycles)
- Update `_methodology_version` when methods change
- Log lessons learned from real projects back into the relevant template's `analysis_notes` or `_methodology_caveats`
