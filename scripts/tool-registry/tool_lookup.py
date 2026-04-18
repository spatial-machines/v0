#!/usr/bin/env python3
"""
GIS Tool Registry Lookup
========================
Query the tool registry by keyword, category, exec_route, or tool_id.

Usage examples:
  python3 tool_lookup.py --search "slope analysis"
  python3 tool_lookup.py --search "buffer" --exec-route pure_python
  python3 tool_lookup.py --category terrain
  python3 tool_lookup.py --exec-route rasterio
  python3 tool_lookup.py --id gdal:aspect
  python3 tool_lookup.py --list-categories
  python3 tool_lookup.py --top20

Python API:
  from tool_lookup import GISToolRegistry
  reg = GISToolRegistry()
  tools = reg.search("watershed delineation", exec_route="grass")
  tool = reg.get("gdal:aspect")
"""

import json
import re
import argparse
from pathlib import Path
from typing import Optional


REGISTRY_PATH = Path(__file__).parent / "tool_registry.json"
VALID_CATEGORIES = [
    "terrain", "raster_ops", "vector_ops", "network", "hydrology",
    "interpolation", "classification", "statistics", "visualization",
    "format_conversion", "remote_sensing"
]
VALID_EXEC_ROUTES = ["rasterio", "pure_python", "gdal_cli", "qgis_headless", "grass"]


