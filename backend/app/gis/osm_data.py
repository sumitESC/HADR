"""
OpenStreetMap Data Fetcher
Strategy:
  1. PRIMARY   — Use local Java Osmosis tool to crop the India PBF to a tiny
                 bounding box per dam, then read the small file with pyosmium.
                 This is blazing fast (~2-5 seconds per dam, 100% offline).
  2. FALLBACK  — Overpass API (multiple mirrors) if PBF/Osmosis not available.
  3. STATIC    — Hardcoded baseline data as last resort.
"""
import json
import math
import time
import subprocess
import tempfile
import httpx
from pathlib import Path
from app.config import SETTLEMENTS_DIR, RIVERS_DIR

# ── Paths ────────────────────────────────────────────────────────────────────
_THIS_FILE = Path(__file__).resolve()
_PROJECT   = _THIS_FILE.parent.parent.parent.parent   # .../sih2

PBF_PATH     = next(_PROJECT.glob("*.osm.pbf"), None)
OSMOSIS_BIN  = _PROJECT / "osmosis" / "bin" / "osmosis.bat"  # Windows batch file

# ── Overpass API mirrors (fallback) ──────────────────────────────────────────
OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
HEADERS = {
    "User-Agent": "HADR-FloodSim/1.0 (research project; bot@hadrfloodsim.org)",
    "Accept": "*/*"
}


# ══════════════════════════════════════════════════════════════════════════════
#  PRIMARY: Osmosis + pyosmium (fast local extraction)
# ══════════════════════════════════════════════════════════════════════════════

def _extract_with_osmosis(lat: float, lon: float, radius_km: float) -> Path:
    """
    Uses Java Osmosis to crop the large India PBF to a tiny bounding-box PBF.
    Returns the path to the cropped temporary PBF file.
    This typically finishes in 2-10 seconds.
    """
    delta_lat = radius_km / 111.32
    delta_lon = radius_km / (111.32 * math.cos(math.radians(lat)))

    south = lat - delta_lat
    north = lat + delta_lat
    west  = lon - delta_lon
    east  = lon + delta_lon

    # Write to a temp file in the project dir (avoids path issues)
    tmp_pbf = _PROJECT / "osmosis" / f"_tmp_dam_{lat:.4f}_{lon:.4f}.osm.pbf"

    cmd = [
        str(OSMOSIS_BIN),
        "--read-pbf",        str(PBF_PATH),
        "--bounding-box",
            f"top={north:.6f}",
            f"left={west:.6f}",
            f"bottom={south:.6f}",
            f"right={east:.6f}",
            "completeWays=yes",
        "--write-pbf",       str(tmp_pbf),
    ]

    print(f"[OSMDataFetcher] Running Osmosis crop: ({south:.3f},{west:.3f}) -> ({north:.3f},{east:.3f})")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        raise RuntimeError(f"Osmosis failed (code {result.returncode}): {result.stderr[-500:]}")

    print(f"[OSMDataFetcher] Osmosis crop done -> {tmp_pbf.name} ({tmp_pbf.stat().st_size // 1024} KB)")
    return tmp_pbf


