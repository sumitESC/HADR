import json
import time
from pathlib import Path
from app.simulation.manager import SimulationManager
from app.config import DAMS_DIR

def main():
    print("="*60)
    print("   PRE-SIMULATING ALL DAMS FOR CLOUD CACHING")
    print("="*60)

    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        print(f"Error: {dams_file} not found.")
        return

    with open(dams_file, "r") as f:
        dams = json.load(f)

    sim_manager = SimulationManager()
    
    total_dams = len(dams)
    print(f"Found {total_dams} dams. Starting simulation generation...\n")

    success_count = 0
    fail_count = 0

    for i, dam in enumerate(dams):
        dam_id = dam['id']
        dam_name = dam['name']
        print(f"[{i+1}/{total_dams}] Simulating {dam_name} ({dam_id})...")
        
        try:
            start_time = time.time()
            # We run the default parameters that the frontend requests by default
            # engine = terrain, release_percent = 30.0, duration = 360
            sim_manager.create_and_run_simulation(
                dam_id=dam_id,
                release_percent=30.0,
                duration_min=360.0,
                time_step_min=30,
                engine_type="terrain"
            )
            elapsed = time.time() - start_time
            print(f"  [OK] Success in {elapsed:.2f}s")
            success_count += 1
        except Exception as e:
            print(f"  [FAIL] Failed: {e}")
            fail_count += 1

    print("\n" + "="*60)
    print(f"Simulation Generation Complete!")
    print(f"Success: {success_count} | Failed: {fail_count}")
    print("All outputs are now cached in backend/outputs/ and ready for Git commit.")
    print("="*60)

if __name__ == "__main__":
    main()
