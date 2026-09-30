export interface Dam {
  id: string;
  name: string;
  state: string;
  river: string;
  lat: number;
  lon: number;
  dam_height_m: number;
  reservoir_water_level_m: number;
  normal_storage_mcm: number;
  spillway_capacity_m3s: number;
  type: string;
  year_completed: number;
  downstream_towns: string[];
  description: string;
}

export interface SimulationResult {
  simulation_id: string;
  status: string;
  engine: string;
  dam_id: string;
  dam_name: string;
  dam_state?: string;
  dam_river?: string;
  dam_lat?: number;
  dam_lon?: number;
  release_percent: number;
  duration_min: number;
  time_step_min: number;
  timesteps_min: number[];
  max_depth_m: number;
  inundated_area_km2: number;
  hydrograph?: {
    q_peak_m3s: number;
    total_volume_m3: number;
    effective_breach_width_m: number;
  };
}

export interface SettlementExposed {
  name: string;
  type: string;
  population: number;
  elevation_m: number;
  coordinates: [number, number];
  water_depth_m?: number;
  damage_ratio_pct?: number;
  hazard_level?: string;
  evacuation_status?: string;
  estimated_loss_inr?: number;
}

export interface RoadExposed {
  name: string;
  category: string;
  flooded_length_km: number;
  max_water_depth_m?: number;
  traffic_status?: string;
}

export interface ExposureSummary {
  settlements_flooded_count: number;
  total_population_exposed: number;
  affected_settlements: SettlementExposed[];
  flooded_roads_km: number;
  affected_roads: RoadExposed[];
  bridges_at_risk: number;
  hospitals_at_risk: number;
  schools_at_risk: number;
  total_estimated_damage_inr_cr?: number;
}

export interface SphParticle {
  particle_id: number;
  trajectories: {
    timestep_min: number;
    lat: number;
    lon: number;
    velocity_ms: number;
    depth_m: number;
  }[];
}

export interface SphData {
  status: string;
  model: string;
  num_particles: number;
  particles: SphParticle[];
}

export interface ComparisonRow {
  engine: string;
  status: string;
  inundated_area_km2: number;
  max_depth_m: number;
  front_arrival_t30_km: number;
  computation_time_sec: number;
}
