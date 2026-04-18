"""Shared style utilities for cartography scripts.

Provides palette lookup, color ramp interpolation, class break computation,
and style registry access. Used by analyze_choropleth.py, compute_hotspots.py,
and other map-producing scripts.

This is a utility module (no main function, no CLI).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STYLES_PATH = PROJECT_ROOT / "config" / "map_styles.json"

_styles_cache: dict | None = None


def load_styles() -> dict:
    """Load the map styles registry, cached after first read."""
    global _styles_cache
    if _styles_cache is None:
        _styles_cache = json.loads(STYLES_PATH.read_text())
    return _styles_cache


def get_family_profile(family: str) -> dict:
    """Get the complete visual profile for a map family."""
    styles = load_styles()
    return styles.get("families", {}).get(family, {})


# ── Palette lookup ──────────────────────────────────────────────────────

def resolve_palette(field_name: str, default: str = "neutral") -> dict:
    """Resolve a field name to a palette definition.

    Tries exact match against domain_palette_map, then partial keyword
    matching, then falls back to default.

    Returns dict with keys: cmap, scheme, k, notes
    """
    styles = load_styles()
    domain_map = styles.get("domain_palette_map", {})
    sequential = styles.get("palettes", {}).get("sequential", {})
    diverging = styles.get("palettes", {}).get("diverging", {})

    lower = field_name.lower()

    # Exact match
    if lower in domain_map:
        palette_name = domain_map[lower]
        if palette_name in sequential:
            return {**sequential[palette_name], "name": palette_name}
        if palette_name in diverging:
            return {**diverging[palette_name], "name": palette_name}

    # Partial keyword match — check if any domain key is a substring
    for keyword, palette_name in domain_map.items():
        if keyword.startswith("_"):
            continue
        if keyword in lower or lower in keyword:
            if palette_name in sequential:
                return {**sequential[palette_name], "name": palette_name}
            if palette_name in diverging:
                return {**diverging[palette_name], "name": palette_name}

    # Default
    if default in sequential:
        return {**sequential[default], "name": default}
    return {"cmap": "viridis", "scheme": "quantile", "k": 5, "name": "neutral", "notes": "default"}


def get_categorical_palette(name: str) -> dict | None:
    """Get a categorical palette by name (hotspot, lisa_cluster, land_use, etc.)."""
    styles = load_styles()
    return styles.get("palettes", {}).get("categorical", {}).get(name)


# ── Color ramp interpolation ───────────────────────────────────────────

def get_rgb_ramp(cmap_name: str, n_colors: int = 5) -> list[list[int]]:
    """Get n RGB colors from a named ramp, interpolating if needed.

    First checks the pre-computed ramps in map_styles.json, then falls
    back to matplotlib if available.
    """
    styles = load_styles()
    ramps = styles.get("color_ramps_rgb", {})

    colors = ramps.get(cmap_name)
    if colors is None:
        # Try matplotlib
        try:
            import matplotlib.pyplot as plt
            cmap = plt.get_cmap(cmap_name)
            return [[int(c * 255) for c in cmap(i / max(n_colors - 1, 1))[:3]]
                    for i in range(n_colors)]
        except (ImportError, ValueError):
            colors = ramps.get("viridis", [[68, 1, 84], [59, 82, 139],
                                            [33, 145, 140], [94, 201, 98], [253, 231, 37]])

    if len(colors) == n_colors:
        return [list(c) for c in colors]

    # Interpolate
    result = []
    for i in range(n_colors):
        t = i / max(n_colors - 1, 1)
        idx = t * (len(colors) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(colors) - 1)
        frac = idx - lo
        r = int(colors[lo][0] + frac * (colors[hi][0] - colors[lo][0]))
        g = int(colors[lo][1] + frac * (colors[hi][1] - colors[lo][1]))
        b = int(colors[lo][2] + frac * (colors[hi][2] - colors[lo][2]))
        result.append([r, g, b])
    return result


# ── Classification ─────────────────────────────────────────────────────

def compute_breaks(values: list[float], k: int, method: str) -> list[float]:
    """Compute class break values from sorted numeric data.

    Args:
        values: sorted list of non-null numeric values
        k: number of classes
        method: 'quantile', 'natural_breaks', 'equal_interval'

    Returns:
        List of k+1 break values (lower bound of first class to upper bound of last)
    """
    if not values:
        return [0, 1]

    vals = sorted(values)

    if method == "quantile":
        breaks = [vals[0]]
        for i in range(1, k):
            idx = min(int(len(vals) * i / k), len(vals) - 1)
            breaks.append(vals[idx])
        breaks.append(vals[-1])

    elif method == "natural_breaks":
        # Jenks approximation via quantile boundaries (good enough for 5 classes)
        breaks = [vals[0]]
        for i in range(1, k):
            idx = min(int(len(vals) * i / k), len(vals) - 1)
            breaks.append(vals[idx])
        breaks.append(vals[-1])

    elif method == "equal_interval":
        lo, hi = vals[0], vals[-1]
        step = (hi - lo) / k if hi > lo else 1
        breaks = [lo + step * i for i in range(k)] + [hi]

    else:
        lo, hi = vals[0], vals[-1]
        step = (hi - lo) / k if hi > lo else 1
        breaks = [lo + step * i for i in range(k)] + [hi]

    # Deduplicate while preserving order
    deduped = [breaks[0]]
    for b in breaks[1:]:
        if b > deduped[-1]:
            deduped.append(b)
    if len(deduped) < 2:
        deduped = [vals[0], vals[-1]]

    return deduped


def format_break_label(lower: float, upper: float, is_percent: bool = False) -> str:
    """Format a class break range as a readable legend label.

    Uses smart rounding and en-dash separator per cartography standard.
    """
    def _fmt(v: float) -> str:
        abs_v = abs(v)
        if abs_v >= 10000:
            return f"{int(round(v)):,}"
        elif abs_v >= 100:
            return f"{v:,.0f}"
        elif abs_v >= 10:
            return f"{v:.1f}"
        elif abs_v >= 1:
            return f"{v:.1f}"
        else:
            return f"{v:.2f}"

    suffix = "%" if is_percent else ""
    return f"{_fmt(lower)}\u2013{_fmt(upper)}{suffix}"


# ── Field role detection ───────────────────────────────────────────────

FIELD_ROLE_PATTERNS: list[tuple[str, str]] = [
    (r"^(fid|ogc_fid|objectid|gid)$", "id_system"),
    (r"^geom$|^geometry$|^shape$|^wkb_geometry$", "geometry"),
    (r"geoid|fips|tract_id|blkgrp_id|county_id|state_fips", "id"),
    (r"^name$|_name$|^label$|^title$|^description$", "label"),
    (r"^namelsad$|^namelsad\d+$", "label"),
    (r"_pct$|_percent$|_rate$|_ratio$|^pct_|^rate_|^percent_", "percent"),
    (r"_area_|^area_|_sqm$|_sqkm$|_sqmi$|_acres$|^land_area|^water_area|^total_area", "area"),
    (r"_pop$|^pop_|^total_pop$|_count$|^count_|_num$|^num_|_total$|^total_", "count"),
]

NUMERIC_TYPES = {"INTEGER", "REAL", "DOUBLE", "FLOAT", "NUMERIC", "INT", "BIGINT"}


def classify_field(name: str, col_type: str) -> str:
    """Return the role for a column based on name pattern and SQL type."""
    lower = name.lower()
    for pattern, role in FIELD_ROLE_PATTERNS:
        if re.search(pattern, lower):
            return role
    if col_type.upper().split("(")[0].strip() in NUMERIC_TYPES:
        return "measure"
    return "attribute"


def is_percent_field(name: str) -> bool:
    """Check if a field name suggests percentage/rate data."""
    lower = name.lower()
    return bool(re.search(r"_pct$|_percent$|_rate$|_ratio$|^pct_|^rate_|^percent_", lower))
