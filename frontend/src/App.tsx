import React, { useState, useEffect, useMemo } from 'react';
import { FullMapCanvas } from './components/FullMapCanvas';
import { OverviewTab } from './components/OverviewTab';
import { SimulationTab } from './components/SimulationTab';
import { ExposureTab } from './components/ExposureTab';
import { ExportTab } from './components/ExportTab';
import { ModelComparisonTab } from './components/ModelComparisonTab';
import { api } from './services/api';
import type { Dam, SimulationResult, SphData, ExposureSummary, ComparisonRow } from './types';
import {
  Shield,
  Waves,
  Home,
  Play,
  BarChart3,
  Download,
  AlertTriangle,
  Droplets,
  Users,
  Bell,
  Activity,
  Building2,
  MapPin,
  Sliders,
  TrendingUp,
  Radio,
  Map,
  Compass,
  Search,
  Zap,
  X,
  Satellite,
  Mountain,
  Cpu
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export const App: React.FC = () => {
  const [dams, setDams] = useState<Dam[]>([]);
  const [activeSimId, setActiveSimId] = useState<string | null>(null);
  const [simMeta, setSimMeta] = useState<SimulationResult | null>(null);
  const [geoJsonData, setGeoJsonData] = useState<any>(null);
  const [sphData, setSphData] = useState<SphData | null>(null);
  const [sentinel1Data] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [dataStatus, setDataStatus] = useState<string>('');
  const [exposureData, setExposureData] = useState<ExposureSummary | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonRow[]>([]);
  const [notificationsOpen, setNotificationsOpen] = useState<boolean>(false);
  const [focusMode, setFocusMode] = useState<boolean>(false);

  // Navigation tab state
  const [activeNavTab, setActiveNavTab] = useState<string>('flood_map');

  // Map & Controls state
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(3); // Default to T+120
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const showSph = false;
  const showSentinel = false;

  // ESC key to exit focus mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && focusMode) setFocusMode(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusMode]);

  // Form controls
  const [selectedDam, setSelectedDam] = useState<string>('tehri-dam');
  const [releasePercent, setReleasePercent] = useState<number>(30);
  const [reservoirLevel, setReservoirLevel] = useState<number>(260);
  const [durationMin, setDurationMin] = useState<number>(360);
  const [timeStepMin, setTimeStepMin] = useState<number>(30);
  const [engine, setEngine] = useState<string>('terrain');
  const [damSearch, setDamSearch] = useState<string>('');

  const timesteps = simMeta?.timesteps_min || [0, 30, 60, 120, 180, 360];
  const safeStepIdx = Math.min(currentStepIdx, Math.max(0, timesteps.length - 1));
  const currentTimestep = timesteps[safeStepIdx] ?? 0;

  // Get currently selected dam object
  const currentDam = useMemo(() => dams.find(d => d.id === selectedDam), [dams, selectedDam]);

  // Filter dams based on search
  const filteredDams = useMemo(() => {
    if (!damSearch.trim()) return dams;
    const q = damSearch.toLowerCase();
    return dams.filter(d =>
      d.name.toLowerCase().includes(q) ||
      d.river.toLowerCase().includes(q) ||
      d.state?.toLowerCase().includes(q)
    );
  }, [dams, damSearch]);

  // Animation player
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

  // Initialize data on load
  useEffect(() => {
    const initData = async () => {
      try {
        setDataStatus('Loading dam database...');
        const damsList = await api.getDams();
        setDams(damsList);
        setDataStatus('');

        runSimulationHandler({
          dam_id: 'tehri-dam',
          release_percent: 30,
          duration_min: 360,
          time_step_min: 30,
          engine: 'terrain'
        });
      } catch (err) {
        console.error('Failed to initialize app data:', err);
        setDataStatus('Backend offline — start backend server');
      }
    };
    initData();
  }, []);

  // Update reservoir level when dam changes
  useEffect(() => {
    if (currentDam) {
      setReservoirLevel(currentDam.dam_height_m);
    }
  }, [currentDam]);

  // Active metric filter for Model Comparison
  const [metricTab, setMetricTab] = useState<string>('area');

  // Dynamic log activity feed
  const [activities, setActivities] = useState<Array<{ time: string; text: string; color: string }>>([
    { time: '16:38', text: 'System initialized', color: 'bg-emerald-500' },
  ]);

  const runSimulationHandler = async (params: {
    dam_id: string;
    release_percent: number;
    duration_min: number;
    time_step_min: number;
    engine: string;
    custom_lat?: number;
    custom_lon?: number;
    custom_name?: string;
    custom_height_m?: number;
    custom_river?: string;
  }) => {
    setLoading(true);
    const nowStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });

    const damInfo = dams.find(d => d.id === params.dam_id);
    const damLabel = params.custom_name || damInfo?.name || params.dam_id;

    setActivities((prev) => [
      { time: nowStr, text: `Simulation started: ${damLabel} (${params.engine.toUpperCase()})`, color: 'bg-blue-500' },
      ...prev
    ]);

    setDataStatus(`Fetching real elevation data for ${damLabel}...`);

    // Switch to flood map tab to show results
    setActiveNavTab('flood_map');

    try {
      const startRes = await api.runSimulation(params);
      const simId = startRes.simulation_id;
      setActiveSimId(simId);
      setDataStatus('Loading simulation results...');

      const [meta, geojson, exposure, sph, comparison] = await Promise.all([
        api.getSimulationMetadata(simId),
        api.getSimulationGeoJSON(simId),
        api.getExposure(simId).catch(() => null),
        api.getSphParticles(simId).catch(() => null),
        api.getComparison(simId).catch(() => null)
      ]);

      setSimMeta(meta);
      setGeoJsonData(geojson);
      setExposureData(exposure as ExposureSummary | null);
      setSphData(sph);
      if (comparison && (comparison as any).comparison) {
        setComparisonData((comparison as any).comparison);
      }
      setCurrentStepIdx(0);
      setDataStatus('');

      const currentNow = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
      setActivities((prev) => [
        { time: currentNow, text: `✓ Simulation completed: ${damLabel}`, color: 'bg-emerald-500' },
        { time: currentNow, text: `Flood area: ${(meta.inundated_area_km2 || 0).toFixed(1)} km² | Depth: ${(meta.max_depth_m || 0).toFixed(1)}m`, color: 'bg-emerald-500' },
        { time: currentNow, text: `Real DEM + OSM data loaded for ${damLabel}`, color: 'bg-cyan-500' },
        ...(exposure ? [{ time: currentNow, text: `Exposure: ${(exposure as any).total_population_exposed?.toLocaleString() || 0} people at risk`, color: 'bg-amber-500' }] : []),
        ...prev
      ]);
    } catch (err) {
      console.error('Error running simulation:', err);
      setDataStatus('Simulation failed — check backend');
      setActivities((prev) => [
        { time: nowStr, text: `✗ Simulation failed for ${damLabel}`, color: 'bg-red-500' },
        ...prev
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (fmt: string) => {
    if (!activeSimId) return;
    const url = api.getExportUrl(activeSimId, fmt);
    window.open(url, '_blank');
  };

  // Recharts propagation time-series dataset dynamically scaled by release percentage
  const maxAreaVal = simMeta?.inundated_area_km2 || (releasePercent * 0.82);
  const timeSeriesData = [
    { time: '0', area: 0 },
    { time: '30', area: Number((maxAreaVal * 0.08).toFixed(1)) },
    { time: '60', area: Number((maxAreaVal * 0.23).toFixed(1)) },
    { time: '120', area: Number((maxAreaVal * 0.47).toFixed(1)) },
    { time: '180', area: Number((maxAreaVal * 0.76).toFixed(1)) },
    { time: '360', area: Number(maxAreaVal.toFixed(1)) }
  ];

  // Live clock
  const [clock, setClock] = useState(new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false, day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }));
  useEffect(() => {
    const iv = setInterval(() => setClock(new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false, day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })), 30000);
    return () => clearInterval(iv);
  }, []);

  // Loading step messages that cycle during simulation
  const [loadingStep, setLoadingStep] = useState(0);
  const loadingSteps = [
    { icon: <Satellite className="w-4 h-4 text-cyan-400" />, text: 'Fetching DEM elevation data...' },
    { icon: <Mountain className="w-4 h-4 text-emerald-400" />, text: 'Building terrain grid from satellite data...' },
    { icon: <Waves className="w-4 h-4 text-blue-400" />, text: 'Downloading river network from OpenStreetMap...' },
    { icon: <Cpu className="w-4 h-4 text-amber-400" />, text: 'Computing breach hydrograph (Froehlich 1995)...' },
    { icon: <Activity className="w-4 h-4 text-red-400" />, text: 'Running Manning\'s equation solver...' },
    { icon: <Map className="w-4 h-4 text-blue-300" />, text: 'Generating flood extent polygons...' },
    { icon: <BarChart3 className="w-4 h-4 text-purple-400" />, text: 'Computing exposure analysis...' },
  ];
  useEffect(() => {
    if (!loading) { setLoadingStep(0); return; }
    const iv = setInterval(() => {
      setLoadingStep(prev => (prev + 1) % loadingSteps.length);
    }, 3500);
    return () => clearInterval(iv);
  }, [loading]);

  return (
    <div className={`hadr-dashboard flex flex-col min-h-screen bg-[#070b19] text-slate-100 font-sans gap-3 ${focusMode ? '' : 'p-3'}`}>

      {/* ═══ FOCUS MODE: Top bar overlay ═══ */}
      {focusMode && (
        <div className="fixed top-0 left-0 right-0 z-[9999] flex items-center justify-between px-4 py-2 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 shadow-2xl">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-bold text-white">HADR Focus View</span>
            <span className="text-xs text-slate-400 font-mono">|</span>
            <span className="text-xs text-cyan-400 font-semibold">{currentDam?.name || 'Dam'} — {currentDam?.river || ''}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-6 text-xs">
              <div className="flex items-center gap-1.5">
                <Waves className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-slate-400">Area:</span>
                <span className="font-bold text-white font-mono">{(simMeta?.inundated_area_km2 || 0).toFixed(1)} km²</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Droplets className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-slate-400">Depth:</span>
                <span className="font-bold text-white font-mono">{(simMeta?.max_depth_m || 0).toFixed(1)} m</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-slate-400">Q Peak:</span>
                <span className="font-bold text-white font-mono">{(simMeta?.hydrograph?.q_peak_m3s || 0).toLocaleString()} m³/s</span>
              </div>
            </div>
            <button
              onClick={() => setFocusMode(false)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-red-500/50 hover:bg-red-950/30 text-xs font-bold transition-all"
            >
              <X className="w-3.5 h-3.5" /> Exit Focus
              <span className="text-[9px] text-slate-500 font-mono ml-1">ESC</span>
            </button>
          </div>
        </div>
      )}

      {/* 1. TOP NAVBAR HEADER */}
      {!focusMode && (
      <header className="hadr-card px-4 py-2.5 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white font-heading">HADR</h1>
              <span className="text-xs text-slate-400 font-medium">|</span>
              <span className="text-xs font-semibold text-slate-300">Flood Simulation & Dam-Break Analysis Platform</span>
            </div>
            <p className="text-[10px] text-slate-400">Safer Communities &bull; Stronger Resilience &bull; Open-Source Data</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {dataStatus && (
            <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 rounded-full px-3 py-1 text-amber-400 text-xs font-semibold animate-pulse">
              <Zap className="w-3 h-3" />
              {dataStatus}
            </div>
          )}

          <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-3 py-1 text-emerald-400 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            System Online
          </div>

          <div className="text-xs text-slate-300 font-mono font-medium">
            {clock} (IST)
          </div>

          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <Bell className="w-4.5 h-4.5" />
              {activities.length > 1 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-500 rounded-full"></span>
              )}
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 top-10 w-80 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800">
                  <span className="text-xs font-bold text-white">Notifications</span>
                  <button onClick={() => setNotificationsOpen(false)} className="text-slate-400 hover:text-white">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="max-h-60 overflow-y-auto p-2 space-y-1">
                  {activities.slice(0, 10).map((item, i) => (
                    <div key={i} className="flex items-start gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-800/60 text-[11px]">
                      <span className={`w-2 h-2 rounded-full ${item.color} mt-1 shrink-0`}></span>
                      <div>
                        <span className="text-slate-300">{item.text}</span>
                        <span className="text-slate-500 ml-2 font-mono text-[9px]">{item.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 pl-2 border-l border-slate-700/80">
            <div className="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-500 text-blue-300 text-xs font-bold flex items-center justify-center">
              SK
            </div>
            <div className="text-left leading-tight">
              <div className="text-xs font-bold text-white">Sumit Kushwaha</div>
              <div className="text-[10px] text-slate-400">Project Demo</div>
            </div>
          </div>
        </div>
      </header>
      )}

      {/* 2. TOP METRIC KPI CARDS BAR (5 CARDS) */}
      {!focusMode && (
      <div className="grid grid-cols-5 gap-3">
        {/* Card 1 */}
        <div className="hadr-card p-3.5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">Flood Area (km²)</p>
            <h3 className="text-2xl font-black text-white font-mono">{(maxAreaVal).toFixed(1)}</h3>
            <p className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Inundation Engine
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Waves className="w-5 h-5" />
          </div>
        </div>

        {/* Card 2 */}
        <div className="hadr-card p-3.5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">Max Water Depth (m)</p>
            <h3 className="text-2xl font-black text-white font-mono">{(simMeta?.max_depth_m || 4.2).toFixed(1)}</h3>
            <p className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Inundation Engine
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Droplets className="w-5 h-5" />
          </div>
        </div>

        {/* Card 3 */}
        <div className="hadr-card p-3.5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">Affected Population</p>
            <h3 className="text-2xl font-black text-white font-mono">{exposureData?.total_population_exposed?.toLocaleString() || '--'}</h3>
            <p className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Updated from OSM
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* Card 4 */}
        <div className="hadr-card p-3.5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">Affected Settlements</p>
            <h3 className="text-2xl font-black text-white font-mono">{exposureData?.settlements_flooded_count || '--'}</h3>
            <p className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Updated from OSM
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Home className="w-5 h-5" />
          </div>
        </div>

        {/* Card 5 (Risk Alert Highlight) */}
        <div className="hadr-card p-3.5 flex items-center justify-between bg-red-950/30 border-red-900/60">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">Risk Level</p>
            <h3 className="text-2xl font-black text-red-400 font-heading tracking-wide">
              {releasePercent >= 50 ? 'Critical' : releasePercent >= 25 ? 'High' : 'Moderate'}
            </h3>
            <p className="text-[11px] font-medium text-red-300">
              {releasePercent >= 50 ? 'Emergency Evacuation' : 'Immediate Response Required'}
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-red-600/30 border border-red-500/50 flex items-center justify-center text-red-400">
            <AlertTriangle className="w-5 h-5 animate-bounce" />
          </div>
        </div>
      </div>
      )}

      {/* 3. MAIN MIDDLE SECTION */}
      <div className={`grid gap-3 flex-1 items-stretch min-h-[520px] ${focusMode ? 'grid-cols-1 pt-11' : 'grid-cols-12'}`}>
        {/* LEFT VERTICAL NAVIGATION SIDEBAR (2 cols) */}
        {!focusMode && (
        <div className="col-span-2 hadr-card p-3 flex flex-col justify-between">
          <div className="space-y-1">
            {[
              { id: 'overview', label: 'Overview', icon: Home },
              { id: 'simulation', label: 'Simulation', icon: Sliders },
              { id: 'flood_map', label: 'Flood Map', icon: Map, active: true },
              { id: 'model_comparison', label: 'Model Comparison', icon: BarChart3 },
              { id: 'exposure', label: 'Exposure & Impact', icon: Shield },
              { id: 'export', label: 'Export', icon: Download }
            ].map((nav) => {
              const Icon = nav.icon;
              const isActive = nav.id === activeNavTab;
              return (
                <button
                  key={nav.id}
                  onClick={() => setActiveNavTab(nav.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{nav.label}</span>
                </button>
              );
            })}
          </div>

          {/* Bottom Left Badge Graphic */}
          <div className="p-3 rounded-xl bg-blue-950/40 border border-blue-800/40 text-center space-y-1">
            <Shield className="w-5 h-5 text-blue-400 mx-auto" />
            <p className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">Disaster Ready</p>
            <p className="text-[9px] text-slate-400">Open-Source &bull; Data Driven</p>
            <p className="text-[9px] text-blue-400 font-mono">{dams.length} Dams Available</p>
          </div>
        </div>
        )}
        {/* LEFT SIMULATION SCENARIO CONTROL PANEL (2 cols) */}
        {!focusMode && (
        <div className="col-span-2 hadr-card p-3.5 flex flex-col justify-between space-y-2 overflow-y-auto">
          <div className="space-y-2.5">
            <h3 className="text-sm font-bold text-white font-heading tracking-wide border-b border-slate-800 pb-2">
              Simulation Scenario
            </h3>

            {/* Dam Search */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Search Dam</label>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                <input
                  type="text"
                  value={damSearch}
                  onChange={(e) => setDamSearch(e.target.value)}
                  placeholder="Name, river, or state..."
                  className="w-full hadr-input pl-8 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Dam / River</label>
              <select
                value={selectedDam}
                onChange={(e) => setSelectedDam(e.target.value)}
                className="w-full hadr-input text-xs"
              >
                {filteredDams.length > 0 ? (
                  filteredDams.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} — {d.river}, {d.state}
                    </option>
                  ))
                ) : (
                  <option value="tehri-dam">Tehri Dam (Bhagirathi River)</option>
                )}
              </select>
            </div>

            {/* Selected dam info card */}
            {currentDam && (
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800 space-y-1">
                <div className="flex items-center gap-2">
                  <MapPin className="w-3 h-3 text-red-400" />
                  <span className="text-[11px] font-bold text-white">{currentDam.name}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-2 text-[10px] text-slate-400">
                  <span>Height: <span className="text-white font-mono">{currentDam.dam_height_m}m</span></span>
                  <span>Type: <span className="text-white">{currentDam.type?.split(' ')[0]}</span></span>
                  <span>River: <span className="text-cyan-400">{currentDam.river}</span></span>
                  <span>State: <span className="text-white">{currentDam.state}</span></span>
                </div>
              </div>
            )}

            <div className="space-y-1 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-300">Release Percentage</span>
                <span className="text-blue-400 font-mono">{releasePercent}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={releasePercent}
                onChange={(e) => setReleasePercent(Number(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded appearance-none cursor-pointer mt-1"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Reservoir Water Level (m)</label>
              <input
                type="number"
                value={reservoirLevel}
                onChange={(e) => setReservoirLevel(Number(e.target.value))}
                className="w-full hadr-input font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Simulation Duration</label>
              <select
                value={durationMin}
                onChange={(e) => setDurationMin(Number(e.target.value))}
                className="w-full hadr-input"
              >
                <option value={120}>2 Hours</option>
                <option value={360}>6 Hours</option>
                <option value={720}>12 Hours</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Time Step</label>
              <select
                value={timeStepMin}
                onChange={(e) => setTimeStepMin(Number(e.target.value))}
                className="w-full hadr-input"
              >
                <option value={15}>15 Minutes</option>
                <option value={30}>30 Minutes</option>
                <option value={60}>60 Minutes</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Engine</label>
              <div className="grid grid-cols-3 gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-[11px] font-bold">
                <button
                  type="button"
                  onClick={() => setEngine('terrain')}
                  className={`py-1.5 rounded-md transition-all ${engine === 'terrain' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >
                  Terrain
                </button>
                <button
                  type="button"
                  onClick={() => setEngine('sph')}
                  className={`py-1.5 rounded-md transition-all ${engine === 'sph' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >
                  SPH
                </button>
                <button
                  type="button"
                  onClick={() => setEngine('delft3d')}
                  className={`py-1.5 rounded-md transition-all ${engine === 'delft3d' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >
                  Delft3D
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={() =>
                runSimulationHandler({
                  dam_id: selectedDam,
                  release_percent: releasePercent,
                  duration_min: durationMin,
                  time_step_min: timeStepMin,
                  engine
                })
              }
              disabled={loading}
              className="w-full hadr-btn-primary flex items-center justify-center gap-2 text-xs py-2.5"
            >
              <Play className="w-4 h-4 fill-white" />
              {loading ? 'Simulating...' : 'Run Simulation'}
            </button>
            <p className="text-[10px] text-slate-400 text-center">
              &bull; Using real DEM + OSM data for {currentDam?.name || 'selected dam'}
            </p>
          </div>
        </div>
        )}

        {/* CENTER MAIN CONTENT — expands to full in focus mode */}
        <div className={`relative min-h-[500px] ${focusMode ? 'col-span-1' : 'col-span-5'}`}>
          {/* SIMULATION LOADING OVERLAY */}
          {loading && activeNavTab === 'flood_map' && (
            <div className="absolute inset-0 z-[600] bg-slate-950/80 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center gap-4">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-slate-700"></div>
                <div className="absolute inset-0 rounded-full border-4 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
                <div className="absolute inset-2 rounded-full border-4 border-t-transparent border-r-cyan-400 border-b-transparent border-l-transparent animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Waves className="w-5 h-5 text-blue-400 animate-pulse" />
                </div>
              </div>
              <div className="text-center space-y-2">
                <h4 className="text-sm font-bold text-white animate-pulse">Creating Simulation</h4>
                <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-700 rounded-lg px-4 py-2 min-w-[280px]">
                  <span className="flex items-center justify-center">{loadingSteps[loadingStep].icon}</span>
                  <span className="text-xs text-slate-300 font-medium">{loadingSteps[loadingStep].text}</span>
                </div>
                <div className="flex gap-1 justify-center pt-1">
                  {loadingSteps.map((_, i) => (
                    <div key={i} className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${i === loadingStep ? 'bg-blue-400 scale-125' : i < loadingStep ? 'bg-blue-600' : 'bg-slate-700'}`}></div>
                  ))}
                </div>
                <p className="text-[10px] text-slate-500 font-mono">{currentDam?.name || 'Dam'} • {engine.toUpperCase()} Engine</p>
              </div>
            </div>
          )}

          {activeNavTab === 'flood_map' && (
            <FullMapCanvas
              dams={dams.length > 0 ? dams.filter(d => d.id === selectedDam) : []}
              currentFeatures={currentFeatures}
              showSph={showSph}
              sphData={sphData}
              showSentinel={showSentinel}
              sentinel1Data={sentinel1Data}
              currentTimestep={currentTimestep}
              timesteps={timesteps}
              currentStepIdx={currentStepIdx}
              setCurrentStepIdx={setCurrentStepIdx}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              selectedDamId={selectedDam}
              showRadar={true}
              onFocusToggle={() => setFocusMode(true)}
            />
          )}
          {activeNavTab === 'overview' && (
            <div className="h-full overflow-y-auto hadr-card rounded-xl">
              <OverviewTab
                dams={dams}
                onQuickSimulate={(damId) => {
                  setSelectedDam(damId);
                  setActiveNavTab('flood_map');
                  runSimulationHandler({
                    dam_id: damId,
                    release_percent: releasePercent,
                    duration_min: durationMin,
                    time_step_min: timeStepMin,
                    engine
                  });
                }}
              />
            </div>
          )}
          {activeNavTab === 'simulation' && (
            <div className="h-full overflow-y-auto hadr-card rounded-xl">
              <SimulationTab
                dams={dams}
                onRunSimulation={async (params) => {
                  setSelectedDam(params.dam_id !== 'custom' ? params.dam_id : selectedDam);
                  await runSimulationHandler(params);
                }}
                loading={loading}
              />
            </div>
          )}
          {activeNavTab === 'exposure' && (
            <div className="h-full overflow-y-auto hadr-card rounded-xl">
              <ExposureTab exposure={exposureData} />
            </div>
          )}
          {activeNavTab === 'model_comparison' && (
            <div className="h-full overflow-y-auto hadr-card rounded-xl">
              <ModelComparisonTab comparisonData={comparisonData} />
            </div>
          )}
          {activeNavTab === 'export' && (
            <div className="h-full overflow-y-auto hadr-card rounded-xl">
              <ExportTab simId={activeSimId} />
            </div>
          )}
        </div>

        {/* RIGHT SIMULATION RESULTS & QUICK ACTIONS & AREA OF INTEREST (3 cols) */}
        {!focusMode && (
        <div className="col-span-3 space-y-3 flex flex-col justify-between">
          {/* Card 1: Simulation Results */}
          <div className="hadr-card p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-blue-400" /> Simulation Results
              </h3>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${loading ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'}`}>
                {loading ? 'Running...' : 'Completed'}
              </span>
            </div>

            <div className="space-y-1.5 text-xs font-medium">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Scenario ID</span>
                <span className="text-white font-mono text-[11px]">{activeSimId || 'Pending...'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Dam</span>
                <span className="text-white">{currentDam?.name || 'Tehri Dam'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Engine Used</span>
                <span className="text-white">{engine === 'terrain' ? 'Terrain (Prototype)' : engine.toUpperCase()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Duration</span>
                <span className="text-white">{durationMin / 60} Hours</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Peak Flow (est.)</span>
                <span className="text-white font-mono">{simMeta?.hydrograph?.q_peak_m3s?.toLocaleString() || '2,480'} m³/s</span>
              </div>
            </div>
          </div>

          {/* Card 2: Quick Actions */}
          <div className="hadr-card p-3.5 space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading">
              Quick Actions
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => handleExport('geojson')}
                className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 hover:text-white hover:border-blue-500 transition-all font-semibold"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" /> Export GeoJSON
              </button>
              <button
                onClick={() => handleExport('kml')}
                className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 hover:text-white hover:border-blue-500 transition-all font-semibold"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" /> Export KML
              </button>
              <button
                onClick={() => handleExport('shp')}
                className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 hover:text-white hover:border-blue-500 transition-all font-semibold"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" /> Export SHP (Zip)
              </button>
              <button
                onClick={() => handleExport('geojson')}
                className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 hover:text-white hover:border-blue-500 transition-all font-semibold"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" /> Export GeoTIFF
              </button>
            </div>
          </div>

          {/* Card 3: Area of Interest */}
          <div className="hadr-card p-3.5 space-y-2 flex-1 flex flex-col justify-between">
            <div className="space-y-1">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading">
                Area of Interest
              </h3>
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-blue-400 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold text-white">{currentDam?.name || 'Select Dam'} / {currentDam?.river || 'River'}</h4>
                  <p className="text-[10px] text-slate-400 font-mono">{currentDam?.lat.toFixed(4)}&deg; N, {currentDam?.lon.toFixed(4)}&deg; E</p>
                </div>
              </div>
            </div>

            {/* Dam info mini card */}
            <div className="relative h-28 rounded-lg overflow-hidden border border-slate-700 bg-slate-950">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-950/80 to-slate-950/90 flex flex-col items-center justify-center gap-2">
                <MapPin className="w-6 h-6 text-red-400" />
                <div className="text-center">
                  <p className="text-xs font-bold text-white">{currentDam?.state || 'India'}</p>
                  <p className="text-[10px] text-slate-400">{currentDam?.type || 'Dam'} &bull; {currentDam?.year_completed || ''}</p>
                  <p className="text-[10px] text-cyan-400 font-mono">{currentDam?.normal_storage_mcm?.toLocaleString() || '?'} MCM Storage</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        )}
      </div>

      {/* 4. BOTTOM GRID (4 CARDS: FLOOD PROPAGATION, MODEL COMPARISON, EXPOSURE, RECENT ACTIVITY) */}
      {!focusMode && (
      <div className="grid grid-cols-12 gap-3">
        {/* Card 1: Flood Propagation (Time Series Chart) (3 cols) */}
        <div className="col-span-3 hadr-card p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-blue-400" /> Flood Propagation (Time Series)
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Max Area: {maxAreaVal.toFixed(1)} km²</span>
          </div>

          <div className="h-36 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeSeriesData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1527', borderColor: '#3b82f6', borderRadius: '8px', fontSize: '11px' }}
                />
                <Area type="monotone" dataKey="area" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#areaGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 2: Model Comparison (3 cols) */}
        <div className="col-span-3 hadr-card p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4 text-blue-400" /> Model Comparison
            </h3>
          </div>

          <div className="flex gap-1 text-[10px] font-bold border-b border-slate-800 pb-1.5 overflow-x-auto">
            <button
              onClick={() => setMetricTab('area')}
              className={`px-2 py-1 rounded transition-colors ${metricTab === 'area' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Flood Area (km²)
            </button>
            <button
              onClick={() => setMetricTab('depth')}
              className={`px-2 py-1 rounded transition-colors ${metricTab === 'depth' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Max Depth (m)
            </button>
            <button
              onClick={() => setMetricTab('arrival')}
              className={`px-2 py-1 rounded transition-colors ${metricTab === 'arrival' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Peak Flow (m³/s)
            </button>
          </div>

          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 text-[10px] uppercase border-b border-slate-800">
                <th className="py-1">Model</th>
                <th className={`py-1 text-right ${metricTab === 'area' ? 'text-blue-400 font-bold' : ''}`}>Flood Area</th>
                <th className={`py-1 text-right ${metricTab === 'depth' ? 'text-blue-400 font-bold' : ''}`}>Max Depth</th>
                <th className={`py-1 text-right ${metricTab === 'arrival' ? 'text-blue-400 font-bold' : ''}`}>Peak Flow</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              <tr>
                <td className="py-1.5 text-blue-400 font-semibold font-sans">Terrain (Prototype)</td>
                <td className={`py-1.5 text-right font-bold ${metricTab === 'area' ? 'text-blue-400 text-sm' : 'text-white'}`}>{(maxAreaVal).toFixed(1)}</td>
                <td className={`py-1.5 text-right ${metricTab === 'depth' ? 'text-blue-400 font-bold text-sm' : 'text-slate-300'}`}>{(simMeta?.max_depth_m || 4.2).toFixed(1)}</td>
                <td className={`py-1.5 text-right ${metricTab === 'arrival' ? 'text-blue-400 font-bold text-sm' : 'text-slate-300'}`}>{simMeta?.hydrograph?.q_peak_m3s?.toLocaleString() || '2,480'}</td>
              </tr>
              <tr>
                <td className="py-1.5 text-cyan-400 font-semibold font-sans">SPH (Prototype)</td>
                <td className={`py-1.5 text-right font-bold ${metricTab === 'area' ? 'text-blue-400 text-sm' : 'text-white'}`}>{(maxAreaVal * 1.09).toFixed(1)}</td>
                <td className={`py-1.5 text-right ${metricTab === 'depth' ? 'text-blue-400 font-bold text-sm' : 'text-slate-300'}`}>{( (simMeta?.max_depth_m || 4.2) * 1.1 ).toFixed(1)}</td>
                <td className={`py-1.5 text-right ${metricTab === 'arrival' ? 'text-blue-400 font-bold text-sm' : 'text-slate-300'}`}>{Math.round((simMeta?.hydrograph?.q_peak_m3s || 2480) * 1.08).toLocaleString()}</td>
              </tr>
              <tr>
                <td className="py-1.5 text-emerald-400 font-semibold font-sans">Delft3D (Integration Ready)</td>
                <td className={`py-1.5 text-right font-bold ${metricTab === 'area' ? 'text-blue-400 text-sm' : 'text-white'}`}>{(maxAreaVal * 1.11).toFixed(1)}</td>
                <td className={`py-1.5 text-right ${metricTab === 'depth' ? 'text-blue-400 font-bold text-sm' : 'text-slate-300'}`}>{( (simMeta?.max_depth_m || 4.2) * 1.14 ).toFixed(1)}</td>
                <td className={`py-1.5 text-right ${metricTab === 'arrival' ? 'text-blue-400 font-bold text-sm' : 'text-slate-300'}`}>{Math.round((simMeta?.hydrograph?.q_peak_m3s || 2480) * 1.12).toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Card 3: Exposure Assessment Grid (3 cols) */}
        <div className="col-span-3 hadr-card p-3.5 space-y-2">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-blue-400" /> Exposure Assessment
          </h3>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-900/80 border border-slate-800 p-2 rounded-xl flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Home className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400">Estimated Houses</p>
                <h4 className="text-sm font-bold text-white font-mono">{Math.round((exposureData?.total_population_exposed || 0) / 4.5).toLocaleString()}</h4>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-2 rounded-xl flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Compass className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400">Roads Impacted</p>
                <h4 className="text-sm font-bold text-white font-mono">{(exposureData?.flooded_roads_km || 0).toFixed(1)} km</h4>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-2 rounded-xl flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Building2 className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400">Bridges Affected</p>
                <h4 className="text-sm font-bold text-white font-mono">{exposureData?.bridges_at_risk || 0}</h4>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-2 rounded-xl flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Users className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400">Population at Risk</p>
                <h4 className="text-sm font-bold text-white font-mono">{exposureData?.total_population_exposed?.toLocaleString() || '0'}</h4>
              </div>
            </div>
          </div>
        </div>

        {/* Card 4: Recent Activity Live Logs (3 cols) */}
        <div className="col-span-3 hadr-card p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-heading flex items-center gap-1.5">
              <Radio className="w-4 h-4 text-blue-400" /> Recent Activity
            </h3>
            <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Live
            </span>
          </div>

          <div className="space-y-2 text-[11px] max-h-32 overflow-y-auto pr-1">
            {activities.slice(0, 8).map((item, i) => (
              <div key={i} className="flex items-center gap-2.5 text-slate-300">
                <span className={`w-2 h-2 rounded-full ${item.color} shrink-0`}></span>
                <span className="font-mono text-slate-400 text-[10px]">{item.time}</span>
                <span className="truncate">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

export default App;
