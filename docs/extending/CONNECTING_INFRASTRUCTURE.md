# Connecting Infrastructure

spatial-machines works out of the box with public APIs and local files. But many teams have their own data infrastructure — PostGIS databases, ArcGIS Online portals, cloud data warehouses, or enterprise file shares. This guide covers how to connect them.

## PostGIS Database

### What it enables
- Bulk POI queries against a local OpenStreetMap extract (millions of features, sub-second)
- Storing and querying analysis outputs in a spatial database
- Cross-project data reuse without file duplication

### Setup

1. **Install PostGIS** on your server or use a managed service (AWS RDS, Google Cloud SQL, Azure).

2. **Configure connection** in `.env`:
```bash
OSM_DB_HOST=localhost
OSM_DB_PORT=5432
OSM_DB_NAME=osmdb
OSM_DB_USER=your_user
OSM_DB_PASSWORD=your_password
```

3. **Load OSM data** (if using for POI):
```bash
# Download a regional extract from Geofabrik
wget https://download.geofabrik.de/north-america/us/nebraska-latest.osm.pbf

# Import with osm2pgsql
osm2pgsql -d osmdb -C 4096 --slim -S default.style nebraska-latest.osm.pbf
```

4. **Use the PostGIS fetch script**:
```bash
python scripts/core/fetch_poi_postgis.py --bbox -96.1,41.2,-95.8,41.4 \
    --amenity hospital -o data/raw/hospitals.gpkg
```

### How it integrates
The `fetch_poi.py` script automatically tries PostGIS first and falls back to Overpass API. If your `.env` has the `OSM_DB_*` variables set and the database is reachable, PostGIS will be used. Otherwise, the system works fine without it.

### SSH tunnel for remote databases
If your PostGIS is on another machine:
```bash
ssh -L 5432:localhost:5432 user@your-server -N &
```
Then set `OSM_DB_HOST=localhost` and `OSM_DB_PORT=5432` in `.env`.

---

## ArcGIS Online / ArcGIS Enterprise

### What it enables
- Pulling feature layers from your ArcGIS Online organization
- Accessing Living Atlas and Esri curated datasets
- Publishing analysis outputs to ArcGIS Online (future — see [Publishing Adapters](PUBLISHING_ADAPTERS.md))

### Reading data from ArcGIS REST services

Many public datasets are served via ArcGIS REST services (FEMA, EPA, state GIS portals). You can query them using the same pattern as `fetch_fema_nfhl.py`:

```python
# Generic ArcGIS REST feature layer query
from urllib.request import urlopen
from urllib.parse import urlencode
import json

params = urlencode({
    "where": "1=1",
    "outFields": "*",
    "f": "geojson",
    "resultRecordCount": 2000,
})
url = f"https://your-server.com/arcgis/rest/services/YourService/MapServer/0/query?{params}"
with urlopen(url) as response:
    data = json.load(response)
```

### Authenticated ArcGIS access

For ArcGIS Online or Enterprise with authentication:

1. Add credentials to `.env`:
```bash
ARCGIS_URL=https://your-org.maps.arcgis.com
ARCGIS_USERNAME=your_username
ARCGIS_PASSWORD=your_password
# Or use an API key:
ARCGIS_API_KEY=your_api_key
```

2. Write a fetch script that generates a token and uses it for queries. The `arcgis` Python package simplifies this but is not stdlib — use it if your environment supports it:
```bash
pip install arcgis
```

### Writing a custom ArcGIS fetch script

Follow the pattern in [Adding Data Sources](ADDING_DATA_SOURCES.md), using the ArcGIS REST API query endpoint. Key differences:
- You may need to generate an OAuth2 token before querying
- Handle `exceededTransferLimit` for pagination (same as `fetch_fema_nfhl.py`)
- ArcGIS returns `esriGeometryPolygon` etc. — request `f=geojson` to get standard GeoJSON

---

## GeoServer / GeoNode

### What it enables
- Pulling WFS (Web Feature Service) layers from your GeoServer
- Querying OGC-standard spatial services
- Publishing analysis outputs as WFS/WMS layers (future)

### Reading WFS data

GeoServer exposes OGC WFS endpoints. Query them with standard HTTP:

```bash
# Download GeoJSON from a WFS endpoint
python scripts/core/retrieve_remote.py \
    "https://your-geoserver.com/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=your:layer&outputFormat=application/json&count=5000" \
    -o data/raw/wfs_layer.geojson
```

Or write a dedicated fetch script following the WFS protocol for pagination (`startIndex` parameter).

---

## Cloud Data Warehouses

### BigQuery, Snowflake, Databricks

For teams using cloud data warehouses with spatial support:

1. **Install the client library** for your platform:
```bash
pip install google-cloud-bigquery  # BigQuery
pip install snowflake-connector-python  # Snowflake
pip install databricks-sql-connector  # Databricks
```

2. **Write a fetch script** that queries your warehouse and saves the result as CSV or GeoPackage. Follow the standard pattern — argparse, output file, manifest sidecar.

3. **Store credentials** in `.env` (never in scripts):
```bash
BIGQUERY_PROJECT=your-project
BIGQUERY_CREDENTIALS_FILE=/path/to/service-account.json
# Or
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
```

### Example: BigQuery spatial query
```python
from google.cloud import bigquery
client = bigquery.Client(project="your-project")
query = """
    SELECT geo_id, total_pop, ST_ASGEOJSON(tract_geom) as geometry
    FROM `bigquery-public-data.census_bureau_acs.censustract_2020_5yr`
    WHERE state_fips_code = '31'
"""
df = client.query(query).to_dataframe()
```

---

## Enterprise File Shares / S3 / Azure Blob

### Local network shares
Use `retrieve_local.py` with the mounted path:
```bash
python scripts/core/retrieve_local.py /mnt/gis-share/parcels/county_parcels.gpkg \
    -o data/raw/parcels.gpkg
```

### AWS S3
```bash
# Using AWS CLI (install separately)
aws s3 cp s3://your-bucket/data/parcels.gpkg data/raw/parcels.gpkg

# Or use retrieve_remote.py with a presigned URL
python scripts/core/retrieve_remote.py \
    "https://your-bucket.s3.amazonaws.com/data/parcels.gpkg?presigned-params" \
    -o data/raw/parcels.gpkg
```

### Azure Blob Storage
```bash
# Using Azure CLI
az storage blob download --container data --name parcels.gpkg --file data/raw/parcels.gpkg

# Or use retrieve_remote.py with a SAS URL
python scripts/core/retrieve_remote.py \
    "https://your-account.blob.core.windows.net/data/parcels.gpkg?sv=...&sig=..." \
    -o data/raw/parcels.gpkg
```

---

## General Integration Pattern

Regardless of the infrastructure, the integration pattern is always:

1. **Write a fetch script** that connects to your system and downloads data into `data/raw/`
2. **Write a manifest sidecar** documenting what was retrieved and from where
3. **Store credentials in `.env`** — never in scripts, never in committed files
4. **Register the source** in `config/data_sources.json` and the wiki
5. **Add the script** to `agents/data-retrieval/TOOLS.md`

The rest of the pipeline (processing, analysis, cartography, QA, reporting) doesn't know or care where the data came from — it works with whatever lands in `data/raw/`.
