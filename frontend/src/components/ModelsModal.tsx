import React from 'react';
import type { ComparisonRow } from '../types';
import { Cpu, X } from 'lucide-react';

interface ModelsModalProps {
  comparisonData: ComparisonRow[];
  onClose: () => void;
}

export const ModelsModal: React.FC<ModelsModalProps> = ({ comparisonData, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl control-sidebar p-6 rounded-2xl border border-cyan-500/40 shadow-2xl space-y-6 relative animate-in fade-in zoom-in duration-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-lg bg-slate-900 border border-slate-800"
        >
          <X className="w-4 h-4" />
        </button>

        <div>
          <h2 className="text-xl font-black text-white flex items-center gap-2 font-heading">
            <Cpu className="w-5 h-5 text-cyan-400" /> SPH & Delft3D Hydrodynamic Model Comparison
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Comparative analysis between Terrain Hydrodynamic Solver, Smooth Particle Hydrodynamics (SPH), and Delft3D 2D benchmark.
          </p>
        </div>

        {/* Model Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/90 text-slate-400 font-bold border-b border-slate-800 uppercase">
              <tr>
                <th className="p-3">Model Engine</th>
                <th className="p-3">Framework Status</th>
                <th className="p-3">Inundated Area</th>
                <th className="p-3">Max Depth</th>
                <th className="p-3">Front Arrival (T+30)</th>
                <th className="p-3">Runtime</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {comparisonData.map((row, idx) => {
                const isActive = row.engine.includes('Terrain');
                return (
                  <tr key={idx} className={isActive ? 'bg-cyan-500/10' : 'hover:bg-slate-900/50'}>
                    <td className="p-3 font-bold text-white flex items-center gap-2">
                      {row.engine}
                      {isActive && (
                        <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                          Active
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-slate-400">{row.status}</td>
                    <td className="p-3 font-mono font-bold text-cyan-400">{row.inundated_area_km2} km²</td>
                    <td className="p-3 font-mono font-bold text-amber-400">{row.max_depth_m} m</td>
                    <td className="p-3 font-mono text-slate-300">{row.front_arrival_t30_km} km</td>
                    <td className="p-3 font-mono text-emerald-400">{row.computation_time_sec} s</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
