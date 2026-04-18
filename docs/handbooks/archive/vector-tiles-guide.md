# Vector Tiles Guide

_Serving and consuming vector tiles with Martin and MapLibre GL JS._

---

## Overview

Vector tiles enable fast, client-rendered maps that scale from local to global without a tile server for every zoom level. This project uses:

- **Martin** (open source Rust, Apache 2.0) — self-hosted tile server backed by PostGIS
- **PMTiles** — single-file tile archive format for offline/static delivery
- **MapLibre GL JS** — open source web map renderer (MIT) for consuming tiles

No Mapbox. No Esri. No CARTO.

---

## Architecture

```
PostGIS (analyses schema)
    └─► Martin tile server (port 3000)
            └─► MapLibre GL JS (browser)

OR

PostGIS / GeoPackage
    └─► tippecanoe / pmtiles
            └─► .pmtiles file
                    └─► MapLibre GL JS (via pmtiles protocol)
```

---

## Starting Martin

```bash
# Martin requires PostGIS to be healthy first
docker compose \
  -f docker/docker-compose.postgis.yml \
  -f docker/docker-compose.tiles.yml \
  up -d

# Verify Martin is running
curl http://localhost:3000/catalog
```

Martin auto-discovers all tables in PostGIS. Any table in the `analyses` schema with a geometry column is automatically available as a tile endpoint.

**Tile URL pattern:**
```
http://localhost:3000/{schema}.{table_name}/{z}/{x}/{y}
```

Example:
```
http://localhost:3000/analyses.mn_tracts/{z}/{x}/{y}
```

---

## Publishing a Layer

Use `publish_tiles.py` to upload a GeoPackage to PostGIS and register it with Martin:

```bash
# Publish a GeoPackage
python scripts/publish_tiles.py \
    --input data/processed/mn_tracts.gpkg \
    --layer-name mn_tracts \
    --min-zoom 4 \
    --max-zoom 12

# Publish and save a PMTiles file for offline delivery
python scripts/publish_tiles.py \
    --input data/processed/mn_tracts.gpkg \
    --layer-name mn_tracts \
    --output-pmtiles outputs/tiles/mn_tracts.pmtiles

# Publish a PostGIS table already loaded in the database
python scripts/publish_tiles.py \
    --input analyses.mn_tracts \
    --layer-name mn_tracts
```

The script outputs:
- Tile endpoint URL
- MapLibre GL JS snippet for immediate use
- Optional `.pmtiles` file
- JSON log

---

## Consuming Tiles in MapLibre GL JS

### Live PostGIS tiles via Martin

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.css" />
  <script src="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.js"></script>
  <style>
    body { margin: 0; }
    #map { width: 100vw; height: 100vh; }
  </style>
</head>
<body>
<div id="map"></div>
<script>
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',  // open base map
  center: [-94.0, 46.0],
  zoom: 6
});

map.on('load', () => {
  // Add PostGIS vector tile source via Martin
  map.addSource('mn_tracts', {
    type: 'vector',
    tiles: ['http://localhost:3000/analyses.mn_tracts/{z}/{x}/{y}'],
    minzoom: 4,
    maxzoom: 14
  });

  // Choropleth fill layer
  map.addLayer({
    id: 'tracts-fill',
    type: 'fill',
    source: 'mn_tracts',
    'source-layer': 'mn_tracts',  // layer name within the tile
    paint: {
      'fill-color': [
        'interpolate', ['linear'],
        ['get', 'poverty_rate'],
        0,    '#ffffcc',
        0.10, '#a1dab4',
        0.20, '#41b6c4',
        0.30, '#2c7fb8',
        0.40, '#253494'
      ],
      'fill-opacity': 0.8
    }
  });

  // Outline layer
  map.addLayer({
    id: 'tracts-outline',
    type: 'line',
    source: 'mn_tracts',
    'source-layer': 'mn_tracts',
    paint: {
      'line-color': '#ffffff',
      'line-width': 0.5,
      'line-opacity': 0.5
    }
  });

  // Click popup
  map.on('click', 'tracts-fill', (e) => {
    const props = e.features[0].properties;
    new maplibregl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(`
        <strong>${props.namelsad}</strong><br>
        Poverty rate: ${(props.poverty_rate * 100).toFixed(1)}%
      `)
      .addTo(map);
  });

  map.on('mouseenter', 'tracts-fill', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'tracts-fill', () => {
    map.getCanvas().style.cursor = '';
  });
});
</script>
</body>
</html>
```

### PMTiles (offline/static)

PMTiles is a single-file format that can be served from any static host (S3, Cloudflare R2, GitHub Pages). No tile server required.

```html
<script src="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/pmtiles@latest/dist/pmtiles.js"></script>
<script>
// Register PMTiles protocol with MapLibre
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
  center: [-94.0, 46.0],
  zoom: 6
});

