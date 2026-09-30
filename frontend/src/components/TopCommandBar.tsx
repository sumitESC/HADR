import React from 'react';
import { Search, Activity, Cpu, Download, Globe } from 'lucide-react';

interface TopCommandBarProps {
  showSph: boolean;
  setShowSph: (val: boolean) => void;
  showSentinel: boolean;
  setShowSentinel: (val: boolean) => void;
  activeTabModal: string | null;
  setActiveTabModal: (tab: string | null) => void;
  onExport: (fmt: string) => void;
}

export const TopCommandBar: React.FC<TopCommandBarProps> = ({
  showSph,
  setShowSph,
  showSentinel,
  setShowSentinel,
  activeTabModal,
  setActiveTabModal,
  onExport
}) => {
  return (
    <div className="absolute top-4 right-4 z-40 flex items-center gap-3 pointer-events-auto">
      {/* Search Input */}
      <div className="relative">
        <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search Dam, Catchment or Town..."
          className="bg-slate-950/80 border border-slate-800 rounded-xl pl-8 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-64 shadow-xl backdrop-blur-md"
        />
      </div>

      {/* Layer Toggles */}
      <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 p-1 rounded-xl shadow-xl backdrop-blur-md">
        <button
          onClick={() => setShowSph(!showSph)}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
            showSph
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-amber-400" /> SPH Particles
        </button>

        <button
          onClick={() => setShowSentinel(!showSentinel)}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
            showSentinel
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Globe className="w-3.5 h-3.5 text-cyan-400" /> GEE Sentinel-1
        </button>
      </div>

      {/* Modal View Triggers */}
      <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 p-1 rounded-xl shadow-xl backdrop-blur-md">
        <button
          onClick={() => setActiveTabModal(activeTabModal === 'models' ? null : 'models')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
            activeTabModal === 'models'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Cpu className="w-3.5 h-3.5 text-cyan-400" /> SPH & Delft3D
        </button>

        <button
          onClick={() => onExport('shp')}
          className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 transition-all shadow-sm"
        >
          <Download className="w-3.5 h-3.5" /> Export .shp
        </button>

        <button
          onClick={() => onExport('kml')}
          className="px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/40 flex items-center gap-1.5 transition-all shadow-sm"
        >
          <Download className="w-3.5 h-3.5" /> Export .kml
        </button>
      </div>
    </div>
  );
};
