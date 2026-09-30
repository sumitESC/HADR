import os
import json
import time
import subprocess
import random
import requests
import logging
from pathlib import Path
import sys

# Setup paths to import from backend
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from app.gis.elevation_api import ElevationFetcher
from app.gis.osm_data import OSMDataFetcher
from app.config import DAMS_DIR, DEM_DIR, SETTLEMENTS_DIR, RIVERS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WINDSCRIBE_CLI = r"C:\Program Files\Windscribe\windscribe-cli.exe"
WINDSCRIBE_LOCATIONS = ["US", "CA", "FR", "DE", "NL", "CH", "NO", "RO"]
_last_vpn_location = None

def run_cli(*args):
    try:
        # Use a longer timeout and avoid CREATE_NO_WINDOW if it causes freezes
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(
            [WINDSCRIBE_CLI] + list(args), 
            capture_output=True, 
            text=True, 
            timeout=60, 
            stdin=subprocess.DEVNULL,
            creationflags=flags
        )
        return (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        logger.error(f"Windscribe CLI Error: Command {' '.join(args)} timed out after 60s")
        return ""
    except Exception as e:
        logger.error(f"Windscribe CLI Error: {e}")
        return ""

def get_current_ip():
    """Get the current public IP address."""
    for service in ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]:
        try:
            resp = requests.get(service, timeout=10)
            if resp.status_code == 200:
                return resp.text.strip()
        except Exception:
            continue
    return None

