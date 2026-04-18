"""Shared chart theming, palette resolution, and output helpers.

Design goals:
  - One place to load config/chart_styles.json + config/map_styles.json.
  - Palette routing mirrors cartography: a field name resolves through
    domain_palette_map -> sequential/diverging palette -> cmap.
    When no field match, fall back to family default palette.
  - Save paired PNG (200 DPI) + SVG + .style.json sidecar so downstream
    consumers (report-writer, ArcGIS Online, QGIS manifest) can pick up
    charts the same way they pick up maps.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
SCRIPTS_CORE = Path(__file__).resolve().parents[1]
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))


_CHART_STYLES_CACHE: dict | None = None
_MAP_STYLES_CACHE: dict | None = None
_PALETTES_CACHE: dict | None = None


def load_chart_styles() -> dict:
    global _CHART_STYLES_CACHE
    if _CHART_STYLES_CACHE is None:
        with (CONFIG_DIR / "chart_styles.json").open() as f:
            _CHART_STYLES_CACHE = json.load(f)
    return _CHART_STYLES_CACHE


def load_map_styles() -> dict:
    global _MAP_STYLES_CACHE
    if _MAP_STYLES_CACHE is None:
        path = CONFIG_DIR / "map_styles.json"
        if path.exists():
            with path.open() as f:
                _MAP_STYLES_CACHE = json.load(f)
        else:
            _MAP_STYLES_CACHE = {}
    return _MAP_STYLES_CACHE


def load_palettes() -> dict:
    global _PALETTES_CACHE
    if _PALETTES_CACHE is None:
        path = CONFIG_DIR / "palettes.json"
        if path.exists():
            with path.open() as f:
                _PALETTES_CACHE = json.load(f)
        else:
            _PALETTES_CACHE = {}
    return _PALETTES_CACHE


def family_profile(family: str) -> dict:
    styles = load_chart_styles()
    if family not in styles.get("families", {}):
        raise ValueError(
            f"Unknown chart family: {family!r}. "
            f"Valid: {sorted(styles.get('families', {}).keys())}"
        )
    return styles["families"][family]


def resolve_cmap_for_field(field: str | None, family: str) -> str:
    """Resolve a matplotlib colormap from a field name, mirroring cartography.

    Order of precedence:
      1. Exact match in map_styles.domain_palette_map -> sequential/diverging cmap
      2. Substring match (e.g., 'pct_poverty' contains 'poverty')
      3. Family default palette from chart_styles.families[family].default_palette
    """
    profile = family_profile(family)
    default = profile.get("default_palette", "neutral")

    if not field:
        return _cmap_from_alias(default)

    map_styles = load_map_styles()
    dpm = map_styles.get("domain_palette_map", {})
    field_l = field.lower()

    if field_l in dpm:
        return _cmap_from_alias(dpm[field_l])

    for key, alias in dpm.items():
        if key.startswith("_"):
            continue
        if key in field_l:
            return _cmap_from_alias(alias)

    return _cmap_from_alias(default)


def _cmap_from_alias(alias: str) -> str:
    """Resolve a palette alias (e.g. 'poverty') to a matplotlib cmap name."""
    if not alias:
        return "viridis"
    map_styles = load_map_styles()
    palettes = map_styles.get("palettes", {})
    for group_name in ("sequential", "diverging"):
        group = palettes.get(group_name, {})
        if alias in group and isinstance(group[alias], dict) and "cmap" in group[alias]:
            return group[alias]["cmap"]

    legacy = load_palettes()
    if alias in legacy and isinstance(legacy[alias], dict) and "cmap" in legacy[alias]:
        return legacy[alias]["cmap"]

    return alias


def categorical_palette(name: str = "qualitative") -> list[str]:
    """Resolve a categorical palette by name.

    Lookup order:
      1. config/palettes.json → `categorical.<name>` (authoritative)
      2. config/chart_styles.json → `palettes_categorical.<name>` (local copy)
      3. Built-in matplotlib tab10 fallback
    """
    palettes = load_palettes()
    categorical = palettes.get("categorical", {}) if isinstance(palettes, dict) else {}
    if name in categorical and isinstance(categorical[name], list):
        return list(categorical[name])

    styles = load_chart_styles()
    chart_cat = styles.get("palettes_categorical", {})
    if name in chart_cat and isinstance(chart_cat[name], list):
        return list(chart_cat[name])

    return ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f"]


def apply_theme(family: str):
    """Apply matplotlib rcParams for a chart family. Returns the mpl module.

    Import is deferred so the rest of the pipeline doesn't pay matplotlib
    import cost when charts aren't in use.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    styles = load_chart_styles()
    profile = family_profile(family)
    typo = styles.get("typography", {})
    fig = profile.get("figure", {})

    plt.rcParams.update({
        "figure.dpi": fig.get("dpi", 200),
        "savefig.dpi": fig.get("dpi", 200),
        "figure.facecolor": fig.get("background", "#ffffff"),
        "axes.facecolor": fig.get("background", "#ffffff"),
        "savefig.facecolor": fig.get("background", "#ffffff"),
        "font.family": typo.get("title", {}).get("family", "sans-serif"),
        "axes.titlesize": typo.get("title", {}).get("size", 14),
        "axes.titleweight": typo.get("title", {}).get("weight", "bold"),
        "axes.titlecolor": typo.get("title", {}).get("color", "#222"),
        "axes.labelsize": typo.get("axis_label", {}).get("size", 10.5),
        "axes.labelcolor": typo.get("axis_label", {}).get("color", "#333"),
        "xtick.labelsize": typo.get("tick_label", {}).get("size", 9),
        "ytick.labelsize": typo.get("tick_label", {}).get("size", 9),
        "xtick.color": typo.get("tick_label", {}).get("color", "#444"),
        "ytick.color": typo.get("tick_label", {}).get("color", "#444"),
        "legend.fontsize": typo.get("legend_label", {}).get("size", 9),
        "legend.title_fontsize": typo.get("legend_title", {}).get("size", 9.5),
        "axes.edgecolor": "#666666",
        "axes.linewidth": 0.8,
        "axes.spines.top": profile.get("axes", {}).get("spine_top", False),
        "axes.spines.right": profile.get("axes", {}).get("spine_right", False),
    })
    return plt


