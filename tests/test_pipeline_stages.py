"""Layer 3: Pipeline Stage Tests.

Run individual pipeline stages with known inputs and verify outputs.
These tests require GIS dependencies (geopandas, fiona) in the active venv.

Usage:
    python -m pytest tests/test_pipeline_stages.py -v
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "core"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _create_small_gpkg(path: Path, n_features: int = 5, crs: str = "EPSG:4269"):
    """Create a minimal GeoPackage with polygon features."""
    import geopandas as gpd
    from shapely.geometry import box

    features = []
    for i in range(n_features):
        geom = box(-100 + i, 40 + i, -99 + i, 41 + i)
        features.append({
            "geometry": geom,
            "GEOID": f"{31:02d}{i:03d}00",
            "NAME": f"Tract {i}",
            "ALAND": 1000000 * (i + 1),
            "AWATER": 50000 * (i + 1),
        })
    gdf = gpd.GeoDataFrame(features, crs=crs)
    gdf.to_file(path, driver="GPKG")
    return path


def _create_small_csv(path: Path, n_rows: int = 5, has_nulls: bool = False):
    """Create a minimal CSV with demographic-style columns."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["GEOID", "total_pop", "median_income"])
        for i in range(n_rows):
            pop = "" if (has_nulls and i == 2) else str(1000 * (i + 1))
            income = "" if (has_nulls and i == 4) else str(50000 + 5000 * i)
            writer.writerow([f"{31:02d}{i:03d}00", pop, income])
    return path


def _create_small_shapefile_zip(path: Path, n_features: int = 5):
    """Create a ZIP containing a minimal shapefile set."""
    import geopandas as gpd
    from shapely.geometry import box

    tmp_dir = path.parent / "_shp_tmp"
    tmp_dir.mkdir(exist_ok=True)

    features = []
    for i in range(n_features):
        geom = box(-100 + i, 40 + i, -99 + i, 41 + i)
        features.append({"geometry": geom, "GEOID": f"{31:02d}{i:03d}00", "NAME": f"Tract {i}"})
    gdf = gpd.GeoDataFrame(features, crs="EPSG:4269")

    shp_stem = "test_tracts"
    shp_path = tmp_dir / f"{shp_stem}.shp"
    gdf.to_file(shp_path, driver="ESRI Shapefile")

    with zipfile.ZipFile(path, "w") as zf:
        for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            f = tmp_dir / f"{shp_stem}{ext}"
            if f.exists():
                zf.write(f, f.name)

    shutil.rmtree(tmp_dir)
    return path


