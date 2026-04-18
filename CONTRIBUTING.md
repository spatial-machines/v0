# Contributing to spatial-machines

Thanks for considering a contribution. This project is built by and for GIS analysts, and community contributions are how we cover the enormous breadth of spatial data and methodology.

## Ways to contribute

### Report a bug
Open a [bug report](https://github.com/spatial-machines/spatial-machines/issues/new?template=bug_report.yml). Include: what you ran, what happened, what you expected. Paste error output and your Python/OS version.

### Request a feature
Open a [feature request](https://github.com/spatial-machines/spatial-machines/issues/new?template=feature_request.yml). If it's a new data source, use the [domain request](https://github.com/spatial-machines/spatial-machines/issues/new?template=domain_request.yml) template instead.

### Add a data source
The most valuable community contribution. Each data source is a single Python script in `scripts/core/` following a consistent pattern. See `docs/extending/ADDING_DATA_SOURCES.md` for the full guide.

Quick version:
1. Copy an existing fetch script (e.g., `fetch_acs_data.py`) as your starting point.
2. Follow the CLI pattern: `--output`, `--geography`, `--variables`, `--year`.
3. Write to `data/raw/` in GeoPackage, CSV, or GeoJSON.
4. Add an entry to `config/data_sources.json`.
5. Add a wiki page to `docs/wiki/data-sources/`.

### Add a domain template
Domain templates in `templates/methodologies/` define reusable analysis patterns (e.g., food access, environmental justice). If you're an expert in a domain, your template helps every user who asks a question in that space.

### Fix a bug or improve a script
1. Open an issue describing the problem first.
2. Fork the repo and create a branch from `main`.
3. Make your changes.
4. Run the smoke test: `python scripts/core/smoke_test.py`.
5. Open a PR referencing the issue.

## Development setup

```bash
git clone https://github.com/spatial-machines/spatial-machines.git
cd spatial-machines
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e ".[dev]"    # installs pytest, pytest-cov
```

### Run tests
```bash
pytest tests/ -x -q
```

### Run the demo (verifies core pipeline)
```bash
python demo.py
```

### Run the smoke test (quick validation)
```bash
python scripts/core/smoke_test.py
```

## Code style

- Python 3.11+. Type hints encouraged but not required.
- Scripts in `scripts/core/` must be CLI-executable with `--help`.
- Follow existing patterns. Read two or three scripts in the same category before writing a new one.
- Don't add dependencies unless absolutely necessary. If you must, add to `requirements.txt` and document why.

## Commit messages

Use conventional-style messages:
- `feat: add USGS streamflow data source`
- `fix: handle empty geometry in batch_join`
- `docs: add food-access workflow to wiki`

## Pull request guidelines

- **One PR per feature or fix.** Don't bundle unrelated changes.
- **Open an issue first** for anything larger than a typo fix.
- **Include a test or demo** showing your change works.
- **Don't modify** `config/map_styles.json` or `config/chart_styles.json` without discussion.
- **Don't modify** agent SOUL.md or TOOLS.md files without discussion.

## What we won't merge

- Changes that add proprietary dependencies (no Esri-only code in the core).
- Changes that break the demo or existing tests.
- Undiscussed architectural changes to the pipeline or handoff contracts.
- Code that doesn't follow the script-first rule.

## License

By contributing, you agree that your contributions will be licensed under Apache-2.0. See `LICENSE`.
