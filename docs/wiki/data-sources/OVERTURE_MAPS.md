# Overture Maps Source Page

Source Summary:
The Overture Maps Foundation provides open, interoperable geospatial datasets covering buildings, places (POI), transportation networks, administrative boundaries, addresses, and land use. Data is sourced from OpenStreetMap, Microsoft, Meta, and other contributors, with structured schemas and quality improvements.

Owner / Publisher:
Overture Maps Foundation (Linux Foundation project; members include Microsoft, Meta, Amazon, TomTom)

Geography Support:
Global coverage. Data can be filtered by bounding box.

Time Coverage:
Quarterly releases. First release 2023; rapidly improving coverage and quality.

Access Method:
Primary distribution is GeoParquet on S3 (cloud-native). Use `fetch_overture.py` for direct URL downloads or guided DuckDB/CLI queries.

Fetch Script:
`scripts/core/fetch_overture.py`

Example:
```bash
# Download a specific release file
python scripts/core/fetch_overture.py \
    --url "https://overturemaps-us-west-2.s3.amazonaws.com/release/2024-11-13.0/theme=places/type=place/part-00000.zstd.parquet" \
    -o data/raw/overture_places.parquet

# List available themes
python scripts/core/fetch_overture.py --help-themes

# Guided bbox query (uses overturemaps CLI if installed, or prints DuckDB query)
python scripts/core/fetch_overture.py --bbox -96.2,41.1,-95.8,41.4 \
    --theme places --type place -o data/raw/omaha_places.geojson
```

Credentials:
None required for S3 downloads.

Licensing / Usage Notes:
Open data — released under CDLA Permissive 2.0 license. Free for commercial and non-commercial use. Attribution appreciated.

Known Caveats:
- GeoParquet files are very large — full themes are hundreds of GB
- Bbox-filtered queries require DuckDB or the overturemaps-py CLI (not stdlib Python)
- Data quality varies by region — dense coverage in North America and Europe, sparser elsewhere
- Places data is richer than raw OSM but may not include all local businesses
- Schema differs from OSM tags — use the Overture schema docs for field reference

Themes:
- **buildings** — Building footprints with height, class, and source attribution
- **places** — Points of interest (businesses, amenities, landmarks) with categories
- **transportation** — Road segments and connectors with routing attributes
- **base** — Land use, water bodies, infrastructure areas
- **addresses** — Structured address points
- **divisions** — Administrative and political boundaries

Optional Enhanced Access:
For bbox-filtered queries, install one of:
- `pip install overturemaps` — CLI tool for direct downloads
- DuckDB with spatial extension — SQL queries against S3 parquet files
- Apache Sedona — Spark-based spatial processing

Best-Fit Workflows:
- domains/SITE_SELECTION.md (buildings + places)
- domains/RETAIL.md (places/POI)
- workflows/WITHIN_DISTANCE_ENRICHMENT.md (using places as reference)

Alternatives:
- OpenStreetMap via Overpass API (real-time, tag-based, less structured)
- Google Places API (commercial, richer metadata)
- Foursquare / SafeGraph (commercial POI databases)

Sources:
- https://overturemaps.org/
- https://docs.overturemaps.org/
- S3 bucket: s3://overturemaps-us-west-2/release/

Trust Level:
Medium-High — strong consortium backing with active quality improvement, but younger dataset than OSM.
