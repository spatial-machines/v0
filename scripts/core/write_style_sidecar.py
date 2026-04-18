#!/usr/bin/env python3
"""Write a styling metadata sidecar (.style.json) for a map output.

The style sidecar records exactly what cartographic decisions were made —
palette, classification, breaks, colors, field, family — so downstream
consumers (QGIS packaging, web maps, reports) can reproduce the same
visual treatment.

This is called by cartography scripts after producing a map. It can also
be called standalone to document styling decisions for manually-created maps.

Usage:
    # Called by other scripts (typical):
    from write_style_sidecar import write_style_sidecar
    write_style_sidecar(
        output_path="outputs/maps/poverty_choropleth.png",
        map_family="thematic_choropleth",
        field="poverty_rate",
        palette="YlOrRd",
        scheme="natural_breaks",
        k=5,
        breaks=[0, 8.2, 14.7, 22.1, 33.5, 58.9],
        colors=[[255,255,178], [254,217,118], [254,178,76], [253,141,60], [240,59,32]],
        title="Poverty Rate by Census Tract, Douglas County, NE (2022)",
        legend_title="Poverty Rate (%)",
        attribution="U.S. Census Bureau ACS 5-Year, 2022",
        crs="EPSG:4269",
        source_gpkg="data/processed/tracts.gpkg",
        layer_name="tracts",
    )

    # Standalone CLI:
    python scripts/core/write_style_sidecar.py \
        --map-path outputs/maps/poverty_choropleth.png \
        --family thematic_choropleth \
        --field poverty_rate \
        --palette YlOrRd \
        --scheme natural_breaks \
        --k 5 \
        --title "Poverty Rate by Census Tract"
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path


def write_style_sidecar(
    output_path: str | Path,
    map_family: str,
    field: str | None = None,
    palette: str | None = None,
    scheme: str | None = None,
    k: int | None = None,
    breaks: list[float] | None = None,
    colors: list[list[int]] | None = None,
    title: str | None = None,
    legend_title: str | None = None,
    attribution: str | None = None,
    crs: str | None = None,
    source_gpkg: str | None = None,
    layer_name: str | None = None,
    categorical_map: dict | None = None,
    pattern: str | None = None,
    extra: dict | None = None,
) -> Path:
    """Write a .style.json sidecar alongside a map output.

    Returns the path to the written sidecar file.
    """
    out = Path(output_path)
    sidecar_path = out.with_suffix(".style.json")

    style: dict = {
        "version": 1,
        "map_path": str(out.name),
        "map_family": map_family,
        "created_at": datetime.now(UTC).isoformat(),
    }

    if field:
        style["field"] = field
    if palette:
        style["palette"] = palette
    if scheme:
        style["scheme"] = scheme
    if k is not None:
        style["k"] = k
    if breaks:
        style["breaks"] = breaks
    if colors:
        style["colors_rgb"] = colors
    if title:
        style["title"] = title
    if legend_title:
        style["legend_title"] = legend_title
    if attribution:
        style["attribution"] = attribution
    if crs:
        style["crs"] = crs
    if source_gpkg:
        style["source_gpkg"] = str(source_gpkg)
    if layer_name:
        style["layer_name"] = layer_name
    if categorical_map:
        style["categorical_map"] = categorical_map
    if pattern:
        style["pattern"] = pattern
    if extra:
        style.update(extra)

    sidecar_path.write_text(json.dumps(style, indent=2))
    return sidecar_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Write a styling metadata sidecar for a map output."
    )
    parser.add_argument("--map-path", required=True, help="Path to the map file (PNG)")
    parser.add_argument("--family", required=True,
                        choices=["thematic_choropleth", "thematic_categorical",
                                 "point_overlay", "reference", "raster_surface"],
                        help="Map family")
    parser.add_argument("--field", help="Thematic field name")
    parser.add_argument("--palette", help="Palette name from map_styles.json")
    parser.add_argument("--scheme", help="Classification scheme (natural_breaks, quantile, equal_interval)")
    parser.add_argument("--k", type=int, help="Number of classes")
    parser.add_argument("--title", help="Map title")
    parser.add_argument("--legend-title", help="Legend title")
    parser.add_argument("--attribution", help="Data source attribution")
    parser.add_argument("--crs", help="CRS (e.g. EPSG:4269)")
    parser.add_argument("--source-gpkg", help="Source GeoPackage path")
    parser.add_argument("--layer-name", help="Layer name within GeoPackage")
    args = parser.parse_args()

    path = write_style_sidecar(
        output_path=args.map_path,
        map_family=args.family,
        field=args.field,
        palette=args.palette,
        scheme=args.scheme,
        k=args.k,
        title=args.title,
        legend_title=args.legend_title,
        attribution=args.attribution,
        crs=args.crs,
        source_gpkg=args.source_gpkg,
        layer_name=args.layer_name,
    )
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
