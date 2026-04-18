"""Shared formatting utilities for GIS analysis outputs."""
from __future__ import annotations


def smart_round(value: float, field_name: str = "") -> float | int:
    """Round a value based on what the field name suggests it contains."""
    fn = field_name.lower()
    if any(k in fn for k in ("rate", "pct", "percent", "ratio", "proportion")):
        return round(value, 2)
    elif any(k in fn for k in ("income", "cost", "price", "rent", "value", "median_h")):
        return int(round(value))
    elif any(k in fn for k in ("count", "total", "pop", "universe", "number")):
        return int(round(value))
    elif abs(value) >= 1000:
        return int(round(value))
    elif abs(value) >= 1:
        return round(value, 1)
    else:
        return round(value, 2)


def auto_label(field_name: str, override: str | None = None) -> str:
    """Convert a snake_case field name to a human-readable label with units."""
    if override:
        return override
    fn = field_name.lower()
    nice = field_name.replace("_", " ").title()
    # Clean up common abbreviations BEFORE adding units
    nice = nice.replace("Pct ", "% ").replace(" Pct", "")
    nice = nice.replace("Per Sqkm", "per sq km").replace("Sqkm", "sq km")
    nice = nice.replace("Nh ", "")
    # Add units based on field semantics
    if any(k in fn for k in ("rate", "pct", "percent")):
        if "%" not in nice:
            return f"{nice} (%)"
        return nice
    elif any(k in fn for k in ("income", "rent", "cost", "price", "value")):
        return f"{nice} ($)"
    elif any(k in fn for k in ("pop", "count", "total", "number", "universe")):
        return f"{nice} (count)"
    elif "per sq km" in nice:
        return nice  # already has unit info
    return nice


def fmt_legend_val(v: float) -> str:
    """Format a value for map legends with smart precision."""
    abs_v = abs(v)
    if abs_v >= 1000:
        return f"{int(round(v)):,}"
    elif abs_v >= 10:
        return f"{v:.0f}"
    elif abs_v >= 1:
        return f"{v:.1f}"
    else:
        return f"{v:.2f}"
