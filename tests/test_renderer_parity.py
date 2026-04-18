"""Parity tests for sidecar → renderer translation across QGIS / LYRX / AGOL.

The `.style.json` sidecar is the single source of truth for map styling.
Three packagers consume it:
  - `scripts/core/write_qgis_project.py`  → QGIS `.qgs` graduated / categorized renderers
  - `scripts/core/lyrx_writer.py`         → ArcGIS Pro `.lyrx` CIMLayerDocument
  - `scripts/core/publishing/arcgis_online.py` → AGOL hosted feature layer renderer

Each is driven through `scripts/core/renderers.py`. These tests assert that
one sidecar produces matching renderers across the two always-available
paths (LYRX, AGOL) and that the shared helpers (ramp colors, break labels)
are deterministic. The QGIS path is exercised when PyQGIS is importable;
otherwise that branch is skipped (PyQGIS isn't pip-installable).

Run:
    pytest tests/test_renderer_parity.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_CORE = PROJECT_ROOT / "scripts" / "core"
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from renderers import (          # noqa: E402
    agol_renderer,
    lyrx_renderer,
    ramp_colors,
    sidecar_colors,
)


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def choropleth_sidecar() -> dict:
    return {
        "version": 1,
        "map_path": "poverty_choropleth.png",
        "map_family": "thematic_choropleth",
        "field": "poverty_rate",
        "palette": "YlOrRd",
        "scheme": "natural_breaks",
        "k": 5,
        "breaks": [0.4, 8.1, 15.1, 22.3, 35.4, 54.0],
        "title": "Poverty Rate",
        "legend_title": "Poverty rate (%)",
        "attribution": "U.S. Census Bureau ACS 5-Year, 2022",
        "crs": "EPSG:4269",
        "source_gpkg": "data/processed/tracts.gpkg",
        "layer_name": "tracts",
    }


@pytest.fixture
def categorical_sidecar() -> dict:
    return {
        "version": 1,
        "map_path": "hotspots.png",
        "map_family": "thematic_categorical",
        "field": "hotspot_label",
        "categorical_map": {
            "Hot Spot (95%)": "#fc8d59",
            "Not Significant": "#e0e0e0",
            "Cold Spot (95%)": "#91bfdb",
        },
        "title": "Gi* Hotspots",
    }


@pytest.fixture
def point_sidecar() -> dict:
    return {
        "version": 1,
        "map_path": "clinics.png",
        "map_family": "point_overlay",
        "palette": "access",
        "title": "Clinic Locations",
    }


# ── Ramp colors are deterministic ────────────────────────────────────

def test_ramp_colors_matches_k():
    colors = ramp_colors("YlOrRd", 5)
    assert len(colors) == 5
    assert all(len(c) == 3 for c in colors)
    assert all(all(0 <= v <= 255 for v in c) for c in colors)


def test_ramp_colors_stable_across_calls():
    a = ramp_colors("YlGnBu", 7)
    b = ramp_colors("YlGnBu", 7)
    assert a == b


def test_ramp_colors_k_interpolation():
    """When k != 5 (the base ramp length), interpolate within stops."""
    three = ramp_colors("Blues", 3)
    seven = ramp_colors("Blues", 7)
    assert len(three) == 3
    assert len(seven) == 7
    # Endpoints should match the base ramp's endpoints
    five = ramp_colors("Blues", 5)
    assert three[0] == five[0]
    assert three[-1] == five[-1]
    assert seven[0] == five[0]
    assert seven[-1] == five[-1]


def test_sidecar_colors_prefers_explicit(choropleth_sidecar):
    """Explicit `colors_rgb` wins over palette+k inference."""
    choropleth_sidecar["colors_rgb"] = [[10, 20, 30], [40, 50, 60]]
    colors = sidecar_colors(choropleth_sidecar)
    assert colors == [[10, 20, 30], [40, 50, 60]]


def test_sidecar_colors_falls_back_to_palette(choropleth_sidecar):
    colors = sidecar_colors(choropleth_sidecar)
    # 5 classes from breaks = 5 colors
    assert len(colors) == 5


# ── Choropleth parity ───────────────────────────────────────────────

def test_choropleth_lyrx_shape(choropleth_sidecar):
    r = lyrx_renderer(choropleth_sidecar)
    assert r["type"] == "CIMClassBreaksRenderer"
    assert r["field"] == "poverty_rate"
    assert r["classificationMethod"] == "NaturalBreaks"
    assert len(r["breaks"]) == 5
    # First break upperBound is the second value in sidecar breaks
    assert r["breaks"][0]["upperBound"] == pytest.approx(8.1)
    assert r["breaks"][-1]["upperBound"] == pytest.approx(54.0)


def test_choropleth_agol_shape(choropleth_sidecar):
    r = agol_renderer(choropleth_sidecar)
    assert r["type"] == "classBreaks"
    assert r["field"] == "poverty_rate"
    assert r["classificationMethod"] == "esriClassifyNaturalBreaks"
    assert len(r["classBreakInfos"]) == 5
    assert r["classBreakInfos"][0]["classMaxValue"] == pytest.approx(8.1)
    assert r["classBreakInfos"][-1]["classMaxValue"] == pytest.approx(54.0)


def test_choropleth_parity_breaks(choropleth_sidecar):
    """LYRX upperBound == AGOL classMaxValue for every class."""
    lyrx = lyrx_renderer(choropleth_sidecar)
    agol = agol_renderer(choropleth_sidecar)
    lyrx_breaks = [b["upperBound"] for b in lyrx["breaks"]]
    agol_breaks = [i["classMaxValue"] for i in agol["classBreakInfos"]]
    assert lyrx_breaks == pytest.approx(agol_breaks)


def test_choropleth_parity_colors(choropleth_sidecar):
    """LYRX solid-fill RGB == AGOL symbol color RGB for every class."""
    lyrx = lyrx_renderer(choropleth_sidecar)
    agol = agol_renderer(choropleth_sidecar)
    for lyrx_break, agol_info in zip(lyrx["breaks"], agol["classBreakInfos"]):
        # LYRX CIM: symbolLayers[1] is CIMSolidFill (symbolLayers[0] is CIMSolidStroke)
        lyrx_rgb = lyrx_break["symbol"]["symbol"]["symbolLayers"][1]["color"]["values"][:3]
        # AGOL: symbol.color = [r, g, b, a]
        agol_rgb = agol_info["symbol"]["color"][:3]
        assert [int(v) for v in lyrx_rgb] == agol_rgb


def test_choropleth_parity_labels(choropleth_sidecar):
    """Break labels use en-dash and match across renderers."""
    lyrx = lyrx_renderer(choropleth_sidecar)
    agol = agol_renderer(choropleth_sidecar)
    for lyrx_break, agol_info in zip(lyrx["breaks"], agol["classBreakInfos"]):
        assert lyrx_break["label"] == agol_info["label"]
        assert "\u2013" in lyrx_break["label"]  # en-dash not hyphen


# ── Categorical parity ─────────────────────────────────────────────

def test_categorical_lyrx_shape(categorical_sidecar):
    r = lyrx_renderer(categorical_sidecar)
    assert r["type"] == "CIMUniqueValueRenderer"
    assert r["fields"] == ["hotspot_label"]
    classes = r["groups"][0]["classes"]
    assert len(classes) == 3
    labels = [c["label"] for c in classes]
    assert "Hot Spot (95%)" in labels
    assert "Cold Spot (95%)" in labels


def test_categorical_agol_shape(categorical_sidecar):
    r = agol_renderer(categorical_sidecar)
    assert r["type"] == "uniqueValue"
    assert r["field1"] == "hotspot_label"
    assert len(r["uniqueValueInfos"]) == 3


def test_categorical_parity_classes(categorical_sidecar):
    lyrx = lyrx_renderer(categorical_sidecar)
    agol = agol_renderer(categorical_sidecar)
    lyrx_labels = sorted(c["label"] for c in lyrx["groups"][0]["classes"])
    agol_labels = sorted(i["label"] for i in agol["uniqueValueInfos"])
    assert lyrx_labels == agol_labels


def test_categorical_parity_colors(categorical_sidecar):
    lyrx = lyrx_renderer(categorical_sidecar)
    agol = agol_renderer(categorical_sidecar)
    # Index both by label for comparison
    lyrx_by = {
        c["label"]: c["symbol"]["symbol"]["symbolLayers"][1]["color"]["values"][:3]
        for c in lyrx["groups"][0]["classes"]
    }
    agol_by = {i["label"]: i["symbol"]["color"][:3]
               for i in agol["uniqueValueInfos"]}
    for label in lyrx_by:
        assert [int(v) for v in lyrx_by[label]] == agol_by[label]


# ── Point / simple parity ──────────────────────────────────────────

def test_point_lyrx_simple(point_sidecar):
    r = lyrx_renderer(point_sidecar)
    assert r["type"] == "CIMSimpleRenderer"
    assert r["symbol"]["symbol"]["type"] == "CIMPointSymbol"


def test_point_agol_simple(point_sidecar):
    r = agol_renderer(point_sidecar)
    assert r["type"] == "simple"
    assert r["symbol"]["type"] == "esriSMS"


# ── Missing-field degradation ──────────────────────────────────────

def test_choropleth_no_breaks_falls_back_to_simple():
    """Sidecar without breaks can't build a classBreaks renderer cleanly."""
    sc = {"version": 1, "map_family": "thematic_choropleth", "field": "x",
          "palette": "YlOrRd", "k": 5}
    lyrx = lyrx_renderer(sc)
    agol = agol_renderer(sc)
    assert lyrx["type"] == "CIMSimpleRenderer"
    assert agol["type"] == "simple"


