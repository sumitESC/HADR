import time
from app.simulation.manager import SimulationManager
from app.config import DAMS_DIR
import json

def test_hang():
    print("Testing if simulation hangs on Almatti Dam...")
    dams_file = DAMS_DIR / "dams.json"
    with open(dams_file, "r") as f:
        dams = json.load(f)
    
    sim_manager = SimulationManager()
    
    # Try the 9th dam (one that hasn't finished)
    # Let's just pick one that is NOT in the 8 generated ones.
    # Generated: tehri, bhakra, hirakud, mettur, nagarjuna, sardar, almatti, koyna
    # Let's test idukki-dam
    dam_id = "idukki-dam"
    
    print(f"Starting simulation for {dam_id}...")
    start_time = time.time()
    try:
        sim_manager.create_and_run_simulation(
            dam_id=dam_id,
            release_percent=30.0,
            duration_min=360.0,
            time_step_min=30,
            engine_type="terrain"
        )
        elapsed = time.time() - start_time
        print(f"Finished successfully in {elapsed:.2f} seconds!")
    except Exception as e:
        print(f"Failed with error: {e}")

if __name__ == "__main__":
    test_hang()
