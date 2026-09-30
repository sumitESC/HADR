from fastapi import APIRouter, HTTPException
from app.simulation.manager import SimulationManager

router = APIRouter(prefix="/api/simulations", tags=["Exposure"])
sim_manager = SimulationManager()

@router.get("/{sim_id}/exposure")
def get_exposure_analysis(sim_id: str):
    """Returns downstream settlement and infrastructure exposure analysis."""
    exp = sim_manager.get_exposure(sim_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Exposure analysis for simulation '{sim_id}' not found")
    return exp
