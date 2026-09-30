import React from 'react';
import { api } from '../services/api';
import { Download, FileCode, Map, Archive } from 'lucide-react';

interface ExportTabProps {
  simId: string | null;
}

export const ExportTab: React.FC<ExportTabProps> = ({ simId }) => {
  if (!simId) {
    return (
      <div className="max-w-3xl mx-auto p-6 text-center text-slate-400">
        Run a hydrodynamic simulation scenario to enable spatial exports.
      </div>
    );
  }

  const handleDownload = (format: string) => {
    const url = api.getExportUrl(simId, format);
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-heading">
            <Download className="w-5 h-5 text-cyan-400" /> Export Hydrodynamic Simulation Deliverables
          </h2>
          <p className="text-xs text-slate-400">
            Export standard GIS inundation layers for scenario <span className="text-cyan-400 font-mono font-bold">{simId}</span>. Fully compatible with QGIS, ArcGIS, and Google Earth.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* ESRI Shapefile .shp */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 transition-all space-y-4 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                <Archive className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-white">ESRI Shapefile Package (.shp)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">ZIP bundle containing .shp, .shx, .dbf, and .prj projection files for desktop GIS analysis.</p>
            </div>
            <button
              onClick={() => handleDownload('shp')}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold transition-all shadow-lg shadow-emerald-500/10"
            >
              <Download className="w-3.5 h-3.5" /> Export .shp Package
            </button>
          </div>

          {/* KML .kml */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 transition-all space-y-4 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/15 text-cyan-400 flex items-center justify-center border border-cyan-500/30">
                <Map className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-white">Google Earth KML File (.kml)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">3D styled polygon layer formatted for Google Earth and field GPS devices.</p>
            </div>
            <button
              onClick={() => handleDownload('kml')}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-bold transition-all shadow-lg shadow-cyan-500/10"
            >
              <Download className="w-3.5 h-3.5" /> Export .kml File
            </button>
          </div>

          {/* GeoJSON */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 transition-all space-y-4 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-blue-500/15 text-blue-400 flex items-center justify-center border border-blue-500/30">
                <FileCode className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-white">Web GeoJSON Layer (.geojson)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">Standard web GIS JSON format containing time-series depth polygon feature collections.</p>
            </div>
            <button
              onClick={() => handleDownload('geojson')}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/40 text-xs font-bold transition-all shadow-lg shadow-blue-500/10"
            >
              <Download className="w-3.5 h-3.5" /> Export GeoJSON
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
