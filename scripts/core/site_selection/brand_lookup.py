#!/usr/bin/env python3
"""Resolve brand names to OSM tags for POI fetching.

Maintains a JSON lookup table of common retail/QSR/service brands with
their OSM tags, Wikidata IDs, and known competitors. Supports fuzzy
matching (case-insensitive, partial) and a --list flag.

Usage:
    python scripts/core/site_selection/brand_lookup.py --brand "Starbucks"
    python scripts/core/site_selection/brand_lookup.py --brand "starbux"
    python scripts/core/site_selection/brand_lookup.py --list
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BRANDS_PATH = Path(__file__).resolve().parent / "brands.json"


def load_brands(path: Path | None = None) -> list[dict]:
    """Load brand definitions from JSON file."""
    p = path or BRANDS_PATH
    if not p.exists():
        print(f"ERROR: brands file not found: {p}", file=sys.stderr)
        return []
    data = json.loads(p.read_text())
    return data.get("brands", [])


def lookup_brand(name: str, brands: list[dict] | None = None) -> dict | None:
    """Resolve a brand name to its entry. Tries exact, then case-insensitive, then partial."""
    if brands is None:
        brands = load_brands()

    query = name.strip()

    # Exact match
    for b in brands:
        if b["name"] == query:
            return b

    # Case-insensitive match
    q_lower = query.lower()
    for b in brands:
        if b["name"].lower() == q_lower:
            return b

    # Partial / fuzzy match — substring in either direction
    for b in brands:
        b_lower = b["name"].lower()
        if q_lower in b_lower or b_lower in q_lower:
            return b

    # Try stripping common suffixes/prefixes and re-matching
    stripped = q_lower.replace("'s", "").replace("'", "").replace("-", " ")
    for b in brands:
        b_stripped = b["name"].lower().replace("'s", "").replace("'", "").replace("-", " ")
        if stripped in b_stripped or b_stripped in stripped:
            return b

    return None


def resolve_brand(name: str, brands: list[dict] | None = None) -> dict:
    """Resolve brand name and return a structured result dict.

    Returns:
        {"found": True, "brand": {...}} or
        {"found": False, "query": name, "suggestion": "Specify tags manually"}
    """
    entry = lookup_brand(name, brands)
    if entry:
        return {"found": True, "brand": entry}
    return {
        "found": False,
        "query": name,
        "suggestion": "Brand not found. Specify OSM tags manually with --tag.",
    }


def list_brands(brands: list[dict] | None = None) -> None:
    """Print all known brands grouped by category."""
    if brands is None:
        brands = load_brands()

    categories: dict[str, list[str]] = {}
    for b in brands:
        cat = b.get("category", "other")
        categories.setdefault(cat, []).append(b["name"])

    print("Known brands:")
    for cat in sorted(categories):
        names = sorted(categories[cat])
        print(f"  {cat}: {', '.join(names)}")
    print(f"\nTotal: {len(brands)} brands across {len(categories)} categories")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Resolve brand names to OSM tags for POI fetching."
    )
    parser.add_argument("--brand", help="Brand name to look up")
    parser.add_argument("--list", action="store_true", help="List all known brands")
    parser.add_argument("--brands-file", default=None,
                        help="Path to brands JSON (default: brands.json alongside this script)")
    args = parser.parse_args()

    brands = load_brands(Path(args.brands_file) if args.brands_file else None)

    if args.list:
        list_brands(brands)
        return 0

    if not args.brand:
        parser.print_help()
        return 1

    result = resolve_brand(args.brand, brands)
    print(json.dumps(result, indent=2))

    return 0 if result["found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
