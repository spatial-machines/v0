"""Distribution charts: histogram, KDE, box, violin.

Shows the shape of a single numeric variable. Pair with a choropleth to
reveal skew and outliers the map alone may hide.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import _base

FAMILY = "distribution"
KINDS = ("histogram", "kde", "box", "violin")


def _mean_median_lines(ax, values, profile):
    import numpy as np
    from scipy.stats import skew as _skew

    cfg = profile.get("annotations", {})
    y_top = ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1

    if cfg.get("mean_line"):
        m = float(np.nanmean(values))
        ax.axvline(m, color=cfg.get("mean_color", "#c04040"),
                   linestyle="--", linewidth=1.1, label=f"Mean = {m:,.2f}")
        ax.annotate(f"Mean\n{m:,.1f}", xy=(m, y_top * 0.92),
                    fontsize=8, fontweight="bold", color=cfg.get("mean_color", "#c04040"),
                    ha="center", va="top",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor=cfg.get("mean_color", "#c04040"), alpha=0.9))

    if cfg.get("median_line"):
        med = float(np.nanmedian(values))
        ax.axvline(med, color=cfg.get("median_color", "#1f4e79"),
                   linestyle=":", linewidth=1.1, label=f"Median = {med:,.2f}")
        ax.annotate(f"Median\n{med:,.1f}", xy=(med, y_top * 0.78),
                    fontsize=8, fontweight="bold", color=cfg.get("median_color", "#1f4e79"),
                    ha="center", va="top",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor=cfg.get("median_color", "#1f4e79"), alpha=0.9))

    # Skewness callout for right-skewed distributions
    try:
        sk = float(_skew(values, nan_policy="omit"))
        if sk > 1.0:
            p90 = float(np.nanpercentile(values, 90))
            ax.annotate(f"Right-skewed (skew = {sk:.2f})\nLong tail indicates outlier tracts",
                        xy=(p90, y_top * 0.5), fontsize=7.5, fontstyle="italic",
                        color="#666666", ha="left", va="center",
                        arrowprops=dict(arrowstyle="->", color="#999999", lw=0.7),
                        xytext=(p90 + (values.max() - values.min()) * 0.05, y_top * 0.65))
    except Exception:
        pass


def render(
    data: str | Path | "Any",
    *,
    field: str,
    kind: str = "histogram",
    output: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
    bins: int = 30,
    layer: str | None = None,
) -> dict:
    import numpy as np

    if kind not in KINDS:
        raise ValueError(f"Unknown distribution kind: {kind!r}. Valid: {KINDS}")

    df = data if hasattr(data, "columns") else _base.load_series(data, field=field, layer=layer)
    values = df[field].dropna().to_numpy()
    if values.size == 0:
        raise ValueError(f"Field {field!r} has no non-null values")

    plt = _base.apply_theme(FAMILY)
    profile = _base.family_profile(FAMILY)
    fig, ax = plt.subplots(figsize=profile["figure"]["size"])

    cmap = _base.resolve_cmap_for_field(field, FAMILY)
    primary_color = plt.get_cmap(cmap)(0.65)

    if kind in ("histogram", "kde"):
        n, edges, _ = ax.hist(
            values, bins=bins, color=primary_color,
            edgecolor="#ffffff", linewidth=0.6, alpha=0.9, zorder=2,
        )
        if kind == "kde":
            try:
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(values)
                xs = np.linspace(values.min(), values.max(), 256)
                scale = (edges[1] - edges[0]) * values.size
                ax.plot(xs, kde(xs) * scale, color="#222222", linewidth=1.6, zorder=3)
            except ImportError:
                pass
        _mean_median_lines(ax, values, profile)
        ax.set_xlabel(field)
        ax.set_ylabel("Count")
        ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#cccccc")
    elif kind == "box":
        bp = ax.boxplot(
            values, vert=False, widths=0.55, patch_artist=True,
            boxprops=dict(facecolor=primary_color, edgecolor="#333333", linewidth=0.9),
            medianprops=dict(color="#1f4e79", linewidth=1.6),
            whiskerprops=dict(color="#333333", linewidth=0.9),
            capprops=dict(color="#333333", linewidth=0.9),
            flierprops=dict(marker="o", markerfacecolor="#c04040",
                            markersize=4, markeredgecolor="#333333", alpha=0.75),
        )
        ax.set_xlabel(field)
        ax.set_yticks([])
    elif kind == "violin":
        parts = ax.violinplot(values, vert=False, widths=0.75, showmeans=True,
                              showmedians=True, showextrema=True)
        for body in parts["bodies"]:
            body.set_facecolor(primary_color)
            body.set_edgecolor("#333333")
            body.set_alpha(0.85)
        for key in ("cbars", "cmins", "cmaxes", "cmeans", "cmedians"):
            if key in parts:
                parts[key].set_color("#333333")
                parts[key].set_linewidth(0.9)
        ax.set_xlabel(field)
        ax.set_yticks([])

    _base.style_axes(ax, FAMILY)
    _base.format_tick_labels(ax, axis="x")
    if kind in ("histogram", "kde"):
        _base.format_tick_labels(ax, axis="y")

    fig.subplots_adjust(top=0.86, bottom=0.14, left=0.08, right=0.97)
    effective_title = title or f"Distribution of {field}"
    effective_subtitle = subtitle or f"n = {values.size:,} · kind = {kind}"
    _base.add_chart_chrome(
        fig,
        title=effective_title,
        subtitle=effective_subtitle,
        attribution=attribution,
    )

    return _base.save_chart(
        fig, output,
        family=FAMILY, kind=kind,
        field=field, title=effective_title, subtitle=effective_subtitle,
        attribution=attribution, palette=cmap,
        extra_sidecar={"n": int(values.size),
                       "mean": float(np.nanmean(values)),
                       "median": float(np.nanmedian(values)),
                       "std": float(np.nanstd(values))},
    )
