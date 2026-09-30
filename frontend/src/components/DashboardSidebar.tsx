import React, { useState } from 'react';
import type { Dam, SimulationResult, ExposureSummary } from '../types';
import { Waves, Sliders, Play, RefreshCw, ShieldAlert, Users, Home, Navigation, ChevronLeft, ChevronRight, Cpu } from 'lucide-react';

interface DashboardSidebarProps {
  dams: Dam[];
  simMeta: SimulationResult | null;
  exposure: ExposureSummary | null;
  onRunSimulation: (params: {
    dam_id: string;
    release_percent: number;
    duration_min: number;
    time_step_min: number;
    engine: string;
  }) => Promise<void>;
  loading: boolean;
  currentTimestep: number;
}

export const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
  dams,
  simMeta,
  exposure,
  onRunSimulation,
  loading,
  currentTimestep
}) => {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [selectedDam, setSelectedDam] = useState<string>('tehri-dam');
  const [releasePercent, setReleasePercent] = useState<number>(30);
  const [durationMin, setDurationMin] = useState<number>(360);
  const [engine, setEngine] = useState<string>('terrain');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onRunSimulation({
      dam_id: selectedDam,
      release_percent: releasePercent,
      duration_min: durationMin,
      time_step_min: 30,
      engine
    });
  };

  const inundatedArea = simMeta ? (simMeta.inundated_area_km2 * Math.min(1, (currentTimestep / 300) + 0.1)).toFixed(2) : '19.9';
  const maxDepth = simMeta ? simMeta.max_depth_m.toFixed(1) : '25.0';
  const qPeak = simMeta?.hydrograph?.q_peak_m3s ? (simMeta.hydrograph.q_peak_m3s / 1000).toFixed(1) : '215.5';

  if (collapsed) {
    return (
      <div className="z-40 my-auto ml-4">
        <button
          onClick={() => setCollapsed(false)}
          className="w-10 h-10 rounded-2xl control-sidebar flex items-center justify-center text-cyan-400 hover:text-white border border-cyan-500/40 shadow-xl"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-[320px] h-[calc(100vh-32px)] my-auto ml-4 z-40 control-sidebar p-4 flex flex-col justify-between space-y-3 overflow-y-auto shrink-0 border border-slate-800/90 shadow-2xl">
      {/* Top Header */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-md shadow-cyan-500/30">
              <Waves className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-black text-white tracking-tight leading-none font-heading">
                AquaBreak <span className="text-cyan-400">HADR</span>
              </h1>
              <p className="text-[9px] text-slate-400 font-medium mt-0.5">Flood Control Panel</p>
            </div>
          </div>
          <button
            onClick={() => setCollapsed(true)}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Catchment Card */}
        <div className="control-card p-2.5 rounded-xl flex items-center justify-between border border-slate-800 text-xs">
          <div>
            <span className="text-[9px] font-bold text-slate-500 uppercase block">Monitored Catchment</span>
            <span className="font-bold text-white text-[11px]">Bhagirathi • Tehri Hydro</span>
          </div>
          <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
        </div>

        {/* Dynamic Metric Gauges */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="control-card p-2 rounded-xl border border-slate-800">
            <span className="text-[9px] font-bold text-slate-400 uppercase block">Area</span>
            <div className="text-sm font-black text-cyan-400 font-mono mt-0.5">{inundatedArea}</div>
            <span className="text-[9px] text-slate-500 font-mono">km²</span>
          </div>

          <div className="control-card p-2 rounded-xl border border-slate-800">
            <span className="text-[9px] font-bold text-slate-400 uppercase block">Depth</span>
            <div className="text-sm font-black text-amber-400 font-mono mt-0.5">{maxDepth}<span className="text-[10px]">m</span></div>
            <span className="text-[9px] text-slate-500 font-mono">Head</span>
          </div>

          <div className="control-card p-2 rounded-xl border border-slate-800">
            <span className="text-[9px] font-bold text-slate-400 uppercase block">Q_peak</span>
            <div className="text-sm font-black text-cyan-400 font-mono mt-0.5">{qPeak}<span className="text-[10px]">k</span></div>
            <span className="text-[9px] text-slate-500 font-mono">m³/s</span>
          </div>
        </div>

        {/* Scenario Controls */}
        <div className="control-card-glow p-3 rounded-xl space-y-2">
          <h3 className="text-[11px] font-extrabold text-white uppercase tracking-wider flex items-center gap-1.5 font-heading">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Controls
          </h3>

          <form onSubmit={handleSubmit} className="space-y-2.5">
            <div className="space-y-0.5">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Dam Asset</label>
              <select
                value={selectedDam}
                onChange={(e) => setSelectedDam(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {dams.map((d) => (
                  <option key={d.id} value={d.id}>{d.name} ({d.dam_height_m}m)</option>
                ))}
              </select>
            </div>

            <div className="space-y-1 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
              <div className="flex justify-between text-[10px] font-bold">
                <span className="text-slate-400 uppercase">Release Volume</span>
                <span className="text-cyan-400 font-mono">{releasePercent}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={releasePercent}
                onChange={(e) => setReleasePercent(Number(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded appearance-none cursor-pointer"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-0.5">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Duration</label>
                <select
                  value={durationMin}
                  onChange={(e) => setDurationMin(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
                >
                  <option value={120}>2 Hours</option>
                  <option value={360}>6 Hours</option>
                  <option value={720}>12 Hours</option>
                </select>
              </div>

              <div className="space-y-0.5">
                <label className="text-[9px] font-bold text-slate-400 uppercase flex items-center gap-0.5">
                  <Cpu className="w-2.5 h-2.5 text-cyan-400" /> Engine
                </label>
                <select
                  value={engine}
                  onChange={(e) => setEngine(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
                >
                  <option value="terrain">Terrain</option>
                  <option value="sph">SPH</option>
                  <option value="delft3d">Delft3D</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-extrabold text-xs shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Simulating...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" /> RUN SCENARIO
                </>
              )}
            </button>
          </form>
        </div>

        {/* Impact Widgets */}
        <div className="space-y-1.5">
          <h3 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">
            HADR Impact
          </h3>
          <div className="grid grid-cols-3 gap-1.5 text-center text-[11px]">
            <div className="control-card p-2 rounded-lg border border-slate-800">
              <Users className="w-3 h-3 text-amber-400 mx-auto mb-0.5" />
              <div className="font-bold text-white font-mono">{exposure?.total_population_exposed.toLocaleString() || '25,400'}</div>
              <span className="text-[8px] text-slate-500 uppercase font-semibold">Exposed Pop</span>
            </div>
            <div className="control-card p-2 rounded-lg border border-slate-800">
              <Home className="w-3 h-3 text-cyan-400 mx-auto mb-0.5" />
              <div className="font-bold text-white font-mono">{exposure?.settlements_flooded_count || '1'}</div>
              <span className="text-[8px] text-slate-500 uppercase font-semibold">Flooded Towns</span>
            </div>
            <div className="control-card p-2 rounded-lg border border-slate-800">
              <Navigation className="w-3 h-3 text-red-400 mx-auto mb-0.5" />
              <div className="font-bold text-white font-mono">{exposure?.flooded_roads_km || '1.5'} <span className="text-[8px]">km</span></div>
              <span className="text-[8px] text-slate-500 uppercase font-semibold">NH-34 Road</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
