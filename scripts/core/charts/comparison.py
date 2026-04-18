"""Comparison charts: bar, grouped_bar, lollipop, dot.

Compare values across categories or geographies. Sorting and top-N
defaults come from config/chart_styles.json families.comparison.sort.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from . import _base

FAMILY = "comparison"
KINDS = ("bar", "grouped_bar", "lollipop", "dot")


def render(
    data: str | Path | "Any",
    *,
    category_field: str,
    value_field: str | None = None,
    value_fields: Sequence[str] | None = None,
    kind: str = "bar",
    output: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
    top_n: int | None = None,
    sort: str | None = None,
    horizontal: bool = True,
    layer: str | None = None,
) -> dict:
    import numpy as np

    if kind not in KINDS:
        raise ValueError(f"Unknown comparison kind: {kind!r}. Valid: {KINDS}")
    if kind == "grouped_bar" and not value_fields:
        raise ValueError("grouped_bar requires value_fields=[...]")
    if kind != "grouped_bar" and not value_field:
        raise ValueError(f"{kind} requires value_field=...")

    df = data if hasattr(data, "columns") else _base.load_series(data, layer=layer)
    for col in [category_field] + list(value_fields or [value_field]):
        if col not in df.columns:
            raise KeyError(f"Field {col!r} not in columns")

    profile = _base.family_profile(FAMILY)
    sort_cfg = profile.get("sort", {})
    if sort is None:
        sort = sort_cfg.get("default", "descending")
    if top_n is None:
        top_n = sort_cfg.get("top_n", 25)

    if kind == "grouped_bar":
        work = df[[category_field] + list(value_fields)].dropna(subset=list(value_fields), how="all")
        work["__total"] = work[list(value_fields)].sum(axis=1)
        sort_key = "__total"
    else:
        work = df[[category_field, value_field]].dropna(subset=[value_field])
        sort_key = value_field

    if sort == "descending":
        work = work.sort_values(sort_key, ascending=False)
    elif sort == "ascending":
        work = work.sort_values(sort_key, ascending=True)
    if top_n and len(work) > top_n:
        work = work.head(top_n) if sort == "descending" else work.tail(top_n)

    plt = _base.apply_theme(FAMILY)
    fig, ax = plt.subplots(figsize=profile["figure"]["size"])

    cmap = _base.resolve_cmap_for_field(value_field or (value_fields[0] if value_fields else None), FAMILY)
    primary = plt.get_cmap(cmap)(0.65)
    cats = work[category_field].astype(str).tolist()

    if kind == "bar":
        vals = work[value_field].to_numpy()
        if horizontal:
            y = np.arange(len(cats))
            ax.barh(y, vals, color=primary, edgecolor="#ffffff", linewidth=0.6, zorder=2)
            ax.set_yticks(y); ax.set_yticklabels(cats)
            ax.invert_yaxis()
            ax.set_xlabel(value_field); ax.set_ylabel(category_field)
            _base.format_tick_labels(ax, axis="x")
        else:
            x = np.arange(len(cats))
            ax.bar(x, vals, color=primary, edgecolor="#ffffff", linewidth=0.6, zorder=2)
            ax.set_xticks(x); ax.set_xticklabels(cats, rotation=45, ha="right")
            ax.set_ylabel(value_field); ax.set_xlabel(category_field)
            _base.format_tick_labels(ax, axis="y")

    elif kind == "grouped_bar":
        categorical = _base.categorical_palette("qualitative")
        n_groups = len(value_fields)
        width = 0.8 / n_groups
        x = np.arange(len(cats))
        for i, vf in enumerate(value_fields):
            offset = (i - (n_groups - 1) / 2) * width
            ax.bar(x + offset, work[vf].to_numpy(), width,
                   color=categorical[i % len(categorical)],
                   edgecolor="#ffffff", linewidth=0.4, label=vf, zorder=2)
        ax.set_xticks(x); ax.set_xticklabels(cats, rotation=45, ha="right")
        ax.set_xlabel(category_field); ax.set_ylabel("Value")
        ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#cccccc")
        _base.format_tick_labels(ax, axis="y")

    elif kind == "lollipop":
        vals = work[value_field].to_numpy()
        y = np.arange(len(cats))
        # Highlight top 3 with accent color, rest muted
        n_highlight = min(3, len(vals))
        colors = ["#c04040" if i < n_highlight else primary for i in range(len(vals))]
        ax.hlines(y, 0, vals, color="#cccccc", linewidth=1.4, zorder=1)
        ax.scatter(vals, y, color=colors, s=55, edgecolor="#1a1a1a",
                   linewidth=0.5, zorder=3)
        # Value labels at end of each stem
        is_pct = _base.is_percent_field(value_field) if hasattr(_base, "is_percent_field") else "rate" in value_field.lower() or "pct" in value_field.lower()
        for i, (v, yi) in enumerate(zip(vals, y)):
            label = f"{v:.1f}%" if is_pct else f"{v:,.1f}"
            ax.text(v + (max(vals) * 0.02), yi, label,
                    va="center", fontsize=7.5, color="#333333",
                    fontweight="bold" if i < n_highlight else "normal")
        ax.set_yticks(y); ax.set_yticklabels(cats)
        ax.invert_yaxis()
        ax.set_xlabel(value_field); ax.set_ylabel(category_field)
        _base.format_tick_labels(ax, axis="x")

    elif kind == "dot":
        vals = work[value_field].to_numpy()
        y = np.arange(len(cats))
        ax.scatter(vals, y, color=primary, s=60, edgecolor="#1a1a1a",
                   linewidth=0.5, zorder=3)
        ax.set_yticks(y); ax.set_yticklabels(cats)
        ax.invert_yaxis()
        ax.set_xlabel(value_field); ax.set_ylabel(category_field)
        _base.format_tick_labels(ax, axis="x")

    _base.style_axes(ax, FAMILY)
    fig.subplots_adjust(top=0.86, bottom=0.18, left=0.22, right=0.97)
    effective_title = title or (
        f"{value_field} by {category_field}" if kind != "grouped_bar"
        else f"{category_field}: {', '.join(value_fields)}"
    )
    effective_subtitle = subtitle or f"n = {len(work):,} · kind = {kind}"
    _base.add_chart_chrome(fig, title=effective_title, subtitle=effective_subtitle,
                           attribution=attribution)

    extra = {"n": int(len(work)), "top_n": int(top_n or 0), "sort": sort}
    if kind == "grouped_bar":
        extra["value_fields"] = list(value_fields)

    return _base.save_chart(
        fig, output,
        family=FAMILY, kind=kind,
        field=value_field or (value_fields[0] if value_fields else None),
        title=effective_title, subtitle=effective_subtitle,
        attribution=attribution, palette=cmap,
        extra_sidecar=extra,
    )
