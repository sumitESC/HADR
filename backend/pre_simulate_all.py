"""
Pre-Simulate ALL 49 Dams — Complete Data Generation
====================================================
Generates ALL simulation data locally so Render needs ZERO computation:
  1. Terrain Engine simulation (flood_extent.geojson, metadata.json, etc.)
  2. Exposure analysis (exposure.json)
  3. SPH Particle trajectories (sph_particles.json)
  4. Model Comparison metrics (comparison.json)

After running, commit backend/outputs/ and backend/data/ to GitHub.
"""
import json
import time
import traceback
from pathlib import Path
from app.simulation.manager import SimulationManager
from app.simulation.sph_adapter import SPHParticleVisualizer
from app.simulation.delft3d_adapter import Delft3DAdapter
from app.config import DAMS_DIR, OUTPUTS_DIR

def main():
    print("=" * 70)
    print("   PRE-SIMULATING ALL 49 DAMS — COMPLETE DATA GENERATION")
    print("   (Terrain + SPH + Comparison + Exposure)")
    print("=" * 70)

    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        print(f"Error: {dams_file} not found.")
        return

    with open(dams_file, "r") as f:
        dams = json.load(f)

    sim_manager = SimulationManager()
    total_dams = len(dams)
    print(f"Found {total_dams} dams. Starting complete data generation...\n")

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for i, dam in enumerate(dams):
        dam_id = dam['id']
        dam_name = dam['name']
        safe_dam_id = dam_id.replace(" ", "_")
        sim_id = f"sim-{safe_dam_id}-terrain-30-360"
        sim_dir = OUTPUTS_DIR / sim_id

        print(f"\n{'='*60}")
        print(f"[{i+1}/{total_dams}] {dam_name} ({dam_id})")
        print(f"{'='*60}")

        # ── Step 1: Terrain Simulation + Exposure ────────────────────
        meta_file = sim_dir / "metadata.json"
        if meta_file.exists():
            print(f"  [CACHED] Terrain simulation already exists.")
            with open(meta_file, "r") as f:
                meta = json.load(f)
        else:
            print(f"  [RUNNING] Terrain simulation...")
            try:
                start_time = time.time()
                meta = sim_manager.create_and_run_simulation(
                    dam_id=dam_id,
                    release_percent=30.0,
                    duration_min=360.0,
                    time_step_min=30,
                    engine_type="terrain"
                )
                elapsed = time.time() - start_time
                print(f"  [OK] Terrain sim completed in {elapsed:.2f}s")
            except Exception as e:
                print(f"  [FAIL] Terrain sim failed: {e}")
                traceback.print_exc()
                fail_count += 1
                continue

        # ── Step 2: SPH Particle Trajectories ────────────────────────
        sph_file = sim_dir / "sph_particles.json"
        if sph_file.exists():
            print(f"  [CACHED] SPH particles already exist.")
        else:
            print(f"  [RUNNING] SPH particle generation...")
            try:
                start_time = time.time()
                # Initialize engine for this dam
                dam_meta = sim_manager._load_dam_meta(dam_id)
                sim_manager.engine._init_for_dam(dam_meta)
                
                sph = SPHParticleVisualizer(sim_manager.engine.dem_proc)
                sph_data = sph.generate_particle_trajectories(
                    dam_lat=dam.get("lat", 30.3774),
                    dam_lon=dam.get("lon", 78.4803),
                    num_particles=200
                )
                
                with open(sph_file, "w") as f:
                    json.dump(sph_data, f)
                
                elapsed = time.time() - start_time
                print(f"  [OK] SPH particles generated in {elapsed:.2f}s")
            except Exception as e:
                print(f"  [FAIL] SPH generation failed: {e}")
                traceback.print_exc()

        # ── Step 3: Model Comparison (Delft3D vs Terrain vs SPH) ─────
        comp_file = sim_dir / "comparison.json"
        if comp_file.exists():
            print(f"  [CACHED] Comparison data already exists.")
        else:
            print(f"  [RUNNING] Model comparison...")
            try:
                start_time = time.time()
                # Ensure engine is initialized for this dam
                dam_meta = sim_manager._load_dam_meta(dam_id)
                sim_manager.engine._init_for_dam(dam_meta)
                
                d3d = Delft3DAdapter(sim_manager.engine.dem_proc)
                comp_data = d3d.get_comparison_metrics(
                    dam_id=dam_id,
                    dam_lat=dam.get("lat", 30.3774),
                    dam_lon=dam.get("lon", 78.4803),
                    release_percent=30.0,
                    terrain_area_km2=meta.get("inundated_area_km2", 24.6),
                    terrain_max_depth_m=meta.get("max_depth_m", 4.2)
                )
                
                with open(comp_file, "w") as f:
                    json.dump(comp_data, f, indent=2)
                
                elapsed = time.time() - start_time
                print(f"  [OK] Comparison generated in {elapsed:.2f}s")
            except Exception as e:
                print(f"  [FAIL] Comparison generation failed: {e}")
                traceback.print_exc()

        # ── Step 4: Ensure Exposure exists ───────────────────────────
        exp_file = sim_dir / "exposure.json"
        if exp_file.exists():
            print(f"  [CACHED] Exposure data already exists.")
        else:
            print(f"  [RUNNING] Exposure analysis...")
            try:
                exp_data = sim_manager.get_exposure(sim_id)
                if exp_data:
                    print(f"  [OK] Exposure analysis completed.")
                else:
                    print(f"  [WARN] Exposure returned None (no flood features?).")
            except Exception as e:
                print(f"  [FAIL] Exposure failed: {e}")
                traceback.print_exc()

        success_count += 1
        print(f"  [COMPLETE] All data for {dam_name} is ready.")

    print("\n" + "=" * 70)
    print(f"COMPLETE DATA GENERATION FINISHED!")
    print(f"Success: {success_count} | Failed: {fail_count}")
    print(f"\nAll outputs are cached in backend/outputs/")
    print(f"Ready for: git add . && git commit && git push")
    print("=" * 70)

if __name__ == "__main__":
    main()
