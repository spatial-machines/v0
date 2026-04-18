#!/usr/bin/env python3
"""Render rich, multi-layer interactive Folium web maps from GeoPackages.

Produces a self-contained HTML file with:
  - Multiple toggleable choropleth layers with independent legends
  - Multiple point overlay layers with styled markers
  - Smart popups with auto-formatted numbers ($, %, commas)
  - Geocoder search, measure/draw tools, minimap, fullscreen
  - Multiple basemap options with layer control
  - Professional title and stats panels

Usage:
    # Single-layer (backwards compatible):
    python render_web_map.py \\
        --input data/processed/tracts.gpkg \\
        --choropleth-col poverty_rate \\
        --title "Poverty by Census Tract"

    # Multi-layer:
    python render_web_map.py \\
        --input data/processed/tracts.gpkg \\
        --layers 'poverty_rate:YlOrRd:Poverty Rate' \\
                 'uninsured_rate:Blues:Uninsured Rate' \\
                 'median_income:Greens:Median Income' \\
        --title "Health & Income Indicators"

    # With point overlays:
    python render_web_map.py \\
        --input data/processed/tracts.gpkg \\
        --layers 'poverty_rate:YlOrRd:Poverty Rate' \\
        --point-layers 'hospitals.gpkg:name:Hospitals:#e74c3c:8' \\
                       'schools.gpkg:name:Schools:#3498db:6' \\
        --title "Community Resources"
"""
import argparse
import json
import re
import sys
from pathlib import Path

import branca.colormap as cm
import folium
import folium.plugins as plugins
import geopandas as gpd
import matplotlib
import matplotlib.colors
import numpy as np
import pandas as pd
from folium.plugins import Draw, Fullscreen, Geocoder, MeasureControl, MiniMap

PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def classify(values, scheme, k):
    """Return (bin_edges, classifier) using mapclassify."""
    import mapclassify
    clean = values.dropna()
    if len(clean) == 0:
        return None, None
    k = min(k, len(clean.unique()))
    if k < 2:
        return None, None

    classifiers = {
        "quantiles": mapclassify.Quantiles,
        "equal_interval": mapclassify.EqualInterval,
        "natural_breaks": mapclassify.NaturalBreaks,
    }
    Clf = classifiers.get(scheme, mapclassify.Quantiles)
    clf = Clf(clean, k=k)
    bins = [clean.min()] + list(clf.bins)
    return bins, clf


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

# Patterns for auto-detecting column formatting
_RATE_PATTERNS = re.compile(r"(pct|rate|percent|proportion|lowincpct|peopcolorpct)", re.I)
_DOLLAR_PATTERNS = re.compile(r"(income|rent|cost|wage|salary|earning|price|value)", re.I)
_CENSUS_CODE = re.compile(r"^[A-Z]\d{5}[_E]\d+E?$")  # e.g. B17001_001E

# Column name aliases for cleaned display
_COLUMN_ALIASES = {
    "PM25": "PM 2.5",
    "LOWINCPCT": "Low Income %",
    "PEOPCOLORPCT": "People of Color %",
    "DEMOGIDX_2": "Demographic Index",
    "high_bp_rate": "High Blood Pressure Rate",
    "hpsa_mean_score": "HPSA Mean Score",
}


def clean_column_name(col):
    """Convert column name to human-readable label."""
    if col in _COLUMN_ALIASES:
        return _COLUMN_ALIASES[col]
    # Strip Census variable codes
    if _CENSUS_CODE.match(col):
        return col  # Leave raw codes as-is if no alias
    # snake_case -> Title Case
    return col.replace("_", " ").title()


def detect_format_type(col_name):
    """Auto-detect how to format values for a column."""
    if _RATE_PATTERNS.search(col_name):
        return "percent"
    if _DOLLAR_PATTERNS.search(col_name):
        return "dollar"
    return "number"