def style_axes(ax, family: str) -> None:
    """Apply grid + spine settings to an axes per the family profile."""
    profile = family_profile(family)
    grid = profile.get("grid", {})
    if grid.get("enabled", True):
        ax.grid(
            True,
            axis=grid.get("axis", "y"),
            color=grid.get("color", "#e6e6e6"),
            linewidth=grid.get("linewidth", 0.6),
            alpha=grid.get("alpha", 0.9),
            zorder=0,
        )
    ax.set_axisbelow(True)
    axes_cfg = profile.get("axes", {})
    if not axes_cfg.get("spine_top", False):
        ax.spines["top"].set_visible(False)
    if not axes_cfg.get("spine_right", False):
        ax.spines["right"].set_visible(False)


def add_chart_chrome(
    fig,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
) -> None:
    """Add title / subtitle / attribution to a figure."""
    styles = load_chart_styles()
    typo = styles.get("typography", {})
    if title:
        fig.suptitle(
            title,
            fontsize=typo.get("title", {}).get("size", 14),
            fontweight=typo.get("title", {}).get("weight", "bold"),
            color=typo.get("title", {}).get("color", "#222"),
            x=0.02, ha="left", y=0.98,
        )
    if subtitle:
        fig.text(
            0.02, 0.935, subtitle,
            fontsize=typo.get("subtitle", {}).get("size", 10),
            color=typo.get("subtitle", {}).get("color", "#666"),
            ha="left",
        )
    if attribution:
        fig.text(
            0.98, 0.01, attribution,
            fontsize=typo.get("attribution", {}).get("size", 7.5),
            color=typo.get("attribution", {}).get("color", "#999"),
            ha="right", va="bottom",
        )


def save_chart(
    fig,
    output_path: str | Path,
    *,
    family: str,
    kind: str,
    field: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
    palette: str | None = None,
    source: str | None = None,
    extra_sidecar: dict | None = None,
) -> dict:
    """Save chart as PNG + SVG and write a .style.json sidecar.

    Returns dict with paths to written files.
    """
    import matplotlib.pyplot as plt

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    png_path = out.with_suffix(".png")
    svg_path = out.with_suffix(".svg")

    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.35)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)

    sidecar = {
        "version": 1,
        "chart_path": png_path.name,
        "chart_svg": svg_path.name,
        "chart_family": family,
        "chart_kind": kind,
        "map_family": f"chart_{family}",
        "created_at": datetime.now(UTC).isoformat(),
    }
    if field:
        sidecar["field"] = field
    if title:
        sidecar["title"] = title
    if subtitle:
        sidecar["subtitle"] = subtitle
    if attribution:
        sidecar["attribution"] = attribution
    if palette:
        sidecar["palette"] = palette
    if source:
        sidecar["source_gpkg"] = source
    if extra_sidecar:
        sidecar.update(extra_sidecar)

    sidecar_path = png_path.with_suffix(".style.json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2))

    return {
        "png": str(png_path),
        "svg": str(svg_path),
        "sidecar": str(sidecar_path),
    }


def load_series(
    data: str | Path,
    *,
    field: str | None = None,
    layer: str | None = None,
) -> "Any":
    """Load a pandas DataFrame from CSV, GeoPackage, Parquet, or GeoJSON.

    Returns a DataFrame (not GeoDataFrame). Geometry column dropped if present.
    """
    import pandas as pd

    path = Path(data)
    suffix = path.suffix.lower()

    if suffix in (".csv", ".tsv"):
        sep = "\t" if suffix == ".tsv" else ","
        df = pd.read_csv(path, sep=sep)
    elif suffix in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    elif suffix in (".gpkg", ".geojson", ".shp"):
        import geopandas as gpd
        kwargs: dict[str, Any] = {}
        if layer and suffix == ".gpkg":
            kwargs["layer"] = layer
        gdf = gpd.read_file(path, **kwargs)
        if "geometry" in gdf.columns:
            df = pd.DataFrame(gdf.drop(columns=["geometry"]))
        else:
            df = pd.DataFrame(gdf)
    elif suffix == ".json":
        df = pd.read_json(path)
    else:
        raise ValueError(f"Unsupported data file: {path}")

    if field and field not in df.columns:
        raise KeyError(
            f"Field {field!r} not in columns. Available: {list(df.columns)[:20]}"
        )
    return df


def format_tick_labels(ax, axis: str = "y", pct: bool = False) -> None:
    """Apply firm-standard thousands separators and optional % suffix."""
    from matplotlib.ticker import FuncFormatter

    def fmt(x, _pos):
        if abs(x) >= 1000:
            s = f"{x:,.0f}"
        elif abs(x) >= 10:
            s = f"{x:.0f}"
        else:
            s = f"{x:.2f}".rstrip("0").rstrip(".")
        return s + "%" if pct else s

    target = ax.xaxis if axis == "x" else ax.yaxis
    target.set_major_formatter(FuncFormatter(fmt))
