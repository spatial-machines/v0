# Troubleshooting

Common issues and how to fix them.

## Installation Issues

### `pip install` fails on fiona, rasterio, or pyogrio (Windows)
**Cause:** You're on Python 3.13 or newer. Prebuilt wheels for the geospatial stack lag one or two Python versions behind; pip then tries to compile from source and fails because GDAL headers aren't on your machine.
**Fix:** Install Python 3.12 (Microsoft Store or [python.org](https://www.python.org/downloads/release/python-3129/)). Delete the broken `venv/` folder. Recreate it with the 3.12 interpreter: `py -3.12 -m venv venv`. Activate and re-run `pip install -r requirements.txt`.

### `claude: command not found` after `npm i -g @anthropic-ai/claude-code`
**Cause:** Windows doesn't pick up the new npm global bin in PATH until you restart the terminal.
**Fix:** Close the terminal, open a new one, try `claude` again. If still missing, check that `%APPDATA%\npm` is in your user PATH (System Properties → Environment Variables).

### "Could not find a version that satisfies the requirement"
**Cause:** A package is unavailable for your Python version or platform.
**Fix:** Ensure Python 3.12 is installed. If a specific package fails, check if it's in the optional section of `requirements.txt` and comment it out if you don't need it.

### GDAL/PROJ/GEOS import errors
**Cause:** System spatial libraries not installed.
**Fix:** Install system dependencies first:
```bash
# Ubuntu/Debian
sudo apt install gdal-bin libgdal-dev libgeos-dev libproj-dev

# macOS
brew install gdal geos proj
```

### "ModuleNotFoundError: No module named 'geopandas'"
**Cause:** Python dependencies not installed.
**Fix:** Run `pip install -r requirements.txt` from the repo root.

## Data Retrieval Issues

### Census API rate limiting
**Cause:** No API key configured, or too many requests.
**Fix:** Add your `CENSUS_API_KEY` to `.env`. Get a free key at https://api.census.gov/data/key_signup.html

### "ERROR: NOAA API token required"
**Cause:** The NOAA climate data API requires a free token.
**Fix:** Get a token at https://www.ncdc.noaa.gov/cdo-web/token and add it as `NOAA_API_TOKEN` in `.env`.

### Fetch script returns empty data
**Cause:** State FIPS code wrong, variable names incorrect, or data not available for the requested geography/year.
**Fix:** Check the wiki data source page for the correct parameters. Run the script with `--help` to see available options.

## Map Generation Issues

### "field not found" error in analyze_choropleth.py
**Cause:** The field name doesn't match what's in the GeoPackage.
**Fix:** The error message prints available field names. Use one of those.

### Map is all one color
**Cause:** All values are the same, or classification produced degenerate breaks.
**Fix:** Check data values. Try `--scheme quantiles` or reduce `--k` to fewer classes.

### Map has no data (all gray)
**Cause:** All values are null for the selected field.
**Fix:** Check your data processing step. Verify the join produced non-null values.

## QGIS Package Issues

### QGIS project opens but layers are unstyled
**Cause:** The GeoPackage wasn't at the expected relative path when the project was generated, OR the `.style.json` sidecar didn't match the layer.
**Fix:** Ensure `outputs/qgis/data/` contains the GeoPackages. For sidecar matching, check `review-spec.json` — it records which sidecar was matched to which layer and via what rule (`source_gpkg`, `field`, or `categorical`).

### "Layer is not valid" in QGIS
**Cause:** GeoPackage file missing from the package, or the package was moved without its `data/` directory.
**Fix:** Keep the entire QGIS package directory together (`project.qgs` + everything beside it). The `.qgs` uses relative paths.

### `.qgs` file didn't get produced
**Cause:** No QGIS installation was found when the packager ran, or PyQGIS couldn't be loaded from the active Python.
**Fix:** Install QGIS 3.28+ LTR. On Windows, use OSGeo4W. The packager auto-discovers QGIS's Python and runs the project-writer in a subprocess; the rest of the package (GeoPackages, review notes, manifest) still ships even when the `.qgs` fails.

## ArcGIS Pro Package Issues

### `.lyrx` files didn't get produced (0 of N)
**Cause:** Sidecar matching couldn't resolve any style sidecar to a feature class in the GDB.
**Fix:** Check `outputs/arcgis/review-spec.json` → `lyrx_layers` for the `match_via` field on each plan. Warnings name the specific sidecar that failed. Common fix: ensure the sidecar's `source_gpkg` field points at a real gpkg in `data/processed/`.

### `.aprx` wasn't auto-built
**Cause:** The packager didn't detect `arcpy` on the producer machine, so it shipped `make_aprx.py` for the user to run inside ArcGIS Pro.
**Fix:** Open ArcGIS Pro, open or create a project, open the Python window, drag `make_aprx.py` into the Python window and run it. A ready-to-share `.aprx` is saved next to it. Alternatively: run the packager from a Pro-bundled Python on a machine with Pro installed.

## ArcGIS Online Publishing Issues

### "publish silently returned item-info instead of services"
**Cause #1 (most common):** Your AGOL subscription is a Location Platform / Developer tier, which doesn't include hosted feature service publishing. Check at https://www.arcgis.com/home/organization.html → if `subscriptionInfo.type` is `"Location Platform"`, you need to upgrade.
**Cause #2:** Your `AGOL_API_KEY` lacks the publish-hosted-feature-layers scope. Switch to `AGOL_USER` + `AGOL_PASSWORD` auth in `.env` — user/password tokens inherit the full account privilege set.
**Full details:** [AGOL workflow doc](../wiki/workflows/ARCGIS_ONLINE_PUBLISHING.md).

### "No File Geodatabase found at outputs/arcgis/data/project.gdb"
**Cause:** You ran `publish_arcgis_online.py` without building the ArcGIS Pro package first.
**Fix:** Run `package_arcgis_pro.py` first — it produces the GDB the AGOL adapter uploads.

### AGOL publish left orphan items behind
**Cause:** Publish failed partway through and auto-cleanup didn't fire.
**Fix:** Run `python scripts/core/teardown_agol.py analyses/<project>/`. It reads `publish-status.json` and deletes every item referenced. Safe to re-run.

## Test Issues

### Many tests skip with "No analysis data found"
**Cause:** Normal on a fresh clone. These tests validate completed analysis outputs.
**Fix:** Run an analysis first, or they'll run against the synthetic test fixture.

### "make verify" fails
**Cause:** A core script has a syntax error or broken import.
**Fix:** Check the error message — it will identify the failing script.

## Getting Help

- Check the [wiki](../wiki/) for methodology questions
- Check [docs/extending/](../extending/) for customization questions
- Open an issue on GitHub for bugs
