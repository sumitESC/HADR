import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Dam, SimulationResult, SphData } from '../types';
import { SphCanvas } from './SphCanvas';
import { Play, Pause, RotateCcw, Activity, Layers } from 'lucide-react';

interface FloodMapTabProps {
  dams: Dam[];
  simMeta: SimulationResult | null;
  geoJsonData: any;
  sphData: SphData | null;
  sentinel1Data: any;
}

// Custom map markers
const damIcon = L.divIcon({
  className: 'custom-dam-marker',
  html: `<div style="background: #ef4444; width: 14px; height: 14px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px #ef4444;"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

const townIcon = L.divIcon({
  className: 'custom-town-marker',
  html: `<div style="background: #38bdf8; width: 10px; height: 10px; border-radius: 2px; border: 2px solid white; box-shadow: 0 0 6px #38bdf8;"></div>`,
  iconSize: [10, 10],
  iconAnchor: [5, 5]
});

export const FloodMapTab: React.FC<FloodMapTabProps> = ({
  dams,
  simMeta,
  geoJsonData,
  sphData,
  sentinel1Data
}) => {
  const timesteps = simMeta?.timesteps_min || [0, 30, 60, 120, 180, 360];
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [showSph, setShowSph] = useState<boolean>(false);
  const [showSentinel, setShowSentinel] = useState<boolean>(false);

  const currentTimestep = timesteps[currentStepIdx] || 0;

  // Animation player loop
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentStepIdx((prev) => (prev + 1) % timesteps.length);
      }, 1200);
    }
    return () => clearInterval(interval);
  }, [isPlaying, timesteps]);

  // Filter GeoJSON features for current timestep
  const currentFeatures: any = geoJsonData
    ? {
        type: 'FeatureCollection',
        features: geoJsonData.features.filter(
          (f: any) => f.properties.timestep_min === currentTimestep
        )
      }
    : null;

  // Extract statistics for current timestep
  const currentArea = currentFeatures?.features[0]?.properties?.inundated_area_km2 || (simMeta ? (simMeta.inundated_area_km2 * (currentTimestep / 360)).toFixed(2) : 0);
  const maxDepth = currentFeatures?.features[0]?.properties?.max_depth_m || simMeta?.max_depth_m || 0;

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] relative bg-gray-950 overflow-hidden">
      {/* Top Floating Map Controls */}
      <div className="absolute top-4 left-4 right-4 z-30 flex flex-wrap items-center justify-between gap-4 pointer-events-none">
        {/* Dynamic Stats Card */}
        <div className="glass-panel p-3.5 px-5 rounded-2xl flex items-center gap-6 pointer-events-auto border border-gray-800 shadow-2xl">
          <div>
            <span className="text-[10px] text-gray-400 font-semibold block uppercase">Current Timestep</span>
            <span className="text-lg font-extrabold text-cyan-400 font-mono">T + {currentTimestep} min</span>
          </div>
          <div className="h-8 w-px bg-gray-800" />
          <div>
            <span className="text-[10px] text-gray-400 font-semibold block uppercase">Flooded Extent</span>
            <span className="text-lg font-extrabold text-white font-mono">{currentArea} km²</span>
          </div>
          <div className="h-8 w-px bg-gray-800" />
          <div>
            <span className="text-[10px] text-gray-400 font-semibold block uppercase">Peak Depth</span>
            <span className="text-lg font-extrabold text-amber-400 font-mono">{maxDepth} m</span>
          </div>
        </div>

        {/* Overlay Toggles */}
        <div className="glass-panel p-2 rounded-2xl flex items-center gap-2 pointer-events-auto border border-gray-800">
          <button
            onClick={() => setShowSph(!showSph)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              showSph
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                : 'bg-gray-900 text-gray-400 hover:bg-gray-800'
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> SPH Particles
          </button>

          <button
            onClick={() => setShowSentinel(!showSentinel)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              showSentinel
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'bg-gray-900 text-gray-400 hover:bg-gray-800'
            }`}
          >
            <Layers className="w-3.5 h-3.5" /> Sentinel-1 SAR Mask
          </button>
        </div>
      </div>

      {/* Main Map Container */}
      <div className="w-full h-full relative z-10">
        <MapContainer
          center={[30.34, 78.50]}
          zoom={12}
          style={{ width: '100%', height: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />

          {/* Dam Markers */}
          {dams.map((d) => (
            <Marker key={d.id} position={[d.lat, d.lon]} icon={damIcon}>
              <Popup>
                <div className="p-2 space-y-1">
                  <h4 className="font-bold text-sm text-cyan-400">{d.name}</h4>
                  <p className="text-xs text-gray-300">Height: {d.dam_height_m}m</p>
                  <p className="text-xs text-gray-400">River: {d.river}</p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Town Markers */}
          <Marker position={[30.375, 78.472]} icon={townIcon}>
            <Popup><div className="text-xs font-bold">New Tehri Town (Pop: 25,400)</div></Popup>
          </Marker>
          <Marker position={[30.291, 78.525]} icon={townIcon}>
            <Popup><div className="text-xs font-bold">Koteshwar Village (Pop: 4,200)</div></Popup>
          </Marker>

          {/* Inundation Polygons */}
          {currentFeatures && (
            <GeoJSON
              key={`inundation-${currentTimestep}-${currentStepIdx}`}
              data={currentFeatures}
              style={() => ({
                color: '#ef4444',
                weight: 2,
                fillColor: '#ef4444',
                fillOpacity: 0.55
              })}
            />
          )}

          {/* Sentinel-1 SAR Comparison Overlay */}
          {showSentinel && sentinel1Data && (
            <GeoJSON
              key="sentinel1-overlay"
              data={sentinel1Data}
              style={() => ({
                color: '#38bdf8',
                weight: 2.5,
                dashArray: '4, 4',
                fillColor: '#38bdf8',
                fillOpacity: 0.35
              })}
            />
          )}
        </MapContainer>

        {/* SPH Particle Canvas Overlay */}
        {showSph && <SphCanvas sphData={sphData} currentTimestep={currentTimestep} />}
      </div>

      {/* Bottom Floating Time Slider Bar */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-11/12 max-w-3xl glass-panel p-4 rounded-2xl border border-gray-800 shadow-2xl flex items-center gap-4">
        {/* Play/Pause Button */}
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-10 h-10 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white flex items-center justify-center shadow-lg shadow-cyan-500/25 transition-all"
        >
          {isPlaying ? <Pause className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-white" />}
        </button>

        <button
          onClick={() => setCurrentStepIdx(0)}
          className="p-2 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-white"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Time Slider */}
        <div className="flex-1 space-y-1">
          <div className="flex justify-between text-[11px] font-semibold text-gray-400">
            <span>T+0 min (Release)</span>
            <span className="text-cyan-400 font-bold">T + {currentTimestep} Minutes</span>
            <span>T+360 min (Peak Spread)</span>
          </div>
          <input
            type="range"
            min={0}
            max={timesteps.length - 1}
            step={1}
            value={currentStepIdx}
            onChange={(e) => setCurrentStepIdx(Number(e.target.value))}
            className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
};
