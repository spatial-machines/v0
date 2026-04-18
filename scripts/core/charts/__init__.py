"""Statistical chart generation for spatial-machines.

Four families:
  - distribution (histogram, kde, box, violin)
  - comparison   (bar, grouped_bar, lollipop, dot)
  - relationship (scatter, scatter_ols, hexbin, correlation_heatmap)
  - timeseries   (line, area, small_multiples)

Entry point: scripts/core/generate_chart.py (CLI) or the family modules directly.
Every rendered chart writes a PNG (200 DPI), an SVG (vector), and a .style.json
sidecar compatible with the map sidecar schema (chart_family field distinguishes).
"""
