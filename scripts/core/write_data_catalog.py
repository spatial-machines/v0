#!/usr/bin/env python3
"""Generate a data_catalog.json from GeoPackage files.

Reads layer metadata, field statistics, and auto-generates descriptions
from common GIS field name patterns.

Usage:
    python write_data_catalog.py --gpkg file1.gpkg [file2.gpkg ...] --output data_catalog.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fiona
    import geopandas as gpd
    import numpy as np
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}. Run: pip install geopandas fiona")
    raise SystemExit(1)


# ── Field name → description heuristics ──────────────────────────────────────

FIELD_DESCRIPTIONS = [
    # Percentages
    (r'^pct_white$', 'Percentage of population identifying as White (non-Hispanic)'),
    (r'^pct_black$', 'Percentage of population identifying as Black (non-Hispanic)'),
    (r'^pct_hispanic$', 'Percentage of population identifying as Hispanic/Latino'),
    (r'^pct_asian$', 'Percentage of population identifying as Asian'),
    (r'^pct_minority$', 'Percentage of population identifying as racial/ethnic minority'),
    (r'^pct_poverty$', 'Percentage of population below poverty level'),
    (r'^pct_uninsured$', 'Percentage of population without health insurance'),
    (r'^pct_snap$', 'Percentage of households receiving SNAP benefits'),
    (r'^pct_renter$', 'Percentage of renter-occupied housing units'),
    (r'^pct_owner$', 'Percentage of owner-occupied housing units'),
    (r'^pct_vacancy$', 'Percentage of vacant housing units'),
    (r'^pct_cost_burdened$', 'Percentage of households spending >30% income on housing'),
    (r'^pct_severe_burden$', 'Percentage of households spending >50% income on housing'),
    (r'^pct_no_vehicle$', 'Percentage of households with no vehicle'),
    (r'^pct_bachelor', 'Percentage of population with bachelor\'s degree or higher'),
    (r'^pct_tree_canopy$', 'Percentage of area covered by tree canopy'),
    (r'^pct_impervious$', 'Percentage of area covered by impervious surfaces'),
    (r'^pct_', 'Percentage of '),

    # Population fields
    (r'^total_pop', 'Total population'),
    (r'^nh_white$', 'Non-Hispanic White population count'),
    (r'^nh_black$', 'Non-Hispanic Black population count'),
    (r'^hispanic$', 'Hispanic/Latino population count'),
    (r'^nh_asian$', 'Non-Hispanic Asian population count'),

    # Income / economic
    (r'^median_income$', 'Median household income ($)'),
    (r'^median_home_value$', 'Median home value ($)'),
    (r'^median_rent$', 'Median gross rent ($)'),
    (r'^median_age$', 'Median age of population'),
    (r'^poverty_rate$', 'Poverty rate (% below poverty level)'),
    (r'^poverty_universe$', 'Population for whom poverty status is determined'),
    (r'^below_poverty$', 'Population below poverty level'),
    (r'^unemployment_rate$', 'Unemployment rate (%)'),
    (r'^gini_index$', 'Gini index of income inequality'),

    # Health
    (r'^obesity_pct$', 'Adult obesity prevalence (%)'),
    (r'^diabetes_pct$', 'Adult diabetes prevalence (%)'),
    (r'^uninsured_pct$', 'Population without health insurance (%)'),
    (r'^life_expectancy$', 'Life expectancy at birth (years)'),
    (r'^mental_health_pct$', 'Poor mental health days prevalence (%)'),

    # Transportation
    (r'^bus_stop_count$', 'Number of bus stops in tract'),
    (r'^bus_stops_per_sqkm$', 'Bus stop density (stops per sq km)'),
    (r'^transit_score$', 'Transit accessibility score'),
    (r'^dist_to_transit', 'Distance to nearest transit stop'),

    # Food access
    (r'^grocery_store_count$', 'Number of grocery stores in tract'),
    (r'^grocery_stores_per_sqkm$', 'Grocery store density (stores per sq km)'),
    (r'^food_desert$', 'USDA food desert flag'),
    (r'^low_food$', 'Low food access flag'),
    (r'^snap_stores$', 'Number of SNAP-authorized retailers'),

    # Environment
    (r'^heat_index$', 'Urban heat island index'),
    (r'^pm25$', 'Particulate matter (PM2.5) concentration'),
    (r'^ozone$', 'Ozone concentration'),
    (r'^ej_score$', 'Environmental justice composite score'),
    (r'^superfund_proximity$', 'Proximity to Superfund sites'),

    # Spatial / geographic
    (r'^area_sqkm$', 'Area in square kilometers'),
    (r'^area_sqmi$', 'Area in square miles'),
    (r'^ALAND$', 'Land area (sq meters, Census)'),
    (r'^AWATER$', 'Water area (sq meters, Census)'),
    (r'^INTPTLAT$', 'Internal point latitude (Census)'),
    (r'^INTPTLON$', 'Internal point longitude (Census)'),

    # Census identifiers
    (r'^GEOID', 'Census geographic identifier'),
    (r'^GEOIDFQ$', 'Fully qualified Census GEOID'),
    (r'^STATEFP$', 'State FIPS code'),
    (r'^COUNTYFP$', 'County FIPS code'),
    (r'^TRACTCE$', 'Census tract code'),
    (r'^BLKGRPCE$', 'Block group code'),
    (r'^NAME$', 'Census feature name'),
    (r'^NAMELSAD$', 'Name with legal/statistical area description'),
    (r'^MTFCC$', 'MAF/TIGER feature class code'),
    (r'^FUNCSTAT$', 'Functional status code'),

    # Flags / scores
    (r'^low_transit$', 'Low transit access flag'),
    (r'^high_obesity$', 'High obesity prevalence flag'),
    (r'^disadvantage_score$', 'Composite disadvantage score'),
    (r'^hotspot_', 'Spatial clustering hotspot classification'),
    (r'^cluster_', 'Spatial cluster assignment'),
    (r'^lisa_', 'Local spatial autocorrelation (LISA) classification'),

    # Competitor / POI
    (r'^competitor_count', 'Number of competitor locations'),
    (r'^competitor_density', 'Competitor density in trade area'),
    (r'^dist_to_nearest', 'Distance to nearest feature'),
    (r'^site_score$', 'Composite site suitability score'),
    (r'^trade_area', 'Trade area indicator or metric'),

    # Change detection
    (r'^change_', 'Change metric between time periods'),
    (r'^diff_', 'Difference between time periods'),

    # Catch-all patterns
    (r'_rate$', 'Rate metric'),
    (r'_count$', 'Count metric'),
    (r'_per_sqkm$', 'Density per square kilometer'),
    (r'_per_capita$', 'Per capita metric'),
    (r'_score$', 'Composite score'),
    (r'_flag$', 'Binary indicator flag'),
    (r'_pct$', 'Percentage metric'),
    (r'_rank$', 'Rank ordering'),
]


def describe_field(name):
    """Return a human-readable description for a field name."""
    for pattern, desc in FIELD_DESCRIPTIONS:
        if re.search(pattern, name, re.IGNORECASE):
            # For catch-all "pct_" pattern, append the rest of the name
            if desc == 'Percentage of ':
                suffix = name.replace('pct_', '').replace('_', ' ')
                return f'Percentage of {suffix}'
            return desc
    # Fallback: humanize the field name
    return name.replace('_', ' ').title()


def dtype_str(dtype):
    """Convert numpy/pandas dtype to a readable string."""
    s = str(dtype)
    if 'int' in s:
        return 'integer'
    if 'float' in s:
        return 'float'
    if s in ('object', 'str', 'string'):
        return 'string'
    if 'bool' in s:
        return 'boolean'
    if 'datetime' in s:
        return 'datetime'
    if s == 'geometry':
        return 'geometry'
    return s


def catalog_layer(gpkg_path, layer_name):
    """Build catalog entry for a single layer."""
    gdf = gpd.read_file(gpkg_path, layer=layer_name)

    geom_type = None
    if 'geometry' in gdf.columns and gdf.geometry is not None and not gdf.geometry.isna().all():
        geom_types = gdf.geometry.geom_type.dropna().unique()
        geom_type = geom_types[0] if len(geom_types) == 1 else '/'.join(sorted(geom_types))

    crs_str = str(gdf.crs) if gdf.crs else None
    bounds = None
    if gdf.geometry is not None and not gdf.geometry.isna().all():
        b = gdf.total_bounds
        bounds = [round(float(x), 6) for x in b]

    columns = []
    for col in gdf.columns:
        if col == 'geometry':
            continue
        series = gdf[col]
        col_info = {
            'name': col,
            'dtype': dtype_str(series.dtype),
            'description': describe_field(col),
            'non_null_count': int(series.notna().sum()),
        }
        if series.dtype.kind in ('i', 'f'):
            valid = series.dropna()
            if len(valid) > 0:
                col_info['min'] = round(float(valid.min()), 4) if series.dtype.kind == 'f' else int(valid.min())
                col_info['max'] = round(float(valid.max()), 4) if series.dtype.kind == 'f' else int(valid.max())
        elif series.dtype == object:
            valid = series.dropna().astype(str)
            if len(valid) > 0:
                top = valid.value_counts().head(3).index.tolist()
                col_info['sample_values'] = top

        columns.append(col_info)

    return {
        'name': layer_name,
        'geometry_type': geom_type,
        'feature_count': len(gdf),
        'crs': crs_str,
        'bbox': bounds,
        'field_count': len(columns),
        'columns': columns,
    }


def build_catalog(gpkg_paths):
    """Build a full catalog from one or more GeoPackages."""
    layers = []
    for gpkg_path in gpkg_paths:
        gpkg_path = Path(gpkg_path)
        if not gpkg_path.exists():
            print(f"  WARN: {gpkg_path} not found, skipping")
            continue
        layer_names = fiona.listlayers(str(gpkg_path))
        for ln in layer_names:
            try:
                entry = catalog_layer(str(gpkg_path), ln)
                entry['source_file'] = gpkg_path.name
                layers.append(entry)
            except Exception as e:
                print(f"  WARN: Failed to catalog {gpkg_path.name}/{ln}: {e}")
    return {'layers': layers}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate data catalog from GeoPackages")
    parser.add_argument('--gpkg', nargs='+', required=True, help='GeoPackage file(s)')
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()

    catalog = build_catalog(args.gpkg)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(catalog, f, indent=2)
    print(f"Catalog written: {args.output} ({len(catalog['layers'])} layers)")


if __name__ == "__main__":
    raise SystemExit(main())
