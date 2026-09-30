import os
import sys
import json
import math
import subprocess
import time
import shutil

# --- Configuration ---
PBF_URL = "https://download.geofabrik.de/asia/india-latest.osm.pbf"
PBF_FILE = "india-latest.osm.pbf"
DAMS_FILE = "dams.json"
RESULTS_DIR = "osm_results"

# --- Setup ---
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
    os.makedirs(os.path.join(RESULTS_DIR, "settlements"))
    os.makedirs(os.path.join(RESULTS_DIR, "rivers"))

def run_cmd(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

print("Checking requirements...")
try:
    import osmium
except ImportError:
    print("Installing osmium...")
    run_cmd("pip install osmium")
    import osmium

if subprocess.run("which osmium", shell=True, capture_output=True).returncode != 0:
    print("Installing osmium-tool C++ binary via apt-get...")
    run_cmd("sudo apt-get update && sudo apt-get install -y osmium-tool")

if not os.path.exists(PBF_FILE):
    print(f"Downloading India PBF ({PBF_URL}) - this will take a minute...")
    run_cmd(f"wget -O {PBF_FILE} {PBF_URL}")

if not os.path.exists(DAMS_FILE):
    print(f"ERROR: You need to upload your '{DAMS_FILE}' to the Colab environment first!")
    sys.exit(1)

with open(DAMS_FILE, "r") as f:
    dams = json.load(f)

# --- Processing Logic ---
PLACE_TYPES    = {"city", "town", "village", "hamlet"}
AMENITY_TYPES  = {"hospital", "school", "fire_station"}
HIGHWAY_TYPES  = {"motorway", "trunk", "primary", "secondary"}
WATERWAY_TYPES = {"river", "canal"}
POP_DEFAULTS   = {"city": 100000, "town": 25000, "village": 5000, "hamlet": 500}

def get_bbox(lat, lon, radius_km):
    delta_lat = radius_km / 111.32
    delta_lon = radius_km / (111.32 * math.cos(math.radians(lat)))
    return (lon - delta_lon, lat - delta_lat, lon + delta_lon, lat + delta_lat) # left, bottom, right, top

print(f"\nStarting processing of {len(dams)} dams using lightning-fast C++ osmium-tool...")

t0 = time.time()
for i, dam in enumerate(dams):
    dam_id = dam["id"]
    lat, lon = dam["lat"], dam["lon"]
    print(f"[{i+1}/{len(dams)}] Processing {dam['name']} ({dam_id})...")
    
    left, bottom, right, top = get_bbox(lat, lon, 120.0)
    tmp_pbf = f"temp_{dam_id}.pbf"
    
    # 1. C++ Crop (Takes 2 seconds)
    crop_cmd = f"osmium extract -b {left:.5f},{bottom:.5f},{right:.5f},{top:.5f} {PBF_FILE} -o {tmp_pbf} --overwrite"
    run_cmd(crop_cmd)
    
    # 2. Python parse (Takes 0.1 seconds on the tiny file)
    settlements, roads, rivers = [], [], []
    fp = osmium.FileProcessor(tmp_pbf).with_locations()
    
    for obj in fp:
        tags = {kv.k: kv.v for kv in obj.tags}
        
        if isinstance(obj, osmium.osm.Node):
            place, amenity = tags.get("place"), tags.get("amenity")
            if place in PLACE_TYPES or amenity in AMENITY_TYPES:
                try: nlat, nlon = obj.location.lat, obj.location.lon
                except: continue
                import re
                ptype = place or amenity or "settlement"
                raw_pop = str(tags.get("population", POP_DEFAULTS.get(ptype, 0)))
                nums = re.findall(r"\d+", raw_pop.replace(",", ""))
                pop = int(nums[0]) if nums else POP_DEFAULTS.get(ptype, 0)
                
                settlements.append({
                    "type": "Feature",
                    "properties": {"name": tags.get("name", "Unknown"), "type": ptype, "population": pop, "elevation_m": 0, "source": "OSM"},
                    "geometry": {"type": "Point", "coordinates": [nlon, nlat]}
                })
                
        elif isinstance(obj, osmium.osm.Way):
            highway, waterway = tags.get("highway"), tags.get("waterway")
            if highway not in HIGHWAY_TYPES and waterway not in WATERWAY_TYPES:
                continue
            
            coords = []
            for node in obj.nodes:
                try:
                    if node.location.valid(): coords.append([node.location.lon, node.location.lat])
                except: continue
                
            if len(coords) < 2: continue
            
            if highway in HIGHWAY_TYPES:
                roads.append({
                    "type": "Feature",
                    "properties": {"name": tags.get("name", "Road"), "category": highway, "source": "OSM"},
                    "geometry": {"type": "LineString", "coordinates": coords}
                })
            elif waterway in WATERWAY_TYPES:
                rivers.append({
                    "type": "Feature",
                    "properties": {"name": tags.get("name", "River"), "waterway": waterway, "source": "OSM"},
                    "geometry": {"type": "LineString", "coordinates": coords}
                })
                
    os.remove(tmp_pbf)
    
    # 3. Save files
    with open(f"{RESULTS_DIR}/settlements/{dam_id}_settlements.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": settlements}, f)
    with open(f"{RESULTS_DIR}/settlements/{dam_id}_roads.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": roads}, f)
    with open(f"{RESULTS_DIR}/rivers/{dam_id}_river.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": rivers}, f)
        
    print(f"  -> Extracted {len(settlements)} settlements, {len(roads)} roads, {len(rivers)} rivers.")

elapsed = time.time() - t0
print(f"\nCOMPLETED ALL {len(dams)} DAMS IN {elapsed:.1f} SECONDS!")

print("Zipping results for easy download...")
run_cmd(f"zip -r {RESULTS_DIR}.zip {RESULTS_DIR}")
print(f"DONE! You can now download '{RESULTS_DIR}.zip' from the Colab file browser.")
