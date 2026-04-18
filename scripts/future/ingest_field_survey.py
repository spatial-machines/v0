"""
ingest_field_survey.py — Bridge ODK/KoboToolbox field survey exports to the GIS pipeline.

Reads a CSV or XLS export from KoboToolbox or ODK, converts it to a point
GeoDataFrame, writes a GeoPackage, a data dictionary, and a JSON processing log.

Supported formats:
  - KoboToolbox CSV export (column prefix: _gps_latitude, _gps_longitude, _accuracy)
  - ODK CSV export         (column prefix: gps_point_latitude, gps_point_longitude)
  - Any CSV with explicit --lat-col / --lon-col

Features handled:
  - GPS accuracy flagging (>10m marked as low_accuracy=True)
  - Multiple-choice columns (select_multiple → boolean flags)
  - Repeat groups (flattened to a separate GeoPackage layer)
  - Photo attachment columns (paths documented, not embedded)
  - Duplicate submission detection (--deduplicate flag)

Usage:
    python scripts/ingest_field_survey.py \\
        --input data/raw/survey_export.csv \\
        --output data/processed/field_survey.gpkg \\
        --deduplicate

    python scripts/ingest_field_survey.py \\
        --input data/raw/kobo_export.xlsx \\
        --lat-col _gps_latitude \\
        --lon-col _gps_longitude \\
        --output data/processed/field_survey.gpkg

Output files:
    <output>.gpkg          — Point GeoPackage (main layer)
    <output>_repeats.gpkg  — Flattened repeat groups (if any)
    <output>_dictionary.json — Data dictionary
    <output>_log.json      — Processing log
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# GPS accuracy threshold in meters — points above this are flagged
GPS_ACCURACY_THRESHOLD = 10.0

# Column name patterns for auto-detecting format
KOBO_LAT_PATTERNS = ["_gps_latitude", "gps_coordinates_latitude", "_GPS_latitude"]
KOBO_LON_PATTERNS = ["_gps_longitude", "gps_coordinates_longitude", "_GPS_longitude"]
KOBO_ACC_PATTERNS = ["_gps_altitude", "_gps_precision", "gps_coordinates_precision"]

ODK_LAT_PATTERNS = ["gps_point_latitude", "gps-point_latitude", "location_latitude"]
ODK_LON_PATTERNS = ["gps_point_longitude", "gps-point_longitude", "location_longitude"]
ODK_ACC_PATTERNS = ["gps_point_accuracy", "gps-point_accuracy", "location_accuracy"]

# Photo/attachment column patterns
ATTACHMENT_PATTERNS = [r".*_URL$", r".*_url$", r".*photo.*", r".*image.*", r".*attachment.*"]

# Multiple-choice column pattern (KoboToolbox/ODK both use space-separated values)
MULTI_CHOICE_PATTERNS = [r"^select_multiple/", r".*\(select all that apply\)"]

# Columns that indicate repeat groups (flattened index)
REPEAT_SUFFIX = "_repeat_"
REPEAT_KOBO_PATTERN = r"^.*_index$"


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(df: pd.DataFrame) -> tuple[str, str, str, Optional[str]]:
    """
    Auto-detect KoboToolbox vs ODK format and return (format, lat_col, lon_col, acc_col).

    Returns:
        Tuple of (format_name, lat_col, lon_col, accuracy_col_or_None)
    """
    cols = set(df.columns)

    for lat, lon in zip(KOBO_LAT_PATTERNS, KOBO_LON_PATTERNS):
        if lat in cols and lon in cols:
            acc = next((a for a in KOBO_ACC_PATTERNS if a in cols), None)
            return "kobotoolbox", lat, lon, acc

    for lat, lon in zip(ODK_LAT_PATTERNS, ODK_LON_PATTERNS):
        if lat in cols and lon in cols:
            acc = next((a for a in ODK_ACC_PATTERNS if a in cols), None)
            return "odk", lat, lon, acc

    return "unknown", "", "", None


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_file(path: str) -> pd.DataFrame:
    """Load CSV or XLS/XLSX into a DataFrame."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        # KoboToolbox CSVs sometimes have BOM
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    elif suffix in (".xls", ".xlsx"):
        return pd.read_excel(path, engine="openpyxl" if suffix == ".xlsx" else "xlrd")
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Expected .csv, .xls, or .xlsx")