def format_value(v, col_name=""):
    """Format a value based on column name heuristics."""
    if pd.isna(v):
        return '<span style="color:#999">N/A</span>'
    fmt_type = detect_format_type(col_name)
    if isinstance(v, (int, np.integer)):
        if fmt_type == "dollar":
            return f"${v:,}"
        return f"{v:,}"
    if isinstance(v, (float, np.floating)):
        if fmt_type == "percent":
            return f"{v:.2f}%"
        if fmt_type == "dollar":
            if v >= 1:
                return f"${v:,.0f}"
            return f"${v:,.2f}"
        if np.isfinite(v) and v == int(v) and abs(v) < 1e12:
            return f"{int(v):,}"
        return f"{v:,.2f}"
    return str(v)


def format_legend_value(v, col_name=""):
    """Shorter format for legend labels."""
    if pd.isna(v):
        return "N/A"
    fmt_type = detect_format_type(col_name)
    if isinstance(v, (float, np.floating)):
        if fmt_type == "dollar":
            if abs(v) >= 1_000_000:
                return f"${v / 1_000_000:.1f}M"
            if abs(v) >= 1_000:
                return f"${v / 1_000:.1f}K"
            return f"${v:,.0f}"
        if fmt_type == "percent":
            return f"{v:.1f}%"
        if v == int(v) and abs(v) < 1e9:
            return f"{int(v):,}"
        return f"{v:,.1f}"
    if isinstance(v, (int, np.integer)):
        if fmt_type == "dollar":
            if abs(v) >= 1_000_000:
                return f"${v / 1_000_000:.1f}M"
            if abs(v) >= 1_000:
                return f"${v / 1_000:.1f}K"
            return f"${v:,}"
        return f"{v:,}"
    return str(v)


# ---------------------------------------------------------------------------
# Layer spec parsers
# ---------------------------------------------------------------------------

def parse_layer_spec(spec):
    """Parse 'column:colormap:label' into dict."""
    parts = spec.split(":")
    if len(parts) < 1:
        raise ValueError(f"Invalid layer spec: {spec}")
    col = parts[0]
    cmap = parts[1] if len(parts) > 1 else "YlOrRd"
    label = parts[2] if len(parts) > 2 else clean_column_name(col)
    return {"column": col, "cmap": cmap, "label": label}


def parse_point_layer_spec(spec):
    """Parse 'file:name_col:label:color:radius' into dict."""
    parts = spec.split(":")
    if len(parts) < 1:
        raise ValueError(f"Invalid point layer spec: {spec}")
    return {
        "file": parts[0],
        "name_col": parts[1] if len(parts) > 1 else None,
        "label": parts[2] if len(parts) > 2 else Path(parts[0]).stem.title(),
        "color": parts[3] if len(parts) > 3 else "#e74c3c",
        "radius": int(parts[4]) if len(parts) > 4 else 6,
    }


# ---------------------------------------------------------------------------
# Legend builder
# ---------------------------------------------------------------------------

def build_legend_html(layer_id, label, bins, hex_colors, col_name):
    """Build an HTML legend div for a choropleth layer."""
    items = ""
    for i, color in enumerate(hex_colors):
        lo = format_legend_value(bins[i], col_name)
        hi = format_legend_value(bins[i + 1], col_name)
        items += f"""
        <div style="display:flex;align-items:center;margin:2px 0">
            <span style="width:18px;height:14px;background:{color};
                         display:inline-block;border-radius:2px;
                         margin-right:6px;flex-shrink:0"></span>
            <span>{lo} &ndash; {hi}</span>
        </div>"""

    return f"""
    <div id="legend-{layer_id}" class="map-legend" style="
        position:fixed; bottom:45px; right:12px; z-index:9998;
        background:rgba(255,255,255,0.95); padding:10px 14px;
        border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,0.2);
        font-family:'Helvetica Neue',Arial,sans-serif; font-size:11px;
        color:#333; max-height:280px; overflow-y:auto;
        min-width:140px; display:none;
    ">
        <div style="font-weight:700;font-size:12px;margin-bottom:6px;
                     border-bottom:1px solid #eee;padding-bottom:4px">
            {label}
        </div>
        {items}
    </div>"""


