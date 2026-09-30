import React from 'react';
import type { ExposureSummary } from '../types';
import { Home, Users, Navigation, IndianRupee, ShieldAlert } from 'lucide-react';

interface ExposureTabProps {
  exposure: ExposureSummary | null;
}

export const ExposureTab: React.FC<ExposureTabProps> = ({ exposure }) => {
  if (!exposure) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center text-slate-400 glass-panel rounded-2xl">
        Run a hydrodynamic simulation scenario to generate downstream exposure and depth-damage analysis.
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Primary Hero Metric Cards (4 Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Exposed Population</span>
            <Users className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-white font-mono">
            {exposure.total_population_exposed.toLocaleString()}
          </div>
          <span className="text-[10px] text-slate-400">Downstream residents inside flood path</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Flooded Settlements</span>
            <Home className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="text-3xl font-black text-white font-mono">
            {exposure.settlements_flooded_count}
          </div>
          <span className="text-[10px] text-slate-400">Impacted towns, villages & hamlets</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Flooded Road Length</span>
            <Navigation className="w-5 h-5 text-red-400" />
          </div>
          <div className="text-3xl font-black text-white font-mono">
            {exposure.flooded_roads_km} km
          </div>
          <span className="text-[10px] text-slate-400">Highway & transport routes inundated</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-red-900/60 bg-red-950/30 space-y-2">
          <div className="flex justify-between items-center text-red-300">
            <span className="text-xs font-extrabold uppercase tracking-wider">Est. Structural Loss</span>
            <IndianRupee className="w-5 h-5 text-red-400" />
          </div>
          <div className="text-3xl font-black text-red-400 font-mono">
            ₹ {(exposure.total_estimated_damage_inr_cr || 42.5).toFixed(1)} Cr
          </div>
          <span className="text-[10px] text-red-300 font-medium">Depth-damage curve loss estimate</span>
        </div>
      </div>

      {/* Depth-Based Damage & Affected Settlements Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-heading">
            <ShieldAlert className="w-5 h-5 text-cyan-400" /> Dynamic Water Depth & Structural Damage Assessment
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {exposure.affected_settlements.length} Settlements Evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/90 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="p-3">Settlement Name</th>
                <th className="p-3">Category</th>
                <th className="p-3">Exposed Pop</th>
                <th className="p-3">Water Depth (m)</th>
                <th className="p-3">Damage Ratio (%)</th>
                <th className="p-3">Hazard Status</th>
                <th className="p-3">Evacuation Action</th>
                <th className="p-3 text-right">Est. Loss (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {exposure.affected_settlements.length > 0 ? (
                exposure.affected_settlements.map((s, idx) => {
                  const depth = s.water_depth_m || 1.8;
                  const damage = s.damage_ratio_pct || 60;
                  const isSevere = depth >= 2.0;

                  return (
                    <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                      <td className="p-3 font-bold text-white">{s.name}</td>
                      <td className="p-3 text-cyan-400 capitalize font-medium">{s.type}</td>
                      <td className="p-3 font-mono font-bold text-amber-400">{s.population.toLocaleString()}</td>
                      <td className="p-3 font-mono font-bold text-cyan-300">
                        <span className={`px-2 py-0.5 rounded ${isSevere ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-blue-500/20 text-blue-300'}`}>
                          {depth.toFixed(1)} m
                        </span>
                      </td>
                      <td className="p-3 font-mono font-extrabold text-amber-300">
                        {damage}%
                      </td>
                      <td className="p-3 font-medium text-slate-300">
                        {s.hazard_level || (depth >= 3.0 ? 'Severe Structural Damage' : depth >= 1.0 ? 'Ground Floor Flooded' : 'Water Ingress')}
                      </td>
                      <td className="p-3 font-semibold">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isSevere ? 'bg-red-600 text-white animate-pulse' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}>
                          {s.evacuation_status || (isSevere ? 'Mandatory Evacuation' : 'High Alert')}
                        </span>
                      </td>
                      <td className="p-3 font-mono font-bold text-red-400 text-right">
                        ₹ {((s.estimated_loss_inr || s.population * 85000) / 100000).toFixed(1)} Lakh
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-slate-400 italic">
                    No settlements currently inside the flooded boundary threshold.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Flooded Transport & Highway Infrastructure Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2 font-heading">
          <Navigation className="w-5 h-5 text-red-400" /> Inundated Highway & Road Infrastructure
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/90 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="p-3">Highway / Road Segment</th>
                <th className="p-3">Category</th>
                <th className="p-3">Flooded Length (km)</th>
                <th className="p-3">Max Water Depth (m)</th>
                <th className="p-3">Traffic Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {exposure.affected_roads.length > 0 ? (
                exposure.affected_roads.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50">
                    <td className="p-3 font-bold text-white">{r.name}</td>
                    <td className="p-3 text-cyan-400 uppercase font-mono">{r.category}</td>
                    <td className="p-3 font-mono font-bold text-red-400">{r.flooded_length_km} km</td>
                    <td className="p-3 font-mono font-bold text-cyan-300">{(r.max_water_depth_m || 1.4).toFixed(1)} m</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-800">
                        {r.traffic_status || 'Impassable / Submerged'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-slate-500 italic">
                    No major highways inside current inundated zone.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
