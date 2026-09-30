import json
from pathlib import Path
from app.gis.dem_processor import DEMProcessor
from app.gis.inundation import InundationSolver
from app.gis.polygonizer import Polygonizer
from app.gis.exporter import Exporter
from app.gis.osm_data import OSMDataFetcher
from app.config import OUTPUTS_DIR, DAMS_DIR

class TerrainEngine:
    def __init__(self):
        """
        Dynamic terrain engine — creates DEM processor and inundation solver
        per-simulation based on the selected dam.
        """
        self.dem_proc = None
        self.solver = None

    def _init_for_dam(self, dam_meta: dict, duration_min: float = 360.0):
        """Initialize DEM and solver for a specific dam."""
        dam_id = dam_meta.get("id", "tehri-dam")
        lat = dam_meta.get("lat", 30.3774)
        lon = dam_meta.get("lon", 78.4803)

        self.dem_proc = DEMProcessor(dam_id=dam_id, lat=lat, lon=lon)
        self.solver = InundationSolver(self.dem_proc, dam_id=dam_id, dam_lat=lat, dam_lon=lon, duration_min=duration_min)

    def run_simulation(self, sim_id: str, dam_id: str, release_percent: float,
                       duration_min: float, time_step_min: int = 30,
                       dam_meta_override: dict = None):
        """
        Executes full simulation pipeline for ANY dam:
        1. Loads dam metadata from database or override
        2. Fetches/loads DEM data for dam location
        3. Fetches/loads OSM river, settlement, road data
        4. Computes physics-based flood propagation
        5. Exports GeoJSON, KML, SHP
        """
        # Use override metadata if provided (for custom dams)
        if dam_meta_override:
            dam_meta = dam_meta_override
        else:
            dam_meta = self._load_dam_meta(dam_id)

        # Initialize terrain engine for this specific dam
        self._init_for_dam(dam_meta, duration_min)

        timesteps = list(range(0, int(duration_min) + 1, int(time_step_min)))
        if 0 not in timesteps:
            timesteps.insert(0, 0)

        # Run physics-based flood propagation
        depth_rasters, hydro, max_depth = self.solver.run_terrain_propagation(
            dam_lat=dam_meta["lat"],
            dam_lon=dam_meta["lon"],
            dam_height_m=dam_meta.get("dam_height_m", 100),
            release_percent=release_percent,
            timesteps_min=timesteps,
            reservoir_capacity_mcm=dam_meta.get("reservoir_capacity_mcm", 0) or 0
        )

        sim_dir = OUTPUTS_DIR / sim_id
        sim_dir.mkdir(parents=True, exist_ok=True)

        all_timestep_features = []
        max_inundated_area = 0.0

        for t in timesteps:
            key = f"t{t}"
            ts_geojson = depth_rasters.get(key)
            if ts_geojson is not None:
                area = ts_geojson.get("properties", {}).get("inundated_area_km2", 0.0)
                max_inundated_area = max(max_inundated_area, area)
                
                # Tag features with timestep
                for feat in ts_geojson.get("features", []):
                    feat["properties"]["timestep_min"] = t
                    all_timestep_features.append(feat)

        combined_geojson = {
            "type": "FeatureCollection",
            "features": all_timestep_features,
            "properties": {
                "simulation_id": sim_id,
                "dam_id": dam_id,
                "dam_name": dam_meta.get("name"),
                "dam_lat": dam_meta.get("lat"),
                "dam_lon": dam_meta.get("lon"),
                "release_percent": release_percent,
                "duration_min": duration_min,
                "max_depth_m": max_depth,
                "max_inundated_area_km2": max_inundated_area,
                "timesteps_min": timesteps,
                "hydrograph": hydro
            }
        }

        # Export GeoJSON, KML, SHP
        Exporter.export_geojson(combined_geojson, sim_dir / "flood_extent.geojson")
        Exporter.export_kml(combined_geojson, sim_dir / "flood_extent.kml", title=f"Simulation {sim_id} - {dam_meta.get('name')}")
        Exporter.export_shp_zip(combined_geojson, sim_dir / "flood_extent_shp.zip")

        metadata = {
            "simulation_id": sim_id,
            "status": "completed",
            "engine": "terrain",
            "engine_name": "Physics-Based Terrain Flood Propagation Engine",
            "dam_id": dam_id,
            "dam_name": dam_meta.get("name"),
            "dam_state": dam_meta.get("state", ""),
            "dam_river": dam_meta.get("river", ""),
            "dam_lat": dam_meta.get("lat"),
            "dam_lon": dam_meta.get("lon"),
            "dam_height_m": dam_meta.get("dam_height_m", 100),
            "release_percent": release_percent,
            "duration_min": duration_min,
            "time_step_min": time_step_min,
            "timesteps_min": timesteps,
            "max_depth_m": max_depth,
            "inundated_area_km2": max_inundated_area,
            "hydrograph": hydro
        }

        with open(sim_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata, combined_geojson

    def _load_dam_meta(self, dam_id: str):
        """Load dam metadata from the database."""
        dams_file = DAMS_DIR / "dams.json"
        if dams_file.exists():
            with open(dams_file, "r") as f:
                dams = json.load(f)
                for d in dams:
                    if d.get("id") == dam_id:
                        return d

        # Fallback default dam (Tehri Dam)
        return {
            "id": dam_id,
            "name": "Unknown Dam",
            "lat": 30.3774,
            "lon": 78.4803,
            "dam_height_m": 100.0,
            "state": "Unknown",
            "river": "Unknown"
        }
