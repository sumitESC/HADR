import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

DEM_DIR = DATA_DIR / "dem"
DAMS_DIR = DATA_DIR / "dams"
RIVERS_DIR = DATA_DIR / "rivers"
SETTLEMENTS_DIR = DATA_DIR / "settlements"
SATELLITE_DIR = DATA_DIR / "satellite"

# Create directories if they do not exist
for folder in [DATA_DIR, OUTPUTS_DIR, DEM_DIR, DAMS_DIR, RIVERS_DIR, SETTLEMENTS_DIR, SATELLITE_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
