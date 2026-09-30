import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Dam, SphData } from '../types';
import { SphCanvas } from './SphCanvas';
import { RadarOverlay } from './RadarOverlay';
import { Plus, Minus, Target, Layers, Play, Pause, Maximize2, ChevronUp, ChevronDown, Check, Building2, Waves, BarChart3, Mountain, Droplet, MapPin, Home, Compass, Satellite, Scan } from 'lucide-react';

interface FullMapCanvasProps {
  dams: Dam[];
  currentFeatures: any;
  showSph: boolean;
  sphData: SphData | null;
  showSentinel: boolean;
  sentinel1Data: any;
  currentTimestep: number;
  timesteps: number[];
  currentStepIdx: number;
  setCurrentStepIdx: (idx: number) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  selectedDamId?: string;
  showRadar?: boolean;
  onFocusToggle?: () => void;
  isFocusMode?: boolean;
}

const damIcon = L.divIcon({
  className: 'custom-dam-marker',
  html: `<div style="background: #ef4444; width: 18px; height: 18px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 15px #ef4444;"></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9]
});

const createTownLabelIcon = (label: string) =>
  L.divIcon({
    className: 'custom-town-label-marker',
    html: `
      <div style="display: flex; align-items: center; gap: 6px; white-space: nowrap; font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 800; color: #ffffff; text-shadow: 0 1px 4px rgba(0,0,0,0.95), 0 0 10px rgba(0,0,0,0.95);">
        <div style="width: 8px; height: 8px; border-radius: 50%; background: #ffffff; border: 2px solid #0284c7; box-shadow: 0 0 10px #38bdf8; flex-shrink: 0;"></div>
        <span>${label}</span>
      </div>
    `,
    iconSize: [100, 16],
    iconAnchor: [4, 8]
  });

/** Recenter map when selected dam changes */
const MapCenterUpdater: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1.5 });
  }, [center[0], center[1], zoom]);
  return null;
};

/** Map control buttons that interact with the Leaflet map instance */
const MapControls: React.FC<{ center: [number, number]; onFocusToggle?: () => void; isFocusMode?: boolean }> = ({ center, onFocusToggle, isFocusMode }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    
    // The most robust fix for Leaflet black tiles: 
    // Watch the actual DOM element for ANY size changes (flex reflows, CSS animations, window resizes)
    const container = map.getContainer();
    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });
    
    observer.observe(container);
    
    // Also trigger on state change just in case
    setTimeout(() => map.invalidateSize(), 100);
    setTimeout(() => map.invalidateSize(), 400);

    return () => observer.disconnect();
  }, [map, isFocusMode]);

  const handleZoomIn = () => map.zoomIn();
  const handleZoomOut = () => map.zoomOut();
  const handleRecenter = () => map.flyTo(center, 12, { duration: 1.2 });
  const handleFullscreen = () => {
    const el = map.getContainer().closest('.relative') as HTMLElement;
    if (el) {
      if (!document.fullscreenElement) {
        el.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }
  };

  return (
    <>
      {/* Zoom Controls */}
      <div className="absolute top-4 left-4 z-[500] flex flex-col gap-1">
        <button onClick={handleZoomIn} className="w-8 h-8 rounded-lg bg-slate-900/90 backdrop-blur-md border border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800 flex items-center justify-center shadow-lg">
          <Plus className="w-4 h-4" />
        </button>
        <button onClick={handleZoomOut} className="w-8 h-8 rounded-lg bg-slate-900/90 backdrop-blur-md border border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800 flex items-center justify-center shadow-lg">
          <Minus className="w-4 h-4" />
        </button>
        <button onClick={handleRecenter} className="w-8 h-8 rounded-lg bg-slate-900/90 backdrop-blur-md border border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800 flex items-center justify-center shadow-lg mt-1" title="Recenter to dam">
          <Target className="w-4 h-4 text-blue-400" />
        </button>
        {onFocusToggle && !isFocusMode && (
          <button
            onClick={onFocusToggle}
            className="w-8 h-8 rounded-lg bg-blue-600/90 backdrop-blur-md border border-blue-500 text-white hover:bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-500/30 mt-1 transition-all hover:scale-110"
            title="Focus Mode — expand map, hide panels"
          >
            <Scan className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Fullscreen button in bottom bar placeholder */}
      <button onClick={handleFullscreen} className="hidden" id="map-fullscreen-btn" />
    </>
  );
};

export const FullMapCanvas: React.FC<FullMapCanvasProps> = ({
  dams,
  currentFeatures,
  showSph,
  sphData,
  showSentinel,
  sentinel1Data,
  currentTimestep,
  timesteps,
  currentStepIdx,
  setCurrentStepIdx,
  isPlaying,
  setIsPlaying,
  selectedDamId,
  showRadar = true,
  onFocusToggle,
  isFocusMode = false
}) => {
  const [mapType, setMapType] = useState<'map' | 'satellite' | 'terrain'>('satellite');
  const [layersOpen, setLayersOpen] = useState<boolean>(true);
  const [radarEnabled, setRadarEnabled] = useState<boolean>(true);
  const [layersState, setLayersState] = useState({
    floodExtent: true,
    floodDepth: true,
    demElevation: false,
    riverNetwork: true,
    damLocation: true,
    settlements: true,
    roads: true,
    satelliteImagery: true,
    sphParticles: true,
    radarOverlay: true
  });

  // Find selected dam for map centering
  const selectedDam = dams.find(d => d.id === selectedDamId) || dams[0];
  const mapCenter: [number, number] = selectedDam
    ? [selectedDam.lat, selectedDam.lon]
    : [30.375, 78.490];

  // Downstream towns from dam data
  const downstreamTowns: { name: string; lat: number; lon: number }[] = [];
  if (selectedDam && 'downstream_towns' in selectedDam) {
    const towns = (selectedDam as any).downstream_towns || [];
    // Generate approximate positions for downstream towns
    towns.slice(0, 4).forEach((name: string, i: number) => {
      const t = (i + 1) / (towns.length + 1);
      downstreamTowns.push({
        name,
        lat: selectedDam.lat - t * 0.08,
        lon: selectedDam.lon + t * 0.06
      });
    });
  }

  // Radar progress based on timestep
  const radarProgress = timesteps.length > 1
    ? currentStepIdx / (timesteps.length - 1)
    : 0.5;

  const tileUrls = {
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    map: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{y}/{x}{r}.png',
    terrain: 'https://{s}.tile.opentopomap.org/{z}/{y}/{x}.png'
  };

  const getFeatureColor = (feature: any) => {
    const props = feature?.properties || {};
    const depthBand = (props.depth_band || '').trim();
    const minD = props.min_depth ?? -1;

    // Priority 1: Match depth_band string from backend tiers
    if (depthBand === '> 5.0' || depthBand === '> 4.0')        return '#dc2626'; // Deep red — critical
    if (depthBand === '3.0 - 5.0' || depthBand === '3.0 - 4.0') return '#f97316'; // Orange — severe
    if (depthBand === '2.0 - 3.0')                              return '#eab308'; // Yellow — high
    if (depthBand === '1.0 - 2.0')                              return '#22c55e'; // Green — moderate
    if (depthBand === '0.5 - 1.0')                              return '#06b6d4'; // Cyan — low
    if (depthBand === '0.1 - 0.5')                              return '#3b82f6'; // Blue — minimal

    // Priority 2: Fallback to min_depth numeric value
    if (minD >= 5.0) return '#dc2626';
    if (minD >= 3.0) return '#f97316';
    if (minD >= 2.0) return '#eab308';
    if (minD >= 1.0) return '#22c55e';
    if (minD >= 0.5) return '#06b6d4';
    return '#3b82f6';
  };

  const toggleLayer = (key: keyof typeof layersState) => {
    setLayersState((prev) => ({ ...prev, [key]: !prev[key] }));
    if (key === 'radarOverlay') setRadarEnabled(!radarEnabled);
  };

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
      {/* Radar Animation Overlay */}
      {radarEnabled && showRadar && layersState.radarOverlay && (
        <RadarOverlay
          damLat={selectedDam?.lat || 30.3774}
          damLon={selectedDam?.lon || 78.4803}
          progress={radarProgress}
          isPlaying={isPlaying}
          currentTimestep={currentTimestep}
          opacity={0.45}
        />
      )}

      {/* Map Header Pin Callout - Dynamic Dam */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[500] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl px-4 py-2 flex items-center gap-3 shadow-xl">
        <div className="w-8 h-8 rounded-lg bg-blue-600/30 border border-blue-500/50 flex items-center justify-center text-blue-400">
          <Building2 className="w-4 h-4" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-white font-heading">{selectedDam?.name || 'Select Dam'}</h4>
          <p className="text-[10px] text-slate-300 font-mono">
            {selectedDam?.river || ''}{selectedDam ? `, ${(selectedDam as any).state || 'India'}` : ''} &bull; {selectedDam?.lat.toFixed(4)}&deg; N, {selectedDam?.lon.toFixed(4)}&deg; E
          </p>
        </div>
      </div>

      {/* Zoom/Recenter controls are rendered inside MapContainer via MapControls */}

      {/* Top Right Map Style Switcher */}
      <div className="absolute top-4 right-4 z-[500] flex items-center bg-slate-900/90 backdrop-blur-md border border-slate-700 p-1 rounded-lg shadow-xl text-xs font-semibold">
        <button
          onClick={() => setMapType('map')}
          className={`px-3 py-1 rounded-md transition-all ${mapType === 'map' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
        >
          Map
        </button>
        <button
          onClick={() => setMapType('satellite')}
          className={`px-3 py-1 rounded-md transition-all ${mapType === 'satellite' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
        >
          Satellite
        </button>
        <button
          onClick={() => setMapType('terrain')}
          className={`px-3 py-1 rounded-md transition-all ${mapType === 'terrain' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
        >
          Terrain
        </button>
      </div>

      {/* Top Right Map Layers Checklist Popover */}
      <div className="absolute top-16 right-4 z-[500] w-56 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl overflow-hidden text-xs">
        <button
          onClick={() => setLayersOpen(!layersOpen)}
          className="w-full px-3 py-2 bg-slate-800/80 flex items-center justify-between text-slate-200 font-bold hover:bg-slate-800"
        >
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-blue-400" /> Map Layers
          </span>
          {layersOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {layersOpen && (
          <div className="p-2 space-y-1 bg-slate-900/90 max-h-64 overflow-y-auto">
            {[
              { key: 'floodExtent', label: 'Flood Extent', icon: Waves, color: 'text-blue-400' },
              { key: 'floodDepth', label: 'Flood Depth', icon: BarChart3, color: 'text-cyan-400' },
              { key: 'radarOverlay', label: 'Radar Animation', icon: Target, color: 'text-emerald-400' },
              { key: 'sphParticles', label: 'SPH Flow Particles', icon: Target, color: 'text-amber-400' },
              { key: 'demElevation', label: 'DEM (Elevation)', icon: Mountain, color: 'text-slate-400' },
              { key: 'riverNetwork', label: 'River Network', icon: Droplet, color: 'text-blue-400' },
              { key: 'damLocation', label: 'Dam Location', icon: MapPin, color: 'text-red-400' },
              { key: 'settlements', label: 'Settlements', icon: Home, color: 'text-cyan-400' },
              { key: 'roads', label: 'Roads', icon: Compass, color: 'text-amber-400' },
              { key: 'satelliteImagery', label: 'Satellite Imagery', icon: Satellite, color: 'text-emerald-400' }
            ].map((item) => {
              const active = layersState[item.key as keyof typeof layersState];
              const IconComp = item.icon;
              return (
                <div
                  key={item.key}
                  onClick={() => toggleLayer(item.key as keyof typeof layersState)}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-800/60 cursor-pointer select-none"
                >
                  <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${active ? 'bg-blue-600 border-blue-500 text-white' : 'border-slate-600 bg-slate-900'}`}>
                    {active && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                  <span className="text-[11px] text-slate-300 flex items-center gap-1.5">
                    <IconComp className={`w-3.5 h-3.5 ${item.color}`} /> {item.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Left Water Depth (m) Color Legend Card */}
      <div className="absolute bottom-16 left-4 z-[500] bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 shadow-2xl space-y-1.5 min-w-[140px]">
        <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Water Depth (m)</h5>
        <div className="space-y-1 text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#dc2626] border border-red-400 inline-block"></span>
            <span className="text-slate-200 font-bold">&gt; 5.0 <span className="text-red-400 text-[9px] font-sans">Critical</span></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#f97316] border border-orange-400 inline-block"></span>
            <span className="text-slate-300">3.0 - 5.0 <span className="text-orange-400 text-[9px] font-sans">Severe</span></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#eab308] border border-yellow-400 inline-block"></span>
            <span className="text-slate-300">2.0 - 3.0 <span className="text-yellow-400 text-[9px] font-sans">High</span></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#22c55e] border border-green-400 inline-block"></span>
            <span className="text-slate-300">1.0 - 2.0 <span className="text-green-400 text-[9px] font-sans">Moderate</span></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#06b6d4] border border-cyan-400 inline-block"></span>
            <span className="text-slate-300">0.5 - 1.0 <span className="text-cyan-400 text-[9px] font-sans">Low</span></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#3b82f6] border border-blue-400 inline-block"></span>
            <span className="text-slate-300">0.1 - 0.5 <span className="text-blue-400 text-[9px] font-sans">Minimal</span></span>
          </div>
        </div>
      </div>

      {/* Bottom Timeline Control Scrubber Overlay */}
      <div className="absolute bottom-3 left-4 right-4 z-[500] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl px-4 py-2.5 flex items-center gap-4 shadow-2xl">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-9 h-9 rounded-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shrink-0 shadow-lg shadow-blue-500/30 transition-all"
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-white" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
        </button>

        {/* Scrubber Ticks */}
        <div className="flex-1 relative flex items-center">
          <div className="w-full bg-slate-800 h-1.5 rounded-full relative">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${(currentStepIdx / Math.max(1, timesteps.length - 1)) * 100}%` }}
            ></div>
          </div>
          <div className="absolute inset-0 flex justify-between items-center px-1">
            {timesteps.map((t, idx) => (
              <button
                key={t}
                onClick={() => setCurrentStepIdx(idx)}
                className={`flex flex-col items-center group focus:outline-none`}
              >
                <span
                  className={`w-3 h-3 rounded-full transition-all ${idx === currentStepIdx ? 'bg-blue-400 ring-4 ring-blue-500/30 scale-125' : idx <= currentStepIdx ? 'bg-blue-500' : 'bg-slate-700'}`}
                ></span>
                <span
                  className={`text-[10px] mt-1 font-mono font-medium ${idx === currentStepIdx ? 'text-blue-400 font-bold' : 'text-slate-400'}`}
                >
                  T+{t}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-blue-600/20 border border-blue-500/40 rounded-lg px-2.5 py-1 text-xs font-mono font-bold text-blue-400 shrink-0">
          T+{currentTimestep} min
        </div>

        <button
          onClick={() => {
            const el = document.querySelector('.relative.w-full.h-full.rounded-xl') as HTMLElement;
            if (el) {
              if (!document.fullscreenElement) {
                el.requestFullscreen().catch(() => {});
              } else {
                document.exitFullscreen().catch(() => {});
              }
            }
          }}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 shrink-0"
          title="Toggle fullscreen"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Main Map Canvas */}
      <MapContainer
        center={mapCenter}
        zoom={12}
        style={{ width: '100%', height: '100%' }}
        zoomControl={false}
      >
        <MapCenterUpdater center={mapCenter} zoom={12} />
        <MapControls center={mapCenter} onFocusToggle={onFocusToggle} isFocusMode={isFocusMode} />
        <TileLayer
          url={tileUrls[mapType]}
          attribution="&copy; Esri, Maxar, Earthstar Geographics, and GIS User Community"
          maxZoom={18}
        />

        {/* Dam Markers */}
        {layersState.damLocation &&
          dams.map((d) => (
            <Marker key={d.id} position={[d.lat, d.lon]} icon={damIcon}>
              <Popup>
                <div className="p-2 space-y-1">
                  <h4 className="font-bold text-sm text-blue-400 font-heading">{d.name}</h4>
                  <p className="text-xs text-slate-300 font-mono">Crest Height: {d.dam_height_m}m</p>
                  <p className="text-xs text-slate-400">River: {d.river}</p>
                  {(d as any).state && <p className="text-xs text-slate-400">State: {(d as any).state}</p>}
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Dynamic Town Labels from downstream_towns */}
        {layersState.settlements && downstreamTowns.map((town, i) => (
          <Marker key={`town-${i}`} position={[town.lat, town.lon]} icon={createTownLabelIcon(town.name)}>
            <Popup>
              <div className="text-xs font-bold font-heading text-cyan-400">{town.name}</div>
            </Popup>
          </Marker>
        ))}

        {/* Hydrodynamic Inundation Vector Layer with Multi-colored Depth Heatmap */}
        {layersState.floodExtent && currentFeatures && (
          <GeoJSON
            key={`inundation-${currentTimestep}-${selectedDamId}`}
            data={currentFeatures}
            style={(feat) => {
              const color = getFeatureColor(feat);
              return {
                color: color,
                weight: 1.5,
                fillColor: color,
                fillOpacity: layersState.floodDepth ? 0.70 : 0.40
              };
            }}
          />
        )}

        {/* Sentinel-1 Overlay */}
        {showSentinel && sentinel1Data && (
          <GeoJSON
            key="sentinel1-overlay"
            data={sentinel1Data}
            style={() => ({
              color: '#10b981',
              weight: 2,
              dashArray: '4, 4',
              fillColor: '#10b981',
              fillOpacity: 0.35
            })}
          />
        )}
      </MapContainer>

      {/* SPH Fluid Particle Overlay */}
      {(showSph || layersState.sphParticles) && <SphCanvas sphData={sphData} currentTimestep={currentTimestep} />}
    </div>
  );
};

export default FullMapCanvas;