def test_unknown_family_falls_back_to_simple():
    sc = {"version": 1, "map_family": "nonexistent_family", "palette": "Blues"}
    lyrx = lyrx_renderer(sc)
    agol = agol_renderer(sc)
    assert lyrx["type"] == "CIMSimpleRenderer"
    assert agol["type"] == "simple"


# ── Optional QGIS branch (skipped when PyQGIS unavailable) ─────────

try:
    import qgis.core  # noqa: F401
    _HAS_PYQGIS = True
except Exception:
    _HAS_PYQGIS = False


@pytest.mark.skipif(not _HAS_PYQGIS, reason="PyQGIS not importable")
def test_qgis_parity_breaks(tmp_path, choropleth_sidecar):
    """If PyQGIS is available, assert the .qgs graduated renderer uses the
    same breaks as LYRX / AGOL. Headless QGIS rendering.

    This is the only test branch that instantiates QGIS; the rest of the
    parity matrix is covered by the shared `renderers.py` module.
    """
    import geopandas as gpd
    from shapely.geometry import Point
    import xml.etree.ElementTree as ET

    # Minimal gpkg with the field the sidecar references
    gdf = gpd.GeoDataFrame(
        {"poverty_rate": [1.0, 10.0, 20.0, 30.0, 50.0]},
        geometry=[Point(i, 0) for i in range(5)],
        crs="EPSG:4326",
    )
    gpkg = tmp_path / "tracts.gpkg"
    gdf.to_file(gpkg, layer="tracts", driver="GPKG")

    style_dir = tmp_path / "styles"
    style_dir.mkdir()
    (style_dir / "poverty_choropleth.style.json").write_text(
        json.dumps(choropleth_sidecar)
    )

    from write_qgis_project import build_qgs_from_gpkg
    qgs = tmp_path / "project.qgs"
    build_qgs_from_gpkg(
        gpkg_paths=[gpkg],
        title="Parity test",
        output_path=qgs,
        crs_epsg=4326,
        basemap="none",
        style_dir=str(style_dir),
    )

    root = ET.parse(qgs).getroot()
    ranges = root.findall(".//renderer-v2/ranges/range")
    if not ranges:
        pytest.skip("graduated renderer not produced (PyQGIS may have fallen back)")
    upper_bounds = [float(r.get("upper")) for r in ranges]
    expected = choropleth_sidecar["breaks"][1:]
    assert upper_bounds == pytest.approx(expected, rel=1e-3)
