import type { Dam, SimulationResult, ExposureSummary, SphData, ComparisonRow } from '../types';

const API_BASE = 'http://localhost:8000/api';

export const api = {
  async getDams(search?: string): Promise<Dam[]> {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    const res = await fetch(`${API_BASE}/dams${params}`);
    if (!res.ok) throw new Error('Failed to fetch dams catalog');
    return res.json();
  },

  async getDamDetail(damId: string): Promise<Dam> {
    const res = await fetch(`${API_BASE}/dams/${damId}`);
    if (!res.ok) throw new Error(`Failed to fetch dam details for ${damId}`);
    return res.json();
  },

  async getDamStates(): Promise<{ state: string; count: number }[]> {
    const res = await fetch(`${API_BASE}/dams/states`);
    if (!res.ok) throw new Error('Failed to fetch dam states');
    return res.json();
  },

  async runSimulation(payload: {
    dam_id: string;
    release_percent: number;
    duration_min: number;
    time_step_min: number;
    engine: string;
    custom_lat?: number;
    custom_lon?: number;
    custom_name?: string;
    custom_height_m?: number;
    custom_river?: string;
  }): Promise<{ simulation_id: string; status: string; engine: string; max_depth_m: number; inundated_area_km2: number; timesteps_min: number[]; dam_name?: string; dam_lat?: number; dam_lon?: number; hydrograph?: any }> {
    const res = await fetch(`${API_BASE}/simulations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Simulation failed to start');
    return res.json();
  },

  async getSimulationMetadata(simId: string): Promise<SimulationResult> {
    const res = await fetch(`${API_BASE}/simulations/${simId}`);
    if (!res.ok) throw new Error(`Failed to fetch simulation metadata for ${simId}`);
    return res.json();
  },

  async getSimulationGeoJSON(simId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/simulations/${simId}/timesteps`);
    if (!res.ok) throw new Error(`Failed to fetch GeoJSON for ${simId}`);
    return res.json();
  },

  async getExposure(simId: string): Promise<ExposureSummary> {
    const res = await fetch(`${API_BASE}/simulations/${simId}/exposure`);
    if (!res.ok) throw new Error(`Failed to fetch exposure data for ${simId}`);
    return res.json();
  },

  async getSphParticles(simId: string): Promise<SphData> {
    const res = await fetch(`${API_BASE}/simulations/${simId}/sph`);
    if (!res.ok) throw new Error(`Failed to fetch SPH particles for ${simId}`);
    return res.json();
  },

  async getComparison(simId: string): Promise<{ comparison: ComparisonRow[] }> {
    const res = await fetch(`${API_BASE}/simulations/${simId}/comparison`);
    if (!res.ok) throw new Error(`Failed to fetch comparison table for ${simId}`);
    return res.json();
  },

  async getSentinel1Mask(damId: string = 'tehri-dam'): Promise<any> {
    const res = await fetch(`${API_BASE}/satellite/sentinel1?dam_id=${damId}`);
    if (!res.ok) throw new Error('Failed to fetch Sentinel-1 SAR mask');
    return res.json();
  },

  getExportUrl(simId: string, format: string): string {
    return `${API_BASE}/simulations/${simId}/export/${format}`;
  }
};
