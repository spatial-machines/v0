"""Shared helpers for composable map-layer scripts.

Each layer script exports a `render(ax, gdf, **kwargs)` function and a CLI.
The CLI creates its own figure when called standalone; `render()` can be
called from another script that already has a matplotlib axes.

This module provides the utilities those layer scripts need in common.
"""
from __future__ import annotations

from pathlib import Path


def font_chain(family_str: str) -> list[str]:
    """Parse a comma-separated font fallback chain into a list for matplotlib."""
    if not family_str:
        return ["sans-serif"]
    return [f.strip().strip('"').strip("'") for f in family_str.split(",") if f.strip()]


def detect_fips(gdf) -> tuple[str | None, str | None]:
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


def load_map_styles() -> dict:
    """Load the unified map style registry."""
    import json
    path = Path(__file__).resolve().parents[3] / "config" / "map_styles.json"
    return json.loads(path.read_text(encoding="utf-8"))


def basemap_theme_from_ax(ax) -> str:
    """Infer basemap theme (light/dark) from the axes background color."""
    # Crude but effective: if background is darker than mid-gray, treat as dark
    try:
        import matplotlib.colors as mcolors
        bg = ax.get_facecolor()
        r, g, b, _ = mcolors.to_rgba(bg)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return "dark" if luminance < 0.5 else "light"
    except Exception:
        return "light"
