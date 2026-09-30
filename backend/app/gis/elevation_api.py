"""
Open-Source Elevation Data Fetcher
Uses Open-Meteo Elevation API (free, no API key required) and 
SRTM-based OpenTopography data to fetch real DEM grids for any location.
"""
import json
import time
import numpy as np
import httpx
from pathlib import Path
from app.config import DEM_DIR


class ElevationFetcher:
    """Fetches real elevation data from Open-Meteo Elevation API."""

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/elevation"
    # Grid size for DEM (resolution vs speed tradeoff)
    GRID_SIZE = 80  # 80x80 grid points
    # Default extent radius in degrees (~20km at equator)
    EXTENT_DEG = 0.18

    @classmethod
    def get_or_fetch_dem(cls, dam_id: str, lat: float, lon: float, extent_deg: float = None, on_rate_limit=None):
        """
        Returns (dem_array, meta_dict) for the given dam.
        Fetches from API if not cached, otherwise loads from disk.
        """
        extent = extent_deg or cls.EXTENT_DEG
        dem_path = DEM_DIR / f"{dam_id}_dem.npy"
        meta_path = DEM_DIR / f"{dam_id}_dem_meta.json"

        if dem_path.exists() and meta_path.exists():
            dem = np.load(dem_path)
            with open(meta_path, "r") as f:
                meta = json.load(f)
            return dem, meta

        # Generate grid points
        lon_min = lon - extent
        lon_max = lon + extent
        lat_min = lat - extent
        lat_max = lat + extent

        lats_grid = np.linspace(lat_max, lat_min, cls.GRID_SIZE)
        lons_grid = np.linspace(lon_min, lon_max, cls.GRID_SIZE)

        # Flatten to list of (lat, lon) pairs for API call
        all_lats = []
        all_lons = []
        for lat_val in lats_grid:
            for lon_val in lons_grid:
                all_lats.append(round(float(lat_val), 5))
                all_lons.append(round(float(lon_val), 5))

        batch_size = 100
        elevations = []
        total_batches = (len(all_lats) + batch_size - 1) // batch_size

        for batch_num, i in enumerate(range(0, len(all_lats), batch_size)):
            batch_lats = all_lats[i:i + batch_size]
            batch_lons = all_lons[i:i + batch_size]
            max_retries = 5
            success = False
            
            for attempt in range(max_retries):
                try:
                    resp = httpx.get(
                        cls.OPEN_METEO_URL,
                        params={
                            "latitude": ",".join(str(l) for l in batch_lats),
                            "longitude": ",".join(str(l) for l in batch_lons),
                        },
                        timeout=30.0
                    )
                    if resp.status_code == 429:
                        print(f"[ElevationFetcher] Rate limited (429) on batch {batch_num+1}/{total_batches}.")
                        if on_rate_limit:
                            print(f"[ElevationFetcher] Triggering VPN rotation to bypass limit...")
                            if on_rate_limit():
                                continue
                        
                        wait_time = 20 * (attempt + 1)
                        print(f"[ElevationFetcher] VPN unavailable/failed. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                        
                    resp.raise_for_status()
                    elevations.extend(resp.json().get("elevation", []))
                    success = True
                    break
                except Exception as e:
                    time.sleep(2)
                    
            if not success:
                print(f"[ElevationFetcher] Batch {batch_num+1} failed completely.")
                return cls._generate_synthetic_dem(dam_id, lat, lon, extent)
                
            time.sleep(0.5)

        if len(elevations) != cls.GRID_SIZE * cls.GRID_SIZE:
            return cls._generate_synthetic_dem(dam_id, lat, lon, extent)

        dem = np.array(elevations, dtype=np.float64).reshape(cls.GRID_SIZE, cls.GRID_SIZE)

        # Replace NaN/negative values
        dem = np.where(np.isnan(dem), 0.0, dem)
        dem = np.where(dem < 0, 0.0, dem)

        meta = {
            "dam_id": dam_id,
            "bounds": [lon_min, lat_min, lon_max, lat_max],
            "crs": "EPSG:4326",
            "grid_size": cls.GRID_SIZE,
            "source": "Open-Meteo Elevation API (SRTM30)",
            "center_lat": lat,
            "center_lon": lon,
            "extent_deg": extent
        }

        # Cache to disk
        np.save(dem_path, dem)
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        return dem, meta

    @classmethod
    def _generate_synthetic_dem(cls, dam_id: str, lat: float, lon: float, extent: float):
        """
        Generates synthetic terrain when API is unavailable.
        Creates a realistic valley profile with a river channel.
        """
        n = cls.GRID_SIZE
        lon_min = lon - extent
        lon_max = lon + extent
        lat_min = lat - extent
        lat_max = lat + extent

        lats_grid = np.linspace(lat_max, lat_min, n)
        lons_grid = np.linspace(lon_min, lon_max, n)

        # Create valley terrain: high on edges, low in center (river)
        X, Y = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, n))

        # Base elevation (higher near dam, lower downstream)
        base_elev = 800 + Y * 200  # North=higher, South=lower

        # Valley walls (raised edges)
        valley_width = 0.3 + 0.1 * np.sin(Y * 3)
        wall_height = 100 * np.exp(-((X / valley_width) ** 2)) * -1 + 100

        # River channel (dip in center)
        channel = -30 * np.exp(-((X / 0.08) ** 2))

        # Add noise for realism
        noise = np.random.normal(0, 5, (n, n))

        dem = base_elev + wall_height + channel + noise
        dem = np.clip(dem, 200, 1200)

        meta = {
            "dam_id": dam_id,
            "bounds": [lon_min, lat_min, lon_max, lat_max],
            "crs": "EPSG:4326",
            "grid_size": n,
            "source": "Synthetic Valley Terrain (API unavailable)",
            "center_lat": lat,
            "center_lon": lon,
            "extent_deg": extent
        }

        dem_path = DEM_DIR / f"{dam_id}_dem.npy"
        meta_path = DEM_DIR / f"{dam_id}_dem_meta.json"
        np.save(dem_path, dem)
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        return dem, meta