def _read_pbf_file(pbf_file: Path, south: float, west: float, north: float, east: float):
    """
    Reads a (small, cropped) PBF file with pyosmium and extracts
    settlements, roads, and rivers as GeoJSON FeatureCollections.
    """
    import osmium

    PLACE_TYPES    = {"city", "town", "village", "hamlet"}
    AMENITY_TYPES  = {"hospital", "school", "fire_station"}
    HIGHWAY_TYPES  = {"motorway", "trunk", "primary", "secondary"}
    WATERWAY_TYPES = {"river", "canal"}
    POP_DEFAULTS   = {"city": 100000, "town": 25000, "village": 5000, "hamlet": 500}

    settlement_features, road_features, river_features = [], [], []

    fp = osmium.FileProcessor(str(pbf_file)).with_locations()

    for obj in fp:
        tags = {kv.k: kv.v for kv in obj.tags}

        if isinstance(obj, osmium.osm.Node):
            try:
                nlat, nlon = obj.location.lat, obj.location.lon
            except Exception:
                continue

            place   = tags.get("place")
            amenity = tags.get("amenity")

            if place in PLACE_TYPES or amenity in AMENITY_TYPES:
                name       = tags.get("name", tags.get("name:en", "Unknown"))
                place_type = place or amenity or "settlement"
                pop = 0
                if "population" in tags:
                    try:    pop = int(tags["population"])
                    except: pass
                else:
                    pop = POP_DEFAULTS.get(place_type, 0)

                settlement_features.append({
                    "type": "Feature",
                    "properties": {
                        "name": name, "type": place_type,
                        "population": pop, "elevation_m": 0,
                        "source": "OpenStreetMap (local PBF)"
                    },
                    "geometry": {"type": "Point", "coordinates": [nlon, nlat]}
                })

        elif isinstance(obj, osmium.osm.Way):
            highway  = tags.get("highway")
            waterway = tags.get("waterway")

            if highway not in HIGHWAY_TYPES and waterway not in WATERWAY_TYPES:
                continue

            coords = []
            for n in obj.nodes:
                try:
                    if n.location.valid():
                        coords.append([n.location.lon, n.location.lat])
                except Exception:
                    continue

            if len(coords) < 2:
                continue

            if highway in HIGHWAY_TYPES:
                road_features.append({
                    "type": "Feature",
                    "properties": {
                        "name": tags.get("name", tags.get("ref", "Road")),
                        "category": highway,
                        "is_bridge": tags.get("bridge") == "yes",
                        "source": "OpenStreetMap (local PBF)"
                    },
                    "geometry": {"type": "LineString", "coordinates": coords}
                })
            elif waterway in WATERWAY_TYPES:
                river_features.append({
                    "type": "Feature",
                    "properties": {
                        "name": tags.get("name", "River"),
                        "waterway": waterway,
                        "source": "OpenStreetMap (local PBF)"
                    },
                    "geometry": {"type": "LineString", "coordinates": coords}
                })

    print(f"[OSMDataFetcher] Extracted: {len(settlement_features)} settlements, "
          f"{len(road_features)} roads, {len(river_features)} rivers.")

    return (
        {"type": "FeatureCollection", "features": settlement_features},
        {"type": "FeatureCollection", "features": road_features},
        {"type": "FeatureCollection", "features": river_features},
    )


def _extract_from_pbf_osmosis(lat: float, lon: float, radius_km: float):
    """Full pipeline: Osmosis crop → pyosmium read → GeoJSON."""
    delta_lat = radius_km / 111.32
    delta_lon = radius_km / (111.32 * math.cos(math.radians(lat)))
    south, north = lat - delta_lat, lat + delta_lat
    west,  east  = lon - delta_lon, lon + delta_lon

    tmp_pbf = None
    try:
        tmp_pbf = _extract_with_osmosis(lat, lon, radius_km)
        return _read_pbf_file(tmp_pbf, south, west, north, east)
    finally:
        # Always clean up the temp file
        if tmp_pbf and tmp_pbf.exists():
            tmp_pbf.unlink()


# ══════════════════════════════════════════════════════════════════════════════
#  FALLBACK: Overpass API with spatial chunking
# ══════════════════════════════════════════════════════════════════════════════

def _overpass_query(query: str):
    """Executes Overpass API query with robust HTTP error handling across mirrors."""
    for mirror_idx, url in enumerate(OVERPASS_URLS):
        for attempt in range(3):
            try:
                resp = httpx.post(url, data={"data": query}, headers=HEADERS, timeout=65.0)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    time.sleep(2 ** attempt + 30)
                    continue
                elif resp.status_code == 400:
                    raise ValueError(f"Overpass QL Syntax Error (400): {resp.text}")
                elif 400 < resp.status_code < 500:
                    print(f"[OSM] {resp.status_code} on mirror {mirror_idx+1} — skipping.")
                    break
                elif resp.status_code in (500, 502, 503, 504):
                    time.sleep(2 ** attempt + 5)
                    continue
                else:
                    break
            except (httpx.TimeoutException, httpx.ConnectError):
                time.sleep(2 ** attempt + 5)
                continue
            except ValueError as e:
                raise e
            except Exception:
                break
    raise RuntimeError("All Overpass API mirrors failed.")


def _fetch_from_overpass(lat: float, lon: float, radius_km: float):
    """Fetch via Overpass API using 20km spatial chunking."""
    CHUNK_KM  = 20.0
    grid_size = max(1, math.ceil((2 * radius_km) / CHUNK_KM))
    delta_lat = radius_km / 111.32
    delta_lon = radius_km / (111.32 * math.cos(math.radians(lat)))
    south, north = lat - delta_lat, lat + delta_lat
    west,  east  = lon - delta_lon, lon + delta_lon
    lat_step = (north - south) / grid_size
    lon_step = (east  - west)  / grid_size

    settlement_features, road_features, river_features = [], [], []
    seen_ids = set()
    total = grid_size * grid_size
    print(f"[OSMDataFetcher] Overpass: {grid_size}x{grid_size}={total} chunks of ~{CHUNK_KM}km.")

    for i in range(grid_size):
        for j in range(grid_size):
            s = south + i       * lat_step
            n = south + (i + 1) * lat_step
            w = west  + j       * lon_step
            e = west  + (j + 1) * lon_step
            cn = i * grid_size + j + 1
            print(f"[OSMDataFetcher] Chunk {cn}/{total}", flush=True)

            try:
                nq = f'[out:json][timeout:30][maxsize:512000000];\n(\n  node["place"~"^(city|town|village)$"]({s},{w},{n},{e});\n  node["amenity"~"^(hospital|school|fire_station)$"]({s},{w},{n},{e});\n);\nout body;'
                for elem in _overpass_query(nq).get("elements", []):
                    eid = elem.get("id")
                    if eid in seen_ids: continue
                    seen_ids.add(eid)
                    t  = elem.get("tags", {})
                    pt = t.get("place", t.get("amenity", "settlement"))
                    try: pop = int(t.get("population", 0))
                    except: pop = {"city": 100000, "town": 25000, "village": 5000}.get(pt, 0)
                    settlement_features.append({"type":"Feature","properties":{"name":t.get("name","Unknown"),"type":pt,"population":pop,"elevation_m":0,"source":"OpenStreetMap"},"geometry":{"type":"Point","coordinates":[elem["lon"],elem["lat"]]}})
            except Exception as ex:
                print(f"[OSM] Node chunk {cn} failed: {ex}")
            time.sleep(0.5)

            try:
                wq = f'[out:json][timeout:30][maxsize:512000000];\n(\n  way["highway"~"^(motorway|trunk|primary|secondary)$"]({s},{w},{n},{e});\n  way["waterway"~"^(river|canal)$"]({s},{w},{n},{e});\n);\nout body geom;'
                for elem in _overpass_query(wq).get("elements", []):
                    eid = elem.get("id")
                    if eid in seen_ids: continue
                    seen_ids.add(eid)
                    t = elem.get("tags", {})
                    if "geometry" not in elem: continue
                    coords = [[pt["lon"], pt["lat"]] for pt in elem["geometry"]]
                    if len(coords) < 2: continue
                    if "highway" in t:
                        road_features.append({"type":"Feature","properties":{"name":t.get("name",t.get("ref","Road")),"category":t.get("highway","road"),"source":"OpenStreetMap"},"geometry":{"type":"LineString","coordinates":coords}})
                    elif "waterway" in t:
                        river_features.append({"type":"Feature","properties":{"name":t.get("name","River"),"waterway":t.get("waterway","river"),"source":"OpenStreetMap"},"geometry":{"type":"LineString","coordinates":coords}})
            except Exception as ex:
                print(f"[OSM] Way chunk {cn} failed: {ex}")
            time.sleep(1.0)

    return (
        {"type": "FeatureCollection", "features": settlement_features},
        {"type": "FeatureCollection", "features": road_features},
        {"type": "FeatureCollection", "features": river_features},
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Main public class
# ══════════════════════════════════════════════════════════════════════════════

class OSMDataFetcher:
    """Fetches real settlement, road, and river data from OpenStreetMap."""

    @classmethod
    def get_or_fetch_data(cls, dam_id: str, lat: float, lon: float,
                          radius_km: float = 25.0, allow_fallback: bool = True):
        settlements_file = SETTLEMENTS_DIR / f"{dam_id}_settlements.geojson"
        roads_file       = SETTLEMENTS_DIR / f"{dam_id}_roads.geojson"
        river_file       = RIVERS_DIR      / f"{dam_id}_river.geojson"

        # Load from cache
        settlements = json.loads(settlements_file.read_text()) if settlements_file.exists() else None
        roads       = json.loads(roads_file.read_text())       if roads_file.exists()       else None
        river       = json.loads(river_file.read_text())       if river_file.exists()        else None

        if settlements and roads and river:
            return settlements, roads, river

        try:
            osmosis_ok = PBF_PATH and PBF_PATH.exists() and OSMOSIS_BIN.exists()

            if osmosis_ok:
                print(f"[OSMDataFetcher] Using Osmosis (Java) + local PBF for {dam_id}")
                settlements, roads, river = _extract_from_pbf_osmosis(lat, lon, radius_km)
            elif PBF_PATH and PBF_PATH.exists():
                # Osmosis missing but PBF exists — use slow Python scan
                print(f"[OSMDataFetcher] Osmosis not found, using slow Python PBF scan for {dam_id}")
                from app.gis.osm_data_pbf_slow import _extract_from_pbf
                settlements, roads, river = _extract_from_pbf(lat, lon, radius_km)
            else:
                print(f"[OSMDataFetcher] No local PBF — using Overpass API for {dam_id}")
                settlements, roads, river = _fetch_from_overpass(lat, lon, radius_km)

            # Cache to disk
            settlements_file.write_text(json.dumps(settlements, indent=2))
            roads_file.write_text(json.dumps(roads, indent=2))
            river_file.write_text(json.dumps(river, indent=2))

        except Exception as e:
            print(f"[OSMDataFetcher] Fetch failed for {dam_id}: {e}")
            if not allow_fallback:
                raise RuntimeError(f"OSM fetch failed: {e}")
            settlements = settlements or cls._fallback_settlements(dam_id, lat, lon)
            roads       = roads       or cls._fallback_roads(dam_id, lat, lon)
            river       = river       or cls._fallback_river(dam_id, lat, lon)

        return settlements, roads, river

    # ── Static fallbacks ──────────────────────────────────────────────────────
    @classmethod
    def _fallback_settlements(cls, dam_id, lat, lon):
        dam_towns = {
            "tehri-dam":      [(-0.015,-0.015,"Tehri","town",25000),(-0.045,-0.040,"New Tehri","town",35000),(-0.250,-0.200,"Rishikesh","city",102000)],
            "bhakra-dam":     [(-0.02,-0.03,"Nangal","town",48000),(-0.05,-0.08,"Anandpur Sahib","town",40000),(-0.08,-0.15,"Ropar","town",55000)],
            "sardar-sarovar": [(-0.03,-0.01,"Kevadia","town",18000),(-0.25,-0.05,"Bharuch","city",170000)],
            "hirakud-dam":    [(0.08,-0.07,"Sambalpur","city",270000),(0.35,-0.25,"Cuttack","city",610000)],
            "nagarjuna-sagar":[(0.12,-0.02,"Macherla","town",106000),(0.85,-0.08,"Vijayawada","city",1040000)],
            "idukki-dam":     [(-0.02,0.02,"Cheruthoni","town",22000),(-0.08,0.05,"Thodupuzha","town",52000)],
        }
        towns = dam_towns.get(dam_id, [(0.01,-0.01,"Downstream Town","town",15000),(0.05,-0.03,"Downstream Village","village",5000)])
        features = [{"type":"Feature","properties":{"name":n,"type":pt,"population":pop,"elevation_m":0,"source":"Local Baseline GIS Database"},"geometry":{"type":"Point","coordinates":[round(lon+dlon,5),round(lat+dlat,5)]}} for dlon,dlat,n,pt,pop in towns]
        return {"type":"FeatureCollection","features":features}

    @classmethod
    def _fallback_roads(cls, dam_id, lat, lon):
        return {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"National Highway","category":"primary","source":"Local Baseline GIS Database"},"geometry":{"type":"LineString","coordinates":[[round(lon-0.05,5),round(lat+0.02,5)],[round(lon,5),round(lat,5)],[round(lon+0.10,5),round(lat-0.06,5)]]}}]}

    @classmethod
    def _fallback_river(cls, dam_id, lat, lon):
        coords = [[round(lon+i*0.01,5),round(lat-i*0.008,5)] for i in range(15)]
        return {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"River Channel","waterway":"river","source":"Local Baseline GIS Database"},"geometry":{"type":"LineString","coordinates":coords}}]}
