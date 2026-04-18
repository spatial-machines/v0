"""Time series charts: line, area, small_multiples.

Temporal change narratives. Expects a time field (year/date) plus one or
more value fields; small_multiples accepts a panel_field for grid layout.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from . import _base

FAMILY = "timeseries"
KINDS = ("line", "area", "small_multiples")


def render(
    data: str | Path | "Any",
    *,
    time_field: str,
    value_field: str | None = None,
    value_fields: Sequence[str] | None = None,
    panel_field: str | None = None,
    kind: str = "line",
    output: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
    layer: str | None = None,
) -> dict:
    import numpy as np
    import pandas as pd

    if kind not in KINDS:
        raise ValueError(f"Unknown timeseries kind: {kind!r}. Valid: {KINDS}")
    if kind == "small_multiples" and not panel_field:
        raise ValueError("small_multiples requires panel_field=...")
    if kind != "small_multiples" and not (value_field or value_fields):
        raise ValueError(f"{kind} requires value_field or value_fields")

    df = data if hasattr(data, "columns") else _base.load_series(data, layer=layer)

    # Parse time
    try:
        df = df.copy()
        df[time_field] = pd.to_datetime(df[time_field], errors="raise")
        time_is_date = True
    except (ValueError, TypeError):
        time_is_date = False

    plt = _base.apply_theme(FAMILY)
    profile = _base.family_profile(FAMILY)
    line_cfg = profile.get("line", {})
    categorical = _base.categorical_palette("qualitative")

    if kind == "small_multiples":
        field_to_plot = value_field or value_fields[0]
        panels = sorted(df[panel_field].dropna().unique())
        n = len(panels)
        ncols = min(4, max(1, int(np.ceil(np.sqrt(n)))))
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(3.2 * ncols + 1.5, 2.6 * nrows + 1.2),
                                 sharex=True, sharey=True)
        axes_flat = np.atleast_1d(axes).flatten()
        cmap = _base.resolve_cmap_for_field(field_to_plot, FAMILY)
        color = plt.get_cmap(cmap)(0.6)
        for ax_i, panel in zip(axes_flat, panels):
            sub = df[df[panel_field] == panel].sort_values(time_field)
            ax_i.plot(sub[time_field], sub[field_to_plot],
                      color=color,
                      linewidth=line_cfg.get("linewidth", 1.6),
                      marker=line_cfg.get("marker", "o"),
                      markersize=line_cfg.get("marker_size", 3),
                      zorder=2)
            ax_i.set_title(str(panel), fontsize=9.5, color="#333333")
            _base.style_axes(ax_i, FAMILY)
        for ax_extra in axes_flat[n:]:
            ax_extra.axis("off")
        fig.text(0.5, 0.02, time_field, ha="center", fontsize=10, color="#333")
        fig.text(0.01, 0.5, field_to_plot, va="center", rotation=90, fontsize=10, color="#333")
        fig.subplots_adjust(top=0.88, bottom=0.1, left=0.06, right=0.98, wspace=0.15, hspace=0.35)
        effective_title = title or f"{field_to_plot} over {time_field}, by {panel_field}"
        effective_subtitle = subtitle or f"{n} panels"
        _base.add_chart_chrome(
            fig,
            title=effective_title, subtitle=effective_subtitle,
            attribution=attribution,
        )
        extra = {"panel_field": panel_field, "n_panels": int(n),
                 "value_field": field_to_plot, "time_is_date": bool(time_is_date)}
        return _base.save_chart(
            fig, output,
            family=FAMILY, kind=kind,
            field=field_to_plot,
            title=effective_title, subtitle=effective_subtitle,
            attribution=attribution, palette=cmap, extra_sidecar=extra,
        )

    fig, ax = plt.subplots(figsize=profile["figure"]["size"])
    fields = list(value_fields) if value_fields else [value_field]
    cmap = _base.resolve_cmap_for_field(fields[0], FAMILY)
    sorted_df = df.sort_values(time_field)

    for i, vf in enumerate(fields):
        color = categorical[i % len(categorical)] if len(fields) > 1 else plt.get_cmap(cmap)(0.6)
        xs = sorted_df[time_field]
        ys = sorted_df[vf]
        if kind == "area":
            ax.fill_between(xs, 0, ys, color=color,
                            alpha=0.35 if len(fields) > 1 else 0.55, zorder=1)
        ax.plot(xs, ys, color=color,
                linewidth=line_cfg.get("linewidth", 2.0),
                marker=line_cfg.get("marker", "o"),
                markersize=line_cfg.get("marker_size", 4),
                label=vf, zorder=2)

    ax.set_xlabel(time_field)
    ax.set_ylabel(fields[0] if len(fields) == 1 else "Value")
    if len(fields) > 1:
        ax.legend(loc="best", frameon=True, framealpha=0.92, edgecolor="#cccccc")
    _base.style_axes(ax, FAMILY)
    _base.format_tick_labels(ax, axis="y")
    fig.autofmt_xdate() if time_is_date else None
    fig.subplots_adjust(top=0.86, bottom=0.14, left=0.08, right=0.97)
    effective_title = title or (
        f"{fields[0]} over {time_field}" if len(fields) == 1
        else f"Trends over {time_field}"
    )
    effective_subtitle = subtitle or f"n = {len(sorted_df):,} · kind = {kind}"
    _base.add_chart_chrome(
        fig,
        title=effective_title, subtitle=effective_subtitle,
        attribution=attribution,
    )
    return _base.save_chart(
        fig, output,
        family=FAMILY, kind=kind,
        field=fields[0],
        title=effective_title, subtitle=effective_subtitle,
        attribution=attribution, palette=cmap,
        extra_sidecar={"time_field": time_field, "value_fields": fields,
                       "time_is_date": bool(time_is_date),
                       "n": int(len(sorted_df))},
    )
