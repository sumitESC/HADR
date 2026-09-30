import React, { useState } from 'react';
import type { Dam } from '../types';
import { Play, Sliders, Clock, Cpu, RefreshCw, CheckCircle2, MapPin, Globe2, Mountain } from 'lucide-react';

interface SimulationTabProps {
  dams: Dam[];
  onRunSimulation: (params: {
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
  }) => Promise<void>;
  loading: boolean;
}

export const SimulationTab: React.FC<SimulationTabProps> = ({ dams, onRunSimulation, loading }) => {
  const [selectedDam, setSelectedDam] = useState<string>('tehri-dam');
  const [releasePercent, setReleasePercent] = useState<number>(30);
  const [durationMin, setDurationMin] = useState<number>(360);
  const [timeStepMin, setTimeStepMin] = useState<number>(30);
  const [engine, setEngine] = useState<string>('terrain');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Custom dam state
  const [useCustomDam, setUseCustomDam] = useState<boolean>(false);
  const [customLat, setCustomLat] = useState<string>('');
  const [customLon, setCustomLon] = useState<string>('');
  const [customName, setCustomName] = useState<string>('');
  const [customHeight, setCustomHeight] = useState<string>('100');
  const [customRiver, setCustomRiver] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);

    const params: any = {
      dam_id: useCustomDam ? 'custom' : selectedDam,
      release_percent: releasePercent,
      duration_min: durationMin,
      time_step_min: timeStepMin,
      engine
    };

    if (useCustomDam) {
      if (!customLat || !customLon) {
        alert('Please enter latitude and longitude for the custom dam');
        return;
      }
      params.custom_lat = parseFloat(customLat);
      params.custom_lon = parseFloat(customLon);
      params.custom_name = customName || `Dam at ${customLat}, ${customLon}`;
      params.custom_height_m = parseFloat(customHeight) || 100;
      params.custom_river = customRiver || undefined;
    }

    await onRunSimulation(params);
    setSuccessMsg('Simulation scenario generated! Time-series inundation results loaded.');
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="glass-panel p-6 rounded-2xl space-y-6 border border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2 font-heading">
              <Sliders className="w-5 h-5 text-cyan-400" /> Scenario Parameter Setup
            </h2>
            <p className="text-xs text-slate-400">Configure dam breach water release, discharge duration, and hydrodynamic engine choice.</p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            Physics-Based Inundation Engine
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dam Source Toggle */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setUseCustomDam(false)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border text-sm font-bold transition-all ${
                !useCustomDam
                  ? 'bg-cyan-500/15 border-cyan-500 text-cyan-300 shadow-md shadow-cyan-500/10'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Mountain className="w-4 h-4" /> Database Dams ({dams.length})
            </button>
            <button
              type="button"
              onClick={() => setUseCustomDam(true)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border text-sm font-bold transition-all ${
                useCustomDam
                  ? 'bg-emerald-500/15 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-500/10'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Globe2 className="w-4 h-4" /> Any Dam in the World
            </button>
          </div>

          {/* Dam Selection - Database */}
          {!useCustomDam && (
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 block uppercase tracking-wider">Select Monitored Dam & Catchment</label>
              <select
                value={selectedDam}
                onChange={(e) => setSelectedDam(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500 font-medium"
              >
                {dams.map((dam) => (
                  <option key={dam.id} value={dam.id}>
                    {dam.name} — {dam.river} (Crest: {dam.dam_height_m}m)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Custom Dam Input */}
          {useCustomDam && (
            <div className="space-y-4 p-4 rounded-xl bg-slate-900/80 border border-emerald-500/20">
              <div className="flex items-center gap-2 mb-1">
                <MapPin className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Custom Dam Coordinates</span>
              </div>
              <p className="text-[10px] text-slate-500 -mt-2">
                Enter the coordinates of any dam worldwide. Real DEM elevation, OSM river data, and settlements will be fetched automatically.
              </p>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="-90"
                    max="90"
                    placeholder="e.g. 30.3774"
                    value={customLat}
                    onChange={(e) => setCustomLat(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
                    required={useCustomDam}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="-180"
                    max="180"
                    placeholder="e.g. 78.4803"
                    value={customLon}
                    onChange={(e) => setCustomLon(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
                    required={useCustomDam}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Dam Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Hoover Dam"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Dam Height (m)</label>
                  <input
                    type="number"
                    step="1"
                    min="5"
                    max="500"
                    placeholder="100"
                    value={customHeight}
                    onChange={(e) => setCustomHeight(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">River Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Colorado"
                    value={customRiver}
                    onChange={(e) => setCustomRiver(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Water Release Percentage Slider */}
          <div className="space-y-3 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-300 uppercase tracking-wider">Water Release / Breach Volume</span>
              <span className="font-extrabold text-cyan-400 text-sm font-mono">{releasePercent}% Release</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={releasePercent}
              onChange={(e) => setReleasePercent(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-medium">
              <span>10% (Spillway Overflow)</span>
              <span>50% (Partial Structural Breach)</span>
              <span>100% (Catastrophic Breach)</span>
            </div>
          </div>

          {/* Duration & Timestep */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                <Clock className="w-3.5 h-3.5 text-cyan-400" /> Simulation Duration
              </label>
              <select
                value={durationMin}
                onChange={(e) => setDurationMin(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-medium"
              >
                <option value={120}>120 Minutes (2 Hours)</option>
                <option value={240}>240 Minutes (4 Hours)</option>
                <option value={360}>360 Minutes (6 Hours - Standard)</option>
                <option value={720}>720 Minutes (12 Hours)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                <Clock className="w-3.5 h-3.5 text-cyan-400" /> Timestep Interval
              </label>
              <select
                value={timeStepMin}
                onChange={(e) => setTimeStepMin(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-medium"
              >
                <option value={15}>15 Minutes (High Resolution)</option>
                <option value={30}>30 Minutes (Standard)</option>
                <option value={60}>60 Minutes (Coarse)</option>
              </select>
            </div>
          </div>

          {/* Hydrodynamic Engine Selection */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Hydrodynamic Model Engine
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <label className={`p-4 rounded-xl border cursor-pointer transition-all ${
                engine === 'terrain'
                  ? 'bg-cyan-500/15 border-cyan-500 text-cyan-300 shadow-md shadow-cyan-500/10'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}>
                <input
                  type="radio"
                  name="engine"
                  value="terrain"
                  checked={engine === 'terrain'}
                  onChange={() => setEngine('terrain')}
                  className="sr-only"
                />
                <div className="font-bold text-xs text-white">Physics-Based Terrain Solver</div>
                <div className="text-[10px] text-slate-400 mt-1">Manning + DEM Cross-Section + Gravity</div>
              </label>

              <label className={`p-4 rounded-xl border cursor-pointer transition-all ${
                engine === 'sph'
                  ? 'bg-amber-500/15 border-amber-500 text-amber-300 shadow-md shadow-amber-500/10'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}>
                <input
                  type="radio"
                  name="engine"
                  value="sph"
                  checked={engine === 'sph'}
                  onChange={() => setEngine('sph')}
                  className="sr-only"
                />
                <div className="font-bold text-xs text-white">Smooth Particle Hydrodynamics</div>
                <div className="text-[10px] text-slate-400 mt-1">SPH Fluid Particle Velocity Model</div>
              </label>

              <label className={`p-4 rounded-xl border cursor-pointer transition-all ${
                engine === 'delft3d'
                  ? 'bg-blue-500/15 border-blue-500 text-blue-300 shadow-md shadow-blue-500/10'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}>
                <input
                  type="radio"
                  name="engine"
                  value="delft3d"
                  checked={engine === 'delft3d'}
                  onChange={() => setEngine('delft3d')}
                  className="sr-only"
                />
                <div className="font-bold text-xs text-white">Delft3D Model Suite</div>
                <div className="text-[10px] text-slate-400 mt-1">2D Shallow-Water Benchmark</div>
              </label>
            </div>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-extrabold text-sm shadow-lg shadow-cyan-500/25 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin text-white" />
                Executing Physics Solver — Fetching DEM & River Data...
              </>
            ) : (
              <>
                <Play className="w-5 h-5 fill-white" />
                Run Physics-Based Simulation
              </>
            )}
          </button>
        </form>

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> {successMsg}
          </div>
        )}
      </div>
    </div>
  );
};
