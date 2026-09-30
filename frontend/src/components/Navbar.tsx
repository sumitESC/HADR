import React from 'react';
import { Waves, BarChart2, ShieldAlert, Cpu, Download, Satellite, Info, Map } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeSimId: string | null;
  status: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, activeSimId, status }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Info },
    { id: 'simulation', label: 'Simulation Setup', icon: ShieldAlert },
    { id: 'map', label: 'Hydrodynamic Map View', icon: Map },
    { id: 'comparison', label: 'SPH & Delft3D Models', icon: Cpu },
    { id: 'exposure', label: 'HADR Damage & Exposure', icon: BarChart2 },
    { id: 'satellite', label: 'GEE Satellite Analysis', icon: Satellite },
    { id: 'export', label: 'GIS Export (.shp/.kml)', icon: Download },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 via-teal-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
          <Waves className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-2 font-heading">
            AquaBreak <span className="text-cyan-400 font-extrabold">HADR</span>
          </h1>
          <p className="text-[11px] text-slate-400 font-medium">Hydrodynamic Dam Break & Flood Inundation Simulator</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className="w-4 h-4 text-cyan-400" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Active Simulation Status Badge */}
      <div className="flex items-center gap-3 text-xs">
        {activeSimId ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-400 font-medium">Scenario:</span>
            <span className="font-mono text-cyan-400 font-bold">{activeSimId}</span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
              status === 'completed' 
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/40' 
                : 'bg-amber-500/15 text-amber-400 border border-amber-500/40'
            }`}>
              {status}
            </span>
          </div>
        ) : (
          <span className="text-slate-500 text-xs italic">Idle</span>
        )}
      </div>
    </header>
  );
};
