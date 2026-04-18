#!/usr/bin/env python3
"""Overlay point features onto polygon features.

Supports:
- Point-in-polygon count (how many points per polygon)
- Nearest distance (distance from polygon centroid to nearest point)
- Buffer count (points within N km of each polygon centroid)
- Map output with points overlaid on choropleth

Usage:
    python overlay_points.py \\
        --polygons data/processed/tracts.gpkg \\
        --points data/raw/hospitals.csv \\
        --points-lat latitude --points-lon longitude \\
        --output data/processed/tracts_with_hospitals.gpkg \\
        [--count-col hospital_count] \\
        [--nearest-col nearest_hospital_km] \\
        [--buffer-km 30] \\
        [--buffer-col hospitals_within_30km] \\
        [--output-map outputs/maps/hospitals_overlay.png] \\
        [--choropleth-col uninsured_rate] \\
        [--map-title "Hospitals and Uninsured Rate"]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

# scripts/core on sys.path so the style registry + sidecar writer import
# cleanly whether this module is invoked directly or via the packager.
_SCRIPTS_CORE = Path(__file__).resolve().parent
if str(_SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_CORE))
try:
    from style_utils import resolve_palette, get_rgb_ramp
    from write_style_sidecar import write_style_sidecar
except ImportError:  # pragma: no cover — style helpers optional
    resolve_palette = None
    get_rgb_ramp = None
    write_style_sidecar = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Point-in-polygon overlay")
    parser.add_argument("--polygons", required=True, help="Polygon GeoPackage")
    parser.add_argument("--polygon-layer", default=None, help="Layer name for polygon GeoPackage")
    parser.add_argument("--points", required=True, help="Point file (CSV, GeoJSON, GeoPackage)")
    parser.add_argument("--point-layer", default=None, help="Layer name for point GeoPackage")
    parser.add_argument("--points-lat", default=None, help="Latitude column (for CSV)")
    parser.add_argument("--points-lon", default=None, help="Longitude column (for CSV)")
    parser.add_argument("--points-crs", default="EPSG:4326", help="CRS of point data")
    parser.add_argument("--output", required=True, help="Output GeoPackage")
    parser.add_argument("--count-col", default="point_count",
                        help="Column name for point count per polygon")
    parser.add_argument("--nearest-col", default=None,
                        help="Column name for nearest point distance (km)")
    parser.add_argument("--buffer-km", type=float, default=None,
                        help="Buffer radius in km for buffer count")
    parser.add_argument("--buffer-col", default=None,
                        help="Column name for buffer count")
    parser.add_argument("--output-map", default=None, help="Output overlay map PNG")
    parser.add_argument("--choropleth-col", default=None,
                        help="Polygon column to use for choropleth background")
    parser.add_argument("--map-title", default=None, help="Map title")
    parser.add_argument("--output-stats", default=None, help="Output stats JSON")
    parser.add_argument("--attribution", default=None,
                        help="Source attribution text to print under the map "
                             "(e.g. 'Sources: Census ACS 2019-2023; OSM').")
    parser.add_argument("--point-label", default=None,
                        help="Legend label for the point layer "
                             "(e.g. 'Supermarket', 'Clinic'). Defaults to "
                             "the title prefix or 'Facilities'.")
    parser.add_argument("--no-sidecar", action="store_true",
                        help="Skip writing the .style.json sidecar next to "
                             "--output-map.")
    args = parser.parse_args()

    # Load polygons
    polys = gpd.read_file(args.polygons, layer=args.polygon_layer) if args.polygon_layer else gpd.read_file(args.polygons)
    print(f"Loaded {len(polys)} polygons from {args.polygons}")

    # Load points
    points_path = Path(args.points)
    if points_path.suffix.lower() == ".csv":
        if not args.points_lat or not args.points_lon:
            print("ERROR: --points-lat and --points-lon required for CSV input")
            return 1
        df = pd.read_csv(args.points)
        # Drop rows with null coords
        df = df.dropna(subset=[args.points_lat, args.points_lon])
        geometry = [Point(xy) for xy in zip(df[args.points_lon], df[args.points_lat])]
        pts = gpd.GeoDataFrame(df, geometry=geometry, crs=args.points_crs)
    else:
        pts = gpd.read_file(args.points)

    print(f"Loaded {len(pts)} points from {args.points}")

    # Ensure same CRS
    if pts.crs != polys.crs:
        pts = pts.to_crs(polys.crs)

    # Point-in-polygon count
    print("Computing point-in-polygon counts...")
    joined = gpd.sjoin(pts, polys, how="inner", predicate="within")
    counts = joined.groupby(joined.index_right).size()
    polys[args.count_col] = polys.index.map(counts).fillna(0).astype(int)
    print(f"  {int(polys[args.count_col].sum())} points matched to polygons")
    print(f"  {int((polys[args.count_col] == 0).sum())} polygons with zero points")

    # Nearest distance
    if args.nearest_col:
        print("Computing nearest point distances...")
        # Project to a meter-based CRS for distance calculation
        proj_crs = "EPSG:3857"  # Web Mercator (approximate but fast)
        polys_proj = polys.to_crs(proj_crs)
        pts_proj = pts.to_crs(proj_crs)
        centroids = polys_proj.geometry.centroid

        from shapely.ops import nearest_points
        from shapely import MultiPoint as ShapelyMultiPoint

        pts_union = pts_proj.geometry.unary_union
        distances = []
        for centroid in centroids:
            nearest = nearest_points(centroid, pts_union)[1]
            dist_m = centroid.distance(nearest)
            distances.append(dist_m / 1000.0)  # Convert to km

        polys[args.nearest_col] = np.round(distances, 2)
        print(f"  Mean nearest distance: {np.mean(distances):.1f} km")
        print(f"  Max nearest distance: {np.max(distances):.1f} km")

    # Buffer count
    if args.buffer_km and args.buffer_col:
        print(f"Computing points within {args.buffer_km} km buffer...")
        proj_crs = "EPSG:3857"
        polys_proj = polys.to_crs(proj_crs)
        pts_proj = pts.to_crs(proj_crs)
        buffer_m = args.buffer_km * 1000

        centroids = polys_proj.geometry.centroid
        buffer_counts = []
        pts_sindex = pts_proj.sindex
        for centroid in centroids:
            buf = centroid.buffer(buffer_m)
            possible = list(pts_sindex.intersection(buf.bounds))
            actual = sum(1 for i in possible if pts_proj.geometry.iloc[i].within(buf))
            buffer_counts.append(actual)

        polys[args.buffer_col] = buffer_counts
        print(f"  Mean count within buffer: {np.mean(buffer_counts):.1f}")

    # Save
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    polys.to_file(args.output, driver="GPKG")
    print(f"Saved: {args.output}")

    # Stats
    stats = {
        "step": "overlay_points",
        "polygons": str(args.polygons),
        "points": str(args.points),
        "n_polygons": len(polys),
        "n_points": len(pts),
        "points_matched": int(polys[args.count_col].sum()),
        "polygons_with_zero_points": int((polys[args.count_col] == 0).sum()),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.nearest_col:
        stats["mean_nearest_km"] = round(float(np.mean(distances)), 2)
        stats["max_nearest_km"] = round(float(np.max(distances)), 2)
    if args.output_stats:
        Path(args.output_stats).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_stats, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Saved stats: {args.output_stats}")

    def _auto_legend_title(field_name):
        fn = field_name.lower()
        nice = field_name.replace("_", " ").title()
        nice = nice.replace("Pct ", "% ").replace(" Pct", "")
        nice = nice.replace("Per Sqkm", "per sq km").replace("Sqkm", "sq km")
        nice = nice.replace("Nh ", "")
        if any(k in fn for k in ("rate", "pct", "percent")):
            return nice if "%" in nice else f"{nice} (%)"
        elif any(k in fn for k in ("income", "rent", "cost", "price", "value")):
            return f"{nice} ($)"
        elif any(k in fn for k in ("pop", "count", "total", "number", "universe")):
            return f"{nice} (count)"
        elif "per sq km" in nice:
            return nice
        return nice

    # Overlay map
    if args.output_map:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        fig.patch.set_facecolor('white')

        def _fmt_val(v):
            abs_v = abs(v)
            if abs_v >= 1000:
                return f"{int(round(v)):,}"
            elif abs_v >= 10:
                return f"{v:.0f}"
            elif abs_v >= 1:
                return f"{v:.1f}"
            else:
                return f"{v:.2f}"

        def _format_legend_labels(ax_obj):
            legend = ax_obj.get_legend()
            if legend is None:
                return
            for text in legend.get_texts():
                label = text.get_text()
                try:
                    parts = label.split(",")
                    if len(parts) == 2:
                        lo, hi = float(parts[0].strip()), float(parts[1].strip())
                    elif len(parts) == 4:
                        lo = float(parts[0].strip() + parts[1].strip())
                        hi = float(parts[2].strip() + parts[3].strip())
                    else:
                        continue
                    text.set_text(f"{_fmt_val(lo)} \u2013 {_fmt_val(hi)}")
                except (ValueError, OverflowError):
                    pass

        # Background choropleth — palette from the style registry when
        # available so this map uses the same colors as the standalone
        # choropleth for the same field (poverty_rate → YlOrRd, etc.).
        cmap_used = "YlOrRd"
        scheme_used = "NaturalBreaks"
        k_used = 5
        breaks_used: list[float] = []
        if args.choropleth_col and args.choropleth_col in polys.columns:
            if resolve_palette is not None:
                pal = resolve_palette(args.choropleth_col)
                cmap_used = pal.get("cmap", cmap_used)
                scheme_used = {"natural_breaks": "NaturalBreaks",
                               "quantile": "Quantiles",
                               "quantiles": "Quantiles",
                               "equal_interval": "EqualInterval"}.get(
                    pal.get("scheme", "natural_breaks"), "NaturalBreaks")
                k_used = pal.get("k", k_used)

            polys.plot(ax=ax, column=args.choropleth_col, cmap=cmap_used,
                       scheme=scheme_used, k=k_used, edgecolor="#33333344",
                       linewidth=0.3, legend=True,
                       legend_kwds={"loc": "lower left", "fontsize": 9,
                                    "framealpha": 0.9, "edgecolor": "#cccccc", "fancybox": False,
                                    "title": _auto_legend_title(args.choropleth_col)})
            _format_legend_labels(ax)

            # Compute explicit break edges so the sidecar can record them —
            # mapclassify is the same classifier geopandas.plot uses.
            try:
                import mapclassify
                non_null = polys[args.choropleth_col].dropna().to_numpy()
                if len(non_null):
                    cls = mapclassify.classify(non_null, scheme=scheme_used, k=k_used)
                    breaks_used = [float(non_null.min())] + [float(b) for b in cls.bins]
            except Exception:
                breaks_used = []
        else:
            polys.plot(ax=ax, color="#e0e0e0", edgecolor="#33333344", linewidth=0.3)

        # State outline on top of choropleth
        try:
            polys.dissolve().boundary.plot(ax=ax, edgecolor='#333333', linewidth=1.2, zorder=15)
        except Exception:
            pass

        # Points — large, visible, with contrast
        pts_plot = pts.to_crs(polys.crs)
        from matplotlib.lines import Line2D
        pts_plot.plot(ax=ax, color="white", edgecolor="#1a1a1a",
                      markersize=80, linewidth=1.5, alpha=0.9,
                      zorder=20)

        # Add point legend entry manually (GeoPandas .plot doesn't combine with choropleth legend)
        if args.point_label:
            point_label = args.point_label
        elif args.map_title and ":" in args.map_title:
            point_label = args.map_title.split(":")[0].strip()
        else:
            point_label = "Facilities"
        point_handle = Line2D([0], [0], marker='o', color='w', markerfacecolor='white',
                              markeredgecolor='#1a1a1a', markersize=10, linewidth=0,
                              label=f"{point_label} ({len(pts_plot)})")
        # Get existing legend handles and add point handle
        existing_legend = ax.get_legend()
        if existing_legend:
            handles = existing_legend.legend_handles[:]
            labels = [t.get_text() for t in existing_legend.get_texts()]
            handles.append(point_handle)
            labels.append(f"{point_label} ({len(pts_plot)})")
            ax.legend(handles=handles, labels=labels, loc="lower left", fontsize=9,
                      framealpha=0.9, edgecolor="#cccccc", title=existing_legend.get_title().get_text())
        else:
            ax.legend(handles=[point_handle], loc="upper right", fontsize=9, framealpha=0.9)

        title = args.map_title or f"Point Overlay: {args.count_col}"
        ax.set_title(title, fontsize=16, fontweight="bold", loc="center", pad=16)
        ax.set_axis_off()

        # Attribution — prefer caller-supplied text, else fall back to a
        # column-name stub. Position bottom-left to match the rest of the
        # cartography family.
        if args.attribution:
            ax.text(0.01, 0.01, args.attribution,
                    transform=ax.transAxes, ha='left', va='bottom',
                    fontsize=7, color='#777777', style='italic')
        elif args.choropleth_col:
            ax.text(0.99, 0.01,
                    f'Source: {args.choropleth_col.replace("_", " ").title()}',
                    transform=ax.transAxes, ha='right', va='bottom',
                    fontsize=7, color='#999999', style='italic')

        plt.tight_layout()

        Path(args.output_map).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output_map, dpi=200, bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)
        print(f"Saved map: {args.output_map}")

        # Sidecar — so the QGIS + ArcGIS packagers can find this map and
        # match it to its source gpkg. Fields recorded: choropleth palette
        # + breaks (like a regular choropleth sidecar) plus the point layer
        # metadata (path, count, label).
        if not args.no_sidecar and write_style_sidecar is not None:
            colors_rgb = []
            if get_rgb_ramp is not None and breaks_used:
                colors_rgb = get_rgb_ramp(cmap_used, len(breaks_used) - 1)

            extra = {
                "point_layer_gpkg": str(Path(args.points).resolve())
                    if not args.points.startswith(("http://", "https://")) else args.points,
                "point_layer_name": args.point_layer,
                "point_count": int(len(pts_plot)),
                "point_label": point_label,
            }
            write_style_sidecar(
                output_path=args.output_map,
                map_family="point_overlay",
                field=args.choropleth_col,
                palette=cmap_used if args.choropleth_col else None,
                scheme=scheme_used.lower() if args.choropleth_col else None,
                k=k_used if args.choropleth_col else None,
                breaks=breaks_used if breaks_used else None,
                colors=colors_rgb if colors_rgb else None,
                title=title,
                attribution=args.attribution,
                crs=str(polys.crs) if polys.crs else None,
                source_gpkg=str(Path(args.polygons).resolve()),
                layer_name=args.polygon_layer,
                extra=extra,
            )
            print(f"Sidecar: {Path(args.output_map).with_suffix('.style.json')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
