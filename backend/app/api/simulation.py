from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.simulation.manager import SimulationManager

router = APIRouter(prefix="/api/simulations", tags=["Simulations"])
sim_manager = SimulationManager()

class SimulationRequest(BaseModel):
    dam_id: str = Field(default="tehri-dam", description="Target dam identifier (use 'custom' for any dam)")
    release_percent: float = Field(default=30.0, ge=1.0, le=100.0, description="Reservoir water release percentage (1-100%)")
    duration_min: float = Field(default=360.0, ge=30.0, le=1440.0, description="Simulation duration in minutes")
    time_step_min: int = Field(default=30, ge=5, le=120, description="Timestep interval in minutes")
    engine: str = Field(default="terrain", description="Simulation engine choice (terrain, sph, delft3d)")

    # Custom dam fields — for simulating ANY dam in the world
    custom_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude for custom dam")
    custom_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude for custom dam")
    custom_name: Optional[str] = Field(default=None, description="Name for custom dam")
    custom_height_m: Optional[float] = Field(default=None, ge=5.0, le=500.0, description="Dam height in meters")
    custom_river: Optional[str] = Field(default=None, description="River name for custom dam")

    @field_validator("engine")
    @classmethod
    def validate_engine(cls, v: str):
        if v not in ["terrain", "sph", "delft3d"]:
            raise ValueError("Engine must be 'terrain', 'sph', or 'delft3d'")
        return v

@router.post("", status_code=status.HTTP_201_CREATED)
def start_simulation(req: SimulationRequest):
    """Triggers dam-break flood simulation. Supports any dam in the world via custom coordinates."""
    try:
        # Build custom dam metadata if provided
        custom_dam_meta = None
        if req.custom_lat is not None and req.custom_lon is not None:
            custom_dam_meta = {
                "id": req.dam_id if req.dam_id != "custom" else f"custom-{abs(hash(f'{req.custom_lat}{req.custom_lon}'))}",
                "name": req.custom_name or f"Custom Dam ({req.custom_lat:.3f}, {req.custom_lon:.3f})",
                "lat": req.custom_lat,
                "lon": req.custom_lon,
                "dam_height_m": req.custom_height_m or 100.0,
                "river": req.custom_river or "Unknown River",
                "state": "Custom",
                "reservoir_capacity_mcm": 0
            }
            # Generate a stable dam_id from coordinates
            dam_id = f"custom-{int(abs(req.custom_lat*1000))}-{int(abs(req.custom_lon*1000))}"
            custom_dam_meta["id"] = dam_id
        else:
            dam_id = req.dam_id

        meta = sim_manager.create_and_run_simulation(
            dam_id=dam_id,
            release_percent=req.release_percent,
            duration_min=req.duration_min,
            time_step_min=req.time_step_min,
            engine_type=req.engine,
            custom_dam_meta=custom_dam_meta
        )
        return {
            "simulation_id": meta["simulation_id"],
            "status": meta["status"],
            "engine": meta["engine_name"],
            "max_depth_m": meta["max_depth_m"],
            "inundated_area_km2": meta["inundated_area_km2"],
            "timesteps_min": meta["timesteps_min"],
            "dam_name": meta.get("dam_name", ""),
            "dam_lat": meta.get("dam_lat"),
            "dam_lon": meta.get("dam_lon"),
            "hydrograph": meta.get("hydrograph"),
            "message": "Simulation executed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.get("/{sim_id}")
def get_simulation_status(sim_id: str):
    """Retrieves metadata, parameters, and status for a simulation ID."""
    meta = sim_manager.get_simulation_metadata(sim_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Simulation '{sim_id}' not found")
    return meta

@router.get("/{sim_id}/timesteps")
def get_simulation_geojson(sim_id: str):
    """Retrieves time-series GeoJSON flood polygons."""
    geojson = sim_manager.get_simulation_geojson(sim_id)
    if not geojson:
        raise HTTPException(status_code=404, detail=f"GeoJSON for simulation '{sim_id}' not found")
    return geojson

@router.get("/{sim_id}/sph")
def get_sph_particles(sim_id: str):
    """Retrieves downhill SPH particle trajectories for visualization."""
    sph_data = sim_manager.get_sph_particles(sim_id)
    if not sph_data:
        raise HTTPException(status_code=404, detail=f"SPH data for simulation '{sim_id}' not found")
    return sph_data

@router.get("/{sim_id}/comparison")
def get_model_comparison(sim_id: str):
    """Retrieves side-by-side comparative hydrodynamics table for Terrain vs SPH vs Delft3D."""
    comp = sim_manager.get_comparison(sim_id)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Comparison data for simulation '{sim_id}' not found")
    return comp
