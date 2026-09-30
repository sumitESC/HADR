from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import OUTPUTS_DIR

router = APIRouter(prefix="/api/simulations", tags=["Export"])

@router.get("/{sim_id}/export/{fmt}")
def export_simulation_results(sim_id: str, fmt: str):
    """
    Downloads GIS file export for simulation.
    Supported formats: geojson, kml, shp
    """
    sim_dir = OUTPUTS_DIR / sim_id
    if not sim_dir.exists():
        raise HTTPException(status_code=404, detail=f"Simulation '{sim_id}' not found")

    fmt_lower = fmt.lower()
    if fmt_lower == "geojson":
        file_path = sim_dir / "flood_extent.geojson"
        media_type = "application/geo+json"
        filename = f"{sim_id}_flood_extent.geojson"
    elif fmt_lower == "kml":
        file_path = sim_dir / "flood_extent.kml"
        media_type = "application/vnd.google-earth.kml+xml"
        filename = f"{sim_id}_flood_extent.kml"
    elif fmt_lower in ["shp", "shapefile", "zip"]:
        file_path = sim_dir / "flood_extent_shp.zip"
        media_type = "application/zip"
        filename = f"{sim_id}_flood_extent_shp.zip"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{fmt}'. Supported: geojson, kml, shp")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Export file for format '{fmt}' not generated")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )
