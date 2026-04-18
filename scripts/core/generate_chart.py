#!/usr/bin/env python3
"""Generate a statistical chart as a required analysis output.

Routes to the right family (distribution / comparison / relationship /
timeseries) and writes PNG + SVG + .style.json sidecar.

Usage examples:

  # Histogram
  python scripts/core/generate_chart.py distribution \\
      --data analyses/p1/data/processed/tracts.gpkg \\
      --field poverty_rate \\
      --kind histogram \\
      --output analyses/p1/outputs/charts/poverty_histogram.png \\
      --title "Poverty rate distribution" \\
      --attribution "U.S. Census Bureau ACS 5-Year, 2022"

  # Bar: top counties
  python scripts/core/generate_chart.py comparison \\
      --data counties.csv \\
      --category-field county --value-field poverty_rate \\
      --kind bar --top-n 15 \\
      --output outputs/charts/top_counties.png

  # Scatter with OLS
  python scripts/core/generate_chart.py relationship \\
      --data tracts.gpkg \\
      --x-field median_income --y-field poverty_rate \\
      --kind scatter_ols \\
      --output outputs/charts/income_vs_poverty.png

  # Correlation heatmap
  python scripts/core/generate_chart.py relationship \\
      --data tracts.gpkg \\
      --fields median_income poverty_rate unemployment pct_bachelors \\
      --kind correlation_heatmap \\
      --output outputs/charts/correlations.png

  # Time series
  python scripts/core/generate_chart.py timeseries \\
      --data poverty_by_year.csv --time-field year --value-field poverty_rate \\
      --kind line \\
      --output outputs/charts/poverty_trend.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_CORE = Path(__file__).resolve().parent
if str(SCRIPTS_CORE) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_CORE))

from charts import distribution, comparison, relationship, timeseries


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a statistical chart as a required analysis output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="family", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", required=True,
                        help="Path to CSV, Parquet, GeoPackage, or GeoJSON")
    common.add_argument("--layer", help="GeoPackage layer name (for .gpkg inputs)")
    common.add_argument("--output", required=True,
                        help="Output path; .png/.svg/.style.json siblings are written")
    common.add_argument("--title")
    common.add_argument("--subtitle")
    common.add_argument("--attribution", help="Source citation text")

    # distribution
    p_dist = sub.add_parser("distribution", parents=[common],
                            help="histogram / kde / box / violin")
    p_dist.add_argument("--field", required=True)
    p_dist.add_argument("--kind", default="histogram",
                        choices=list(distribution.KINDS))
    p_dist.add_argument("--bins", type=int, default=30)

    # comparison
    p_cmp = sub.add_parser("comparison", parents=[common],
                           help="bar / grouped_bar / lollipop / dot")
    p_cmp.add_argument("--category-field", required=True)
    p_cmp.add_argument("--value-field")
    p_cmp.add_argument("--value-fields", nargs="+",
                       help="Required for grouped_bar")
    p_cmp.add_argument("--kind", default="bar",
                       choices=list(comparison.KINDS))
    p_cmp.add_argument("--top-n", type=int)
    p_cmp.add_argument("--sort", choices=["ascending", "descending", "none"])
    p_cmp.add_argument("--vertical", action="store_true",
                       help="Vertical bars (default: horizontal)")

    # relationship
    p_rel = sub.add_parser("relationship", parents=[common],
                           help="scatter / scatter_ols / hexbin / correlation_heatmap")
    p_rel.add_argument("--x-field")
    p_rel.add_argument("--y-field")
    p_rel.add_argument("--fields", nargs="+",
                       help="Required for correlation_heatmap")
    p_rel.add_argument("--kind", default="scatter",
                       choices=list(relationship.KINDS))
    p_rel.add_argument("--gridsize", type=int, default=30)

    # timeseries
    p_ts = sub.add_parser("timeseries", parents=[common],
                          help="line / area / small_multiples")
    p_ts.add_argument("--time-field", required=True)
    p_ts.add_argument("--value-field")
    p_ts.add_argument("--value-fields", nargs="+")
    p_ts.add_argument("--panel-field",
                      help="Required for small_multiples")
    p_ts.add_argument("--kind", default="line", choices=list(timeseries.KINDS))

    return p


def main() -> int:
    args = build_parser().parse_args()

    kwargs = {
        "data": args.data,
        "output": args.output,
        "title": args.title,
        "subtitle": args.subtitle,
        "attribution": args.attribution,
        "layer": args.layer,
        "kind": args.kind,
    }

    if args.family == "distribution":
        result = distribution.render(
            field=args.field, bins=args.bins, **kwargs,
        )
    elif args.family == "comparison":
        result = comparison.render(
            category_field=args.category_field,
            value_field=args.value_field,
            value_fields=args.value_fields,
            top_n=args.top_n,
            sort=args.sort,
            horizontal=not args.vertical,
            **kwargs,
        )
    elif args.family == "relationship":
        result = relationship.render(
            x_field=args.x_field, y_field=args.y_field,
            fields=args.fields, gridsize=args.gridsize, **kwargs,
        )
    elif args.family == "timeseries":
        result = timeseries.render(
            time_field=args.time_field,
            value_field=args.value_field,
            value_fields=args.value_fields,
            panel_field=args.panel_field,
            **kwargs,
        )
    else:
        print(f"unknown family: {args.family}", file=sys.stderr)
        return 2

    print(f"chart: {result['png']}")
    print(f"svg:   {result['svg']}")
    print(f"sidecar: {result['sidecar']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
