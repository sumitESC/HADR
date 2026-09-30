import json
from fastapi import APIRouter, HTTPException, Query
from shapely.geometry import LineString, mapping
from shapely.ops import unary_union
from app.config import SATELLITE_DIR, DAMS_DIR

router = APIRouter(prefix="/api/satellite", tags=["Satellite"])

@router.get("/sentinel1")
def get_sentinel1_water_mask(dam_id: str = "tehri-dam"):
    """
    Returns Sentinel-1 SAR water mask comparison GeoJSON.
    Generates a synthetic SAR flood mask for demonstration if real data unavailable.
    """
    # Check for pre-cached data first
    sat_file = SATELLITE_DIR / f"{dam_id}_sentinel1.geojson"
    if sat_file.exists():
        with open(sat_file, "r") as f:
            return json.load(f)

    # Fallback: check legacy file
    legacy_file = SATELLITE_DIR / "sentinel1_water_mask.geojson"
    if legacy_file.exists() and dam_id == "tehri-dam":
        with open(legacy_file, "r") as f:
            return json.load(f)

    # Generate synthetic SAR mask for the dam location
    dam_meta = _load_dam(dam_id)
    if not dam_meta:
        raise HTTPException(status_code=404, detail=f"Dam '{dam_id}' not found")

    lat, lon = dam_meta["lat"], dam_meta["lon"]

    # Create a synthetic flood footprint offset from simulation
    synthetic_line = LineString([
        [lon, lat],
        [lon + 0.02, lat - 0.015],
        [lon + 0.04, lat - 0.03],
        [lon + 0.06, lat - 0.05],
    ])
    buffer_geom = synthetic_line.buffer(0.008, cap_style=1)

    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "source": "Sentinel-1 SAR (Synthetic Demo)",
                "acquisition_date": "2025-09-10",
                "polarization": "VV",
                "dam_id": dam_id
            },
            "geometry": mapping(buffer_geom)
        }]
    }

    # Cache
    with open(sat_file, "w") as f:
        json.dump(geojson, f, indent=2)

    return geojson


def _load_dam(dam_id: str):
    dams_file = DAMS_DIR / "dams.json"
    if dams_file.exists():
        with open(dams_file, "r") as f:
            for d in json.load(f):
                if d.get("id") == dam_id:
                    return d
    return None
