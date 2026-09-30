import numpy as np
from scipy.ndimage import gaussian_filter
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.ops import unary_union
from app.gis.dem_processor import DEMProcessor

class Polygonizer:
    def __init__(self, dem_processor: DEMProcessor):
        self.dem_proc = dem_processor
        self.nx = dem_processor.nx
        self.ny = dem_processor.ny
        self.lons = dem_processor.lons
        self.lats = dem_processor.lats
        self.res_x = (dem_processor.lon_max - dem_processor.lon_min) / self.nx
        self.res_y = (dem_processor.lat_max - dem_processor.lat_min) / self.ny

    def depth_raster_to_geojson(self, depth_array: np.ndarray, timestep_min: int, min_depth_threshold: float = 0.1):
        """
        Converts 2D depth raster array into smooth, organic river valley inundation GeoJSON polygons.
        Applies spatial Gaussian smoothing and Shapely buffer ops to eliminate grid cell artifacts.
        """
        # Apply spatial smoothing to emulate fluid surface continuity
        smoothed_depth = gaussian_filter(depth_array, sigma=1.2)
        smoothed_depth = np.where(smoothed_depth >= min_depth_threshold, smoothed_depth, 0.0)
        
        # Grid cell dimensions in approx km
        cell_area_km2 = (self.res_x * 96.0) * (self.res_y * 111.0)
        flooded_mask = smoothed_depth >= min_depth_threshold
        total_flooded_cells = int(np.sum(flooded_mask))
        
        if total_flooded_cells == 0:
            return {
                "type": "FeatureCollection",
                "features": [],
                "properties": {
                    "timestep_min": timestep_min,
                    "inundated_area_km2": 0.0,
                    "max_depth_m": 0.0,
                    "avg_depth_m": 0.0
                }
            }

        # Create depth contour bands for heatmap rendering
        depth_bands = [
            {"min": 0.1, "max": 0.5, "label": "0.1 - 0.5"},
            {"min": 0.5, "max": 1.0, "label": "0.5 - 1.0"},
            {"min": 1.0, "max": 2.0, "label": "1.0 - 2.0"},
            {"min": 2.0, "max": 3.0, "label": "2.0 - 3.0"},
            {"min": 3.0, "max": 4.0, "label": "3.0 - 4.0"},
            {"min": 4.0, "max": 999.0, "label": "> 4.0"}
        ]

        features = []
        depth_values = [float(smoothed_depth[i, j]) for i in range(self.ny) for j in range(self.nx) if smoothed_depth[i, j] >= min_depth_threshold]
        inundated_area_km2 = round(total_flooded_cells * cell_area_km2, 2)
        max_depth = round(float(np.max(depth_values)), 2) if depth_values else 0.0
        avg_depth = round(float(np.mean(depth_values)), 2) if depth_values else 0.0

        for band in depth_bands:
            band_mask = (smoothed_depth >= band["min"]) & (smoothed_depth < band["max"])
            if not np.any(band_mask):
                continue
            
            band_polys = []
            for i in range(self.ny):
                for j in range(self.nx):
                    if band_mask[i, j]:
                        lon_left = self.lons[j] - self.res_x / 2.0
                        lon_right = self.lons[j] + self.res_x / 2.0
                        lat_top = self.lats[i] + self.res_y / 2.0
                        lat_bottom = self.lats[i] - self.res_y / 2.0
                        
                        band_polys.append(Polygon([
                            (lon_left, lat_bottom),
                            (lon_right, lat_bottom),
                            (lon_right, lat_top),
                            (lon_left, lat_top),
                            (lon_left, lat_bottom)
                        ]))

            if band_polys:
                raw_union = unary_union(band_polys)
                smoothed_geom = raw_union.buffer(self.res_x * 0.45).buffer(-self.res_x * 0.25)
                
                geoms = list(smoothed_geom.geoms) if isinstance(smoothed_geom, MultiPolygon) else [smoothed_geom]
                for g in geoms:
                    if g.is_valid and not g.is_empty:
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "timestep_min": timestep_min,
                                "depth_band": band["label"],
                                "min_depth": band["min"],
                                "max_depth": band["max"],
                                "max_depth_m": max_depth,
                                "avg_depth_m": avg_depth,
                                "inundated_area_km2": inundated_area_km2,
                                "hazard_tier": "High Surge" if band["min"] >= 3.0 else "Moderate"
                            },
                            "geometry": mapping(g)
                        })

        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "timestep_min": timestep_min,
                "inundated_area_km2": inundated_area_km2,
                "max_depth_m": max_depth,
                "avg_depth_m": avg_depth
            }
        }
