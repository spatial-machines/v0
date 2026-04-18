# Field Data Collection Guide

_KoboToolbox/ODK form design, exports, and ingestion into the GIS pipeline._

---

## Overview

The GIS firm supports primary data collection via **KoboToolbox** and **ODK** (Open Data Kit). Field surveys generate GPS-located point data that feeds directly into the analysis pipeline alongside secondary data sources (ACS, HRSA, etc.).

Use `ingest_field_survey.py` to convert raw exports to GeoPackage format ready for analysis.

---

## Setting Up a KoboToolbox Form for GIS Data Collection

### Required Fields

Every form intended for GIS analysis needs:

1. **GPS point** — Use the `geopoint` question type. This generates lat/lon/altitude/accuracy.
   - KoboToolbox column output: `_gps_latitude`, `_gps_longitude`, `_gps_altitude`, `_gps_precision`
   - Set accuracy threshold in the form settings: require < 10m before allowing submission

2. **Submission metadata** — KoboToolbox auto-generates:
   - `_uuid` — unique submission ID (critical for deduplication)
   - `_submission_time` — UTC timestamp
   - `_submitted_by` — enumerator username

3. **Data quality fields:**
   - `enumerator_name` — text field (cross-check with `_submitted_by`)
   - `data_quality_notes` — text field for any issues observed in the field
   - `photo_site` — image question (generates URL in export, not embedded data)

### Form Design Best Practices

**GPS accuracy:**
```
Question type: geopoint
Label: "Record your current GPS location"
Constraint: ${gps_point_accuracy} < 10
Constraint message: "GPS accuracy must be under 10 meters. Please wait for a better signal."
```

**Multiple-choice questions** (becomes boolean flags in GIS pipeline):
```
Question type: select_multiple
Label: "Land use types present (select all that apply)"
Options: residential / commercial / industrial / agricultural / vacant / greenspace
```

**Repeat groups** (e.g., multiple buildings at one site):
```
Question type: begin_repeat
Label: "Building survey"
  - building_type: select_one
  - building_condition: select_one (good / fair / poor / collapsed)
  - estimated_occupants: integer
end_repeat
```

**Photo attachments:**
```
Question type: image
Label: "Site photo (wide angle)"
Name: photo_site_wide
```

The ingest script documents photo column names but does **not** download or embed the images.

---

## Export Formats

### KoboToolbox CSV Export

1. Go to your project → **Data** → **Downloads**
2. Select **CSV** format
3. Under **Value and header format**, choose **XML values and headers** (best for auto-detection)
4. Check **Include groups in headers**
5. Download

Key columns in XML-header export:
- `_gps_latitude`, `_gps_longitude`, `_gps_altitude`, `_gps_precision`
- `_uuid`, `_submission_time`, `_submitted_by`
- Repeat groups appear as `group_name/field_name`

### KoboToolbox XLS Export

Same settings as CSV but choose **XLS** format. The ingest script handles both.

### ODK Central / ODK Collect

1. ODK Central: **Submissions** → **Export to CSV**
2. Key columns: `gps_point_latitude`, `gps_point_longitude`, `gps_point_accuracy`, `instanceID`
3. Repeat groups export as separate CSV files (handle manually or use the repeat group flattener)

---

## Using ingest_field_survey.py

### Basic Usage

```bash
# Auto-detect KoboToolbox format
python scripts/ingest_field_survey.py \
    --input data/raw/survey_2024_kobo.csv \
    --output data/processed/field_survey.gpkg

# ODK export with explicit columns
python scripts/ingest_field_survey.py \
    --input data/raw/survey_2024_odk.csv \
    --lat-col gps_point_latitude \
    --lon-col gps_point_longitude \
    --output data/processed/field_survey.gpkg

# Flag duplicate submissions
python scripts/ingest_field_survey.py \
    --input data/raw/survey_2024_kobo.csv \
    --output data/processed/field_survey.gpkg \
    --deduplicate
```

### What the Script Does

1. **Format detection** — auto-detects KoboToolbox vs ODK from column names
2. **GPS accuracy flagging** — adds `low_accuracy=True` for points with >10m GPS accuracy
3. **Coordinate validation** — drops rows with missing/invalid coordinates (logged)
4. **Duplicate detection** — flags `is_duplicate=True` based on UUID or lat/lon/timestamp
5. **Multiple-choice expansion** — space-separated choice columns become boolean flag columns (`land_use__residential`, `land_use__commercial`, etc.)
6. **Repeat group flattening** — `household_members_1_name`, `household_members_2_name`, etc. → a separate `_repeats.gpkg` layer
7. **Attachment documentation** — photo/image column names documented in data dictionary (files not downloaded)
8. **Output** — GeoPackage + data dictionary JSON + processing log JSON