map.on('load', () => {
  map.addSource('mn_tracts', {
    type: 'vector',
    url: 'pmtiles://outputs/tiles/mn_tracts.pmtiles'
  });

  map.addLayer({
    id: 'tracts-fill',
    type: 'fill',
    source: 'mn_tracts',
    'source-layer': 'mn_tracts',
    paint: {
      'fill-color': '#41b6c4',
      'fill-opacity': 0.7
    }
  });
});
</script>
```

---

## PMTiles vs Live PostGIS Tiles — When to Use Which

| Scenario | Recommendation |
|---|---|
| Interactive web map updated daily | **Martin + PostGIS** — data auto-updates when PostGIS is updated |
| Client deliverable (offline, static) | **PMTiles** — single file, no server dependency |
| Public web portfolio / GitHub Pages | **PMTiles** — host on S3/R2/GH Pages, no server required |
| Large dataset (>50M features) | **Martin + PostGIS** — PostGIS spatial index handles scale; PMTiles file would be huge |
| Rapid prototyping | **Martin + PostGIS** — publish_tiles.py is fast, no file to generate |
| Long-term archival | **PMTiles** — self-contained, readable in 10 years with any compliant reader |
| Multi-layer story map | **Martin + PostGIS** — manage many layers centrally, add/remove without regenerating |
| Mobile / field use | **PMTiles** — download once, works without connectivity |

**Rule of thumb:**
- Serving live to a web app → Martin
- Delivering to a client or archiving → PMTiles
- Both → use `publish_tiles.py --output-pmtiles` to generate both simultaneously

---

## Zoom Level Guidelines

| Geography | Recommended zoom range |
|---|---|
| National (US) | 2–8 |
| State-level | 4–10 |
| County-level | 6–12 |
| Census tract | 8–14 |
| Parcel/block | 12–18 |
| Points of interest | 4–18 |

Higher max zoom = more detail but larger tile files. For most analyses, `--max-zoom 14` is the sweet spot.

---

## Martin Configuration

Martin can also be configured via a YAML file for more control:

```yaml
# martin.yaml
listen_addresses: "0.0.0.0:3000"
connection_string: "postgresql://gis:gis@postgis:5432/gisdb"
cache_size: 256  # MB

# Expose only the analyses schema
postgres:
  connection_string: "postgresql://gis:gis@postgis:5432/gisdb"
  default_srid: 4326
  pool_size: 20

# Health check endpoint
health_check: true
```

Mount via Docker:
```yaml
services:
  martin:
    volumes:
      - ./martin.yaml:/config/martin.yaml
    command: --config /config/martin.yaml
```

---

## Troubleshooting

**Martin returns 404 for a layer:**
- Verify the table exists: `SELECT * FROM analyses.spatial_layers WHERE table_name = 'your_table';`
- Restart Martin after uploading new layers: `docker compose restart martin`
- Check Martin logs: `docker compose logs martin`

**Tiles are slow at high zoom:**
- Add a spatial index: `CREATE INDEX ON analyses.your_table USING GIST (geometry);`
- Vacuum the table: `VACUUM ANALYZE analyses.your_table;`
- Reduce `--max-zoom` to 12 for polygon layers

**PMTiles generation fails:**
- Install tippecanoe for best results: `brew install tippecanoe` or `apt-get install tippecanoe`
- For the Python fallback: `pip install pmtiles`
