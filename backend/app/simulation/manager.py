import json
import uuid
from pathlib import Path
from app.simulation.terrain_engine import TerrainEngine
from app.simulation.sph_adapter import SPHParticleVisualizer
from app.simulation.delft3d_adapter import Delft3DAdapter
from app.gis.exposure import ExposureAnalyzer
from app.gis.osm_data import OSMDataFetcher
from app.config import OUTPUTS_DIR, DAMS_DIR

class SimulationManager:
    def __init__(self):
        self.engine = TerrainEngine()
        self.exposure_analyzer = ExposureAnalyzer()

    def _load_dam_meta(self, dam_id: str):
        """Load dam metadata from database."""
        dams_file = DAMS_DIR / "dams.json"
        if dams_file.exists():
            with open(dams_file, "r") as f:
                dams = json.load(f)
                for d in dams:
                    if d.get("id") == dam_id:
                        return d
        return {"id": dam_id, "name": "Unknown", "lat": 30.3774, "lon": 78.4803, "dam_height_m": 100}

    def create_and_run_simulation(self, dam_id: str = "tehri-dam", release_percent: float = 30.0,
                                   duration_min: float = 360.0, time_step_min: int = 30,
                                   engine_type: str = "terrain", custom_dam_meta: dict = None):
        
        # Generate a deterministic ID based on the input parameters
        safe_dam_id = dam_id.replace(" ", "_")
        sim_id = f"sim-{safe_dam_id}-{engine_type}-{int(release_percent)}-{int(duration_min)}"

        # Check if this exact simulation has already been cached
        sim_dir = OUTPUTS_DIR / sim_id
        if sim_dir.exists() and (sim_dir / "metadata.json").exists():
            print(f"[SimulationManager] Returning cached simulation: {sim_id}")
            meta = self.get_simulation_metadata(sim_id)
            if meta:
                # Ensure exposure summary is attached if it exists
                exp = self.get_exposure(sim_id)
                if exp:
                    meta["exposure_summary"] = exp
                return meta

        # If custom dam metadata provided (any dam in the world), use it directly
        if custom_dam_meta:
            dam_meta = custom_dam_meta
        else:
            dam_meta = self._load_dam_meta(dam_id)

        meta, geojson_data = self.engine.run_simulation(
            sim_id=sim_id,
            dam_id=dam_id,
            release_percent=release_percent,
            duration_min=duration_min,
            time_step_min=time_step_min,
            dam_meta_override=dam_meta
        )

        # Fetch real OSM data for exposure analysis
        try:
            settlements, roads, _ = OSMDataFetcher.get_or_fetch_data(
                dam_id, dam_meta.get("lat", 30.3774), dam_meta.get("lon", 78.4803)
            )
            self.exposure_analyzer.load_dynamic_data(settlements, roads)
        except Exception as e:
            print(f"[SimulationManager] Could not load OSM data for exposure: {e}")

        # Run exposure analysis & cache
        exposure_results = self.exposure_analyzer.analyze_exposure(geojson_data)
        sim_dir = OUTPUTS_DIR / sim_id
        with open(sim_dir / "exposure.json", "w") as f:
            json.dump(exposure_results, f, indent=2)

        meta["exposure_summary"] = exposure_results
        return meta

    def get_simulation_metadata(self, sim_id: str):
        sim_dir = OUTPUTS_DIR / sim_id
        meta_file = sim_dir / "metadata.json"
        if not meta_file.exists():
            return None
        with open(meta_file, "r") as f:
            return json.load(f)

    def get_simulation_geojson(self, sim_id: str):
        sim_dir = OUTPUTS_DIR / sim_id
        geojson_file = sim_dir / "flood_extent.geojson"
        if not geojson_file.exists():
            return None
        with open(geojson_file, "r") as f:
            return json.load(f)

    def get_exposure(self, sim_id: str):
        sim_dir = OUTPUTS_DIR / sim_id
        exp_file = sim_dir / "exposure.json"
        if not exp_file.exists():
            # Compute on the fly if needed
            geojson_data = self.get_simulation_geojson(sim_id)
            if not geojson_data:
                return None
            results = self.exposure_analyzer.analyze_exposure(geojson_data)
            with open(exp_file, "w") as f:
                json.dump(results, f, indent=2)
            return results
        with open(exp_file, "r") as f:
            return json.load(f)

    def get_sph_particles(self, sim_id: str):
        # Serve from pre-computed cache first (for low-RAM deployment)
        sim_dir = OUTPUTS_DIR / sim_id
        sph_file = sim_dir / "sph_particles.json"
        if sph_file.exists():
            with open(sph_file, "r") as f:
                return json.load(f)

        # Fallback: compute on-the-fly (only for local dev / custom dams)
        meta = self.get_simulation_metadata(sim_id)
        if not meta:
            return None
        dam_lat = meta.get("dam_lat", 30.3774)
        dam_lon = meta.get("dam_lon", 78.4803)
        dam_id = meta.get("dam_id", "tehri-dam")
        
        # Ensure engine has correct DEM for this dam
        dam_meta = self._load_dam_meta(dam_id)
        # If custom dam, reconstruct meta from simulation metadata
        if dam_meta.get("name") == "Unknown" and meta.get("dam_name"):
            dam_meta = {
                "id": dam_id,
                "name": meta["dam_name"],
                "lat": dam_lat,
                "lon": dam_lon,
                "dam_height_m": meta.get("dam_height_m", 100)
            }
        self.engine._init_for_dam(dam_meta)
        
        sph = SPHParticleVisualizer(self.engine.dem_proc)
        sph_data = sph.generate_particle_trajectories(dam_lat=dam_lat, dam_lon=dam_lon, num_particles=200)
        
        # Cache to disk for future requests
        try:
            with open(sph_file, "w") as f:
                json.dump(sph_data, f)
        except Exception:
            pass
        
        return sph_data

    def get_comparison(self, sim_id: str):
        # Serve from pre-computed cache first (for low-RAM deployment)
        sim_dir = OUTPUTS_DIR / sim_id
        comp_file = sim_dir / "comparison.json"
        if comp_file.exists():
            with open(comp_file, "r") as f:
                return json.load(f)

        # Fallback: compute on-the-fly (only for local dev / custom dams)
        meta = self.get_simulation_metadata(sim_id)
        if not meta:
            return None
            
        dam_id = meta.get("dam_id", "tehri-dam")
        dam_lat = meta.get("dam_lat", 30.3774)
        dam_lon = meta.get("dam_lon", 78.4803)
        release_percent = meta.get("release_percent", 30.0)
        
        # Ensure engine has correct DEM for this dam
        dam_meta = self._load_dam_meta(dam_id)
        if dam_meta.get("name") == "Unknown" and meta.get("dam_name"):
            dam_meta = {
                "id": dam_id,
                "name": meta["dam_name"],
                "lat": dam_lat,
                "lon": dam_lon,
                "dam_height_m": meta.get("dam_height_m", 100)
            }
        self.engine._init_for_dam(dam_meta)
        
        d3d = Delft3DAdapter(self.engine.dem_proc)
        comp_data = d3d.get_comparison_metrics(
            dam_id=dam_id,
            dam_lat=dam_lat,
            dam_lon=dam_lon,
            release_percent=release_percent,
            terrain_area_km2=meta.get("inundated_area_km2", 24.6),
            terrain_max_depth_m=meta.get("max_depth_m", 4.2)
        )
        
        # Cache to disk for future requests
        try:
            with open(comp_file, "w") as f:
                json.dump(comp_data, f, indent=2)
        except Exception:
            pass
        
        return comp_data
