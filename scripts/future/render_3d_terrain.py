#!/usr/bin/env python3
"""3D Terrain Visualization — combine DEM elevation with optional thematic overlay.

Generates two outputs:
  1. PNG preview — matplotlib mpl_toolkits.mplot3d with hillshade lighting
  2. HTML page  — self-contained MapLibre GL JS + deck.gl TerrainLayer (all open source)

Open source only:
  - MapLibre GL JS (BSD-3-Clause) via unpkg CDN
  - deck.gl TerrainLayer (Apache 2.0) via unpkg CDN
  - rasterio (BSD) for DEM reading and tile export
  - geopandas (BSD) for overlay GeoPackage
  - matplotlib (BSD) for PNG preview
  - numpy (BSD) for array math

Usage:
    python render_3d_terrain.py \\
        --dem data/rasters/dem.tif \\
        --overlay data/processed/tracts.gpkg \\
        --overlay-col poverty_rate \\
        --output-html outputs/terrain/terrain_viewer.html \\
        --output-png  outputs/terrain/terrain_preview.png \\
        --title "Poverty Rate Over Minnesota Terrain" \\
        --exaggeration 2.5

    # DEM only (no overlay)
    python render_3d_terrain.py \\
        --dem data/rasters/dem.tif \\
        --output-html outputs/terrain/terrain_viewer.html \\
        --output-png  outputs/terrain/terrain_preview.png
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# DEM reading
# ---------------------------------------------------------------------------

def read_dem(dem_path: Path) -> tuple[np.ndarray, object, dict]:
    """Read DEM raster. Returns (array, transform, profile)."""
    try:
        import rasterio
        from rasterio.enums import Resampling
    except ImportError:
        print("ERROR: rasterio required. Install with: pip install rasterio", file=sys.stderr)
        sys.exit(1)

    with rasterio.open(dem_path) as src:
        profile = src.profile.copy()
        # Reproject to EPSG:4326 if not already
        crs = src.crs
        if crs and not crs.to_epsg() == 4326:
            from rasterio.warp import calculate_default_transform, reproject
            transform, width, height = calculate_default_transform(
                src.crs, "EPSG:4326", src.width, src.height, *src.bounds
            )
            data = np.zeros((height, width), dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=data,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs="EPSG:4326",
                resampling=Resampling.bilinear,
            )
            nodata = src.nodata
            profile.update({"crs": "EPSG:4326", "transform": transform,
                            "width": width, "height": height})
        else:
            data = src.read(1).astype(np.float32)
            transform = src.transform
            nodata = src.nodata

        if nodata is not None:
            data[data == nodata] = np.nan

        # Bounds [west, south, east, north]
        from rasterio.transform import array_bounds
        bounds = array_bounds(profile.get("height", data.shape[0]),
                              profile.get("width", data.shape[1]), transform)
        # (south, west, north, east) from rasterio
        profile["bounds"] = {
            "west": bounds[0], "south": bounds[1],
            "east": bounds[2], "north": bounds[3],
        }
        profile["transform_obj"] = transform

    return data, transform, profile


# ---------------------------------------------------------------------------
# Hillshade helper
# ---------------------------------------------------------------------------

def compute_hillshade(arr: np.ndarray, transform, azimuth: float = 315.0, altitude: float = 45.0) -> np.ndarray:
    """Compute hillshade array (0–255)."""
    az_rad = np.deg2rad(360.0 - azimuth + 90.0)
    alt_rad = np.deg2rad(altitude)

    # Pixel sizes
    px = abs(transform.a) if hasattr(transform, "a") else abs(transform[0])
    py = abs(transform.e) if hasattr(transform, "e") else abs(transform[4])

    arr_f = arr.astype(float)
    nan_mask = np.isnan(arr_f)
    arr_f[nan_mask] = 0.0

    dz_dx = np.gradient(arr_f, px, axis=1)
    dz_dy = np.gradient(arr_f, py, axis=0)

    slope = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))
    aspect = np.arctan2(-dz_dy, dz_dx)

    hs = (np.cos(alt_rad) * np.cos(slope) +
          np.sin(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
    hs = np.clip(hs, 0, 1) * 255.0
    hs[nan_mask] = 0.0
    return hs.astype(np.float32)


# ---------------------------------------------------------------------------
# PNG output — matplotlib 3D
# ---------------------------------------------------------------------------

def render_png(
    dem_array: np.ndarray,
    transform,
    output_path: Path,
    title: str,
    exaggeration: float,
    max_pixels: int = 200,
) -> None:
    """Render a 3D perspective PNG with hillshade lighting."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        from matplotlib.colors import LightSource
    except ImportError:
        print("ERROR: matplotlib required. Install with: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    print("  Generating PNG 3D preview...")

    # Downsample for performance
    h, w = dem_array.shape
    step_y = max(1, h // max_pixels)
    step_x = max(1, w // max_pixels)
    arr = dem_array[::step_y, ::step_x]

    # Replace NaN with min
    nan_mask = np.isnan(arr)
    fill_val = np.nanmin(arr) if not np.all(nan_mask) else 0.0
    arr_filled = np.where(nan_mask, fill_val, arr)

    rows, cols = arr_filled.shape
    # Build lat/lon grids from transform
    xs = np.linspace(transform.c, transform.c + transform.a * (w - 1), cols)
    ys = np.linspace(transform.f, transform.f + transform.e * (h - 1), rows)
    X, Y = np.meshgrid(xs, ys)
    Z = arr_filled * exaggeration

    # Hillshade for coloring
    ls = LightSource(azdeg=315, altdeg=45)
    hs = ls.hillshade(arr_filled, vert_exag=exaggeration, dx=abs(transform.a), dy=abs(transform.e))
    rgba = ls.shade(arr_filled, cmap=plt.cm.terrain, vert_exag=exaggeration,
                    blend_mode="overlay",
                    dx=abs(transform.a), dy=abs(transform.e))

    fig = plt.figure(figsize=(12, 8), facecolor="#1a1a2e")
    ax = fig.add_subplot(111, projection="3d", facecolor="#1a1a2e")

    surf = ax.plot_surface(
        X, Y, Z,
        facecolors=rgba,
        linewidth=0,
        antialiased=True,
        shade=False,
    )

    ax.set_title(title, color="white", fontsize=14, pad=12)
    ax.set_xlabel("Longitude", color="#aaaaaa", fontsize=8)
    ax.set_ylabel("Latitude", color="#aaaaaa", fontsize=8)
    ax.set_zlabel(f"Elevation (×{exaggeration})", color="#aaaaaa", fontsize=8)
    ax.tick_params(colors="#888888", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    ax.view_init(elev=30, azim=-75)
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="#1a1a2e", edgecolor="none")
    plt.close(fig)
    print(f"  ✅ PNG saved: {output_path}")


# ---------------------------------------------------------------------------
# DEM → PNG tile for TerrainLayer (Terrarium encoding)
# ---------------------------------------------------------------------------

def encode_terrarium(arr: np.ndarray) -> np.ndarray:
    """Encode elevation array as Terrarium RGB tiles (meters → RGB24).
    Formula: elevation = (R * 256 + G + B / 256) - 32768
    → R = floor((elev + 32768) / 256)
    → G = floor((elev + 32768) % 256)
    → B = floor(((elev + 32768) - floor(elev + 32768)) * 256)
    """
    nan_mask = np.isnan(arr)
    elev = np.where(nan_mask, 0.0, arr + 32768.0)
    R = np.floor(elev / 256.0).astype(np.uint8)
    G = np.floor(elev % 256.0).astype(np.uint8)
    B = np.floor((elev - np.floor(elev)) * 256.0).astype(np.uint8)
    rgb = np.stack([R, G, B], axis=-1)
    return rgb


def export_dem_as_png_tile(dem_array: np.ndarray, output_dir: Path) -> str:
    """Export DEM as a single Terrarium-encoded PNG tile. Returns relative URL."""
    try:
        from PIL import Image
    except ImportError:
        print("WARNING: Pillow not available, using base64 embedded approach", file=sys.stderr)
        return None

    tile_dir = output_dir / "tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)

    # Terrarium encode
    rgb = encode_terrarium(dem_array)
    img = Image.fromarray(rgb, mode="RGB")
    tile_path = tile_dir / "dem_terrarium.png"
    img.save(tile_path, format="PNG")
    return "tiles/dem_terrarium.png"


def dem_to_base64_terrarium(dem_array: np.ndarray) -> tuple[str, int, int]:
    """Encode DEM as base64 Terrarium PNG for inline embedding."""
    try:
        from PIL import Image
    except ImportError:
        # Fallback: just encode as raw 16-bit grayscale via numpy only
        return None, 0, 0

    rgb = encode_terrarium(dem_array)
    img = Image.fromarray(rgb, mode="RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return b64, dem_array.shape[1], dem_array.shape[0]


# ---------------------------------------------------------------------------
# Overlay GeoJSON loading
# ---------------------------------------------------------------------------

def load_overlay_geojson(overlay_path: Path, overlay_col: str) -> dict | None:
    """Load GeoPackage overlay and return as GeoJSON dict with normalized values."""
    if not overlay_path or not overlay_path.exists():
        return None
    try:
        import geopandas as gpd
    except ImportError:
        print("WARNING: geopandas not available; skipping overlay", file=sys.stderr)
        return None

    gdf = gpd.read_file(overlay_path)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    if overlay_col and overlay_col in gdf.columns:
        # Normalize 0–1 for color scaling
        col_vals = gdf[overlay_col].dropna()
        vmin, vmax = col_vals.min(), col_vals.max()
        gdf["_norm_val"] = (gdf[overlay_col] - vmin) / (vmax - vmin + 1e-9)
        gdf["_raw_val"] = gdf[overlay_col]
        gdf["_col_label"] = overlay_col
    else:
        gdf["_norm_val"] = 0.5
        gdf["_raw_val"] = 0
        gdf["_col_label"] = ""

    return json.loads(gdf.to_json())


# ---------------------------------------------------------------------------
# HTML output — MapLibre GL JS + deck.gl TerrainLayer
# ---------------------------------------------------------------------------

def render_html(
    dem_array: np.ndarray,
    transform,
    profile: dict,
    output_path: Path,
    title: str,
    exaggeration: float,
    overlay_geojson: dict | None,
    overlay_col: str | None,
) -> None:
    """Generate self-contained MapLibre GL JS HTML with deck.gl TerrainLayer."""
    print("  Generating HTML 3D terrain viewer...")

    bounds = profile.get("bounds", {})
    west = bounds.get("west", -100)
    south = bounds.get("south", 40)
    east = bounds.get("east", -90)
    north = bounds.get("north", 50)
    center_lon = (west + east) / 2
    center_lat = (south + north) / 2

    # Encode DEM as base64 Terrarium PNG
    b64_dem, tile_w, tile_h = dem_to_base64_terrarium(dem_array)

    # Prepare overlay GeoJSON block
    overlay_js = "null"
    overlay_col_js = "null"
    if overlay_geojson:
        overlay_js = json.dumps(overlay_geojson)
        overlay_col_js = json.dumps(overlay_col or "")

    # If Pillow unavailable, fall back to flat elevation image
    dem_data_url = f"data:image/png;base64,{b64_dem}" if b64_dem else ""
    dem_available = "true" if b64_dem else "false"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0f0f1a; color: #f0f0f0; font-family: 'Segoe UI', system-ui, sans-serif; height: 100vh; overflow: hidden; }}
    #app {{ position: relative; width: 100%; height: 100vh; }}
    #map {{ width: 100%; height: 100%; }}
    #header {{
      position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
      background: rgba(15,15,26,0.85); backdrop-filter: blur(8px);
      padding: 8px 18px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.12);
      font-size: 14px; font-weight: 600; color: #e8e8ff; pointer-events: none;
      white-space: nowrap;
    }}
    #tooltip {{
      position: absolute; pointer-events: none; display: none;
      background: rgba(15,15,26,0.9); border: 1px solid rgba(100,150,255,0.3);
      border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #d0d8ff;
      max-width: 240px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}
    #controls {{
      position: absolute; bottom: 20px; right: 16px;
      background: rgba(15,15,26,0.85); backdrop-filter: blur(8px);
      border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
      padding: 12px 16px; font-size: 12px; color: #aaaacc; min-width: 160px;
    }}
    #controls h4 {{ color: #c8c8ff; margin-bottom: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }}
    #controls label {{ display: block; margin: 4px 0 2px; }}
    #controls input[type=range] {{ width: 100%; accent-color: #6688ff; }}
    #legend {{ position: absolute; bottom: 20px; left: 16px; background: rgba(15,15,26,0.85);
      backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
      padding: 10px 14px; font-size: 11px; color: #aaaacc; }}
    #legend h4 {{ color: #c8c8ff; margin-bottom: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .legend-bar {{ height: 10px; width: 140px; border-radius: 3px;
      background: linear-gradient(to right, #3b4cc0, #b0c5e8, #f7b799, #d65028); margin: 4px 0; }}
    .legend-labels {{ display: flex; justify-content: space-between; font-size: 10px; color: #8888aa; }}
  </style>

  <!-- MapLibre GL JS (BSD-3-Clause) -->
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>

  <!-- deck.gl (Apache 2.0) -->
  <script src="https://unpkg.com/deck.gl@9.0.28/dist.min.js"></script>
</head>
<body>
<div id="app">
  <div id="map"></div>
  <div id="header">{title}</div>
  <div id="tooltip"></div>

  <div id="controls">
    <h4>⚙ Controls</h4>
    <label>Exaggeration: <span id="exag-val">{exaggeration}</span>×</label>
    <input type="range" id="exag-slider" min="0.5" max="8" step="0.1" value="{exaggeration}" />
    <label style="margin-top:8px;">Opacity: <span id="opacity-val">80</span>%</label>
    <input type="range" id="opacity-slider" min="0" max="100" step="1" value="80" />
  </div>

  {'<div id="legend"><h4>📊 ' + (overlay_col or '') + '</h4><div class="legend-bar"></div><div class="legend-labels"><span>Low</span><span>High</span></div></div>' if overlay_geojson else ''}
</div>

<script>
(function() {{
  const DEM_AVAILABLE = {dem_available};
  const DEM_DATA_URL = "{dem_data_url}";
  const BOUNDS = [{west}, {south}, {east}, {north}];
  const CENTER = [{center_lon}, {center_lat}];
  let exaggeration = {exaggeration};
  let overlayOpacity = 0.8;

  const overlayGeoJSON = {overlay_js};
  const overlayCol = {overlay_col_js};

  // ---- MapLibre init ----
  const map = new maplibregl.Map({{
    container: 'map',
    style: {{
      version: 8,
      sources: {{
        'carto-dark': {{
          type: 'raster',
          tiles: ['https://basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}.png'],
          tileSize: 256,
          attribution: '© OpenStreetMap contributors © CARTO',
        }}
      }},
      layers: [{{ id: 'carto-bg', type: 'raster', source: 'carto-dark' }}],
    }},
    center: CENTER,
    zoom: 7,
    pitch: 50,
    bearing: -15,
    maxPitch: 85,
    antialias: true,
  }});

  // ---- deck.gl overlay ----
  let deckLayers = [];

  function buildTerrainLayer() {{
    if (!DEM_AVAILABLE) return null;

    // Use deck.gl TerrainLayer with our embedded Terrarium PNG
    // TerrainLayer decodes Terrarium encoding: elev = R*256 + G + B/256 - 32768
    return new deck.TerrainLayer({{
      id: 'terrain',
      elevationDecoder: {{
        rScaler: 256,
        gScaler: 1,
        bScaler: 1 / 256,
        offset: -32768,
      }},
      elevationData: DEM_DATA_URL,
      texture: DEM_DATA_URL,
      bounds: BOUNDS,
      meshMaxError: 2,
      elevationScale: exaggeration,
      pickable: true,
      onHover: (info) => {{
        const tt = document.getElementById('tooltip');
        if (info.object && info.object.position) {{
          const [lon, lat, elev] = info.object.position;
          tt.style.display = 'block';
          tt.style.left = (info.x + 14) + 'px';
          tt.style.top = (info.y - 30) + 'px';
          tt.innerHTML = `
            <strong>Elevation</strong><br/>
            ${{Math.round(elev)}} m<br/>
            <span style="color:#888;font-size:10px">${{lat.toFixed(4)}}°N, ${{lon.toFixed(4)}}°W</span>
          `;
        }} else {{
          tt.style.display = 'none';
        }}
      }},
    }});
  }}

  function colorFromNorm(norm) {{
    // RdYlBu diverging: low=blue, high=red
    const stops = [
      [0.0,  [59,  76,  192]],
      [0.25, [144, 188, 219]],
      [0.5,  [255, 255, 180]],
      [0.75, [246, 147,  82]],
      [1.0,  [220,  44,  37]],
    ];
    for (let i = 0; i < stops.length - 1; i++) {{
      const [t0, c0] = stops[i];
      const [t1, c1] = stops[i+1];
      if (norm <= t1) {{
        const t = (norm - t0) / (t1 - t0);
        return c0.map((v,j) => Math.round(v + t * (c1[j] - v)));
      }}
    }}
    return stops[stops.length-1][1];
  }}

  function buildOverlayLayer() {{
    if (!overlayGeoJSON) return null;
    return new deck.GeoJsonLayer({{
      id: 'overlay',
      data: overlayGeoJSON,
      pickable: true,
      stroked: true,
      filled: true,
      extruded: false,
      getFillColor: f => {{
        const norm = f.properties._norm_val || 0;
        return [...colorFromNorm(norm), Math.round(overlayOpacity * 255)];
      }},
      getLineColor: [255, 255, 255, 40],
      lineWidthMinPixels: 0.5,
      onHover: (info) => {{
        const tt = document.getElementById('tooltip');
        if (info.object) {{
          const props = info.object.properties;
          const val = props._raw_val != null ? Number(props._raw_val).toFixed(2) : 'N/A';
          const label = props._col_label || overlayCol || 'value';
          const geoid = props.GEOID || props.geoid || props.GEO_ID || props.fid || '';
          tt.style.display = 'block';
          tt.style.left = (info.x + 14) + 'px';
          tt.style.top = (info.y - 30) + 'px';
          tt.innerHTML = `
            ${{geoid ? '<strong>' + geoid + '</strong><br/>' : ''}}
            ${{label}}: <strong>${{val}}</strong>
          `;
        }} else {{
          tt.style.display = 'none';
        }}
      }},
    }});
  }}

  function updateDeck() {{
    const layers = [buildTerrainLayer(), buildOverlayLayer()].filter(Boolean);
    if (!window._deckOverlay) {{
      window._deckOverlay = new deck.MapboxOverlay({{ layers }});
      map.addControl(window._deckOverlay);
    }} else {{
      window._deckOverlay.setProps({{ layers }});
    }}
  }}

  map.on('load', () => {{
    updateDeck();

    // Add attribution
    map.addControl(new maplibregl.AttributionControl({{
      customAttribution: 'Terrain: open DEM | deck.gl Apache-2.0 | MapLibre GL JS BSD-3'
    }}), 'bottom-right');
  }});

  // Controls
  document.getElementById('exag-slider').addEventListener('input', e => {{
    exaggeration = parseFloat(e.target.value);
    document.getElementById('exag-val').textContent = exaggeration.toFixed(1);
    updateDeck();
  }});

  document.getElementById('opacity-slider').addEventListener('input', e => {{
    overlayOpacity = parseInt(e.target.value) / 100;
    document.getElementById('opacity-val').textContent = e.target.value;
    updateDeck();
  }});

}})();
</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"  ✅ HTML saved: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate 3D terrain visualization (PNG + MapLibre GL JS HTML)."
    )
    parser.add_argument("--dem", required=True, help="Input DEM GeoTIFF path")
    parser.add_argument("--overlay", help="Optional overlay GeoPackage for thematic color")
    parser.add_argument("--overlay-col", help="Column in overlay for color ramp")
    parser.add_argument("--output-html", help="Output HTML file path")
    parser.add_argument("--output-png", help="Output PNG preview path")
    parser.add_argument("--title", default="3D Terrain Visualization", help="Map title")
    parser.add_argument(
        "--exaggeration",
        type=float,
        default=2.0,
        help="Vertical exaggeration factor (default: 2.0)",
    )
    args = parser.parse_args()

    if not args.output_html and not args.output_png:
        print("ERROR: Specify at least --output-html or --output-png", file=sys.stderr)
        return 1

    dem_path = Path(args.dem).expanduser().resolve()
    if not dem_path.exists():
        print(f"ERROR: DEM file not found: {dem_path}", file=sys.stderr)
        return 1

    print(f"=== 3D Terrain Visualization ===")
    print(f"  DEM:          {dem_path}")
    print(f"  Title:        {args.title}")
    print(f"  Exaggeration: {args.exaggeration}×")

    # Read DEM
    print("\n[1/4] Reading DEM...")
    dem_array, transform, profile = read_dem(dem_path)
    h, w = dem_array.shape
    elev_min = float(np.nanmin(dem_array))
    elev_max = float(np.nanmax(dem_array))
    print(f"  Size: {w}×{h}px | Elevation: {elev_min:.0f}–{elev_max:.0f} m")
    print(f"  Bounds: W={profile['bounds']['west']:.4f} S={profile['bounds']['south']:.4f} "
          f"E={profile['bounds']['east']:.4f} N={profile['bounds']['north']:.4f}")

    # Load overlay
    overlay_geojson = None
    if args.overlay:
        print(f"\n[2/4] Loading overlay: {args.overlay}")
        overlay_path = Path(args.overlay).expanduser().resolve()
        overlay_geojson = load_overlay_geojson(overlay_path, args.overlay_col)
        if overlay_geojson:
            feat_count = len(overlay_geojson.get("features", []))
            print(f"  Loaded {feat_count} features (column: {args.overlay_col or 'none'})")
        else:
            print("  WARNING: Could not load overlay — continuing without it")
    else:
        print("\n[2/4] No overlay specified — terrain-only output")

    # PNG
    if args.output_png:
        print(f"\n[3/4] Rendering PNG preview...")
        render_png(
            dem_array=dem_array,
            transform=transform,
            output_path=Path(args.output_png).expanduser().resolve(),
            title=args.title,
            exaggeration=args.exaggeration,
        )
    else:
        print("\n[3/4] Skipping PNG (--output-png not specified)")

    # HTML
    if args.output_html:
        print(f"\n[4/4] Building HTML viewer...")
        render_html(
            dem_array=dem_array,
            transform=transform,
            profile=profile,
            output_path=Path(args.output_html).expanduser().resolve(),
            title=args.title,
            exaggeration=args.exaggeration,
            overlay_geojson=overlay_geojson,
            overlay_col=args.overlay_col,
        )
    else:
        print("\n[4/4] Skipping HTML (--output-html not specified)")

    # JSON log
    log = {
        "script": "render_3d_terrain.py",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "dem": str(dem_path),
        "overlay": args.overlay,
        "overlay_col": args.overlay_col,
        "title": args.title,
        "exaggeration": args.exaggeration,
        "dem_shape": [h, w],
        "dem_elevation_range": [elev_min, elev_max],
        "bounds": profile.get("bounds", {}),
        "output_html": args.output_html,
        "output_png": args.output_png,
    }

    # Write log alongside outputs
    log_target = args.output_html or args.output_png
    if log_target:
        log_path = Path(log_target).with_suffix(".log.json")
        log_path.write_text(json.dumps(log, indent=2))
        print(f"\n  Log: {log_path}")

    print("\n✅ Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