# ---------------------------------------------------------------------------
# Multiple-choice expansion
# ---------------------------------------------------------------------------

def expand_multiple_choice(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """
    Detect space-separated multiple-choice columns and expand to boolean flags.

    A column is treated as multi-choice if:
      - Its name contains 'select_multiple' or similar pattern, OR
      - Its values contain spaces AND the set of unique tokens is small (< 50)
    """
    expanded_cols = []

    for col in df.columns:
        # Skip obviously non-categorical columns
        if df[col].dtype in [np.float64, np.int64]:
            continue
        if df[col].isna().all():
            continue

        # Heuristic: non-null string values that contain spaces with repeated tokens
        sample = df[col].dropna().astype(str)
        if len(sample) == 0:
            continue

        has_spaces = sample.str.contains(" ").any()
        if not has_spaces:
            continue

        # Collect all unique tokens
        all_tokens = set()
        for val in sample:
            all_tokens.update(val.strip().split())

        # If token set is reasonable (looks like choices, not free text)
        if 2 <= len(all_tokens) <= 50 and all(len(t) < 50 for t in all_tokens):
            for token in sorted(all_tokens):
                new_col = f"{col}__{token}"
                df[new_col] = df[col].apply(
                    lambda v: token in str(v).split() if pd.notna(v) else False
                )
                expanded_cols.append(new_col)

            log.append({
                "action": "expand_multiple_choice",
                "source_col": col,
                "choices": sorted(all_tokens),
                "new_cols": [f"{col}__{t}" for t in sorted(all_tokens)],
            })
            logger.info(
                "Expanded multi-choice column '%s' → %d boolean flags",
                col, len(all_tokens)
            )

    return df


# ---------------------------------------------------------------------------
# Repeat group handling
# ---------------------------------------------------------------------------

def extract_repeat_groups(df: pd.DataFrame, log: list) -> tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Detect and flatten repeat group columns.

    KoboToolbox repeat groups appear as columns with a shared prefix and an
    index suffix (e.g., household_members_1_name, household_members_2_name).

    Returns:
        (main_df_without_repeat_cols, repeat_df_or_None)
    """
    # Detect repeat group columns: pattern like prefix_N_suffix
    repeat_pattern = re.compile(r"^(.+?)_(\d+)_(.+)$")
    repeat_cols = [c for c in df.columns if repeat_pattern.match(c)]

    if not repeat_cols:
        return df, None

    # Group by prefix
    groups: dict[str, list] = {}
    for col in repeat_cols:
        m = repeat_pattern.match(col)
        prefix = m.group(1)
        groups.setdefault(prefix, []).append(col)

    repeat_rows = []
    id_col = "_id" if "_id" in df.columns else df.columns[0]

    for prefix, cols in groups.items():
        # Find all indices used
        indices = sorted(set(
            int(repeat_pattern.match(c).group(2)) for c in cols
        ))
        field_names = sorted(set(
            repeat_pattern.match(c).group(3) for c in cols
        ))

        for _, row in df.iterrows():
            for idx in indices:
                record = {
                    "parent_id": row.get(id_col),
                    "repeat_group": prefix,
                    "repeat_index": idx,
                }
                for field in field_names:
                    col_name = f"{prefix}_{idx}_{field}"
                    if col_name in df.columns:
                        record[field] = row.get(col_name)
                repeat_rows.append(record)

    repeat_df = pd.DataFrame(repeat_rows).dropna(
        subset=[c for c in ["parent_id"] if c in repeat_rows[0] if repeat_rows else []]
    )

    # Remove repeat cols from main df
    main_df = df.drop(columns=repeat_cols)

    log.append({
        "action": "extract_repeat_groups",
        "groups": list(groups.keys()),
        "repeat_records": len(repeat_df),
    })
    logger.info(
        "Extracted %d repeat group records from %d groups",
        len(repeat_df), len(groups)
    )

    return main_df, repeat_df


# ---------------------------------------------------------------------------
# Photo/attachment handling
# ---------------------------------------------------------------------------

def document_attachments(df: pd.DataFrame, log: list) -> tuple[pd.DataFrame, list]:
    """
    Find photo/attachment columns, document them, and add a note column.
    Does NOT embed or download the files.
    """
    attachment_cols = []
    for col in df.columns:
        for pattern in ATTACHMENT_PATTERNS:
            if re.search(pattern, col, re.IGNORECASE):
                attachment_cols.append(col)
                break

    if attachment_cols:
        log.append({
            "action": "document_attachments",
            "columns": attachment_cols,
            "note": "Attachment paths documented. Files not downloaded or embedded.",
        })
        logger.info("Found %d attachment column(s): %s", len(attachment_cols), attachment_cols)

    return df, attachment_cols


# ---------------------------------------------------------------------------
# Data dictionary
# ---------------------------------------------------------------------------

def build_data_dictionary(
    gdf: gpd.GeoDataFrame,
    attachment_cols: list,
    format_name: str,
    source_path: str,
) -> list:
    """Build a data dictionary describing every column."""
    dictionary = []
    for col in gdf.columns:
        if col == "geometry":
            entry = {
                "column": col,
                "type": "geometry",
                "description": "Point geometry (WGS84 / EPSG:4326)",
            }
        else:
            series = gdf[col]
            entry = {
                "column": col,
                "dtype": str(series.dtype),
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
                "unique_values": int(series.nunique()),
                "is_attachment": col in attachment_cols,
            }
            if series.dtype in [np.float64, np.int64]:
                entry["min"] = float(series.min()) if series.notna().any() else None
                entry["max"] = float(series.max()) if series.notna().any() else None
                entry["mean"] = float(series.mean()) if series.notna().any() else None
            elif series.dtype == object:
                top_vals = series.value_counts().head(5).to_dict()
                entry["top_values"] = {str(k): int(v) for k, v in top_vals.items()}

        dictionary.append(entry)

    return dictionary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest ODK/KoboToolbox field survey exports into the GIS pipeline."
    )
    parser.add_argument("--input", required=True, help="CSV or XLS/XLSX survey export.")
    parser.add_argument(
        "--lat-col", default=None,
        help="Latitude column name. Auto-detected if not provided."
    )
    parser.add_argument(
        "--lon-col", default=None,
        help="Longitude column name. Auto-detected if not provided."
    )
    parser.add_argument("--output", required=True, help="Output GeoPackage path (.gpkg).")
    parser.add_argument(
        "--deduplicate", action="store_true",
        help="Flag likely duplicate submissions (same UUID or identical lat/lon/timestamp)."
    )
    args = parser.parse_args()

    started_at = datetime.utcnow().isoformat() + "Z"
    processing_log = {
        "started_at": started_at,
        "input": args.input,
        "output": args.output,
        "steps": [],
    }
    steps = processing_log["steps"]

    # --- Load ---
    logger.info("Loading: %s", args.input)
    df = load_file(args.input)
    steps.append({"step": "load", "rows": len(df), "columns": len(df.columns)})
    logger.info("Loaded %d rows × %d columns", len(df), len(df.columns))

    # --- Detect format ---
    if args.lat_col and args.lon_col:
        fmt = "manual"
        lat_col = args.lat_col
        lon_col = args.lon_col
        acc_col = None
        logger.info("Using manual lat/lon columns: %s / %s", lat_col, lon_col)
    else:
        fmt, lat_col, lon_col, acc_col = detect_format(df)
        if not lat_col:
            logger.error(
                "Could not auto-detect lat/lon columns. "
                "Specify --lat-col and --lon-col explicitly.\n"
                "Available columns: %s",
                list(df.columns[:20])
            )
            sys.exit(1)
        logger.info("Detected format: %s (lat=%s, lon=%s)", fmt, lat_col, lon_col)

    steps.append({
        "step": "detect_format",
        "format": fmt,
        "lat_col": lat_col,
        "lon_col": lon_col,
        "acc_col": acc_col,
    })

    # --- GPS accuracy flagging ---
    df["low_accuracy"] = False
    if acc_col and acc_col in df.columns:
        acc_numeric = pd.to_numeric(df[acc_col], errors="coerce")
        low_acc_mask = acc_numeric > GPS_ACCURACY_THRESHOLD
        df["low_accuracy"] = low_acc_mask
        df["gps_accuracy_m"] = acc_numeric
        n_low = int(low_acc_mask.sum())
        steps.append({
            "step": "gps_accuracy_flag",
            "threshold_m": GPS_ACCURACY_THRESHOLD,
            "flagged_count": n_low,
        })
        if n_low > 0:
            logger.warning(
                "%d points flagged as low accuracy (>%dm)", n_low, GPS_ACCURACY_THRESHOLD
            )

    # --- Deduplicate ---
    if args.deduplicate:
        initial = len(df)
        dup_col = None

        # KoboToolbox uses _uuid, ODK uses instanceID
        for candidate in ["_uuid", "instanceID", "meta/instanceID", "KEY"]:
            if candidate in df.columns:
                dup_col = candidate
                break

        if dup_col:
            df["is_duplicate"] = df.duplicated(subset=[dup_col], keep="first")
        else:
            # Fall back to lat/lon + first non-GPS column as fingerprint
            fp_cols = [lat_col, lon_col]
            ts_candidates = ["_submission_time", "SubmissionDate", "end", "today"]
            fp_cols += [c for c in ts_candidates if c in df.columns][:1]
            df["is_duplicate"] = df.duplicated(subset=fp_cols, keep="first")

        n_dup = int(df["is_duplicate"].sum())
        steps.append({
            "step": "deduplicate",
            "method": f"uuid:{dup_col}" if dup_col else "lat/lon/timestamp",
            "duplicates_flagged": n_dup,
        })
        logger.info("%d duplicate submissions flagged (kept, marked is_duplicate=True)", n_dup)

    # --- Repeat groups ---
    df, repeat_df = extract_repeat_groups(df, steps)

    # --- Multiple-choice expansion ---
    df = expand_multiple_choice(df, steps)

    # --- Attachment documentation ---
    df, attachment_cols = document_attachments(df, steps)

    # --- Build geometry ---
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

    missing_coords = df[lat_col].isna() | df[lon_col].isna()
    n_missing = int(missing_coords.sum())
    if n_missing > 0:
        logger.warning("%d rows missing coordinates — excluded from GeoPackage", n_missing)
        steps.append({"step": "drop_missing_coords", "count": n_missing})
        df = df[~missing_coords].copy()

    geometry = [Point(lon, lat) for lon, lat in zip(df[lon_col], df[lat_col])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    steps.append({
        "step": "build_geometry",
        "feature_count": len(gdf),
        "crs": "EPSG:4326",
    })
    logger.info("Built GeoDataFrame: %d point features", len(gdf))

    # --- Write main GeoPackage ---
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(str(output_path), driver="GPKG", layer="survey")
    steps.append({"step": "write_gpkg", "path": str(output_path), "layer": "survey"})
    logger.info("Wrote main GeoPackage: %s", output_path)

    # --- Write repeat groups GeoPackage ---
    if repeat_df is not None and len(repeat_df) > 0:
        repeat_path = output_path.with_name(output_path.stem + "_repeats.gpkg")
        repeat_df.to_file(str(repeat_path), driver="GPKG", layer="repeats")
        steps.append({
            "step": "write_repeats_gpkg",
            "path": str(repeat_path),
            "rows": len(repeat_df),
        })
        logger.info("Wrote repeat groups GeoPackage: %s", repeat_path)

    # --- Write data dictionary ---
    dictionary = build_data_dictionary(gdf, attachment_cols, fmt, args.input)
    dict_path = output_path.with_name(output_path.stem + "_dictionary.json")
    dict_path.write_text(json.dumps(dictionary, indent=2, default=str))
    steps.append({"step": "write_dictionary", "path": str(dict_path), "columns": len(dictionary)})
    logger.info("Wrote data dictionary: %s", dict_path)

    # --- Write processing log ---
    processing_log["finished_at"] = datetime.utcnow().isoformat() + "Z"
    processing_log["summary"] = {
        "input_rows": int(df.__len__() + n_missing),
        "output_features": len(gdf),
        "missing_coords_dropped": n_missing,
        "low_accuracy_flagged": int(df.get("low_accuracy", pd.Series(False)).sum()),
        "duplicates_flagged": int(df.get("is_duplicate", pd.Series(False)).sum()),
        "attachment_columns": len(attachment_cols),
        "format_detected": fmt,
    }
    log_path = output_path.with_name(output_path.stem + "_log.json")
    log_path.write_text(json.dumps(processing_log, indent=2, default=str))
    logger.info("Wrote processing log: %s", log_path)

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"  Field Survey Ingest Complete")
    print(f"  Format:   {fmt}")
    print(f"  Features: {len(gdf)}")
    print(f"  Output:   {output_path}")
    if repeat_df is not None:
        print(f"  Repeats:  {output_path.with_name(output_path.stem + '_repeats.gpkg')}")
    print(f"  Dict:     {dict_path}")
    print(f"  Log:      {log_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
