#!/usr/bin/env python3
"""Render hydrography (lakes, rivers, oceans) as a reference layer.

Pulls water features from OpenStreetMap via the Overpass API. This is a
proper reference layer sourced from actual hydrography data — not from
Census tract geometry artifacts (AWATER columns, which are not designed
to be a map layer).

Usable two ways:
1. As a CLI: produces a standalone PNG showing water in the context of a
   study area (useful for review or composing side-by-side).
2. As a module: `from layers.add_water_layer import render` — call
   `render(ax, study_gdf, ...)` from another script that owns the figure.

Water features pulled from OSM: natural=water, waterway=river|canal,
and the Great Lakes polygons. Results are cached locally on first fetch.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "core" / "layers"))

from _base import basemap_theme_from_ax

CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "hydrography"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _cache_key(bounds: tuple[float, float, float, float]) -> str:
    s = json.dumps(bounds, sort_keys=True)
    return hashlib.md5(s.encode()).hexdigest()[:12]


def fetch_water_osm(bounds: tuple[float, float, float, float],
                    min_area_sqm: float = 50000,
                    use_cache: bool = True) -> gpd.GeoDataFrame:
    """Fetch water features from OSM Overpass API for a bounding box.

    Returns GeoDataFrame in EPSG:4326 (WGS84).
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"osm_water_{_cache_key(bounds)}.gpkg"

    if use_cache and cache_path.exists():
        gdf = gpd.read_file(cache_path)
        return gdf

    import requests
    import shapely.geometry as sg
    from shapely.geometry import shape

    south, west, north, east = bounds[1], bounds[0], bounds[3], bounds[2]
    bbox_str = f"{south},{west},{north},{east}"

    # Query OSM for water polygons and major rivers within bbox
    query = f"""
    [out:json][timeout:60];
    (
      way["natural"="water"]({bbox_str});
      relation["natural"="water"]({bbox_str});
      way["water"="lake"]({bbox_str});
      relation["water"="lake"]({bbox_str});
      way["waterway"="riverbank"]({bbox_str});
      relation["waterway"="riverbank"]({bbox_str});
    );
    out geom;
    """

    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=120)
    resp.raise_for_status()
    payload = resp.json()

    features = []
    for el in payload.get("elements", []):
        try:
            if el.get("type") == "way" and "geometry" in el:
                coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
                if len(coords) >= 4 and coords[0] == coords[-1]:
                    geom = sg.Polygon(coords)
                    if geom.is_valid and not geom.is_empty:
                        features.append({
                            "geometry": geom,
                            "name": el.get("tags", {}).get("name", ""),
                            "type": el.get("tags", {}).get("natural", "") or
                                    el.get("tags", {}).get("water", ""),
                        })
            elif el.get("type") == "relation" and "members" in el:
                # Assemble multipolygon from outer rings
                outer_polys = []
                for member in el.get("members", []):
                    if member.get("role") == "outer" and "geometry" in member:
                        coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
                        if len(coords) >= 4 and coords[0] == coords[-1]:
                            poly = sg.Polygon(coords)
                            if poly.is_valid:
                                outer_polys.append(poly)
                if outer_polys:
                    geom = sg.MultiPolygon(outer_polys) if len(outer_polys) > 1 else outer_polys[0]
                    features.append({
                        "geometry": geom,
                        "name": el.get("tags", {}).get("name", ""),
                        "type": el.get("tags", {}).get("natural", "") or
                                el.get("tags", {}).get("water", ""),
                    })
        except Exception:
            continue

    if not features:
        return gpd.GeoDataFrame({"geometry": []}, crs="EPSG:4326")

    gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")

    # Filter by area: reproject to equal-area CRS for measurement
    if min_area_sqm > 0:
        gdf_m = gdf.to_crs(5070)  # NAD83 / Conus Albers for CONUS
        gdf = gdf[gdf_m.geometry.area > min_area_sqm].copy()

    if use_cache and not gdf.empty:
        gdf.to_file(cache_path, driver="GPKG")

    return gdf


def render(ax, study_gdf: gpd.GeoDataFrame, *,
           min_area_sqm: float = 100000,
           theme: str | None = None,
           zorder: int = 10) -> bool:
    """Render OSM hydrography as a reference overlay on an existing axes.

    Fetches water from OSM Overpass based on the study area's bounding box,
    clips to the current axes view, and draws with z-order above the data
    layer but below annotations and place labels.

    Returns True if water was rendered, False if unavailable or none found.
    """
    # Get view bounds in study-area CRS, then reproject to WGS84 for OSM query
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    # Use the axes bounds (which may include basemap padding)
    import shapely.geometry as sg
    view_bbox_local = sg.box(xmin, ymin, xmax, ymax)

    # If study CRS isn't lat/lon, reproject the bbox to WGS84 for the OSM query
    if study_gdf.crs and study_gdf.crs.to_epsg() != 4326:
        view_gdf = gpd.GeoDataFrame({"geometry": [view_bbox_local]}, crs=study_gdf.crs)
        bbox_wgs84 = view_gdf.to_crs(4326).total_bounds
    else:
        bbox_wgs84 = view_bbox_local.bounds  # (minx, miny, maxx, maxy)

    try:
        water = fetch_water_osm(tuple(bbox_wgs84), min_area_sqm=min_area_sqm)
    except Exception as e:
        print(f"  water fetch failed: {e}")
        return False

    if water.empty:
        return False

    # Reproject water to study area CRS
    if study_gdf.crs and water.crs != study_gdf.crs:
        water = water.to_crs(study_gdf.crs)

    # Clip to current view
    water = water[water.intersects(view_bbox_local)].copy()
    if water.empty:
        return False

    # Theme-aware palette
    if theme is None:
        theme = basemap_theme_from_ax(ax)
    if theme == "dark":
        fill, edge = "#1a5f7a", "#0a3d52"
    else:
        fill, edge = "#a8d0e6", "#6fa8c4"

    water.plot(ax=ax, color=fill, edgecolor=edge, linewidth=0.4,
               alpha=1.0, zorder=zorder)
    return True


def main() -> int:
    import argparse
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = argparse.ArgumentParser(description="Render OSM hydrography on a map.")
    p.add_argument("input", help="Study area GeoPackage or shapefile (provides bbox)")
    p.add_argument("--layer", help="Layer name for GeoPackage")
    p.add_argument("--min-area-sqm", type=float, default=100000,
                   help="Drop water features smaller than this (sq meters)")
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("-o", "--output", required=True, help="Output PNG path")
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    gdf = gpd.read_file(args.input, layer=args.layer) if args.layer else gpd.read_file(args.input)

    fig, ax = plt.subplots(figsize=(10, 10))
    bg = "#222222" if args.theme == "dark" else "#ffffff"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    study_color = "#888888" if args.theme == "light" else "#aaaaaa"
    gdf.boundary.plot(ax=ax, color=study_color, linewidth=0.5)

    # Seed ax limits from data bounds if no plot has set them yet
    bounds = gdf.total_bounds
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])

    ok = render(ax, gdf, min_area_sqm=args.min_area_sqm, theme=args.theme)

    ax.set_axis_off()
    fig.tight_layout()

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi, bbox_inches="tight")

    print(f"water layer: {'rendered' if ok else 'SKIPPED (no data)'} -> {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
