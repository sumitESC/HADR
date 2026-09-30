"""Test that different durations produce meaningfully different results."""
from app.simulation.manager import SimulationManager

mgr = SimulationManager()

for dur in [60, 180, 360, 720]:
    meta = mgr.create_and_run_simulation(
        dam_id="tehri-dam", release_percent=30.0,
        duration_min=dur, time_step_min=30, engine_type="terrain"
    )
    area = meta["inundated_area_km2"]
    depth = meta["max_depth_m"]
    exp = meta.get("exposure_summary", {})
    pop = exp.get("total_population_exposed", 0)
    settlements = exp.get("settlements_flooded_count", 0)
    hydro = meta.get("hydrograph", {})
    q_peak = hydro.get("q_peak_m3s", 0)
    
    print(f"Duration={dur:4d}min | Area={area:6.1f}km² | MaxDepth={depth:4.1f}m | Pop={pop:6d} | Settlements={settlements:3d} | Q_peak={q_peak:.0f} m³/s")
