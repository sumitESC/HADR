import json
from fastapi import APIRouter, HTTPException, Query
from app.config import DAMS_DIR

router = APIRouter(prefix="/api/dams", tags=["Dams"])

@router.get("")
def list_dams(state: str = None, search: str = None):
    """Returns list of dams. Optionally filter by state or search by name/river."""
    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        raise HTTPException(status_code=404, detail="Dam catalog not found")
    with open(dams_file, "r") as f:
        dams = json.load(f)
    
    if state:
        dams = [d for d in dams if d.get("state", "").lower() == state.lower()]
    
    if search:
        q = search.lower()
        dams = [d for d in dams if 
                q in d.get("name", "").lower() or 
                q in d.get("river", "").lower() or
                q in d.get("state", "").lower()]
    
    return dams

@router.get("/states")
def list_states():
    """Returns unique list of states with dam counts."""
    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        raise HTTPException(status_code=404, detail="Dam catalog not found")
    with open(dams_file, "r") as f:
        dams = json.load(f)
    
    state_counts = {}
    for d in dams:
        st = d.get("state", "Unknown")
        state_counts[st] = state_counts.get(st, 0) + 1
    
    return [{"state": s, "count": c} for s, c in sorted(state_counts.items())]

@router.get("/{dam_id}")
def get_dam_detail(dam_id: str):
    """Returns specific dam details by ID."""
    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        raise HTTPException(status_code=404, detail="Dam catalog not found")
    with open(dams_file, "r") as f:
        dams = json.load(f)
        for d in dams:
            if d.get("id") == dam_id:
                return d
    raise HTTPException(status_code=404, detail=f"Dam with ID '{dam_id}' not found")
