# Adding Data Sources

This guide walks through adding a new data source to spatial-machines. By the end, your new source will be:
- Fetchable via a script that any agent can call
- Registered in the data source catalog
- Documented in the wiki so agents know when and how to use it
- Available to the data-retrieval agent's toolset

## The Pattern

Every fetch script in spatial-machines follows the same interface:

```python
#!/usr/bin/env python3
"""Fetch [data source name] data.

Usage:
    python scripts/core/fetch_example.py [args] -o data/raw/output.csv
"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_api_key() -> str | None:
    """Read YOUR_API_KEY from the project .env file."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "YOUR_API_KEY" and value.strip():
            return value.strip()
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch data from [source].")
    parser.add_argument("--some-arg", required=True, help="...")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ... fetch logic here ...

    # Write manifest sidecar
    manifest = {
        "dataset_id": out_path.stem,
        "retrieval_method": "your-method",
        "source_name": "Your Source Name",
        "source_type": "api|download|database",
        "source_url": "https://...",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(out_path),
        "format": "csv|json|geojson|geotiff",
        "notes": [],
        "warnings": [],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Step-by-Step

### 1. Write the fetch script

Create `scripts/core/fetch_yourdata.py` following the pattern above.

**Requirements:**
- Standard library only (`urllib`, `json`, `csv`, `pathlib`, `argparse`). No `requests`, `httpx`, or `pandas`.
- `def main() -> int:` with argparse — must support `--help` and return 0 on success, 1 on failure.
- `if __name__ == "__main__": raise SystemExit(main())` guard.
- `-o / --output` flag for the output file path. Auto-create parent directories.
- Write a `.manifest.json` sidecar alongside the output with provenance metadata.
- Print progress to stdout (what's being fetched, how many records, where it was saved).
- Handle errors gracefully — catch `HTTPError`/`URLError`, print useful messages, return 1.
- If the API requires a key, read it from `.env` using the `_load_api_key()` helper pattern. Never hardcode keys.

**If the API requires authentication:**
- Read the key from `.env` using the established pattern (see any existing fetch script).
- Add the key variable to `.env.example` with a comment explaining where to sign up.
- If the key is optional (increases rate limits but works without), make this clear in the help text and print a warning when missing.
- If the key is required, exit with a helpful error message including the signup URL.

### 2. Register in the data source catalog

Add an entry to `config/data_sources.json`:

```json
{
  "id": "your-source-id",
  "name": "Human-Readable Source Name",
  "provider": "Publishing Organization",
  "script": "fetch_yourdata.py",
  "endpoint": "https://api.example.com/v1/data",
  "auth": "none|optional|required",
  "auth_env_var": "YOUR_API_KEY",
  "auth_signup": "https://example.com/signup",
  "free": true,
  "returns": "Description of what the data looks like",
  "geography": ["tract", "county", "point", "bbox"],
  "update_frequency": "daily|monthly|annual|periodic",
  "category": "demographics|health|environment|etc"
}
```

### 3. Add a wiki page

Create `docs/wiki/data-sources/YOUR_SOURCE.md` following the format of existing pages. Key sections:

- **Source Summary** — what the data is and why it matters
- **Owner / Publisher** — the authoritative organization
- **Geography Support** — what spatial units are available
- **Time Coverage** — how far back the data goes and how often it's updated
- **Access Method** — how to get the data (API, download, etc.)
- **Fetch Script** — link to your script with usage examples
- **Credentials** — what keys/tokens are needed (if any)
- **Known Caveats** — limitations, gotchas, data quality issues
- **Best-Fit Workflows** — which analysis types benefit from this data
- **Trust Level** — how authoritative is this source

### 4. Update the data-retrieval agent

Add your script to `agents/data-retrieval/TOOLS.md` under the appropriate category section.

### 5. Update .env.example (if auth required)

Add the API key variable with a comment:

```bash
# Your Source API key (free: https://example.com/signup)
# Used by: fetch_yourdata.py
YOUR_API_KEY=
```

### 6. Test it

Run your script with real arguments and verify:
- Output file is created and non-empty
- Manifest sidecar is created with correct metadata
- `--help` exits with code 0
- Missing API key produces a helpful error (if auth required)

Consider adding a test case to `tests/benchmarks/DATA_SOURCE_BENCHMARK.md`.

## Examples

Look at these existing scripts as reference implementations:

| Complexity | Script | Pattern |
|---|---|---|
| Simple (no auth, direct download) | `fetch_usda_food_access.py` | Download CSV, optionally filter by state |
| Simple (no auth, REST API) | `fetch_ejscreen.py` | Query REST endpoint, save JSON |
| Medium (Socrata API, optional auth) | `fetch_cdc_places.py` | SoQL query, pagination, CSV output |
| Medium (pagination, required auth) | `fetch_noaa_climate.py` | Token auth, offset-based pagination |
| Medium (POST request) | `fetch_bls_employment.py` | JSON POST body, series-based query |
| Complex (ArcGIS REST, pagination) | `fetch_fema_nfhl.py` | Feature layer query with transfer limit handling |
| Complex (multi-mode, optional CLI) | `fetch_overture.py` | Direct download OR guided CLI/DuckDB query |

## Common Patterns

### Rate limiting / retry
```python
import time
for attempt in range(3):
    try:
        with urlopen(url, timeout=60) as response:
            data = json.load(response)
        break
    except HTTPError as exc:
        if exc.code == 429 and attempt < 2:
            time.sleep(2 ** (attempt + 1))
            continue
        raise
```

### Pagination
```python
all_results = []
offset = 0
while offset < max_records:
    url = f"{endpoint}?offset={offset}&limit={page_size}"
    with urlopen(url) as response:
        page = json.load(response)
    results = page.get("results", [])
    if not results:
        break
    all_results.extend(results)
    offset += len(results)
```

### Reading API keys from .env
```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _load_api_key() -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "MY_API_KEY" and value.strip():
            return value.strip()
    return None
```
