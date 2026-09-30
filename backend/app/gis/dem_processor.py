import json
import numpy as np
from pathlib import Path
from app.config import DEM_DIR
from app.gis.elevation_api import ElevationFetcher


class DEMProcessor:
    def __init__(self, dem_name: str = "tehri_dem", dam_id: str = None, lat: float = None, lon: float = None):
        """
        Dynamic DEM processor that can load pre-cached DEMs or fetch new ones.
        
        If dam_id + lat + lon are provided, fetches/loads DEM for that specific dam.
        If only dem_name is provided, tries to load legacy cached DEM files.
        """
        if dam_id and lat is not None and lon is not None:
            # Dynamic mode: fetch or load DEM for any dam
            self.dem, meta = ElevationFetcher.get_or_fetch_dem(dam_id, lat, lon)
            self.meta = meta
        else:
            # Legacy mode: load pre-existing DEM files
            self.dem_path = DEM_DIR / f"{dem_name}.npy"
            self.meta_path = DEM_DIR / f"{dem_name}_meta.json"

            if self.dem_path.exists() and self.meta_path.exists():
                self.dem = np.load(self.dem_path)
                with open(self.meta_path, "r") as f:
                    self.meta = json.load(f)
            else:
                # Auto-fetch for tehri if legacy files missing
                self.dem, self.meta = ElevationFetcher.get_or_fetch_dem(
                    "tehri-dam", 30.3774, 78.4803
                )

        self.ny, self.nx = self.dem.shape
        self.bounds = self.meta.get("bounds", [78.30, 30.20, 78.66, 30.56])
        self.lon_min, self.lat_min, self.lon_max, self.lat_max = self.bounds
        self.lons = np.linspace(self.lon_min, self.lon_max, self.nx)
        self.lats = np.linspace(self.lat_max, self.lat_min, self.ny)

    def get_stats(self):
        return {
            "nx": self.nx,
            "ny": self.ny,
            "min_elevation_m": float(np.min(self.dem)),
            "max_elevation_m": float(np.max(self.dem)),
            "mean_elevation_m": float(np.mean(self.dem)),
            "bounds": self.bounds,
            "crs": self.meta.get("crs", "EPSG:4326")
        }

    def compute_slope(self):
        """Computes elevation gradient magnitude per cell."""
        gy, gx = np.gradient(self.dem)
        slope = np.sqrt(gx**2 + gy**2)
        return slope

    def latlon_to_grid(self, lat: float, lon: float):
        """Converts geographic lat/lon to grid row (i) and col (j)."""
        j = int(np.clip((lon - self.lon_min) / (self.lon_max - self.lon_min) * (self.nx - 1), 0, self.nx - 1))
        i = int(np.clip((self.lat_max - lat) / (self.lat_max - self.lat_min) * (self.ny - 1), 0, self.ny - 1))
        return i, j

    def grid_to_latlon(self, i: int, j: int):
        """Converts grid row (i) and col (j) to geographic lon/lat."""
        lon = float(self.lons[j])
        lat = float(self.lats[i])
        return lat, lon

    def compute_d8_flow(self):
        """Calculates D8 flow direction vector for each cell towards steepest neighbor."""
        # 8 direction offsets: N, NE, E, SE, S, SW, W, NW
        offsets = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
        d8_dir = np.zeros((self.ny, self.nx), dtype=int)
        
        for i in range(self.ny):
            for j in range(self.nx):
                curr_elev = self.dem[i, j]
                max_drop = 0.0
                best_dir = 0
                for idx, (di, dj) in enumerate(offsets):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < self.ny and 0 <= nj < self.nx:
                        drop = curr_elev - self.dem[ni, nj]
                        dist = np.sqrt(di**2 + dj**2)
                        slope = drop / dist
                        if slope > max_drop:
                            max_drop = slope
                            best_dir = idx + 1
                d8_dir[i, j] = best_dir
        return d8_dir
