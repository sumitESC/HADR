import React from 'react';
import { Satellite, ShieldCheck, Layers, Radio, Globe } from 'lucide-react';

interface SatelliteTabProps {
  sentinel1Data: any;
}

export const SatelliteTab: React.FC<SatelliteTabProps> = ({ sentinel1Data: _sentinel1Data }) => {
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2 font-heading">
              <Satellite className="w-5 h-5 text-cyan-400" /> Google Earth Engine (GEE) Near Real-Time Flood Analysis
            </h2>
            <p className="text-xs text-slate-400">
              Open-source Copernicus Sentinel-1 Synthetic Aperture Radar (SAR) imagery pipeline for near real-time flood mapping & change detection.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5" /> GEE Open Source Pipeline
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* GEE Sensor Info Card */}
          <div className="space-y-4 bg-slate-900/90 p-5 rounded-2xl border border-slate-800">
            <h3 className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-wider">
              <Radio className="w-4 h-4 text-cyan-400" /> Copernicus Sentinel-1 SAR Parameters
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Constellation & Mode</span>
                <span className="font-bold text-white">Sentinel-1A / 1B IW GRDH</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Radar Polarization</span>
                <span className="font-mono font-bold text-cyan-400">VV + VH Dual Polarization</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">SAR Flood Masking Method</span>
                <span className="font-bold text-amber-400">Otsu Thresholding & Speckle Filter</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-400">Catchment Validation Layer</span>
                <span className="font-bold text-emerald-400">Bhagirathi River Valley (Tehri)</span>
              </div>
            </div>
          </div>

          {/* GEE Map Integration Banner */}
          <div className="space-y-4 bg-slate-900/90 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-wider">
                <Layers className="w-4 h-4 text-cyan-400" /> Interactive Map Layer Integration
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                The near real-time Sentinel-1 SAR water mask vector layer is automatically synchronized with open-source data and can be toggled on the <strong className="text-cyan-400">Hydrodynamic Map View</strong> for direct overlay comparison against simulated dam breach extents.
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0" />
              GEE SAR overlay active in GIS layer controls.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