def _run_script(script_name: str, args: list[str]) -> subprocess.CompletedProcess:
    """Run a script and return the result."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


# ---------------------------------------------------------------------------
# Tests — each uses the ACTUAL CLI interface from --help
# ---------------------------------------------------------------------------


class TestProcessTable:
    """process_table.py: positional input, -o OUTPUT, --fields, --rename, --types"""

    def test_basic_processing(self, tmp_path):
        src = _create_small_csv(tmp_path / "input.csv")
        out = tmp_path / "output.csv"
        result = _run_script("process_table.py", [str(src), "-o", str(out)])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        processing_json = Path(str(out).replace(".csv", ".processing.json"))
        assert processing_json.exists(), "Expected processing sidecar JSON"

    def test_column_rename(self, tmp_path):
        src = _create_small_csv(tmp_path / "input.csv")
        out = tmp_path / "output.csv"
        result = _run_script("process_table.py", [
            str(src), "-o", str(out),
            "--rename", "total_pop=population,median_income=income",
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        with open(out) as f:
            headers = f.readline().strip().split(",")
        assert "population" in headers
        assert "income" in headers


class TestProcessVector:
    """process_vector.py: positional input, -o OUTPUT, --fields, --set-crs, --reproject"""

    def test_basic_processing(self, tmp_path):
        src = _create_small_gpkg(tmp_path / "input.gpkg")
        out = tmp_path / "output.gpkg"
        result = _run_script("process_vector.py", [str(src), "-o", str(out)])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        processing_json = Path(str(out).replace(".gpkg", ".processing.json"))
        assert processing_json.exists()

    def test_field_selection(self, tmp_path):
        src = _create_small_gpkg(tmp_path / "input.gpkg")
        out = tmp_path / "output.gpkg"
        result = _run_script("process_vector.py", [
            str(src), "-o", str(out),
            "--fields", "GEOID,NAME",
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        import geopandas as gpd
        gdf = gpd.read_file(out)
        non_geom = [c for c in gdf.columns if c != "geometry"]
        assert "GEOID" in non_geom
        assert "NAME" in non_geom


class TestExtractArchive:
    """extract_archive.py: positional ZIP, --dest DIR"""

    def test_extract_shapefile_zip(self, tmp_path):
        script = SCRIPTS_DIR / "extract_archive.py"
        if not script.exists():
            pytest.skip("extract_archive.py not present in scripts/core/")
        zip_path = _create_small_shapefile_zip(tmp_path / "test.zip")
        out_dir = tmp_path / "interim"
        out_dir.mkdir()
        result = _run_script("extract_archive.py", [str(zip_path), "--dest", str(out_dir)])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        extracted = list(out_dir.glob("*"))
        extensions = {f.suffix for f in extracted}
        assert ".shp" in extensions, f"Expected .shp in {extensions}"
        assert ".dbf" in extensions, f"Expected .dbf in {extensions}"
        json_files = list(out_dir.glob("*.extraction.json"))
        assert len(json_files) >= 1


class TestJoinData:
    """join_data.py: positional spatial table, --spatial-key, --table-key, -o OUTPUT"""

    def test_basic_join(self, tmp_path):
        gpkg = _create_small_gpkg(tmp_path / "spatial.gpkg")
        csv_path = _create_small_csv(tmp_path / "table.csv")
        out = tmp_path / "joined.gpkg"
        result = _run_script("join_data.py", [
            str(gpkg), str(csv_path),
            "--spatial-key", "GEOID",
            "--table-key", "GEOID",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        join_json = Path(str(out).replace(".gpkg", ".join.json"))
        assert join_json.exists(), "Expected join diagnostics JSON"
        diag = json.loads(join_json.read_text())
        assert len(diag) > 0


class TestDeriveFields:
    """derive_fields.py: positional input, -d 'col=expr', -o OUTPUT"""

    def test_derive_water_pct(self, tmp_path):
        gpkg = _create_small_gpkg(tmp_path / "input.gpkg")
        out = tmp_path / "output.gpkg"
        result = _run_script("derive_fields.py", [
            str(gpkg),
            "-d", "water_pct=AWATER / (ALAND + AWATER) * 100",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        import geopandas as gpd
        gdf = gpd.read_file(out)
        assert "water_pct" in gdf.columns
        assert gdf["water_pct"].notna().all()


class TestAnalyzeSummaryStats:
    """analyze_summary_stats.py: positional input, --fields, -o OUTPUT"""

    def test_summary_stats(self, tmp_path):
        csv_path = _create_small_csv(tmp_path / "input.csv")
        out = tmp_path / "summary.csv"
        result = _run_script("analyze_summary_stats.py", [
            str(csv_path),
            "--fields", "total_pop,median_income",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0, "Summary stats should produce at least one row"


class TestAnalyzeTopN:
    """analyze_top_n.py: positional input field, --n, -o OUTPUT"""

    def test_top_n(self, tmp_path):
        csv_path = _create_small_csv(tmp_path / "input.csv")
        out = tmp_path / "top.csv"
        result = _run_script("analyze_top_n.py", [
            str(csv_path), "total_pop",
            "--n", "3",
            "--label", "GEOID",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        with open(out) as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Header + at least 3 data rows (may have top + bottom sections)
        assert len(rows) >= 4, f"Expected header + 3 rows, got {len(rows)}"


class TestAnalyzeChoropleth:
    """analyze_choropleth.py: positional input field, -o OUTPUT"""

    def test_choropleth_output(self, tmp_path):
        gpkg = _create_small_gpkg(tmp_path / "input.gpkg")
        out = tmp_path / "map.png"
        result = _run_script("analyze_choropleth.py", [
            str(gpkg), "ALAND",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        assert out.stat().st_size > 1000, "Choropleth PNG should be > 1KB"


class TestValidateVector:
    """validate_vector.py: positional input, --expected-crs, -o OUTPUT"""

    def test_valid_vector(self, tmp_path):
        gpkg = _create_small_gpkg(tmp_path / "input.gpkg")
        out = tmp_path / "validation.json"
        result = _run_script("validate_vector.py", [
            str(gpkg),
            "--expected-crs", "EPSG:4269",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        report = json.loads(out.read_text())
        status = report.get("status", report.get("overall_status", ""))
        assert "PASS" in status.upper(), f"Expected PASS, got {status}"


class TestValidateTabular:
    """validate_tabular.py: positional input, --required-fields, -o OUTPUT"""

    def test_valid_csv(self, tmp_path):
        csv_path = _create_small_csv(tmp_path / "input.csv")
        out = tmp_path / "validation.json"
        result = _run_script("validate_tabular.py", [
            str(csv_path),
            "--required-fields", "GEOID,total_pop",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()

    def test_csv_with_nulls_warns(self, tmp_path):
        csv_path = _create_small_csv(tmp_path / "input.csv", has_nulls=True)
        out = tmp_path / "validation.json"
        result = _run_script("validate_tabular.py", [
            str(csv_path),
            "--required-fields", "GEOID,total_pop",
            "-o", str(out),
        ])
        # May return 0 (pass with warnings) or 1 (rework) depending on threshold
        assert out.exists()
        report = json.loads(out.read_text())
        report_str = json.dumps(report).lower()
        assert "null" in report_str or "warning" in report_str or "missing" in report_str


class TestValidateJoinCoverage:
    """validate_join_coverage.py: positional input, --key-field, -o OUTPUT"""

    def test_full_coverage(self, tmp_path):
        gpkg = _create_small_gpkg(tmp_path / "spatial.gpkg")
        csv_path = _create_small_csv(tmp_path / "table.csv")
        # First join
        joined = tmp_path / "joined.gpkg"
        join_result = _run_script("join_data.py", [
            str(gpkg), str(csv_path),
            "--spatial-key", "GEOID",
            "--table-key", "GEOID",
            "-o", str(joined),
        ])
        assert join_result.returncode == 0, f"Join failed: {join_result.stderr}"
        assert joined.exists()

        # Now validate coverage
        out = tmp_path / "coverage.json"
        result = _run_script("validate_join_coverage.py", [
            str(joined),
            "--key-field", "GEOID",
            "-o", str(out),
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