def wait_for_vpn_connected(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        output = run_cli("status")
        if "CONNECTED" in output.upper() and "DISCONNECTED" not in output.upper():
            return True
        time.sleep(3)
    return False

def wait_for_vpn_disconnected(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        output = run_cli("status")
        if "DISCONNECTED" in output.upper() or "NOT" in output.upper():
            return True
        time.sleep(3)
    return False

def rotate_ip():
    global _last_vpn_location
    logger.info("Rotating IP via Windscribe...")
    
    old_ip = get_current_ip()
    logger.info(f"Current IP before rotation: {old_ip}")
    
    run_cli("disconnect")
    logger.info("Sent disconnect command. Waiting for disconnection...")
    wait_for_vpn_disconnected(timeout=30)
    
    available = [loc for loc in WINDSCRIBE_LOCATIONS if loc != _last_vpn_location]
    chosen_location = random.choice(available)
    _last_vpn_location = chosen_location
    
    logger.info(f"Connecting to Windscribe location: {chosen_location}")
    run_cli("connect", chosen_location)
    logger.info("Sent connect command. Waiting for connection...")
    
    if not wait_for_vpn_connected(timeout=60):
        logger.warning(f"VPN connection to {chosen_location} timed out. Trying 'best' as fallback...")
        run_cli("disconnect")
        wait_for_vpn_disconnected(timeout=15)
        run_cli("connect", "best")
        if not wait_for_vpn_connected(timeout=60):
            logger.error("VPN connection failed even with 'best' fallback!")
            return False
    
    logger.info("VPN seems connected. Waiting 5 seconds before checking new IP...")
    time.sleep(5)
    new_ip = get_current_ip()
    logger.info(f"New IP after rotation: {new_ip}")
    
    if old_ip and new_ip and old_ip == new_ip:
        logger.warning(f"IP did NOT change after rotation! ({old_ip} -> {new_ip}). Trying another location...")
        run_cli("disconnect")
        wait_for_vpn_disconnected(timeout=15)
        available = [loc for loc in WINDSCRIBE_LOCATIONS if loc != chosen_location and loc != _last_vpn_location]
        if available:
            second_location = random.choice(available)
            _last_vpn_location = second_location
            logger.info(f"Retrying with location: {second_location}")
            run_cli("connect", second_location)
            if wait_for_vpn_connected(timeout=60):
                time.sleep(5)
                new_ip = get_current_ip()
                logger.info(f"New IP after second rotation attempt: {new_ip}")
                
    logger.info(f"IP rotated successfully: {old_ip} -> {new_ip}")
    return True

def delete_synthetic_dem(dam_id):
    dem_path = DEM_DIR / f"{dam_id}_dem.npy"
    meta_path = DEM_DIR / f"{dam_id}_dem_meta.json"
    if dem_path.exists():
        dem_path.unlink()
    if meta_path.exists():
        meta_path.unlink()

def delete_osm_cache(dam_id):
    settlements = SETTLEMENTS_DIR / f"{dam_id}_settlements.geojson"
    roads = SETTLEMENTS_DIR / f"{dam_id}_roads.geojson"
    river = RIVERS_DIR / f"{dam_id}_river.geojson"
    for f in [settlements, roads, river]:
        if f.exists():
            f.unlink()

def pre_download_data():
    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        logger.error(f"Dams file not found: {dams_file}")
        return

    with open(dams_file, "r") as f:
        dams = json.load(f)

    logger.info(f"Starting pre-download for {len(dams)} dams.")

    for i, dam in enumerate(dams):
        dam_id = dam["id"]
        lat = dam["lat"]
        lon = dam["lon"]
        logger.info(f"[{i+1}/{len(dams)}] Fetching data for {dam['name']} ({dam_id})")

        # FETCH DEM
        while True:
            # Check if valid DEM exists
            dem_meta_path = DEM_DIR / f"{dam_id}_dem_meta.json"
            dem_valid = False
            if dem_meta_path.exists():
                with open(dem_meta_path, "r") as f:
                    meta = json.load(f)
                    if "Synthetic" not in meta.get("source", ""):
                        dem_valid = True

            if dem_valid:
                logger.info(f"  [DEM] Valid real DEM already exists for {dam_id}.")
                break
                
            # If synthetic exists, delete it before trying
            if dem_meta_path.exists():
                delete_synthetic_dem(dam_id)

            logger.info(f"  [DEM] Fetching elevation from Open-Meteo...")
            try:
                dem, meta = ElevationFetcher.get_or_fetch_dem(dam_id, lat, lon, on_rate_limit=rotate_ip)
                if "Synthetic" in meta.get("source", ""):
                    logger.warning(f"  [DEM] Fetched synthetic DEM due to API limits. Rotating IP and retrying...")
                    delete_synthetic_dem(dam_id)
                    rotate_ip()
                    time.sleep(2)
                    continue
                else:
                    logger.info(f"  [DEM] Successfully fetched real DEM for {dam_id}.")
                    break
            except Exception as e:
                logger.error(f"  [DEM] Error fetching DEM: {e}. Rotating IP...")
                rotate_ip()
                time.sleep(2)

        # FETCH OSM
        # Use 120km radius to allow long simulations
        while True:
            river_file = RIVERS_DIR / f"{dam_id}_river.geojson"
            if river_file.exists():
                logger.info(f"  [OSM] Valid OSM data already exists for {dam_id}.")
                break
                
            logger.info(f"  [OSM] Fetching OpenStreetMap data (120km radius)...")
            try:
                OSMDataFetcher.get_or_fetch_data(dam_id, lat, lon, radius_km=120.0, allow_fallback=False)
                logger.info(f"  [OSM] Successfully fetched OSM data for {dam_id}.")
                break
            except RuntimeError as e:
                if "rate limited" in str(e).lower() or "timeout" in str(e).lower() or "mirrors unavailable" in str(e).lower():
                    logger.warning(f"  [OSM] Rate limit/Timeout hit: {e}. Rotating IP and retrying...")
                    delete_osm_cache(dam_id)
                    rotate_ip()
                    time.sleep(2)
                else:
                    logger.error(f"  [OSM] Unhandled error: {e}")
                    raise e
            except Exception as e:
                logger.error(f"  [OSM] Error fetching OSM: {e}. Rotating IP...")
                delete_osm_cache(dam_id)
                rotate_ip()
                time.sleep(2)

    logger.info("Pre-download complete for all dams!")
    
if __name__ == "__main__":
    pre_download_data()