# ---------------------------------------------------------------------------
# Popup builder
# ---------------------------------------------------------------------------

def build_popup_html(row, popup_cols):
    """Build styled popup HTML for a feature."""
    rows_html = ""
    for col in popup_cols:
        if col not in row or col == "geometry":
            continue
        label = clean_column_name(col)
        val = format_value(row[col], col)
        rows_html += f"""<tr>
            <td style="padding:3px 10px 3px 0;color:#777;font-size:11px;
                       white-space:nowrap;vertical-align:top">{label}</td>
            <td style="padding:3px 0;font-weight:600;font-size:12px">{val}</td>
        </tr>"""
    return f"""<div style="font-family:'Helvetica Neue',Arial,sans-serif;
                           min-width:200px;max-width:320px">
        <table style="border-collapse:collapse;width:100%">{rows_html}</table>
    </div>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Input/output
    parser.add_argument("--input", required=True,
                        help="Input GeoPackage or shapefile")
    parser.add_argument("-o", "--output",
                        help="Output HTML path (default: outputs/web/<stem>.html)")

    # Single-layer (backwards compat)
    parser.add_argument("--choropleth-col",
                        help="Numeric column for single choropleth (backwards compat)")
    parser.add_argument("--cmap", default="YlOrRd",
                        help="Colormap for single-layer mode (default: YlOrRd)")

    # Multi-layer choropleths
    parser.add_argument("--layers", nargs="+",
                        help="Layer specs: 'column:colormap:label' (multiple allowed)")

    # Popup/tooltip
    parser.add_argument("--popup-cols", nargs="+",
                        help="Columns to show in popup (default: all numeric + name cols)")
    parser.add_argument("--tooltip-col",
                        help="Column to show on hover tooltip")

    # Styling
    parser.add_argument("--title", help="Map title")
    parser.add_argument("--scheme", default="quantiles",
                        choices=["quantiles", "equal_interval", "natural_breaks"],
                        help="Classification scheme (default: quantiles)")
    parser.add_argument("--k", type=int, default=5,
                        help="Number of classes (default: 5)")
    parser.add_argument("--missing-color", default="#d0d0d0",
                        help="Color for null/missing values (default: #d0d0d0)")
    parser.add_argument("--fill-opacity", type=float, default=0.70)
    parser.add_argument("--line-opacity", type=float, default=0.4)
    parser.add_argument("--line-weight", type=float, default=0.5)

    # Single point layer (backwards compat)
    parser.add_argument("--points",
                        help="Optional points file to overlay (backwards compat)")
    parser.add_argument("--points-lat", default="latitude")
    parser.add_argument("--points-lon", default="longitude")
    parser.add_argument("--points-name-col",
                        help="Column for point popup label")
    parser.add_argument("--points-label", default="Points",
                        help="Layer name for points")
    parser.add_argument("--points-color", default="#1a1a1a",
                        help="Point marker color")
    parser.add_argument("--points-radius", type=int, default=6,
                        help="Point circle radius px")

    # Multi point layers
    parser.add_argument("--point-layers", nargs="+",
                        help="Point layer specs: 'file:name_col:label:color:radius'")

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load polygon data
    # ------------------------------------------------------------------
    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        return 1

    gdf = gpd.read_file(src)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf = gdf.to_crs("EPSG:4326")
    gdf["geometry"] = gdf["geometry"].buffer(0)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    print(f"Loaded {len(gdf)} features from {src.name}")

    # ------------------------------------------------------------------
    # Resolve layer specs
    # ------------------------------------------------------------------
    layer_specs = []
    if args.layers:
        for spec_str in args.layers:
            layer_specs.append(parse_layer_spec(spec_str))
    elif args.choropleth_col:
        # Backwards compat: single layer from --choropleth-col
        layer_specs.append({
            "column": args.choropleth_col,
            "cmap": args.cmap,
            "label": clean_column_name(args.choropleth_col),
        })

    # Validate columns exist
    for spec in layer_specs:
        if spec["column"] not in gdf.columns:
            print(f"Warning: column '{spec['column']}' not found in {src.name}. "
                  f"Available: {[c for c in gdf.columns if c != 'geometry']}",
                  file=sys.stderr)
            layer_specs.remove(spec)

    # ------------------------------------------------------------------
    # Resolve point layer specs
    # ------------------------------------------------------------------
    point_specs = []
    if args.point_layers:
        for spec_str in args.point_layers:
            point_specs.append(parse_point_layer_spec(spec_str))
    if args.points:
        # Backwards compat: single point layer
        point_specs.append({
            "file": args.points,
            "name_col": args.points_name_col,
            "label": args.points_label,
            "color": args.points_color,
            "radius": args.points_radius,
        })

    # ------------------------------------------------------------------
    # Output path
    # ------------------------------------------------------------------
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "web"
        stem = src.stem
        if layer_specs:
            stem += f"_{layer_specs[0]['column']}"
        out_path = out_dir / f"{stem}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Popup columns
    # ------------------------------------------------------------------
    all_cols = [c for c in gdf.columns if c != "geometry"]
    if args.popup_cols:
        popup_cols = [c for c in args.popup_cols if c in gdf.columns]
    else:
        # Auto-select: name-like columns first, then numeric columns
        popup_cols = []
        for c in all_cols:
            if c.lower() in ("name", "geoid", "tractce", "namelsad"):
                popup_cols.insert(0, c)
            elif pd.api.types.is_numeric_dtype(gdf[c]):
                popup_cols.append(c)
        if not popup_cols:
            popup_cols = all_cols[:15]

    # ------------------------------------------------------------------
    # Initialize map
    # ------------------------------------------------------------------
    bounds = gdf.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    m = folium.Map(
        location=center,
        zoom_start=10,
        tiles=None,
        prefer_canvas=True,
    )

    # Basemaps
    folium.TileLayer("CartoDB positron", name="Light (CartoDB)",
                     control=True).add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark (CartoDB)",
                     control=True).add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap",
                     control=True).add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite (Esri)", control=True,
    ).add_to(m)

    # ------------------------------------------------------------------
    # Build choropleth layers
    # ------------------------------------------------------------------
    legend_html_parts = []
    layer_meta = []  # for stats panel JS

    for idx, spec in enumerate(layer_specs):
        col = spec["column"]
        cmap_name = spec["cmap"]
        label = spec["label"]
        layer_id = f"layer_{idx}"
        show = (idx == 0)  # only first layer visible by default

        col_data = pd.to_numeric(gdf[col], errors="coerce")
        bins, clf = classify(col_data, args.scheme, args.k)

        if not bins:
            print(f"Warning: could not classify '{col}' - skipping layer",
                  file=sys.stderr)
            continue

        # Build color ramp
        mpl_cmap = matplotlib.colormaps.get_cmap(cmap_name)
        n = len(bins) - 1
        hex_colors = [
            matplotlib.colors.to_hex(mpl_cmap(i / max(n - 1, 1)))
            for i in range(n)
        ]

        # Branca colormap (for internal color lookups)
        colormap = cm.StepColormap(
            hex_colors, vmin=bins[0], vmax=bins[-1],
            index=bins, caption=label,
        )

        # Build legend HTML
        legend_html_parts.append(
            build_legend_html(layer_id, label, bins, hex_colors, col)
        )

        missing_color = args.missing_color

        def make_style_fn(colormap_ref, col_ref, missing_ref, opacity, lw, lo):
            def style_fn(feature):
                try:
                    val = feature["properties"].get(col_ref)
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        fill = missing_ref
                    else:
                        fill = colormap_ref(float(val))
                except (TypeError, ValueError):
                    fill = missing_ref
                return {
                    "fillColor": fill,
                    "fillOpacity": opacity,
                    "color": "#555",
                    "weight": lw,
                    "opacity": lo,
                }
            return style_fn

        def make_highlight_fn(opacity):
            def highlight_fn(feature):
                return {
                    "weight": 2.5,
                    "color": "#222",
                    "fillOpacity": min(opacity + 0.15, 1.0),
                }
            return highlight_fn

        style_fn = make_style_fn(
            colormap, col, missing_color,
            args.fill_opacity, args.line_weight, args.line_opacity,
        )
        highlight_fn = make_highlight_fn(args.fill_opacity)

        # Tooltip field
        tt_field = args.tooltip_col if args.tooltip_col else col
        tt_alias = clean_column_name(tt_field)

        geojson_layer = folium.GeoJson(
            gdf.__geo_interface__,
            name=label,
            style_function=style_fn,
            highlight_function=highlight_fn,
            show=show,
            tooltip=folium.GeoJsonTooltip(
                fields=[tt_field],
                aliases=[tt_alias + ":"],
                style=("background-color:rgba(255,255,255,0.95);"
                       "border:1px solid #ccc;padding:4px 10px;"
                       "font-size:12px;font-family:'Helvetica Neue',Arial,sans-serif;"
                       "border-radius:3px;box-shadow:0 1px 3px rgba(0,0,0,0.15)"),
            ),
            popup=folium.GeoJsonPopup(
                fields=popup_cols,
                aliases=[clean_column_name(c) for c in popup_cols],
                style=("font-family:'Helvetica Neue',Arial,sans-serif;"
                       "font-size:12px"),
                max_width=360,
            ),
        )
        geojson_layer.add_to(m)

        # Track valid count
        valid_count = int(col_data.notna().sum())
        layer_meta.append({
            "id": layer_id,
            "label": label,
            "column": col,
            "count": len(gdf),
            "valid": valid_count,
            "min": float(col_data.min()) if valid_count > 0 else None,
            "max": float(col_data.max()) if valid_count > 0 else None,
            "show": show,
        })

        print(f"  Layer '{label}' ({col}): {valid_count} valid / {len(gdf)} features")

    # If no layer specs, add a plain polygon layer
    if not layer_specs:
        layer_name = args.title or src.stem.replace("_", " ").title()

        def plain_style(feature):
            return {
                "fillColor": "#3388ff",
                "fillOpacity": args.fill_opacity,
                "color": "#555",
                "weight": args.line_weight,
                "opacity": args.line_opacity,
            }

        folium.GeoJson(
            gdf.__geo_interface__,
            name=layer_name,
            style_function=plain_style,
            highlight_function=lambda f: {"weight": 2.5, "color": "#222"},
            popup=folium.GeoJsonPopup(
                fields=popup_cols[:10],
                aliases=[clean_column_name(c) for c in popup_cols[:10]],
                max_width=360,
            ),
        ).add_to(m)

    # ------------------------------------------------------------------
    # Point overlays
    # ------------------------------------------------------------------
    for pt_spec in point_specs:
        pts_path = Path(pt_spec["file"]).expanduser().resolve()
        if not pts_path.exists():
            # Try relative to input directory
            pts_path = src.parent / pt_spec["file"]
        if not pts_path.exists():
            print(f"Warning: point file not found: {pt_spec['file']}",
                  file=sys.stderr)
            continue

        if pts_path.suffix.lower() == ".csv":
            pts_df = pd.read_csv(pts_path)
            pts_gdf = gpd.GeoDataFrame(
                pts_df,
                geometry=gpd.points_from_xy(
                    pts_df.get(args.points_lon, pts_df.columns[0]),
                    pts_df.get(args.points_lat, pts_df.columns[0]),
                ),
                crs="EPSG:4326",
            )
        else:
            pts_gdf = gpd.read_file(pts_path).to_crs("EPSG:4326")

        color = pt_spec["color"]
        radius = pt_spec["radius"]
        name_col = pt_spec["name_col"]
        label = pt_spec["label"]

        pts_fg = folium.FeatureGroup(name=label)
        count = 0
        for _, pt_row in pts_gdf.iterrows():
            if pt_row.geometry is None or pt_row.geometry.is_empty:
                continue
            # Build point popup
            popup_text = ""
            if name_col and name_col in pt_row.index:
                popup_text = f"<b>{pt_row[name_col]}</b>"
            # Add other attributes
            extra_cols = [c for c in pts_gdf.columns
                          if c not in ("geometry", name_col) and pd.notna(pt_row.get(c))]
            if extra_cols:
                rows = "".join(
                    f"<tr><td style='padding:2px 6px;color:#777;font-size:11px'>"
                    f"{clean_column_name(c)}</td>"
                    f"<td style='padding:2px 6px;font-size:11px'>"
                    f"{format_value(pt_row[c], c)}</td></tr>"
                    for c in extra_cols[:8]
                )
                popup_text += f"<table style='margin-top:4px'>{rows}</table>"

            folium.CircleMarker(
                location=[pt_row.geometry.y, pt_row.geometry.x],
                radius=radius,
                color=color,
                weight=2,
                fill=True,
                fill_color="white",
                fill_opacity=0.9,
                popup=folium.Popup(
                    f"<div style='font-family:\"Helvetica Neue\",Arial,sans-serif;"
                    f"min-width:160px'>{popup_text}</div>",
                    max_width=280,
                ) if popup_text else None,
                tooltip=pt_row[name_col] if name_col and name_col in pt_row.index else None,
            ).add_to(pts_fg)
            count += 1

        pts_fg.add_to(m)
        print(f"  Points '{label}': {count} features from {pts_path.name}")

    # ------------------------------------------------------------------
    # Plugins
    # ------------------------------------------------------------------
    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright", width=120, height=120).add_to(m)
    folium.plugins.MousePosition(
        position="bottomleft", separator=" | ",
        prefix="Lat/Lon:", num_digits=5,
    ).add_to(m)
    Geocoder(position="topleft", collapsed=True,
             placeholder="Search location...").add_to(m)
    MeasureControl(
        position="bottomleft",
        primary_length_unit="miles",
        secondary_length_unit="kilometers",
        primary_area_unit="acres",
        secondary_area_unit="sqmeters",
    ).add_to(m)
    Draw(
        position="topleft",
        draw_options={"polyline": True, "polygon": True,
                      "circle": True, "marker": True,
                      "circlemarker": False, "rectangle": True},
        edit_options={"edit": True, "remove": True},
    ).add_to(m)

    # ------------------------------------------------------------------
    # Title panel
    # ------------------------------------------------------------------
    title = args.title or (layer_specs[0]["label"] if layer_specs
                           else src.stem.replace("_", " ").title())
    subtitle_parts = []
    if layer_specs:
        subtitle_parts = [s["label"] for s in layer_specs]

    subtitle_html = ""
    if len(subtitle_parts) > 1:
        tags = " ".join(
            f'<span style="display:inline-block;background:#f0f0f0;'
            f'padding:1px 7px;border-radius:10px;margin:1px 2px;'
            f'font-size:10px;color:#555">{s}</span>'
            for s in subtitle_parts
        )
        subtitle_html = f'<div style="margin-top:4px">{tags}</div>'

    title_html = f"""
    <div style="
        position:fixed; top:12px; left:55px; z-index:9999;
        background:rgba(255,255,255,0.95); padding:10px 16px;
        border-radius:6px; box-shadow:0 2px 10px rgba(0,0,0,0.2);
        font-family:'Helvetica Neue',Arial,sans-serif;
        max-width:420px; backdrop-filter:blur(4px);
    ">
        <div style="font-size:15px;font-weight:700;color:#1a1a1a;
                     letter-spacing:-0.2px">{title}</div>
        {subtitle_html}
        <div style="font-size:10px;color:#999;margin-top:3px">
            {len(gdf):,} census tracts &middot; {len(layer_specs)} layer{'s' if len(layer_specs) != 1 else ''}
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # ------------------------------------------------------------------
    # Stats panel
    # ------------------------------------------------------------------
    stats_rows = ""
    for lm in layer_meta:
        fmt_min = format_legend_value(lm["min"], lm["column"]) if lm["min"] is not None else "N/A"
        fmt_max = format_legend_value(lm["max"], lm["column"]) if lm["max"] is not None else "N/A"
        vis = "inline" if lm["show"] else "none"
        stats_rows += f"""
        <div class="stat-row" data-layer="{lm['id']}" style="display:{vis};margin-bottom:4px">
            <div style="font-weight:600;font-size:11px;color:#333">{lm['label']}</div>
            <div style="font-size:10px;color:#777">
                Range: {fmt_min} &ndash; {fmt_max}
                &middot; {lm['valid']:,} valid
            </div>
        </div>"""

    stats_html = f"""
    <div id="stats-panel" style="
        position:fixed; bottom:40px; left:12px; z-index:9999;
        background:rgba(255,255,255,0.93); padding:8px 14px;
        border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,0.15);
        font-family:'Helvetica Neue',Arial,sans-serif;
        font-size:11px; color:#444; max-width:260px;
        backdrop-filter:blur(4px);
    ">
        <div style="font-weight:700;font-size:11px;margin-bottom:4px;
                     color:#222;border-bottom:1px solid #eee;padding-bottom:3px">
            Layer Statistics
        </div>
        {stats_rows}
    </div>
    """
    m.get_root().html.add_child(folium.Element(stats_html))

    # ------------------------------------------------------------------
    # Legends
    # ------------------------------------------------------------------
    for legend_html in legend_html_parts:
        m.get_root().html.add_child(folium.Element(legend_html))

    # ------------------------------------------------------------------
    # JavaScript: sync legend visibility with layer toggles
    # ------------------------------------------------------------------
    if layer_meta:
        layer_js_map = json.dumps({
            lm["label"]: lm["id"] for lm in layer_meta
        })
        sync_js = f"""
        <script>
        (function() {{
            var layerMap = {layer_js_map};
            // Show initial legend
            var firstId = Object.values(layerMap)[0];
            var firstLeg = document.getElementById('legend-' + firstId);
            if (firstLeg) firstLeg.style.display = 'block';

            // Watch for layer toggle changes via MutationObserver on the layer control
            function syncLegends() {{
                var inputs = document.querySelectorAll(
                    '.leaflet-control-layers-overlays label');
                inputs.forEach(function(label) {{
                    var input = label.querySelector('input');
                    var text = label.textContent.trim();
                    if (layerMap[text] !== undefined) {{
                        var legEl = document.getElementById(
                            'legend-' + layerMap[text]);
                        var statEl = document.querySelector(
                            '[data-layer="' + layerMap[text] + '"]');
                        if (legEl) {{
                            legEl.style.display = input.checked ? 'block' : 'none';
                        }}
                        if (statEl) {{
                            statEl.style.display = input.checked ? 'block' : 'none';
                        }}
                    }}
                }});
            }}

            // Poll briefly until layer control is rendered, then attach listeners
            var attempts = 0;
            var poller = setInterval(function() {{
                var inputs = document.querySelectorAll(
                    '.leaflet-control-layers-overlays input');
                if (inputs.length > 0 || attempts > 50) {{
                    clearInterval(poller);
                    inputs.forEach(function(input) {{
                        input.addEventListener('change', syncLegends);
                    }});
                    syncLegends();
                }}
                attempts++;
            }}, 100);
        }})();
        </script>
        """
        m.get_root().html.add_child(folium.Element(sync_js))

    # ------------------------------------------------------------------
    # Layer control
    # ------------------------------------------------------------------
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # Fit bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    m.save(str(out_path))
    size_kb = out_path.stat().st_size / 1024
    print(f"Saved web map: {out_path} ({size_kb:.0f} KB)")

    # ------------------------------------------------------------------
    # Handoff log
    # ------------------------------------------------------------------
    log = {
        "step": "render_web_map",
        "source": str(src),
        "output": str(out_path),
        "layers": [s["column"] for s in layer_specs] if layer_specs else None,
        "choropleth_col": layer_specs[0]["column"] if layer_specs else None,
        "scheme": args.scheme,
        "k": args.k,
        "features": len(gdf),
        "point_layers": [s["label"] for s in point_specs] if point_specs else None,
        "has_points": len(point_specs) > 0,
        "output_size_kb": round(size_kb, 1),
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
