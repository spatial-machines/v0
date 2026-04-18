#!/usr/bin/env python3
"""Auto-generate properly formatted data source citations from a project's log files.

Scans all *.log.json files in the project directory for `source`, `vintage`, and
`description` fields, then matches them against a built-in citation registry covering
common GIS/Census/federal data sources.

Usage:
    python generate_citations.py \\
        --project-dir runs/analysis_2024_poverty/ \\
        --format apa \\
        --output outputs/reports/citations.md

    python generate_citations.py \\
        --project-dir . \\
        --format plain \\
        --output outputs/reports/citations.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Citation template registry ────────────────────────────────────────────────
# Keys are matched case-insensitively against the `source` field in log files.
# Each entry has templates for apa, chicago, and plain formats.
# Placeholders: {vintage}, {accessed}, {url}

CITATION_REGISTRY: dict[str, dict] = {
    "acs": {
        "match_keywords": ["acs", "american community survey", "b17001", "b19013", "s2701",
                           "b01003", "b15003", "c17002"],
        "label": "ACS 5-Year Estimates",
        "apa": (
            "U.S. Census Bureau. ({year}). *American Community Survey {vintage} 5-Year Estimates* "
            "[Data set]. U.S. Department of Commerce. {url}"
        ),
        "chicago": (
            'U.S. Census Bureau. "{vintage} American Community Survey 5-Year Estimates." '
            "U.S. Department of Commerce, {year}. {url}"
        ),
        "plain": (
            "U.S. Census Bureau. American Community Survey {vintage} 5-Year Estimates. "
            "U.S. Department of Commerce. {url}"
        ),
        "default_url": "https://data.census.gov",
    },
    "tiger": {
        "match_keywords": ["tiger", "census tiger", "tigerweb", "tiger/line", "tracts", "counties", "cbsa"],
        "label": "Census TIGER/Line Shapefiles",
        "apa": (
            "U.S. Census Bureau. ({year}). *TIGER/Line Shapefiles {vintage}* [Geospatial data]. "
            "U.S. Department of Commerce. {url}"
        ),
        "chicago": (
            'U.S. Census Bureau. "TIGER/Line Shapefiles {vintage}." '
            "U.S. Department of Commerce, {year}. {url}"
        ),
        "plain": (
            "U.S. Census Bureau. TIGER/Line Shapefiles {vintage}. "
            "U.S. Department of Commerce. {url}"
        ),
        "default_url": "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html",
    },
    "cdc_places": {
        "match_keywords": ["cdc places", "places", "500 cities", "cdc 500", "chronic disease",
                           "health outcomes", "places.cdc"],
        "label": "CDC PLACES",
        "apa": (
            "Centers for Disease Control and Prevention. ({year}). *PLACES: Local Data for Better "
            "Health {vintage}* [Data set]. CDC. {url}"
        ),
        "chicago": (
            'Centers for Disease Control and Prevention. "PLACES: Local Data for Better Health '
            "{vintage}.\" CDC, {year}. {url}"
        ),
        "plain": (
            "Centers for Disease Control and Prevention. PLACES: Local Data for Better Health "
            "{vintage}. CDC. {url}"
        ),
        "default_url": "https://www.cdc.gov/places",
    },
    "hrsa": {
        "match_keywords": ["hrsa", "health resources", "services administration", "hpsa",
                           "medically underserved", "mua", "shortage area", "uds mapper"],
        "label": "HRSA Data",
        "apa": (
            "Health Resources and Services Administration. ({year}). *{description}* "
            "[Data set]. U.S. Department of Health and Human Services. {url}"
        ),
        "chicago": (
            'Health Resources and Services Administration. "{description}." '
            "U.S. Department of Health and Human Services, {year}. {url}"
        ),
        "plain": (
            "Health Resources and Services Administration. {description}. "
            "U.S. Department of Health and Human Services. {url}"
        ),
        "default_url": "https://data.hrsa.gov",
    },
    "usda_food_atlas": {
        "match_keywords": ["usda", "food access", "food atlas", "food desert", "ers", "food environment",
                           "snap", "food access research"],
        "label": "USDA Food Access Research Atlas",
        "apa": (
            "U.S. Department of Agriculture, Economic Research Service. ({year}). "
            "*Food Access Research Atlas {vintage}* [Data set]. USDA ERS. {url}"
        ),
        "chicago": (
            'U.S. Department of Agriculture, Economic Research Service. "Food Access Research '
            "Atlas {vintage}.\" USDA ERS, {year}. {url}"
        ),
        "plain": (
            "USDA Economic Research Service. Food Access Research Atlas {vintage}. "
            "U.S. Department of Agriculture. {url}"
        ),
        "default_url": "https://www.ers.usda.gov/data-products/food-access-research-atlas/",
    },
    "epa_ejscreen": {
        "match_keywords": ["ejscreen", "epa", "environmental justice", "ej screen",
                           "environmental protection agency"],
        "label": "EPA EJScreen",
        "apa": (
            "U.S. Environmental Protection Agency. ({year}). *EJScreen: Environmental Justice "
            "Screening and Mapping Tool {vintage}* [Data set]. EPA. {url}"
        ),
        "chicago": (
            'U.S. Environmental Protection Agency. "EJScreen: Environmental Justice Screening '
            "and Mapping Tool {vintage}.\" EPA, {year}. {url}"
        ),
        "plain": (
            "U.S. Environmental Protection Agency. EJScreen: Environmental Justice Screening "
            "and Mapping Tool {vintage}. EPA. {url}"
        ),
        "default_url": "https://www.epa.gov/ejscreen",
    },
    "fema_nfhl": {
        "match_keywords": ["fema", "nfhl", "flood", "national flood hazard", "firm", "floodplain",
                           "special flood hazard"],
        "label": "FEMA National Flood Hazard Layer",
        "apa": (
            "Federal Emergency Management Agency. ({year}). *National Flood Hazard Layer (NFHL) "
            "{vintage}* [Geospatial data]. FEMA. {url}"
        ),
        "chicago": (
            'Federal Emergency Management Agency. "National Flood Hazard Layer (NFHL) {vintage}." '
            "FEMA, {year}. {url}"
        ),
        "plain": (
            "Federal Emergency Management Agency. National Flood Hazard Layer (NFHL) {vintage}. "
            "FEMA. {url}"
        ),
        "default_url": "https://msc.fema.gov/portal/advanceSearch",
    },
    "bls_laus": {
        "match_keywords": ["bls", "laus", "local area unemployment", "bureau of labor statistics",
                           "unemployment rate", "labor force"],
        "label": "BLS Local Area Unemployment Statistics",
        "apa": (
            "U.S. Bureau of Labor Statistics. ({year}). *Local Area Unemployment Statistics "
            "(LAUS) {vintage}* [Data set]. U.S. Department of Labor. {url}"
        ),
        "chicago": (
            'U.S. Bureau of Labor Statistics. "Local Area Unemployment Statistics (LAUS) '
            "{vintage}.\" U.S. Department of Labor, {year}. {url}"
        ),
        "plain": (
            "U.S. Bureau of Labor Statistics. Local Area Unemployment Statistics (LAUS) "
            "{vintage}. U.S. Department of Labor. {url}"
        ),
        "default_url": "https://www.bls.gov/lau/",
    },
    "openstreetmap": {
        "match_keywords": ["openstreetmap", "osm", "osmnx", "open street map"],
        "label": "OpenStreetMap",
        "apa": (
            "OpenStreetMap contributors. ({year}). *OpenStreetMap* [Geospatial data]. "
            "OpenStreetMap Foundation. {url}"
        ),
        "chicago": (
            'OpenStreetMap contributors. "OpenStreetMap." OpenStreetMap Foundation, {year}. {url}'
        ),
        "plain": (
            "OpenStreetMap contributors. OpenStreetMap. OpenStreetMap Foundation. "
            "Accessed {accessed}. {url}"
        ),
        "default_url": "https://www.openstreetmap.org",
    },
}


def extract_log_entries(project_dir: Path) -> list[dict]:
    """Scan all *.log.json files and collect entries with source/vintage/description."""
    log_files = sorted(project_dir.rglob("*.log.json"))
    entries = []
    seen_sources: set[str] = set()

    for log_file in log_files:
        try:
            data = json.loads(log_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # Handle both single-object and list-of-objects log files
        records = data if isinstance(data, list) else [data]

        for rec in records:
            if not isinstance(rec, dict):
                continue
            source = rec.get("source") or rec.get("data_source") or ""
            vintage = rec.get("vintage") or rec.get("year") or ""
            description = rec.get("description") or rec.get("step") or ""
            url = rec.get("url") or rec.get("data_url") or ""

            if not source:
                continue

            key = source.lower().strip()
            if key in seen_sources:
                continue
            seen_sources.add(key)

            entries.append({
                "source": source,
                "vintage": str(vintage),
                "description": description,
                "url": url,
                "log_file": str(log_file.relative_to(project_dir)),
            })

    return entries


def match_registry(source: str, description: str) -> str | None:
    """Return the registry key that best matches a source string, or None."""
    combined = (source + " " + description).lower()
    for key, entry in CITATION_REGISTRY.items():
        for kw in entry["match_keywords"]:
            if kw.lower() in combined:
                return key
    return None


def format_citation(registry_key: str, entry: dict, fmt: str, accessed_date: str) -> str:
    """Render a citation string from a registry entry + log data."""
    reg = CITATION_REGISTRY[registry_key]
    template = reg[fmt]

    vintage = entry.get("vintage") or "n.d."
    description = entry.get("description") or reg["label"]
    url = entry.get("url") or reg["default_url"]

    # Parse year from vintage string if possible
    year = vintage
    for part in vintage.split("-"):
        part = part.strip()
        if part.isdigit() and len(part) == 4:
            year = part
            break
    if not (isinstance(year, str) and year.isdigit()):
        year = str(datetime.now(timezone.utc).year)

    return template.format(
        vintage=vintage,
        year=year,
        description=description,
        url=url,
        accessed=accessed_date,
    )


def build_citations_markdown(
    entries: list[dict],
    fmt: str,
    accessed_date: str,
) -> tuple[str, list[dict]]:
    """Build the full Markdown citations block. Returns (markdown, log_records)."""
    matched: list[tuple[str, str, dict]] = []   # (registry_key, citation_text, entry)
    unmatched: list[dict] = []

    for entry in entries:
        key = match_registry(entry["source"], entry["description"])
        if key:
            citation = format_citation(key, entry, fmt, accessed_date)
            matched.append((key, citation, entry))
        else:
            unmatched.append(entry)

    # Deduplicate by registry key (keep first occurrence per source type)
    seen_keys: set[str] = set()
    unique_matched: list[tuple[str, str, dict]] = []
    for key, citation, entry in matched:
        if key not in seen_keys:
            seen_keys.add(key)
            unique_matched.append((key, citation, entry))

    lines = ["# Data Sources and Citations", ""]
    lines.append(f"*Format: {fmt.upper()} | Generated: {accessed_date}*")
    lines.append("")

    if unique_matched:
        lines.append("## Cited Sources")
        lines.append("")
        for _, citation, entry in unique_matched:
            lines.append(f"- {citation}")
            lines.append("")

    if unmatched:
        lines.append("## Additional Sources (unmatched to registry)")
        lines.append("")
        for entry in unmatched:
            source = entry["source"]
            vintage = entry.get("vintage") or ""
            desc = entry.get("description") or ""
            note = f"- {source}"
            if vintage:
                note += f" ({vintage})"
            if desc:
                note += f". {desc}"
            lines.append(note)
            lines.append("")

    if not unique_matched and not unmatched:
        lines.append("*No source fields found in project log files.*")

    md = "\n".join(lines)

    log_records = [
        {
            "registry_key": key,
            "source": entry["source"],
            "vintage": entry.get("vintage"),
            "log_file": entry.get("log_file"),
        }
        for key, _, entry in unique_matched
    ]
    log_records += [
        {
            "registry_key": None,
            "source": e["source"],
            "vintage": e.get("vintage"),
            "log_file": e.get("log_file"),
        }
        for e in unmatched
    ]

    return md, log_records


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project-dir", required=True,
        help="Project analysis directory to scan for *.log.json files",
    )
    parser.add_argument(
        "--format", dest="fmt", default="plain",
        choices=["apa", "chicago", "plain"],
        help="Citation format (default: plain)",
    )
    parser.add_argument(
        "--output",
        help="Output Markdown file path",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        print(f"ERROR: project-dir not found: {project_dir}")
        return 1

    accessed_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"generate_citations: scanning {project_dir}")
    entries = extract_log_entries(project_dir)
    print(f"  found {len(entries)} unique source entries across log files")

    md, log_records = build_citations_markdown(entries, args.fmt, accessed_date)

    # Output path
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "reports"
        out_path = out_dir / "citations.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md)
    print(f"  citations written: {out_path} ({len(log_records)} entries)")

    # JSON handoff log
    log = {
        "step": "generate_citations",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(project_dir),
        "format": args.fmt,
        "output": str(out_path),
        "sources_found": len(entries),
        "citations_generated": len([r for r in log_records if r["registry_key"]]),
        "unmatched": len([r for r in log_records if not r["registry_key"]]),
        "citations": log_records,
    }
    log_path = out_path.with_suffix(".log.json")
    log_path.write_text(json.dumps(log, indent=2))
    print(json.dumps({
        "output": str(out_path),
        "sources_found": log["sources_found"],
        "citations_generated": log["citations_generated"],
        "unmatched": log["unmatched"],
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
