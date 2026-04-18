#!/usr/bin/env python3
"""Generate a data dictionary for a GeoPackage or CSV deliverable.

For each column, documents:
  - Column name
  - Data type
  - Non-null count and null rate
  - Min / max / mean / median (numeric)
  - Unique value count (categorical)
  - Description (from --descriptions JSON or auto-generated)

Output: Markdown file suitable for including with deliverables.

Usage:
    python write_data_dictionary.py \\
        --input data/processed/tracts_poverty.gpkg \\
        --output outputs/reports/data_dictionary.md \\
        [--title "Kansas Poverty Analysis — Data Dictionary"] \\
        [--source "ACS 2022 5-Year Estimates"] \\
        [--vintage "2018-2022"] \\
        [--descriptions descriptions.json]

descriptions.json format:
    {"poverty_rate": "Percent of population below federal poverty line",
     "GEOID": "11-digit Census tract FIPS code"}
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent

# Common column description hints
AUTO_DESCRIPTIONS = {
    "geoid": "Census tract FIPS code (11 digits: 2-digit state + 3-digit county + 6-digit tract)",
    "tractce": "Census tract code (6 digits)",
    "statefp": "State FIPS code (2 digits)",
    "countyfp": "County FIPS code (3 digits)",
    "name": "Census tract name",
    "namelsad": "Census tract name with suffix (e.g., 'Census Tract 1.01')",
    "aland": "Land area in square meters",
    "awater": "Water area in square meters",
    "geometry": "Geographic geometry (polygon/multipolygon in WGS84)",
    "poverty_rate": "Percent of population with income below the federal poverty level (ACS B17001)",
    "uninsured_rate": "Percent of civilian non-institutionalized population with no health insurance (ACS S2701)",
    "median_income": "Median household income in inflation-adjusted dollars (ACS B19013)",
    "total_population": "Total population estimate (ACS B01003)",
    "pct_rural": "Percent of housing units in rural areas",
    "nearest_hospital_km": "Straight-line distance in kilometers to the nearest hospital facility",
    "hospital_count": "Number of hospital facilities within the analysis area",
    "gi_z": "Getis-Ord Gi* z-score (positive = hot spot, negative = cold spot)",
    "gi_p": "Permutation-based pseudo p-value for Gi* (FDR-corrected threshold applied)",
    "hotspot_class": "Gi* significance category: Hot Spot (99%/95%/90%), Cold Spot (90%/95%/99%), Not Significant",
    "lisa_cluster": "Local Moran's I cluster type: High-High, Low-Low, High-Low, Low-High, Not Significant",
    "lisa_p": "Permutation-based pseudo p-value for Local Moran's I (FDR-corrected)",
    "moe": "Margin of error at 90% confidence interval",
}


def describe_column(series, name):
    """Generate stats summary for a single column."""
    total = len(series)
    null_count = int(series.isna().sum())
    null_pct = round(null_count / total * 100, 1) if total > 0 else 0
    non_null = series.dropna()

    row = {
        "column": name,
        "dtype": str(series.dtype),
        "non_null": len(non_null),
        "null_count": null_count,
        "null_pct": null_pct,
    }

    if pd.api.types.is_numeric_dtype(series):
        if len(non_null) > 0:
            row.update({
                "min": round(float(non_null.min()), 4),
                "max": round(float(non_null.max()), 4),
                "mean": round(float(non_null.mean()), 4),
                "median": round(float(non_null.median()), 4),
                "std": round(float(non_null.std()), 4),
            })
    else:
        unique = series.nunique(dropna=True)
        row["unique_values"] = int(unique)
        if unique <= 10:
            row["values"] = sorted([str(v) for v in series.dropna().unique()])

    return row


def auto_describe(col_name):
    """Look up a canned description for known column names."""
    lower = col_name.lower()
    for key, desc in AUTO_DESCRIPTIONS.items():
        if lower == key or lower.startswith(key + "_") or lower.endswith("_" + key):
            return desc
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="GeoPackage or CSV to document")
    parser.add_argument("-o", "--output", help="Output Markdown path")
    parser.add_argument("--title", help="Dictionary title")
    parser.add_argument("--source", help="Data source description")
    parser.add_argument("--vintage", help="Data vintage (e.g. '2018-2022 ACS 5-Year')")
    parser.add_argument("--descriptions", help="JSON file with column descriptions")
    parser.add_argument("--exclude-geometry", action="store_true", default=True)
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    if src.suffix.lower() in (".gpkg", ".shp", ".geojson"):
        gdf = gpd.read_file(src)
        crs = str(gdf.crs) if gdf.crs else "Unknown"
        feature_count = len(gdf)
        df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
        geom_type = gdf.geometry.geom_type.value_counts().index[0] if len(gdf) > 0 else "Unknown"
    else:
        df = pd.read_csv(src, low_memory=False)
        crs = "N/A"
        feature_count = len(df)
        geom_type = "N/A"

    # Load custom descriptions
    custom_descriptions = {}
    if args.descriptions:
        desc_path = Path(args.descriptions)
        if desc_path.exists():
            custom_descriptions = json.loads(desc_path.read_text())

    # Build column stats
    stats = []
    for col in df.columns:
        s = describe_column(df[col], col)
        # Description: custom > auto > empty
        s["description"] = custom_descriptions.get(col) or auto_describe(col)
        stats.append(s)

    # Output path
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "reports"
        out_path = out_dir / f"{src.stem}_data_dictionary.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown
    title = args.title or f"{src.stem.replace('_', ' ').title()} — Data Dictionary"
    lines = [
        f"# {title}",
        "",
        "## File Information",
        "",
        f"| Property | Value |",
        f"|---|---|",
        f"| File | `{src.name}` |",
        f"| Features | {feature_count:,} |",
        f"| Geometry type | {geom_type} |",
        f"| CRS | {crs} |",
        f"| Columns | {len(df.columns)} |",
    ]
    if args.source:
        lines.append(f"| Source | {args.source} |")
    if args.vintage:
        lines.append(f"| Vintage | {args.vintage} |")
    lines += ["", "---", "", "## Column Definitions", ""]

    for s in stats:
        lines.append(f"### `{s['column']}`")
        lines.append("")
        if s["description"]:
            lines.append(f"**{s['description']}**")
            lines.append("")

        lines.append(f"| Property | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Type | `{s['dtype']}` |")
        lines.append(f"| Non-null | {s['non_null']:,} / {s['non_null'] + s['null_count']:,} ({100 - s['null_pct']:.1f}% complete) |")
        if s["null_count"] > 0:
            lines.append(f"| Null count | {s['null_count']:,} ({s['null_pct']:.1f}%) |")

        if "min" in s:
            lines.append(f"| Min | {s['min']:,} |")
            lines.append(f"| Max | {s['max']:,} |")
            lines.append(f"| Mean | {s['mean']:,} |")
            lines.append(f"| Median | {s['median']:,} |")
        elif "unique_values" in s:
            lines.append(f"| Unique values | {s['unique_values']:,} |")
            if "values" in s:
                vals = ", ".join([f"`{v}`" for v in s["values"][:10]])
                lines.append(f"| Values | {vals} |")

        lines.append("")

    content = "\n".join(lines)
    out_path.write_text(content)
    print(f"Saved data dictionary: {out_path} ({len(stats)} columns documented)")

    # Handoff log
    log = {
        "step": "write_data_dictionary",
        "source": str(src),
        "output": str(out_path),
        "columns": len(stats),
        "features": feature_count,
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