class GISToolRegistry:
    """Queryable interface for the GIS tool registry."""

    def __init__(self, registry_path: str = None):
        path = Path(registry_path) if registry_path else REGISTRY_PATH
        with open(path) as f:
            self._tools = json.load(f)
        self._index = {t["tool_id"]: t for t in self._tools}

    def get(self, tool_id: str) -> Optional[dict]:
        """Fetch a single tool by its exact ID (e.g., 'gdal:aspect')."""
        return self._index.get(tool_id)

    def search(
        self,
        query: str,
        exec_route: str = None,
        category: str = None,
        provider: str = None,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Search tools by keyword across name, descriptions, and use_cases.

        Args:
            query: Free-text search query
            exec_route: Filter by execution route (rasterio, pure_python, gdal_cli, qgis_headless, grass)
            category: Filter by category (terrain, vector_ops, hydrology, etc.)
            provider: Filter by provider prefix (gdal, native, grass7, qgis, 3d)
            max_results: Maximum number of results to return

        Returns:
            List of matching tool dicts, sorted by relevance score
        """
        query_terms = re.findall(r'\w+', query.lower())

        results = []
        for tool in self._tools:
            # Apply filters first
            if exec_route and tool["exec_route"] != exec_route:
                continue
            if category and tool["category"] != category:
                continue
            if provider and tool["provider"] != provider:
                continue

            # Score against query terms
            score = self._score_tool(tool, query_terms, query.lower())
            if score > 0:
                results.append((score, tool))

        # Sort by score descending
        results.sort(key=lambda x: -x[0])
        return [t for _, t in results[:max_results]]

    def filter(
        self,
        exec_route: str = None,
        category: str = None,
        provider: str = None,
        has_python_equivalent: bool = None,
    ) -> list[dict]:
        """Filter tools by field values without keyword search."""
        results = []
        for tool in self._tools:
            if exec_route and tool["exec_route"] != exec_route:
                continue
            if category and tool["category"] != category:
                continue
            if provider and tool["provider"] != provider:
                continue
            if has_python_equivalent is not None:
                if has_python_equivalent and not tool.get("python_equivalent"):
                    continue
                if not has_python_equivalent and tool.get("python_equivalent"):
                    continue
            results.append(tool)
        return results

    def summary(self) -> dict:
        """Return a summary of the registry contents."""
        from collections import Counter
        cats = Counter(t["category"] for t in self._tools)
        routes = Counter(t["exec_route"] for t in self._tools)
        providers = Counter(t["provider"] for t in self._tools)
        with_py_equiv = sum(1 for t in self._tools if t.get("python_equivalent"))
        return {
            "total_tools": len(self._tools),
            "by_category": dict(sorted(cats.items())),
            "by_exec_route": dict(sorted(routes.items())),
            "by_provider": dict(sorted(providers.items())),
            "tools_with_python_equivalent": with_py_equiv,
        }

    def _score_tool(self, tool: dict, terms: list, raw_query: str) -> float:
        """Score a tool's relevance to a query."""
        score = 0.0

        # Tool ID exact/partial match (highest weight)
        tool_id = tool["tool_id"].lower()
        if raw_query in tool_id:
            score += 10
        for term in terms:
            if term in tool_id:
                score += 3

        # Tool name match
        tool_name = tool["tool_name"].lower()
        if raw_query in tool_name:
            score += 8
        for term in terms:
            if term in tool_name:
                score += 2

        # Brief description match
        brief = tool.get("brief_description", "").lower()
        for term in terms:
            if term in brief:
                score += 1.5

        # Full description match
        full = tool.get("full_description", "").lower()
        for term in terms:
            if term in full:
                score += 1

        # Use cases match
        use_cases_text = " ".join(tool.get("use_cases", [])).lower()
        for term in terms:
            if term in use_cases_text:
                score += 0.5

        # Category match
        if raw_query in tool.get("category", ""):
            score += 2

        return score

    def format_tool(self, tool: dict, verbose: bool = False) -> str:
        """Format a tool for display."""
        lines = [
            f"  tool_id:     {tool['tool_id']}",
            f"  name:        {tool['tool_name']}",
            f"  category:    {tool['category']}",
            f"  exec_route:  {tool['exec_route']}",
            f"  brief:       {tool['brief_description'][:100]}...",
        ]
        if tool.get("python_equivalent"):
            lines.append(f"  python:      {tool['python_equivalent']}")
        if tool.get("python_libs"):
            lines.append(f"  libs:        {', '.join(tool['python_libs'])}")
        if verbose:
            lines.append(f"  full_description: {tool['full_description'][:300]}...")
            lines.append(f"  parameters ({len(tool['parameters'])} total):")
            for p in tool["parameters"][:5]:
                req = "required" if p.get("required") else "optional"
                lines.append(f"    - {p['name']} ({p['type']}, {req}): {p['description'][:80]}")
            if len(tool["parameters"]) > 5:
                lines.append(f"    ... and {len(tool['parameters'])-5} more")
            lines.append(f"  use_cases:")
            for uc in tool.get("use_cases", []):
                lines.append(f"    - {uc}")
            if tool.get("related_tools"):
                lines.append(f"  related:     {', '.join(tool['related_tools'])}")
            if tool.get("original_code_example"):
                lines.append(f"  code_example (QGIS):\n{tool['original_code_example'][:500]}")
        return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────────

TOP20_CONSULTING_TOOLS = [
    "native:buffer",
    "native:clip",
    "native:dissolve",
    "native:intersection",
    "native:joinattributesbylocation",
    "native:reprojectlayer",
    "native:zonalstatisticsfb",
    "native:extractbyattribute",
    "native:extractbylocation",
    "native:fixgeometries",
    "gdal:cliprasterbymasklayer",
    "gdal:aspect",
    "gdal:slope",
    "gdal:hillshade",
    "gdal:merge",
    "gdal:contour",
    "gdal:warpreproject",
    "gdal:proximity",
    "gdal:rastercalculator",
    "grass7:r.watershed",
]


def main():
    parser = argparse.ArgumentParser(
        description="Query the GIS Tool Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--search", "-s", help="Search by keyword")
    parser.add_argument("--id", help="Look up a specific tool by ID (e.g., gdal:aspect)")
    parser.add_argument("--category", "-c", choices=VALID_CATEGORIES, help="Filter by category")
    parser.add_argument("--exec-route", "-e", choices=VALID_EXEC_ROUTES, help="Filter by exec route")
    parser.add_argument("--provider", "-p", help="Filter by provider (gdal, native, grass7, qgis)")
    parser.add_argument("--list-categories", action="store_true", help="List all categories with counts")
    parser.add_argument("--list-routes", action="store_true", help="List all exec routes with counts")
    parser.add_argument("--top20", action="store_true", help="Show top 20 consulting tools")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full tool details")
    parser.add_argument("--max-results", "-n", type=int, default=10, help="Max results to show (default: 10)")
    parser.add_argument("--registry", help="Path to registry JSON file (default: ./tool_registry.json)")
    parser.add_argument("--json-output", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    reg = GISToolRegistry(args.registry)

    if args.list_categories or args.list_routes:
        summary = reg.summary()
        if args.list_categories:
            print("\n── Categories ──────────────────────────────")
            for cat, count in summary["by_category"].items():
                print(f"  {cat:<30} {count:>4} tools")
        if args.list_routes:
            print("\n── Exec Routes ─────────────────────────────")
            for route, count in summary["by_exec_route"].items():
                print(f"  {route:<20} {count:>4} tools")
        print(f"\nTotal: {summary['total_tools']} tools")
        print(f"With Python equivalent: {summary['tools_with_python_equivalent']}")
        return

    if args.top20:
        print("\n── Top 20 GIS Consulting Tools ─────────────────────────────")
        for tid in TOP20_CONSULTING_TOOLS:
            tool = reg.get(tid)
            if tool:
                print(f"\n[{tid}]")
                print(reg.format_tool(tool, verbose=args.verbose))
            else:
                print(f"\n[{tid}] - NOT FOUND IN REGISTRY")
        return

    if args.id:
        tool = reg.get(args.id)
        if tool:
            if args.json_output:
                print(json.dumps(tool, indent=2))
            else:
                print(f"\n── {args.id} ───────────────────────────────")
                print(reg.format_tool(tool, verbose=True))
        else:
            print(f"Tool not found: {args.id}")
            # Try fuzzy match
            candidates = reg.search(args.id.split(":")[-1], max_results=3)
            if candidates:
                print(f"\nDid you mean one of these?")
                for c in candidates:
                    print(f"  {c['tool_id']}: {c['brief_description'][:80]}")
        return

    # Search or filter
    if args.search:
        results = reg.search(
            args.search,
            exec_route=args.exec_route,
            category=args.category,
            provider=args.provider,
            max_results=args.max_results,
        )
        label = f"Search: '{args.search}'"
    else:
        results = reg.filter(
            exec_route=args.exec_route,
            category=args.category,
            provider=args.provider,
        )[:args.max_results]
        parts = []
        if args.category:
            parts.append(f"category={args.category}")
        if args.exec_route:
            parts.append(f"exec_route={args.exec_route}")
        if args.provider:
            parts.append(f"provider={args.provider}")
        label = "Filter: " + (", ".join(parts) if parts else "all tools")

    if args.json_output:
        print(json.dumps(results, indent=2))
        return

    print(f"\n── {label} ({len(results)} results) ──────────────────────────")
    for tool in results:
        print(f"\n[{tool['tool_id']}]")
        print(reg.format_tool(tool, verbose=args.verbose))

    if not results:
        print("No matching tools found.")
        print("Try: python3 tool_lookup.py --list-categories")


if __name__ == "__main__":
    main()
