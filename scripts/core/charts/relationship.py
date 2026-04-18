"""Relationship charts: scatter, scatter_ols, hexbin, correlation_heatmap.

Bivariate / multivariate relationships. Pairs with bivariate maps.
Uses statsmodels for OLS trendlines when available; falls back to numpy
polyfit otherwise.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from . import _base

FAMILY = "relationship"
KINDS = ("scatter", "scatter_ols", "hexbin", "correlation_heatmap")


def _fit_ols(x, y):
    import numpy as np
    try:
        import statsmodels.api as sm
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        xs = np.linspace(x.min(), x.max(), 200)
        pred = model.get_prediction(sm.add_constant(xs))
        ci = pred.conf_int(alpha=0.05)
        return {
            "xs": xs,
            "ys": pred.predicted_mean,
            "lower": ci[:, 0],
            "upper": ci[:, 1],
            "r2": float(model.rsquared),
            "slope": float(model.params[1]),
            "intercept": float(model.params[0]),
            "p_value": float(model.pvalues[1]),
        }
    except ImportError:
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 200)
        ys = slope * xs + intercept
        ss_res = ((y - (slope * x + intercept)) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
        return {"xs": xs, "ys": ys, "lower": None, "upper": None,
                "r2": float(r2), "slope": float(slope),
                "intercept": float(intercept), "p_value": None}


def render(
    data: str | Path | "Any",
    *,
    x_field: str | None = None,
    y_field: str | None = None,
    fields: Sequence[str] | None = None,
    kind: str = "scatter",
    output: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
    gridsize: int = 30,
    layer: str | None = None,
) -> dict:
    import numpy as np

    if kind not in KINDS:
        raise ValueError(f"Unknown relationship kind: {kind!r}. Valid: {KINDS}")
    if kind == "correlation_heatmap" and not fields:
        raise ValueError("correlation_heatmap requires fields=[...]")
    if kind != "correlation_heatmap" and not (x_field and y_field):
        raise ValueError(f"{kind} requires x_field and y_field")

    df = data if hasattr(data, "columns") else _base.load_series(data, layer=layer)

    plt = _base.apply_theme(FAMILY)
    profile = _base.family_profile(FAMILY)

    if kind == "correlation_heatmap":
        sub = df[list(fields)].apply(lambda s: s.astype(float) if s.dtype != object else s)
        corr = sub.corr(numeric_only=True).to_numpy()
        labels = list(sub.select_dtypes(include="number").columns)
        size = max(profile["figure"]["size"][0], 0.55 * len(labels) + 2)
        fig, ax = plt.subplots(figsize=(size, size))
        cmap = _base.resolve_cmap_for_field("correlation", FAMILY)
        im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1, aspect="equal")
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        for i in range(len(labels)):
            for j in range(len(labels)):
                v = corr[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=8,
                        color="#ffffff" if abs(v) > 0.55 else "#222222")
        cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.ax.set_ylabel("Pearson r", fontsize=9, color="#333333")
        ax.set_title("")
        fig.subplots_adjust(top=0.88, bottom=0.22, left=0.22, right=0.97)
        effective_title = title or "Correlation heatmap"
        effective_subtitle = subtitle or f"{len(labels)} variables · Pearson"
        _base.add_chart_chrome(
            fig,
            title=effective_title, subtitle=effective_subtitle,
            attribution=attribution,
        )
        return _base.save_chart(
            fig, output,
            family=FAMILY, kind=kind,
            title=effective_title, subtitle=effective_subtitle,
            attribution=attribution, palette=cmap,
            extra_sidecar={"fields": list(labels), "n_variables": len(labels)},
        )

    work = df[[x_field, y_field]].dropna()
    x = work[x_field].to_numpy(dtype=float)
    y = work[y_field].to_numpy(dtype=float)
    cmap = _base.resolve_cmap_for_field(y_field, FAMILY)

    fig, ax = plt.subplots(figsize=profile["figure"]["size"])

    if kind == "hexbin":
        hb = ax.hexbin(x, y, gridsize=gridsize, cmap=cmap, mincnt=1, linewidths=0)
        cbar = fig.colorbar(hb, ax=ax, shrink=0.85, pad=0.02)
        cbar.ax.set_ylabel("Count", fontsize=9, color="#333333")
        extra = {"gridsize": int(gridsize), "n": int(len(work))}
    else:
        scfg = profile.get("scatter", {})
        ax.scatter(
            x, y,
            s=scfg.get("size", 28),
            alpha=scfg.get("alpha", 0.65),
            color=plt.get_cmap(cmap)(0.55),
            edgecolor=scfg.get("edgecolor", "#1a1a1a"),
            linewidth=scfg.get("edgewidth", 0.3),
            zorder=2,
        )
        extra = {"n": int(len(work))}
        if kind == "scatter_ols":
            fit = _fit_ols(x, y)
            ols_cfg = profile.get("ols", {})
            ax.plot(fit["xs"], fit["ys"], color=ols_cfg.get("line_color", "#c04040"),
                    linewidth=1.8, zorder=3,
                    label=f"OLS  R² = {fit['r2']:.3f}")
            if fit["lower"] is not None:
                ax.fill_between(fit["xs"], fit["lower"], fit["upper"],
                                color=ols_cfg.get("band_color", "#c04040"),
                                alpha=ols_cfg.get("band_alpha", 0.15), zorder=1)
            ax.legend(loc="best", frameon=True, framealpha=0.92, edgecolor="#cccccc")
            extra.update({k: fit[k] for k in ("r2", "slope", "intercept", "p_value")
                          if fit[k] is not None})

    ax.set_xlabel(x_field)
    ax.set_ylabel(y_field)
    _base.style_axes(ax, FAMILY)
    _base.format_tick_labels(ax, axis="x")
    _base.format_tick_labels(ax, axis="y")
    fig.subplots_adjust(top=0.86, bottom=0.13, left=0.11, right=0.97)
    effective_title = title or f"{y_field} vs. {x_field}"
    effective_subtitle = subtitle or f"n = {len(work):,} · kind = {kind}"
    _base.add_chart_chrome(
        fig,
        title=effective_title, subtitle=effective_subtitle,
        attribution=attribution,
    )
    return _base.save_chart(
        fig, output,
        family=FAMILY, kind=kind,
        field=y_field, title=effective_title, subtitle=effective_subtitle,
        attribution=attribution, palette=cmap,
        extra_sidecar={"x_field": x_field, "y_field": y_field, **extra},
    )
