import type { ComparisonRow } from '../types';
import { Cpu, Info } from 'lucide-react';

interface ModelComparisonTabProps {
  comparisonData: ComparisonRow[];
}

export const ModelComparisonTab: React.FC<ModelComparisonTabProps> = ({ comparisonData }) => {
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" /> Multi-Model Hydrodynamic Comparison
          </h2>
          <p className="text-xs text-gray-400">
            Side-by-side performance and spatial inundation comparative metrics between active 2-day terrain engine and scientific model adapters.
          </p>
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-900/90 text-gray-400 uppercase font-bold border-b border-gray-800">
              <tr>
                <th className="p-3.5">Model Engine</th>
                <th className="p-3.5">Designation Status</th>
                <th className="p-3.5">Inundated Area (km²)</th>
                <th className="p-3.5">Max Depth (m)</th>
                <th className="p-3.5">Front Speed (T+30 km)</th>
                <th className="p-3.5">Runtime (sec)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {comparisonData.map((row, idx) => {
                const isActive = row.engine.includes('Terrain');
                return (
                  <tr key={idx} className={isActive ? 'bg-cyan-500/5' : 'hover:bg-gray-900/40'}>
                    <td className="p-3.5 font-bold text-white flex items-center gap-2">
                      {row.engine}
                      {isActive && (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                          Active Demo
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 text-gray-400">{row.status}</td>
                    <td className="p-3.5 font-mono font-bold text-cyan-400">{row.inundated_area_km2} km²</td>
                    <td className="p-3.5 font-mono font-bold text-amber-400">{row.max_depth_m} m</td>
                    <td className="p-3.5 font-mono text-gray-200">{row.front_arrival_t30_km} km</td>
                    <td className="p-3.5 font-mono text-emerald-400">{row.computation_time_sec} s</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Note Disclaimer */}
        <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 text-xs text-gray-400 flex items-start gap-3">
          <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-white">Hydrodynamic Solver Architecture Note:</span> The **Terrain-Based Flood Propagation Engine** provides rapid high-fidelity elevation slope diffusion in real-time (~0.45s runtime). The modular backend architecture supports plug-and-play adapter integration for SPH particle solvers and Delft3D 2D/3D hydrodynamic suites across any river basin.
          </div>
        </div>
      </div>
    </div>
  );
};