### Output Files

| File | Contents |
|---|---|
| `field_survey.gpkg` | Main point layer (WGS84, EPSG:4326) |
| `field_survey_repeats.gpkg` | Flattened repeat group records (if present) |
| `field_survey_dictionary.json` | Column types, counts, value distributions |
| `field_survey_log.json` | Processing log (format detected, flags raised, row counts) |

### Integrating with the Analysis Pipeline

After ingestion, the GeoPackage is standard and works with all existing pipeline scripts:

```bash
# Validate the output
python scripts/inspect_dataset.py data/processed/field_survey.gpkg

# Upload to PostGIS for large-scale analysis
python -c "
from scripts.postgis_utils import connect, upload_layer
import geopandas as gpd
gdf = gpd.read_file('data/processed/field_survey.gpkg')
upload_layer(gdf, 'field_survey_2024', schema='analyses')
"

# Spatial join with census tracts
python scripts/spatial_join.py \
    --left data/processed/field_survey.gpkg \
    --right data/processed/tracts.gpkg \
    --how left \
    --predicate within \
    --output data/processed/survey_with_tracts.gpkg
```

---

## Common Field Data Quality Issues

### GPS Issues

**Low accuracy (>10m)**
- Cause: indoors, tree canopy, urban canyon, or rushed collection
- Symptom: `low_accuracy=True` flag in output
- Fix: re-collect with enumerator standing outdoors, waiting for accuracy to stabilize
- Rule: exclude `low_accuracy=True` points from final analysis unless explicitly justified

**GPS drift / coordinate swap**
- Cause: device bug, manual entry error (lat/lon swapped)
- Symptom: points in ocean, wrong country, or outside expected study area
- Detection: `inspect_dataset.py` bounding box check; visually review on web map
- Fix: cross-reference with enumerator records; exclude or correct in post-processing

**Missing coordinates**
- Cause: enumerator skipped GPS step, device failure
- Symptom: blank lat/lon columns
- Fix: ask enumerator for address; use `geocode_addresses.py` to recover approximate location

### Data Entry Issues

**Duplicate submissions**
- Cause: form submitted twice (network retry, enumerator error)
- Symptom: identical `_uuid` or matching lat/lon/timestamp
- Fix: use `--deduplicate` flag; review `is_duplicate=True` records before excluding

**Multiple-choice misuse**
- Cause: enumerator entered free text in a select_multiple field
- Symptom: unexpected tokens in boolean expansion
- Fix: review `data dictionary → top_values` for suspicious entries; clean in post-processing

**Repeat group inconsistencies**
- Cause: enumerator added repeat entries without a parent record
- Symptom: orphaned repeat rows (null `parent_id`)
- Fix: join repeats back to main survey on `parent_id`; orphans indicate data collection error

### Survey Design Issues

**Ambiguous GPS point**
- Cause: form asks for "location" but doesn't specify centroid of polygon feature vs entry point
- Fix: always specify "stand at the center of the site" or "stand at the main entrance"

**Photo naming collisions**
- Cause: multiple photo questions with similar names
- Symptom: URLs overwritten in KoboToolbox export
- Fix: use unique, descriptive names (`photo_north_facade`, `photo_interior_main`)

**Offline sync failures**
- Cause: ODK Collect submissions cached but never synced
- Symptom: missing submissions in export despite enumerator completing them
- Fix: have enumerators verify sync completion before leaving the field; check ODK Central pending queue

---

## Quality Control Checklist (post-ingest)

```bash
# 1. Check output
python scripts/inspect_dataset.py data/processed/field_survey.gpkg

# 2. Review processing log
cat data/processed/field_survey_log.json | python -m json.tool | grep -A5 "summary"

# 3. Map it — spot visual outliers
python scripts/render_web_map.py \
    --input data/processed/field_survey.gpkg \
    --output data/processed/field_survey_preview.html

# 4. Flag review — how many low-accuracy or duplicate points?
python -c "
import geopandas as gpd
gdf = gpd.read_file('data/processed/field_survey.gpkg')
print('Total:', len(gdf))
print('Low accuracy:', gdf.get('low_accuracy', False).sum())
print('Duplicates:', gdf.get('is_duplicate', False).sum())
"
```
