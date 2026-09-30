import React from 'react';
import type { Dam } from '../types';
import { ShieldAlert, Play, Layers, Activity, Cpu, MapPin, Zap } from 'lucide-react';

interface OverviewTabProps {
  dams: Dam[];
  onQuickSimulate: (damId: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ dams, onQuickSimulate }) => {
  const historicalEvents = [
    { name: 'Rishi Ganga, Uttarakhand', year: 'Feb 2021', type: 'Natural Lake Outburst / Flash Flood' },
    { name: 'Wapriyang River', year: 'Nov 2021', type: 'Sudden River Blockage Surge' },
    { name: 'Phuktal River, J&K', year: 'Mar 2015', type: 'Landslide Dam Outburst' },
    { name: 'Kosi River & Kashmir Valley', year: '2008 / 2014', type: 'Catastrophic Dam Breach & Inundation' },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-6">
      {/* Primary Hero Header */}
      <div className="glass-panel-cyan p-8 rounded-2xl relative overflow-hidden">
        <div className="relative z-10 max-w-4xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-300 text-xs font-semibold border border-cyan-500/30">
            <ShieldAlert className="w-4 h-4 text-cyan-400" /> SIH Problem Statement Framework
          </div>
          
          <h2 className="text-3xl font-black text-white tracking-tight leading-tight font-heading">
            Dam Break Inundation Modelling Using Hydrodynamic Modelling of Any River
          </h2>
          
          <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
            Generalized HADR simulation software automatically generating dam break water release surge scenarios, time-series inundation maps, and downstream damage analysis using <strong className="text-cyan-400">Smooth Particle Hydrodynamics (SPH)</strong> and <strong className="text-cyan-400">Delft3D</strong> hydrodynamic modeling.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4">
            <button
              onClick={() => onQuickSimulate('tehri-dam')}
              className="flex items-center gap-2.5 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-sm shadow-xl shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <Play className="w-4 h-4 fill-white" /> Simulate Tehri Dam Breach (Bhagirathi River)
            </button>
          </div>
        </div>
      </div>

      {/* HADR Historical Context Catchment Cards */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
          <MapPin className="w-4 h-4 text-cyan-400" /> Historical HADR Flash Flood & Dam Outburst Catchments
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {historicalEvents.map((evt, idx) => (
            <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">{evt.year}</span>
              <h4 className="text-xs font-bold text-white">{evt.name}</h4>
              <p className="text-[11px] text-slate-400">{evt.type}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Target Monitored Dams */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
          <Layers className="w-4 h-4 text-cyan-400" /> Indian Dam & River Datasets
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dams.map((dam) => (
            <div key={dam.id} className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4 hover:border-cyan-500/40 transition-all">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-base font-bold text-white">{dam.name}</h4>
                  <p className="text-xs text-cyan-400 font-medium">{dam.river} • Lat {dam.lat}, Lon {dam.lon}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  {dam.dam_height_m}m Crest Height
                </span>
              </div>
              
              <div className="grid grid-cols-3 gap-3 text-xs bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold block">Reservoir Level</span>
                  <span className="font-bold text-white font-mono">{dam.reservoir_water_level_m} m</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold block">Normal Storage</span>
                  <span className="font-bold text-white font-mono">{( (dam.normal_storage_mcm || 0) / 1000 ).toFixed(2)} B m³</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold block">Spillway Capacity</span>
                  <span className="font-bold text-white font-mono">{dam.spillway_capacity_m3s.toLocaleString()} m³/s</span>
                </div>
              </div>

              <button
                onClick={() => onQuickSimulate(dam.id)}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-slate-900 hover:bg-cyan-500/15 text-xs font-bold text-cyan-300 border border-slate-800 hover:border-cyan-500/40 transition-all"
              >
                <Zap className="w-4 h-4 text-cyan-400" /> Run Hydrodynamic Scenario for {dam.name}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Model Engines Framework */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
          <Cpu className="w-4 h-4 text-cyan-400" /> Hydrodynamic Engines & Framework Architecture
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/30 space-y-2">
            <div className="font-bold text-white flex items-center justify-between">
              <span>Terrain Hydrodynamic Solver</span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
            <p className="text-slate-400">Iterative D8 elevation diffusion + weir breach hydrograph calculating real-time depth arrays.</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-amber-500/30 space-y-2">
            <div className="font-bold text-white flex items-center justify-between">
              <span>Smooth Particle Hydrodynamics (SPH)</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-slate-400">Lagrangian fluid particle velocity visualizer tracking downhill water front dynamics.</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-blue-500/30 space-y-2">
            <div className="font-bold text-white flex items-center justify-between">
              <span>Delft3D 2D Hydrodynamic Suite</span>
              <Layers className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-slate-400">2D/3D shallow-water netCDF grid solver adapter for comparative benchmark validation.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
