#!/usr/bin/env python3
"""Generate a delivery-quality choropleth map from a spatial dataset.

Produces styled thematic choropleth maps following the firm's cartography
standard. Integrates with the map style registry for palette selection,
writes a style sidecar for QGIS inheritance, and supports label halos,
inset locator maps, and pattern fills for accessibility.

Usage:
    python scripts/core/analyze_choropleth.py data/processed/tracts.gpkg poverty_rate \
        -o outputs/maps/poverty_choropleth.png

    python scripts/core/analyze_choropleth.py data/processed/tracts.gpkg median_income \
        --title "Median Household Income, Douglas County, NE (2022)" \
        --attribution "U.S. Census Bureau ACS 5-Year Estimates, 2022" \
        --basemap light --labels -o outputs/maps/income_choropleth.png

To add inset locators, water features, place labels, or top-N annotations,
use the composable layer scripts in scripts/core/layers/ after generating
the base choropleth with this script.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, Patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_CORE))

from style_utils import resolve_palette, get_rgb_ramp, is_percent_field, load_styles
from write_style_sidecar import write_style_sidecar


def _font_chain(family_str: str) -> list[str]:
    """Parse a comma-separated font fallback chain into a list for matplotlib."""
    if not family_str:
        return ["sans-serif"]
    return [f.strip().strip('"').strip("'") for f in family_str.split(",") if f.strip()]


def _detect_fips(gdf) -> tuple[str | None, str | None]:
    """Pull state and county FIPS from data columns if present."""
    state = county = None
    for col in ["STATEFP", "statefp", "STATE"]:
        if col in gdf.columns:
            state = str(gdf[col].iloc[0]).zfill(2)
            break
    for col in ["COUNTYFP", "countyfp", "COUNTY"]:
        if col in gdf.columns:
            county = str(gdf[col].iloc[0]).zfill(3)
            break
    return state, county


def _pick_legend_position(ax, gdf, field: str) -> str:
    """Choose the emptiest corner for legend placement based on data density.

    Divides the map bbox into four quadrants and counts how many features'
    centroids fall in each. The quadrant with the fewest features wins.
    """
    try:
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        xmid = (xmin + xmax) / 2
        ymid = (ymin + ymax) / 2

        # Only consider features that have data
        valid = gdf.dropna(subset=[field])
        if valid.empty:
            return "lower right"

        # Compute density per quadrant weighted by feature value (darker = more weight)
        counts = {"upper-left": 0, "upper-right": 0,
                  "lower-left": 0, "lower-right": 0}
        for geom in valid.geometry:
            pt = geom.representative_point()
            if pt.x < xmid and pt.y >= ymid:
                counts["upper-left"] += 1
            elif pt.x >= xmid and pt.y >= ymid:
                counts["upper-right"] += 1
            elif pt.x < xmid and pt.y < ymid:
                counts["lower-left"] += 1
            else:
                counts["lower-right"] += 1

        # Pick the emptiest quadrant
        emptiest = min(counts, key=counts.get)
        # Convert to matplotlib loc
        loc_map = {
            "upper-left": "upper left",
            "upper-right": "upper right",
            "lower-left": "lower left",
            "lower-right": "lower right",
        }
        return loc_map[emptiest]
    except Exception:
        return "lower right"


def _format_val(v: float, precision: int | None = None) -> str:
    """Format a numeric value for legend labels with smart rounding."""
    if precision is not None:
        if precision == 0:
            return f"{int(round(v)):,}" if abs(v) >= 1000 else f"{v:.0f}"
        return f"{v:.{precision}f}"
    abs_v = abs(v)
    if abs_v >= 1000:
        return f"{int(round(v)):,}"
    elif abs_v >= 10:
        return f"{v:.0f}"
    elif abs_v >= 1:
        return f"{v:.1f}"
    else:
        return f"{v:.2f}"


def _consistent_precision(values: list[float]) -> int:
    """Determine uniform decimal precision for a set of break values."""
    if not values:
        return 0
    if all(abs(v - round(v)) < 0.01 for v in values):
        return 0
    max_prec = 0
    for v in values:
        abs_v = abs(v)
        if abs_v < 1:
            max_prec = max(max_prec, 2)
        elif abs_v < 10:
            max_prec = max(max_prec, 1)
    return max_prec


def _format_legend_labels(ax):
    """Reformat mapclassify bracket notation to clean en-dash labels."""
    legend = ax.get_legend()
    if legend is None:
        return
    all_values = []
    for text in legend.get_texts():
        label = text.get_text()
        try:
            cleaned = re.sub(r'[\[\]\(\)]', '', label)
            parts = cleaned.split(",")
            if len(parts) == 2:
                all_values.extend([float(parts[0].strip()), float(parts[1].strip())])
            elif len(parts) == 4:
                all_values.extend([float(parts[0].strip() + parts[1].strip()),
                                   float(parts[2].strip() + parts[3].strip())])
        except (ValueError, OverflowError):
            pass
    prec = _consistent_precision(all_values)
    for text in legend.get_texts():
        label = text.get_text()
        try:
            cleaned = re.sub(r'[\[\]\(\)]', '', label)
            parts = cleaned.split(",")
            if len(parts) == 2:
                lo, hi = float(parts[0].strip()), float(parts[1].strip())
            elif len(parts) == 4:
                lo = float(parts[0].strip() + parts[1].strip())
                hi = float(parts[2].strip() + parts[3].strip())
            else:
                continue
            text.set_text(f"{_format_val(lo, prec)} \u2013 {_format_val(hi, prec)}")
        except (ValueError, OverflowError):
            pass


def _add_feature_labels(ax, gdf, label_field: str, styles: dict):
    """Add feature labels with halos for readability."""
    label_cfg = styles.get("families", {}).get("thematic_choropleth", {}).get("labels", {})
    font_size = label_cfg.get("font_size", 7.5)
    halo = label_cfg.get("halo", True)
    halo_color = label_cfg.get("halo_color", "#ffffff")
    halo_width = label_cfg.get("halo_width", 2.0)
    font_color = label_cfg.get("color", "#333333")

    path_effects = []
    if halo:
        path_effects = [
            pe.withStroke(linewidth=halo_width, foreground=halo_color),
        ]

    for idx, row in gdf.iterrows():
        label = str(row.get(label_field, ""))
        if not label or label == "None":
            continue
        try:
            centroid = row.geometry.representative_point()
            ax.text(centroid.x, centroid.y, label,
                    fontsize=font_size, ha="center", va="center",
                    color=font_color, fontfamily=_font_chain(label_cfg.get("font_family", "Gill Sans MT, Calibri, sans-serif")),
                    path_effects=path_effects, zorder=15)
        except Exception:
            pass


def _build_legend_title(field: str, legend_title_override: str | None) -> str:
    """Build a human-readable legend title from a field name."""
    if legend_title_override:
        return legend_title_override

    fn = field.lower()
    nice = field.replace("_", " ").title()
    nice = nice.replace("Pct ", "% ").replace(" Pct", "")
    nice = nice.replace("Per Sqkm", "per sq km").replace("Sqkm", "sq km")
    nice = nice.replace("Nh ", "")

    if any(k in fn for k in ("rate", "pct", "percent")):
        return nice if "%" in nice else f"{nice} (%)"
    elif any(k in fn for k in ("income", "rent", "cost", "price", "value")):
        return f"{nice} ($)"
    elif any(k in fn for k in ("pop", "count", "total", "number", "universe")):
        return f"{nice} (count)"
    return nice


def _parse_category_colors(spec: str) -> dict[str, str]:
    """Parse a --category-colors argument as inline JSON or a file path.

    Accepts:
      - inline JSON object: ``'{"Food desert": "#b30000", ...}'``
      - path to a file containing the same JSON object

    Returns an ordered dict (Python 3.7+ dicts preserve insertion order) of
    category -> hex color. Raises ValueError on malformed input.
    """
    spec = spec.strip()
    if not spec:
        raise ValueError("--category-colors is empty")
    if spec.startswith("{") or spec.startswith("["):
        data = json.loads(spec)
    else:
        p = Path(spec).expanduser()
        if not p.exists():
            raise ValueError(
                f"--category-colors: not JSON and file not found: {p}"
            )
        data = json.loads(p.read_text())
    if not isinstance(data, dict):
        raise ValueError(
            "--category-colors must be a JSON object mapping category -> hex color"
        )
    return {str(k): str(v) for k, v in data.items()}


def _render_categorical(gdf, args, src: Path) -> int:
    """Render a thematic_categorical map.

    Mirrors the numeric choropleth's cartographic contract (title,
    dissolved outline, legend, attribution, basemap, sidecar) but draws
    each category as a solid fill from an explicit color mapping.
    """
    warnings_list: list[str] = []
    assumptions: list[str] = []

    # Resolve the category -> color mapping.
    if not args.category_colors:
        print("--categorical requires --category-colors")
        return 2
    try:
        color_map = _parse_category_colors(args.category_colors)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"--category-colors invalid: {exc}")
        return 2

    # Render order — later categories plot on top of earlier ones. Respect
    # caller-supplied order when given; otherwise use color_map insertion order.
    if args.category_order:
        render_order = [c for c in args.category_order if c in color_map]
        missing = [c for c in color_map if c not in render_order]
        render_order.extend(missing)  # paint any leftover colors too
    else:
        render_order = list(color_map.keys())

    # Count each category + flag unknown values.
    unique_vals = set(gdf[args.field].dropna().astype(str).unique())
    known = set(render_order)
    unknown = sorted(unique_vals - known)
    if unknown:
        warnings_list.append(
            f"{len(unknown)} unmapped category value(s) in '{args.field}' "
            f"(shown in missing color): {unknown[:5]}"
            + ("..." if len(unknown) > 5 else "")
        )
    null_count = int(gdf[args.field].isna().sum())
    total = len(gdf)

    # ── Figure sizing (same logic as the numeric branch) ────────────────
    styles = load_styles()
    family_profile = styles.get("families", {}).get("thematic_categorical", {})
    fig_cfg = family_profile.get("figure", {})
    if args.figsize:
        fw, fh = [float(x) for x in args.figsize.split(",")]
    else:
        import math
        bounds = gdf.total_bounds
        data_w = bounds[2] - bounds[0]
        data_h = bounds[3] - bounds[1]
        mean_lat = (bounds[1] + bounds[3]) / 2
        aspect = ((data_w * math.cos(math.radians(mean_lat))) / data_h
                  if data_h > 0 else 1.0)
        target_area = fig_cfg.get("size_state", [14, 10])
        target_area_val = target_area[0] * target_area[1]
        map_area = target_area_val * 0.85
        fh = math.sqrt(map_area / aspect) if aspect > 0 else 10
        fw = fh * aspect
        fw = max(7, min(16, fw))
        fh = max(6, min(18, fh))

    dpi = args.dpi or fig_cfg.get("dpi", 200)
    title = args.title or args.field.replace("_", " ").title()

    # ── Stroke styling ──────────────────────────────────────────────────
    stroke_cfg = family_profile.get("stroke", {})
    if args.no_border:
        edge_color = "none"
        edge_width = 0
    else:
        interior = stroke_cfg.get("interior", {})
        edge_color = interior.get("color", "white")
        edge_width = interior.get("width", 0.25)

    # ── Build figure ────────────────────────────────────────────────────
    fig, ax = plt.subplots(1, 1, figsize=(fw, fh))
    bg = fig_cfg.get("background", "#ffffff")
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    # Missing / unknown rows rendered first so known categories paint over them.
    missing_mask = gdf[args.field].isna() | gdf[args.field].astype(str).isin(unknown)
    if missing_mask.any():
        gdf[missing_mask].plot(ax=ax, color=args.missing_color,
                               edgecolor=edge_color, linewidth=edge_width)

    # Known categories in render order.
    counts: dict[str, int] = {}
    for cat in render_order:
        color = color_map[cat]
        subset = gdf[gdf[args.field].astype(str) == cat]
        counts[cat] = int(len(subset))
        if len(subset) == 0:
            continue
        subset.plot(ax=ax, color=color, edgecolor=edge_color, linewidth=edge_width)

    # ── Basemap ─────────────────────────────────────────────────────────
    if args.basemap and args.basemap != "none":
        try:
            import contextily as cx
            basemap_sources = {
                "light": cx.providers.CartoDB.PositronNoLabels,
                "dark": cx.providers.CartoDB.DarkMatterNoLabels,
                "terrain": cx.providers.OpenTopoMap,
            }
            source = basemap_sources.get(args.basemap,
                                         cx.providers.CartoDB.PositronNoLabels)
            cx.add_basemap(ax, crs=gdf.crs, source=source,
                           attribution=False, zoom="auto")
            assumptions.append(f"basemap: {args.basemap} (CartoDB/CC BY)")
        except Exception as e:
            warnings_list.append(f"basemap skipped: {e}")

    # ── Dissolved outline ───────────────────────────────────────────────
    if args.state_outline and not args.no_state_outline:
        boundary_cfg = stroke_cfg.get("boundary", {})
        try:
            outline = gdf.dissolve()
            outline.boundary.plot(
                ax=ax,
                edgecolor=boundary_cfg.get("color", "#555555"),
                linewidth=boundary_cfg.get("width", 0.5),
                zorder=20,
            )
        except Exception:
            pass

    # ── Title ───────────────────────────────────────────────────────────
    title_cfg = family_profile.get("title", {})
    ax.set_title(title,
                 fontsize=title_cfg.get("fontsize", 14),
                 fontweight=title_cfg.get("fontweight", "bold"),
                 color=title_cfg.get("color", "#222222"),
                 loc="center",
                 pad=title_cfg.get("pad", 16))
    ax.set_axis_off()

    # ── Legend ──────────────────────────────────────────────────────────
    legend_cfg = family_profile.get("legend", {})
    handles = [
        Patch(facecolor=color_map[cat], edgecolor="#888", linewidth=0.4,
              label=f"{cat} ({counts.get(cat, 0):,})" if counts.get(cat, 0) else cat)
        for cat in render_order if counts.get(cat, 0) > 0
    ]
    if missing_mask.any():
        n_miss = int(missing_mask.sum())
        handles.append(Patch(
            facecolor=args.missing_color, edgecolor="#888", linewidth=0.4,
            label=f"No data ({n_miss:,})",
        ))
    legend_loc = {
        "upper-left": "upper left", "upper-right": "upper right",
        "lower-left": "lower left", "lower-right": "lower right",
    }.get(args.legend_pos, "lower right")
    legend_title = args.legend_title or "Classification"
    leg = ax.legend(
        handles=handles,
        loc=legend_loc,
        title=legend_title,
        fontsize=legend_cfg.get("fontsize", 9),
        title_fontsize=legend_cfg.get("title_fontsize", 10),
        framealpha=legend_cfg.get("framealpha", 1.0),
        edgecolor=legend_cfg.get("edgecolor", "#333333"),
        facecolor=legend_cfg.get("facecolor", "#ffffff"),
        borderpad=legend_cfg.get("borderpad", 0.8),
        labelspacing=legend_cfg.get("labelspacing", 0.5),
        fancybox=False,
    )
    # Harden the frame — `facecolor`/`framealpha` args above don't always stick
    # when a basemap renders under the axes. Set them explicitly on the patch
    # so the legend is guaranteed to be solid and readable.
    _frame = leg.get_frame()
    _frame.set_facecolor(legend_cfg.get("facecolor", "#ffffff"))
    _frame.set_edgecolor(legend_cfg.get("edgecolor", "#333333"))
    _frame.set_linewidth(legend_cfg.get("linewidth", 1.2))
    _frame.set_alpha(legend_cfg.get("framealpha", 1.0))
    _frame.set_zorder(10)  # keep the frame above the basemap + data

    # ── Attribution ─────────────────────────────────────────────────────
    annotation_y = 0.02
    if args.attribution:
        attr_cfg = family_profile.get("attribution", {})
        typo_attr = styles.get("typography", {}).get("attribution", {})
        ax.text(0.01, 0.01, args.attribution, transform=ax.transAxes,
                ha='left', va='bottom',
                fontsize=typo_attr.get("size", attr_cfg.get("fontsize", 7)),
                fontfamily=_font_chain(typo_attr.get(
                    "family", "Gill Sans MT, Calibri, sans-serif")),
                color=typo_attr.get("color", attr_cfg.get("color", "#888888")),
                style=typo_attr.get("style", "italic"))
        annotation_y += 0.02

    crs_label = str(gdf.crs) if gdf.crs else "CRS unknown"
    assumptions.append(f"CRS: {crs_label}")
    assumptions.append(f"classification: categorical, k={len(render_order)}")

    fig.tight_layout(rect=[0, 0.04, 1, 1])

    # ── Output ──────────────────────────────────────────────────────────
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "maps"
        out_path = out_dir / f"{src.stem}_{args.field}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor=bg)
    plt.close(fig)

    # ── Sidecar ─────────────────────────────────────────────────────────
    if not args.no_sidecar:
        write_style_sidecar(
            output_path=out_path,
            map_family="thematic_categorical",
            field=args.field,
            title=title,
            legend_title=legend_title,
            attribution=args.attribution,
            crs=crs_label,
            source_gpkg=str(src),
            layer_name=args.layer,
            categorical_map=color_map,
            extra={
                "classification": "categorical",
                "category_counts": counts,
                "unmapped_values": unknown,
            },
        )

    # ── Metadata log ────────────────────────────────────────────────────
    log = {
        "step": "analyze_choropleth",
        "mode": "categorical",
        "source": str(src),
        "output": str(out_path),
        "field": args.field,
        "title": title,
        "categories": counts,
        "unmapped_values": unknown,
        "null_features": null_count,
        "total_features": total,
        "assumptions": assumptions,
        "warnings": warnings_list,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    log_path = out_path.with_name(f"{out_path.stem}.choropleth.json")
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"categorical ({sum(counts.values())} mapped, "
          f"{null_count + len(unknown)} missing/unmapped) -> {out_path}")
    print(f"  categories: {len(render_order)} ({', '.join(render_order)})")
    print(f"  log: {log_path}")
    if not args.no_sidecar:
        print(f"  style: {out_path.with_suffix('.style.json')}")
    for w in warnings_list:
        print(f"  WARNING: {w}")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a delivery-quality choropleth map from a spatial dataset."
    )
    parser.add_argument("input", help="Path to spatial file (GeoPackage, shapefile, GeoJSON)")
    parser.add_argument("field", help="Numeric field to map")
    parser.add_argument("--title", help="Map title (default: auto-generated from field)")
    parser.add_argument("--cmap", help="Matplotlib colormap (default: auto from style registry)")
    parser.add_argument("--scheme", help="Classification: quantiles, equal_interval, natural_breaks (default: auto)")
    parser.add_argument("--k", type=int, help="Number of classes (default: from style registry, typically 5)")
    parser.add_argument("--missing-color", default="#d0d0d0", help="Color for null values (default: #d0d0d0)")
    parser.add_argument("-o", "--output", help="Output PNG path")
    parser.add_argument("--figsize", help="Figure size as width,height inches (default: from style registry)")
    parser.add_argument("--legend-title", help="Override legend title")
    parser.add_argument("--attribution", help="Source attribution text")
    parser.add_argument("--dpi", type=int, help="Output DPI (default: from style registry)")
    parser.add_argument("--no-border", action="store_true", help="Remove interior edge lines")
    parser.add_argument("--state-outline", action="store_true", default=True, help="Draw dissolved boundary (default: on)")
    parser.add_argument("--no-state-outline", action="store_true", help="Disable dissolved boundary")
    parser.add_argument("--layer", help="Layer name within GeoPackage")
    parser.add_argument("--labels", action="store_true", help="Add feature labels (auto-detects label field)")
    parser.add_argument("--label-field", help="Field to use for labels (default: NAME or first label-role field)")
    parser.add_argument("--pattern", help="Hatching pattern for print accessibility (e.g. ///, xxx, ...)")
    parser.add_argument("--basemap", choices=["light", "dark", "terrain", "none"], default="none",
                        help="Add a basemap behind the data (requires internet for tile fetch)")
    parser.add_argument("--legend-pos", default="auto",
                        help="Legend position: auto|upper-left|upper-right|lower-left|lower-right. Auto picks the corner with the least data.")
    parser.add_argument("--no-sidecar", action="store_true", help="Skip writing .style.json sidecar")
    parser.add_argument("--categorical", action="store_true",
                        help="Render as a thematic categorical map (fixed category -> color "
                             "mapping, no classification). Auto-enabled when the field is "
                             "non-numeric and --category-colors is supplied.")
    parser.add_argument("--category-colors",
                        help="Category -> color mapping for --categorical mode. Either a JSON "
                             "object (e.g. '{\"Food desert\": \"#b30000\", \"Not a food desert\": \"#e6e6e6\"}') "
                             "or a path to a JSON file with the same shape. Keys are category "
                             "values (matched against the field); values are hex colors.")
    parser.add_argument("--category-order", nargs="*",
                        help="Optional render order for --categorical mode. Later categories "
                             "plot on top. Defaults to --category-colors key order.")
    args = parser.parse_args()

    # ── Load source data ────────────────────────────────────────────────
    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"input not found: {src}")
        return 1

    gdf = gpd.read_file(src, layer=args.layer) if args.layer else gpd.read_file(src)
    warnings_list = []
    assumptions = []

    if args.field not in gdf.columns:
        print(f"field not found: {args.field}")
        print(f"available: {[c for c in gdf.columns if c != 'geometry']}")
        return 2

    # ── Categorical branch ──────────────────────────────────────────────
    # Triggers when --categorical is set, or when the field is non-numeric
    # AND the caller provided --category-colors (we won't guess a palette
    # for a text field the caller hasn't annotated).
    is_text_field = not pd.api.types.is_numeric_dtype(gdf[args.field])
    if args.categorical or (is_text_field and args.category_colors):
        return _render_categorical(gdf, args, src)

    # Coerce to numeric
    if not pd.api.types.is_numeric_dtype(gdf[args.field]):
        gdf[args.field] = pd.to_numeric(gdf[args.field], errors="coerce")
        assumptions.append(f"coerced '{args.field}' to numeric")

    null_count = int(gdf[args.field].isna().sum())
    total = len(gdf)
    if null_count > 0:
        pct = round(null_count / total * 100, 1)
        warnings_list.append(f"{null_count}/{total} ({pct}%) null values shown in gray")

    non_null = gdf[gdf[args.field].notna()]
    if len(non_null) == 0:
        print(f"no non-null values for '{args.field}'")
        return 3

    # ── Resolve styling from registry ───────────────────────────────────
    styles = load_styles()
    family_profile = styles.get("families", {}).get("thematic_choropleth", {})
    palette = resolve_palette(args.field)

    cmap = args.cmap or palette.get("cmap", "YlOrRd")
    scheme = args.scheme or palette.get("scheme", "natural_breaks")
    k = args.k or palette.get("k", 5)

    if len(non_null) < k:
        warnings_list.append(f"only {len(non_null)} features, using {len(non_null)} classes")
        k = len(non_null)

    fig_cfg = family_profile.get("figure", {})
    if args.figsize:
        fw, fh = [float(x) for x in args.figsize.split(",")]
    else:
        # Compute figure size from data aspect ratio — fit the frame to the geography
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        data_w = bounds[2] - bounds[0]
        data_h = bounds[3] - bounds[1]
        # Adjust for latitude-based distortion (longitude degrees shrink with latitude)
        import math
        mean_lat = (bounds[1] + bounds[3]) / 2
        aspect = (data_w * math.cos(math.radians(mean_lat))) / data_h if data_h > 0 else 1.0

        # Target: figure area roughly matches registry's preferred size,
        # but aspect ratio matches the data.
        target_area = fig_cfg.get("size_state", [14, 10])
        target_area_val = target_area[0] * target_area[1]

        # Allocate extra height for title, legend, attribution margins
        map_area = target_area_val * 0.85
        fh = math.sqrt(map_area / aspect) if aspect > 0 else 10
        fw = fh * aspect

        # Enforce min/max to keep things sensible
        fw = max(7, min(16, fw))
        fh = max(6, min(18, fh))

    dpi = args.dpi or fig_cfg.get("dpi", 200)
    title = args.title or args.field.replace("_", " ").title()
    legend_title = _build_legend_title(args.field, args.legend_title)

    # ── Stroke styling from registry ────────────────────────────────────
    stroke_cfg = family_profile.get("stroke", {})
    if args.no_border:
        edge_color = "none"
        edge_width = 0
        edge_alpha = 1.0
    else:
        interior = stroke_cfg.get("interior", {})
        edge_color = interior.get("color", "#444444")
        edge_width = interior.get("width", 0.3)
        edge_alpha = interior.get("alpha", 0.6)

    # ── Build figure ────────────────────────────────────────────────────
    fig, ax = plt.subplots(1, 1, figsize=(fw, fh))
    bg = fig_cfg.get("background", "#ffffff")
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    # Plot missing features first
    if null_count > 0:
        gdf[gdf[args.field].isna()].plot(
            ax=ax, color=args.missing_color, edgecolor=edge_color, linewidth=edge_width
        )

    # Classification
    scheme_map = {
        "quantiles": "Quantiles", "quantile": "Quantiles",
        "equal_interval": "EqualInterval",
        "natural_breaks": "NaturalBreaks",
        "std_mean": "StdMean",
    }
    mc_scheme = scheme_map.get(scheme, "NaturalBreaks")

    # Classify up-front so we can persist breaks in the sidecar. The
    # downstream plot() call re-classifies internally; we accept the small
    # duplicate cost to buy renderer parity across QGIS / ArcGIS Pro / AGOL.
    breaks: list[float] = []
    try:
        import mapclassify
        cls = mapclassify.classify(non_null[args.field].to_numpy(),
                                    scheme=mc_scheme, k=k)
        bins = list(cls.bins)
        # mapclassify gives upper edges; prepend the min to form full ranges
        min_v = float(non_null[args.field].min())
        breaks = [min_v] + [float(b) for b in bins]
    except Exception:
        breaks = []

    # Detect FIPS codes for water/labels layers
    state_fips, county_fips = _detect_fips(gdf)

    # Dynamic legend position: find the emptiest quadrant
    if args.legend_pos == "auto":
        legend_loc = _pick_legend_position(ax, non_null, args.field)
    else:
        pos_map = {
            "upper-left": "upper left", "upper-right": "upper right",
            "lower-left": "lower left", "lower-right": "lower right",
        }
        legend_loc = pos_map.get(args.legend_pos, "lower right")

    # Legend styling from registry — solid background, clean border
    legend_cfg = family_profile.get("legend", {})
    legend_kwds = {
        "loc": legend_loc,
        "fontsize": legend_cfg.get("fontsize", 9),
        "title": legend_title,
        "title_fontsize": legend_cfg.get("title_fontsize", 10),
        "framealpha": legend_cfg.get("framealpha", 1.0),
        "edgecolor": legend_cfg.get("edgecolor", "#666666"),
        "facecolor": legend_cfg.get("facecolor", "#ffffff"),
        "borderpad": legend_cfg.get("borderpad", 1.0),
        "labelspacing": legend_cfg.get("labelspacing", 0.5),
        "fancybox": False,
    }

    # Plot the choropleth
    plot_kwargs = dict(
        column=args.field,
        ax=ax,
        legend=True,
        scheme=mc_scheme,
        k=k,
        cmap=cmap,
        edgecolor=edge_color,
        linewidth=edge_width,
        legend_kwds=legend_kwds,
        missing_kwds={"color": args.missing_color},
    )

    # Add hatching if requested
    if args.pattern:
        plot_kwargs["hatch"] = args.pattern

    # Stroke alpha: geopandas.plot doesn't accept edgecolor alpha directly,
    # but we can draw the interior boundaries as a second pass with transparency.
    # For simplicity, apply alpha via rgba edge color.
    if edge_color != "none" and edge_alpha < 1.0:
        import matplotlib.colors as mcolors
        rgba = mcolors.to_rgba(edge_color, alpha=edge_alpha)
        plot_kwargs["edgecolor"] = rgba

    non_null.plot(**plot_kwargs)

    # ── Basemap (optional, requires internet) ───────────────────────────
    if args.basemap and args.basemap != "none":
        try:
            import contextily as cx
            basemap_sources = {
                "light": cx.providers.CartoDB.PositronNoLabels,
                "dark": cx.providers.CartoDB.DarkMatterNoLabels,
                "terrain": cx.providers.OpenTopoMap,
            }
            source = basemap_sources.get(args.basemap, cx.providers.CartoDB.PositronNoLabels)
            cx.add_basemap(ax, crs=non_null.crs, source=source, attribution=False, zoom="auto")
            assumptions.append(f"basemap: {args.basemap} (CartoDB/CC BY)")
        except Exception as e:
            warnings_list.append(f"basemap skipped: {e}")

    # Clean up legend labels
    _format_legend_labels(ax)

    # ── Typography from registry ────────────────────────────────────────
    title_cfg = family_profile.get("title", {})
    ax.set_title(title,
                 fontsize=title_cfg.get("fontsize", 14),
                 fontweight=title_cfg.get("fontweight", "bold"),
                 color=title_cfg.get("color", "#222222"),
                 loc="center",
                 pad=title_cfg.get("pad", 16))
    ax.set_axis_off()

    # ── Dissolved boundary ──────────────────────────────────────────────
    if args.state_outline and not args.no_state_outline:
        boundary_cfg = stroke_cfg.get("boundary", {})
        try:
            outline = gdf.dissolve()
            outline.boundary.plot(ax=ax,
                                  edgecolor=boundary_cfg.get("color", "#555555"),
                                  linewidth=boundary_cfg.get("width", 0.35),
                                  zorder=20)
        except Exception:
            pass

    # ── Feature labels ──────────────────────────────────────────────────
    if args.labels:
        label_field = args.label_field
        if not label_field:
            # Auto-detect label field
            for candidate in ["NAME", "NAMELSAD", "name", "label", "tract_name"]:
                if candidate in gdf.columns:
                    label_field = candidate
                    break
        if label_field and label_field in gdf.columns:
            label_threshold = family_profile.get("labels", {}).get("enabled_threshold", 50)
            if len(gdf) <= label_threshold:
                _add_feature_labels(ax, gdf, label_field, styles)
            else:
                warnings_list.append(f"labels skipped: {len(gdf)} features exceeds threshold of {label_threshold}")

    # ── Attribution (lower-left to avoid legend overlap) ──────────────
    annotation_y = 0.02
    if args.attribution:
        attr_cfg = family_profile.get("attribution", {})
        typo_attr = styles.get("typography", {}).get("attribution", {})
        ax.text(0.01, 0.01, args.attribution, transform=ax.transAxes,
                ha='left', va='bottom',
                fontsize=typo_attr.get("size", attr_cfg.get("fontsize", 7)),
                fontfamily=_font_chain(typo_attr.get("family", "Gill Sans MT, Calibri, sans-serif")),
                color=typo_attr.get("color", attr_cfg.get("color", "#888888")),
                style=typo_attr.get("style", "italic"))
        annotation_y += 0.02

    if null_count > 0:
        caveat = f"Note: {null_count}/{total} features lack data (shown in gray)"
        fig.text(0.01, annotation_y, caveat, ha="left", fontsize=7,
                 style="italic", color="#666666")

    crs_label = str(gdf.crs) if gdf.crs else "CRS unknown"
    assumptions.append(f"CRS: {crs_label}")
    assumptions.append(f"classification: {scheme}, k={k}")
    assumptions.append(f"palette: {palette.get('name', cmap)} ({cmap})")

    fig.tight_layout(rect=[0, 0.04, 1, 1])

    # ── Output ──────────────────────────────────────────────────────────
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "maps"
        out_path = out_dir / f"{src.stem}_{args.field}.png"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor=bg)
    plt.close(fig)

    # ── Style sidecar ───────────────────────────────────────────────────
    if not args.no_sidecar:
        colors = get_rgb_ramp(cmap, k)
        write_style_sidecar(
            output_path=out_path,
            map_family="thematic_choropleth",
            field=args.field,
            palette=palette.get("name", cmap),
            scheme=scheme,
            k=k,
            breaks=breaks if breaks else None,
            colors=colors,
            title=title,
            legend_title=legend_title,
            attribution=args.attribution,
            crs=crs_label,
            source_gpkg=str(src),
            layer_name=args.layer,
            pattern=args.pattern,
        )

    # ── Metadata log ────────────────────────────────────────────────────
    log = {
        "step": "analyze_choropleth",
        "source": str(src),
        "output": str(out_path),
        "field": args.field,
        "title": title,
        "cmap": cmap,
        "palette_resolved": palette.get("name", "manual"),
        "legend_title": legend_title,
        "dpi": dpi,
        "scheme": scheme,
        "k": k,
        "total_features": total,
        "null_features": null_count,
        "non_null_features": total - null_count,
        "labels": args.labels,
        "pattern": args.pattern,
        "assumptions": assumptions,
        "warnings": warnings_list,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    log_path = out_path.with_name(f"{out_path.stem}.choropleth.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(f"choropleth ({total - null_count} mapped, {null_count} missing) -> {out_path}")
    print(f"  palette: {palette.get('name', cmap)} ({cmap}, {scheme}, k={k})")
    if args.labels:
        print(f"  labels: {args.label_field or 'auto-detected'}")
    print(f"  log: {log_path}")
    if not args.no_sidecar:
        print(f"  style: {out_path.with_suffix('.style.json')}")
    if warnings_list:
        for w in warnings_list:
            print(f"  WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
