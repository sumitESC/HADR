"""
FAST Pre-Simulate ALL 49 Dams — Parallel Processing
=====================================================
Uses multiprocessing to run 4 dams simultaneously.
Generates: terrain sim, SPH particles, comparison, exposure.
"""
import json
import time
import traceback
import sys
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Must be at top-level for multiprocessing
def simulate_single_dam(dam_dict):
    """Run full simulation pipeline for a single dam. Runs in a subprocess."""
    # Import inside function for subprocess safety
    from app.simulation.manager import SimulationManager
    from app.simulation.sph_adapter import SPHParticleVisualizer
    from app.simulation.delft3d_adapter import Delft3DAdapter
    from app.config import OUTPUTS_DIR

    dam_id = dam_dict['id']
    dam_name = dam_dict['name']
    safe_dam_id = dam_id.replace(" ", "_")
    sim_id = f"sim-{safe_dam_id}-terrain-30-360"
    sim_dir = OUTPUTS_DIR / sim_id
    results = {"dam_id": dam_id, "dam_name": dam_name, "status": "success", "steps": []}

    try:
        sim_manager = SimulationManager()

        # ── Step 1: Terrain Simulation ────────────────────────────────
        meta_file = sim_dir / "metadata.json"
        if meta_file.exists():
            results["steps"].append("terrain:cached")
            with open(meta_file, "r") as f:
                meta = json.load(f)
        else:
            t0 = time.time()
            meta = sim_manager.create_and_run_simulation(
                dam_id=dam_id, release_percent=30.0,
                duration_min=360.0, time_step_min=30,
                engine_type="terrain"
            )
            results["steps"].append(f"terrain:{time.time()-t0:.1f}s")

        # ── Step 2: SPH Particles ─────────────────────────────────────
        sph_file = sim_dir / "sph_particles.json"
        if sph_file.exists():
            results["steps"].append("sph:cached")
        else:
            t0 = time.time()
            dam_meta = sim_manager._load_dam_meta(dam_id)
            sim_manager.engine._init_for_dam(dam_meta)
            sph = SPHParticleVisualizer(sim_manager.engine.dem_proc)
            sph_data = sph.generate_particle_trajectories(
                dam_lat=dam_dict.get("lat", 30.3774),
                dam_lon=dam_dict.get("lon", 78.4803),
                num_particles=200
            )
            with open(sph_file, "w") as f:
                json.dump(sph_data, f)
            results["steps"].append(f"sph:{time.time()-t0:.1f}s")

        # ── Step 3: Comparison ────────────────────────────────────────
        comp_file = sim_dir / "comparison.json"
        if comp_file.exists():
            results["steps"].append("comp:cached")
        else:
            t0 = time.time()
            dam_meta = sim_manager._load_dam_meta(dam_id)
            sim_manager.engine._init_for_dam(dam_meta)
            d3d = Delft3DAdapter(sim_manager.engine.dem_proc)
            comp_data = d3d.get_comparison_metrics(
                dam_id=dam_id,
                dam_lat=dam_dict.get("lat", 30.3774),
                dam_lon=dam_dict.get("lon", 78.4803),
                release_percent=30.0,
                terrain_area_km2=meta.get("inundated_area_km2", 24.6),
                terrain_max_depth_m=meta.get("max_depth_m", 4.2)
            )
            with open(comp_file, "w") as f:
                json.dump(comp_data, f, indent=2)
            results["steps"].append(f"comp:{time.time()-t0:.1f}s")

        # ── Step 4: Exposure ──────────────────────────────────────────
        exp_file = sim_dir / "exposure.json"
        if exp_file.exists():
            results["steps"].append("exp:cached")
        else:
            t0 = time.time()
            exp_data = sim_manager.get_exposure(sim_id)
            results["steps"].append(f"exp:{time.time()-t0:.1f}s")

    except Exception as e:
        results["status"] = f"FAILED: {str(e)}"
        traceback.print_exc()

    return results


def main():
    print("=" * 70)
    print("   FAST PARALLEL PRE-SIMULATION — ALL 49 DAMS")
    print("   (4 workers, Terrain + SPH + Comparison + Exposure)")
    print("=" * 70)

    # Change to backend dir for imports
    backend_dir = Path(__file__).parent.resolve()
    sys.path.insert(0, str(backend_dir))
    os.chdir(backend_dir)

    from app.config import DAMS_DIR
    dams_file = DAMS_DIR / "dams.json"
    with open(dams_file, "r") as f:
        dams = json.load(f)

    print(f"Total dams: {len(dams)}")
    start_time = time.time()

    # Use 4 parallel workers
    NUM_WORKERS = 4
    success = 0
    failed = 0

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(simulate_single_dam, dam): dam for dam in dams}

        for future in as_completed(futures):
            dam = futures[future]
            try:
                result = future.result(timeout=600)  # 10 min max per dam
                status = result["status"]
                steps = " | ".join(result["steps"])
                if "FAILED" in status:
                    failed += 1
                    print(f"  [FAIL] {result['dam_name']}: {status}")
                else:
                    success += 1
                    print(f"  [OK] {result['dam_name']} ({steps})")
            except Exception as e:
                failed += 1
                print(f"  [FAIL] {dam['name']}: {e}")

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"DONE! Success: {success} | Failed: {failed} | Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
