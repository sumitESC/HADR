import json
import math
import numpy as np
from pathlib import Path
from app.config import DEM_DIR, DAMS_DIR, RIVERS_DIR, SETTLEMENTS_DIR, SATELLITE_DIR

def generate_sample_data():
    """
    Generates realistic sample DEM elevation data, river network, dam details, 
    downstream settlements, and satellite SAR comparison layers for Tehri Dam region.
    """
    # 1. Dam Metadata
    dams = [
        {
            "id": "tehri-dam",
            "name": "Tehri Dam",
            "river": "Bhagirathi River",
            "lat": 30.3774,
            "lon": 78.4803,
            "dam_height_m": 260.5,
            "reservoir_water_level_m": 830.0,
            "normal_storage_m3": 3540000000,
            "spillway_capacity_m3s": 15500,
            "description": "Primary rock and earth-fill dam on Bhagirathi River near Tehri, Uttarakhand."
        },
        {
            "id": "koteshwar-dam",
            "name": "Koteshwar Dam",
            "river": "Bhagirathi River",
            "lat": 30.2825,
            "lon": 78.5302,
            "dam_height_m": 97.5,
            "reservoir_water_level_m": 612.0,
            "normal_storage_m3": 88000000,
            "spillway_capacity_m3s": 13200,
            "description": "Downstream regulating dam serving Tehri Hydro Power Complex."
        }
    ]
    with open(DAMS_DIR / "dams.json", "w") as f:
        json.dump(dams, f, indent=2)

    # 2. Synthetic DEM (Tehri Valley, 120x120 grid ~ 18km x 18km)
    # Bounding box: Min Lon 78.40, Max Lon 78.60, Min Lat 30.25, Max Lat 30.45
    nx, ny = 120, 120
    lon_min, lon_max = 78.40, 78.60
    lat_min, lat_max = 30.25, 30.45

    lons = np.linspace(lon_min, lon_max, nx)
    lats = np.linspace(lat_max, lat_min, ny) # Top to bottom

    # Create terrain valley (river flows from North-West to South-East)
    dem = np.zeros((ny, nx))
    for i in range(ny):
        curr_lat = lats[i]
        for j in range(nx):
            curr_lon = lons[j]
            # Centerline of valley equation
            valley_x = 78.45 + (30.45 - curr_lat) * 0.75
            dist_to_river = abs(curr_lon - valley_x) * 111.0 # approx km
            
            # Elevation decreases downstream (North to South)
            downstream_gradient = 850 - (30.45 - curr_lat) * 1500
            
            # V-shaped valley profile with mountain ridges on both sides
            ridge_elevation = 400 + (dist_to_river ** 1.6) * 180
            noise = math.sin(j * 0.2) * math.cos(i * 0.2) * 25
            
            dem[i, j] = max(downstream_gradient + ridge_elevation + noise, 350.0)

    # Save DEM matrix & metadata
    dem_meta = {
        "nx": nx,
        "ny": ny,
        "bounds": [lon_min, lat_min, lon_max, lat_max],
        "res_deg": [(lon_max - lon_min) / nx, (lat_max - lat_min) / ny],
        "crs": "EPSG:4326"
    }
    np.save(DEM_DIR / "tehri_dem.npy", dem)
    with open(DEM_DIR / "tehri_dem_meta.json", "w") as f:
        json.dump(dem_meta, f, indent=2)

    # 3. River Centerline GeoJSON
    river_coords = []
    for i in range(0, ny, 3):
        c_lat = float(lats[i])
        c_lon = float(78.45 + (30.45 - c_lat) * 0.75)
        river_coords.append([round(c_lon, 5), round(c_lat, 5)])

    river_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Bhagirathi River",
                    "width_m": 80,
                    "avg_depth_m": 8.5
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": river_coords
                }
            }
        ]
    }
    with open(RIVERS_DIR / "bhagirathi_river.geojson", "w") as f:
        json.dump(river_geojson, f, indent=2)

    # 4. Downstream Settlements & Infrastructure GeoJSON
    settlements = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "New Tehri Town", "type": "settlement", "population": 25400, "elevation_m": 780},
                "geometry": {"type": "Point", "coordinates": [78.4720, 30.3750]}
            },
            {
                "type": "Feature",
                "properties": {"name": "Koteshwar Village", "type": "settlement", "population": 4200, "elevation_m": 540},
                "geometry": {"type": "Point", "coordinates": [78.5250, 30.2910]}
            },
            {
                "type": "Feature",
                "properties": {"name": "Bhagirathipuram", "type": "settlement", "population": 8100, "elevation_m": 610},
                "geometry": {"type": "Point", "coordinates": [78.4910, 30.3520]}
            },
            {
                "type": "Feature",
                "properties": {"name": "Dobra Chanti Bridge", "type": "bridge", "population": 0, "elevation_m": 650},
                "geometry": {"type": "Point", "coordinates": [78.4420, 30.4120]}
            },
            {
                "type": "Feature",
                "properties": {"name": "Devprayag Junction", "type": "settlement", "population": 12500, "elevation_m": 460},
                "geometry": {"type": "Point", "coordinates": [78.5950, 30.1460]}
            }
        ]
    }
    with open(SETTLEMENTS_DIR / "settlements.geojson", "w") as f:
        json.dump(settlements, f, indent=2)

    # 5. Roads GeoJSON
    roads = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "NH-34 Highway Segment 1", "category": "national_highway"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[78.43, 30.44], [78.47, 30.38], [78.51, 30.31], [78.58, 30.20]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Tehri Bypass Road", "category": "state_highway"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[78.45, 30.39], [78.48, 30.36], [78.53, 30.28]]
                }
            }
        ]
    }
    with open(SETTLEMENTS_DIR / "roads.geojson", "w") as f:
        json.dump(roads, f, indent=2)

    # 6. Sentinel-1 SAR Satellite Observation Comparison Layer
    # Simulated satellite SAR water classification poly (T+120 min reference)
    sat_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "satellite": "Sentinel-1A SAR",
                    "mode": "IW GRDH",
                    "polarization": "VV+VH",
                    "observation_time": "2026-09-15T12:00:00Z",
                    "water_mask_type": "SAR Thresholding & Backscatter Deviation"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.4800, 30.3770],
                        [78.4950, 30.3650],
                        [78.5100, 30.3350],
                        [78.5280, 30.2950],
                        [78.5200, 30.2900],
                        [78.5000, 30.3300],
                        [78.4850, 30.3600],
                        [78.4750, 30.3750],
                        [78.4800, 30.3770]
                    ]]
                }
            }
        ]
    }
    with open(SATELLITE_DIR / "sentinel1_water_mask.geojson", "w") as f:
        json.dump(sat_geojson, f, indent=2)

    print("Sample HADR dataset for Tehri Dam successfully generated.")

if __name__ == "__main__":
    generate_sample_data()
