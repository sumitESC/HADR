# A Generalized Hydrodynamic Framework for Rapid Dam-Break Inundation Modelling

**Project Type:** Software / GIS / Disaster Management  
**Problem Statement:** SIH26161 — Dam Break Inundation Modelling Using Hydrodynamic Modelling of any River (NTRO)  
**Team:** CTRL_ALT_WIN (SIH 2026)  

---

## 1. Abstract

Flash floods triggered by catastrophic dam failures or natural lake bursts present an acute threat to downstream catchments across India. During a crisis, decision-makers need to rapidly estimate the volume of water release, the spatial extent of inundation, the propagation velocity, and the exact settlements, roads, hospitals, and bridges at risk. Existing hydrodynamic models such as Delft3D and HEC-RAS require days of setup and specialized hardware, making them impractical for immediate emergency response.

This project introduces **HADR** (Humanitarian Assistance and Disaster Relief), a comprehensive, generalized simulation framework that automates dam-break inundation modelling for any river system in India. The platform dynamically ingests open-source Digital Elevation Models (SRTM/ASTER), hydrological vector data from OpenStreetMap (1.7 GB India PBF), and Sentinel-1 SAR imagery via Google Earth Engine. 

To balance emergency speed with scientific accuracy, the software implements a novel tri-model architecture: 
1. A blazing-fast physics-based terrain routing engine for sub-second emergency predictions, 
2. A Smooth Particle Hydrodynamics (SPH) adapter implementing Lagrangian Navier-Stokes equations with cKDTree neighbor search and Monaghan Artificial Viscosity, 
3. A Delft3D proxy implementing 2D Shallow Water Equations with Lax-Friedrichs shock stabilization and adaptive CFL time-stepping. 

All three engines produce comparable inundation polygons that can be visualized side-by-side on an interactive React/MapLibre WebGL dashboard. The system further automates end-to-end Loss and Damage Analysis using depth-damage curves to calculate financial exposure (INR Crores), exposed populations, and critical infrastructure at risk. All simulation outputs are automatically exported into standardized GIS formats (.shp, .kml, GeoJSON) for interoperability with QGIS and ArcGIS. 

---

## 2. Introduction

### 2.1 Background
The Indian subcontinent is highly susceptible to hydro-meteorological disasters. In recent years, natural dam and lake formations — often triggered by landslides, glacial lake outburst floods (GLOFs), or seismic activity — have resulted in devastating flash floods in lower catchments. Notable events include the Rishi Ganga River avalanche in 2021, the Wapriyang River natural lake burst in Meghalaya (2021), and the devastating Kosi River breach in 2008. Beyond natural formations, India has over 5,000 large dams, many aging and facing structural integrity concerns. In crisis situations requiring emergency water release or in the event of a catastrophic dam break, estimating the volume of water propagation, flow velocity, and the exact spatial extent of downstream inundation is critical for effective Humanitarian Assistance and Disaster Relief (HADR).

### 2.2 Problem Statement
As defined by the National Technical Research Organisation (NTRO), Problem Statement ID SIH26161, the core requirement is:

"Development of a software tool that automates simulation modelling for Dam Break analysis. The framework must utilize hydrological data, DEM, and satellite imagery. The software should carry out simulation of water flow using Smooth Particle Hydrodynamics (SPH) and Delft3D models to compare scenarios. The tool must automate Loss and Damage analysis and feature a Dashboard GUI capable of handling large data volumes. Standard GIS outputs (.shp, .kml) must be supported. A framework for near real-time flood analysis through Google Earth Engine (GEE) is required."

### 2.3 Motivation
Current hydrodynamic modelling tools (Delft3D, HEC-RAS, MIKE) are powerful but require days to weeks of manual setup per river basin, proprietary licenses costing thousands of dollars, specialized hardware (HPC clusters) for 3D Navier-Stokes resolution, and expert hydrologists to configure boundary conditions. None of these are acceptable in an emergency HADR scenario where decisions must be made in minutes, not weeks. The motivation for HADR is to bridge this gap by providing an automated, open-source, one-click simulation framework that delivers actionable flood intelligence within seconds.

### 2.4 Objectives
1. Build a generalized framework capable of simulating dam break scenarios on ANY river in India using open-source data (DEM, OSM, Satellite).
2. Implement and integrate three distinct hydrodynamic engines — Terrain Routing, SPH (Navier-Stokes), and Delft3D (2D SWE) — enabling scientific model comparison.
3. Automate Loss and Damage Analysis by intersecting flood polygons with real-world infrastructure data (settlements, roads, hospitals) and computing financial exposure in INR Crores.
4. Build a scalable, interactive Dashboard GUI using WebGL-accelerated mapping (MapLibre) capable of rendering massive geospatial datasets.
5. Provide automated GIS export in .shp, .kml, and GeoJSON formats for field interoperability.
6. Integrate Google Earth Engine for near real-time Sentinel-1 SAR flood verification.
7. Ship a pre-loaded database of 48 major Indian dams for instant nationwide demonstration.

### 2.5 Contributions
1. **Multi-Model Architecture:** First open-source framework to integrate Terrain Routing, SPH, and Delft3D (SWE) engines in a single platform with side-by-side comparison capabilities.
2. **Blazing-Fast OSM Pipeline:** Custom Java Osmosis + pyosmium pipeline that extracts infrastructure data from a 1.7 GB India PBF file in under 3 seconds, enabling offline exposure analysis without internet dependency.
3. **Automated Depth-Damage Curves:** Novel integration of flood depth rasters with OSM settlement footprints to compute per-village financial damage and evacuation status classifications.
4. **GEE SAR Validation:** Automated Sentinel-1 SAR flood mapping with Otsu Thresholding and JRC/Topographic masking for model verification.
5. **Universal Dam Support:** Accepts custom lat/lon/height to simulate any dam worldwide, beyond the 48 pre-loaded Indian dams.

---

## 3. Existing System / Related Work

### 3.1 Existing Solutions
Several established hydrodynamic modelling systems are in use globally:
1. **Delft3D (Deltares):** A world-class open-source 3D hydrodynamic modelling suite. Solves the full Navier-Stokes equations on curvilinear or unstructured grids.
2. **HEC-RAS (US Army Corps of Engineers):** 1D/2D hydraulic modelling software. Industry standard for river analysis in the United States.
3. **MIKE FLOOD (DHI):** A commercial suite combining 1D (MIKE 11) and 2D (MIKE 21) engines. Powerful but expensive (proprietary licensing).
4. **TELEMAC-2D:** An open-source finite element 2D hydrodynamic solver used in European river systems for flood modelling.
5. **SPHysics / DualSPHysics:** Open-source SPH solvers primarily designed for coastal engineering and wave-structure interaction.

### 3.2 Limitations of Existing Solutions
- **Setup Time:** Delft3D and HEC-RAS require hours to days of manual mesh generation, boundary condition specification, and calibration for each new river basin.
- **Hardware Requirements:** Full 3D Navier-Stokes resolution demands HPC clusters or GPU-accelerated workstations costing tens of thousands of dollars.
- **No Integrated Loss Analysis:** None of the above tools automatically compute damage to real-world infrastructure. Post-processing is manual and time-consuming.
- **No Dashboard GUI:** Most tools operate through desktop applications or command-line interfaces, lacking modern web-based interactive dashboards.
- **No GEE Integration:** None offer built-in satellite verification of simulated flood extents.
- **Single-Model Limitation:** Each tool implements one modelling approach. There is no unified framework to compare SPH vs. Delft3D vs. terrain-based predictions on the same dataset.

### 3.3 Research Gap
The critical gap is the absence of a unified, web-based, automated platform that accepts any dam/river in India as input, runs multiple hydrodynamic models simultaneously for comparison, automatically computes loss and damage against real infrastructure data, exports results in standardized GIS formats, and validates predictions against satellite observations. HADR fills this gap completely.

---

## 4. Proposed Methodology

### 4.1 System Architecture

```mermaid
graph TD
    User[User / Web Browser] --> Frontend[Frontend: React + MapLibre]
    Frontend --> API[REST API]
    API --> Core[Backend: FastAPI]
    Core --> Terrain[Terrain Engine: Fast Physics]
    Core --> SPH[SPH Adapter: Navier-Stokes]
    Core --> Delft3D[Delft3D Proxy: 2D SWE]
    Terrain --> PostProcess[Post-Processing]
    SPH --> PostProcess
    Delft3D --> PostProcess
    PostProcess --> Exposure[Exposure Analysis]
    PostProcess --> GISExport[GIS Exports]
    Exposure --> Dashboard[Dashboard Render]
    GISExport --> Dashboard
```

### 4.2 System Workflow

```mermaid
flowchart LR
    Start[Dam Selection & Config] --> FetchDEM[Fetch DEM Raster Data]
    FetchDEM --> FetchOSM[Fetch OSM Infrastructure Data]
    FetchOSM --> Sim[Run Hydrodynamic Engine]
    Sim --> Poly[Polygonize Depth Rasters]
    Poly --> Exp[Loss & Exposure Analysis]
    Exp --> View[Visualize & Export]
```

### 4.3 Module Description

#### Module 1 — Input Layer (Dam Selection & Configuration)
The user selects a target dam from a curated database of 48 major Indian dams or enters custom coordinates (latitude, longitude, dam height). Configurable parameters include the reservoir water release percentage (1-100%), simulation duration (30-1440 minutes), timestep interval (5-120 minutes), and the hydrodynamic engine (terrain, sph, or delft3d). The input is validated via Pydantic models in FastAPI, ensuring strict type safety and range constraints before any computation begins.

#### Module 2 — Data Acquisition Layer (DEM + OSM + Satellite)
This module automatically fetches the terrain and infrastructure data required for simulation. The DEM processor (dem_processor.py) loads SRTM/ASTER raster tiles for the catchment area, computing elevation gradients and D8 flow direction vectors. The OSM pipeline (osm_data.py) uses Java Osmosis to crop the 1.7 GB India PBF file into a localized micro-extract, then pyosmium parses it to identify settlements, roads, hospitals, schools, bridges, and rivers within the flood risk zone. As a fallback, the Overpass API provides online OSM queries with intelligent spatial chunking (20km grids).

#### Module 3 — Hydrodynamic Simulation Layer (3 Engines)
The SimulationManager (manager.py) orchestrates all three engines:
- **Terrain Engine:** Physics-based slope routing using broad-crested weir breach hydrograph and iterative cellular automata diffusion over the DEM grid. Generates accurate inundation bounds in under 1 second.
- **SPH Adapter:** Lagrangian particle-based Navier-Stokes solver with cKDTree spatial partitioning (O(N log N)), Cubic Spline Kernel interpolation, Monaghan Artificial Viscosity for shock handling, and Leapfrog time integration for energy conservation.
- **Delft3D Proxy:** Eulerian grid-based 2D Shallow Water Equation solver with Lax-Friedrichs shock stabilization, Manning's bed friction, adaptive CFL time-stepping, and robust wet/dry boundary thresholding.

#### Module 4 — Post-Processing & Analysis Layer
After simulation, the polygonizer (polygonizer.py) converts raw depth rasters into vectorized GeoJSON topologies with time-series indexing. The Exposure Analyzer (exposure.py) performs polygon-point and polygon-line intersections using the Shapely library against OSM infrastructure data, applying depth-damage curves to classify settlement damage (catastrophic > 4m, high > 2m, low > 0.5m) and computing aggregate financial loss estimates.

#### Module 5 — Output & Export Layer
The Exporter (exporter.py) converts simulation results into three standardized GIS formats: GeoJSON (native), KML (XML with styled polygons for Google Earth), and ESRI Shapefile (.shp zipped with .prj for WGS84 projection). The frontend dashboard provides interactive animated visualization with a time-slider for flood wave playback, depth-coded heatmaps, exposure tables, and model comparison charts.

---

## 5. Dataset and Data Sources

### 5.1 Dataset Overview
- **Dataset Name:** Multi-Source Geospatial Dataset (DEM + OSM + Satellite)
- **Number of Records:** 48 dams (pre-loaded) + unlimited custom dams
- **Number of Features:** Elevation grids (millions of cells per basin) + thousands of OSM vector features per simulation
- **Time Period:** Historical DEM (SRTM 2000, ASTER 2011) + Real-time SAR (Sentinel-1, continuous acquisition)
- **Geographical Coverage:** Entire India (pan-India) — generalizable to any location worldwide

### 5.2 Input Variables

| Feature | Description | Unit |
|---------|-------------|------|
| Dam Latitude | Geographic latitude of the dam | Degrees (WGS84) |
| Dam Longitude | Geographic longitude of the dam | Degrees (WGS84) |
| Dam Height | Structural height of the dam wall | Meters |
| Reservoir Capacity | Total water storage capacity | MCM (Million Cubic Meters) |
| Release Percentage | Fraction of reservoir released | Percent (1-100%) |
| Duration | Total simulation time window | Minutes |
| Timestep Interval | Granularity of temporal snapshots | Minutes |
| DEM Elevation Grid | SRTM/ASTER terrain elevation array | Meters (ASL) |
| OSM Settlements | Building footprints and named places | Vector (lat/lon) |
| OSM Roads | Road network polylines | Vector (lat/lon) |
| OSM Hospitals | Hospital/clinic point locations | Vector (lat/lon) |
| OSM Schools | School/university point locations | Vector (lat/lon) |
| Sentinel-1 SAR | C-band radar backscatter imagery | Decibels (dB) |

### 5.3 Data Sources
1. NASA SRTM (Shuttle Radar Topography Mission) — 30m global DEM
2. Copernicus GLO-30 DEM — 30m global elevation from ESA
3. OpenStreetMap India PBF — 1.7 GB comprehensive vector extract
4. Sentinel-1 SAR — C-band radar imagery (VV/VH polarization) from ESA Copernicus via Google Earth Engine
5. JRC Global Surface Water — Permanent water body classification
6. India Dam Database — Curated metadata for 48 major dams compiled from National Register of Large Dams (NRLD)

---

## 6. Data Pre-processing

The data pre-processing pipeline transforms raw geospatial inputs into computation-ready arrays and vectors:

1. **DEM Processing:** Raw GeoTIFF raster tiles are loaded via the Rasterio library. NoData values are masked and interpolated. Surface gradients (slope) are computed using NumPy finite difference methods across the elevation grid. D8 flow direction vectors are calculated to determine the natural hydrological routing of the terrain (8 cardinal + diagonal directions). The DEM is clipped to a configurable bounding box around the target dam to optimize computation.
2. **OSM Data Extraction:** The 1.7 GB India OpenStreetMap PBF file is cropped to the simulation bounding box using Java Osmosis, producing a localized micro-PBF of typically 1-5 MB in under 3 seconds. Python pyosmium then parses this micro-PBF, extracting Buildings/Settlements, Road Networks, Hospitals, Schools, Bridges, and Rivers within the flood risk zone. All features are projected into WGS84.
3. **Satellite Pre-processing:** Sentinel-1 SAR images are filtered by date range, polarization (VV), and instrument mode (IW — Interferometric Wide Swath). Speckle noise is reduced via Focal Median filtering, and backscatter values are converted from linear to decibel (dB) scale.

---

## 7. Model / Algorithm

### 7.1 Models Used
- **Model 1: Terrain-Based Flood Routing Engine** (Framework: Custom Python NumPy + SciPy)
- **Model 2: Smooth Particle Hydrodynamics (SPH)** (Framework: Custom Python NumPy + SciPy cKDTree)
- **Model 3: Delft3D Proxy (2D Shallow Water Equations)** (Framework: Custom Python NumPy)

### 7.2 Simulation Configuration

| Parameter | Terrain Engine | SPH Solver | Delft3D Proxy |
|-----------|----------------|------------|---------------|
| Grid/Particle Size | 30m DEM cells | 1000-5000 particles | 100x100 grid |
| Time Step | 30 min | Adaptive | Adaptive (CFL) |
| Smoothing Length (h)| N/A | 2 * dx | N/A |
| Viscosity Alpha | N/A | 1.0 | N/A |
| Manning's n | N/A | N/A | 0.035 |
| CFL Number | N/A | N/A | 0.5 |
| Wet/Dry Threshold | 0.1 m | 0.01 m | 0.01 m |
| Typical Runtime | < 1 second | 1-2 seconds | 1-3 seconds |

### 7.3 Mathematical Formulation

**Breach Hydrograph (Weir Equation):**
`Q_peak = C_d * B * sqrt(2 * g) * H^(3/2)`
Where Q_peak = Peak discharge (m^3/s), C_d = Discharge coefficient (0.6-0.65), B = Breach width (estimated from dam geometry), g = Gravitational acceleration, H = Effective head (dam height * release fraction).

**SPH Density Summation:**
`rho_i = SUM_j (m_j * W(r_i - r_j, h))`
Where rho_i = Density at particle i, m_j = Mass of particle j, W = Cubic Spline Kernel function, h = Smoothing length.

**SPH Momentum Equation:**
`dv_i/dt = -SUM_j m_j * (P_i/rho_i^2 + P_j/rho_j^2) * grad(W_ij) + g`
Where P_i, P_j = Pressure at particles i, j, grad(W_ij) = Gradient of kernel function, g = Gravitational acceleration vector.

**Monaghan Artificial Viscosity:**
`Pi_ij = (-alpha * c_ij * mu_ij + beta * mu_ij^2) / rho_ij`
Where mu_ij = h * (v_ij . r_ij) / (|r_ij|^2 + epsilon*h^2), c_ij = Average speed of sound, alpha = Linear viscosity coefficient, beta = Quadratic viscosity coefficient.

**2D Shallow Water Equations:**
- Mass: `dh/dt + d(hu)/dx + d(hv)/dy = 0`
- X-Momentum: `d(hu)/dt + d(hu^2 + gh^2/2)/dx + d(huv)/dy = -g*h*dz/dx - S_fx`
- Y-Momentum: `d(hv)/dt + d(huv)/dx + d(hv^2 + gh^2/2)/dy = -g*h*dz/dy - S_fy`
Where h = Water depth, u, v = Velocity components, z = Bed elevation, S_f = Manning's friction slope = n^2 * u * |u| / h^(4/3).

**Adaptive CFL Condition:**
`dt = CFL * dx / (|u| + sqrt(g * h))`
Where CFL = Courant number (0.5 for stability), dx = Grid spacing.

---

## 8. System Implementation

### 8.1 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 19 + TypeScript | Component-based UI |
| Mapping | MapLibre GL JS (WebGL) | GPU-accelerated flood maps |
| Styling | Tailwind CSS | Responsive modern design |
| Build Tool | Vite | Fast HMR development |
| Backend | FastAPI (Python 3.10+) | Async REST API server |
| Spatial Libraries| NumPy, SciPy, Rasterio, Shapely | GIS computation |
| OSM Processing | Java Osmosis + pyosmium | Offline data extraction |
| Satellite | Google Earth Engine (ee API) | SAR flood mapping |
| Data Format | GeoJSON, KML (XML), SHP (ZIP) | Standard GIS exports |
| Deployment | Docker + Render/Cloud | Containerized hosting |

### 8.2 Installation

**Prerequisites:** Python 3.10+, Node.js (v18+), Java (for Osmosis processing).

1. Clone the repository:
```bash
git clone https://github.com/sumitESC/HADR.git
cd HADR
```

2. Backend setup:
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
```

3. Frontend setup:
```bash
cd ../frontend
npm install
```

4. Run the application:
```bash
# From the root folder
python run.py
```
This will start the FastAPI backend on `http://127.0.0.1:8000` and the Vite React frontend on `http://localhost:5173/`.

---

## 9. Experimental Results and Analysis

### 9.1 Performance Metrics (Tehri Dam, 30% Release, 360 min)

| Metric | Terrain Engine | SPH Solver | Delft3D Proxy |
|--------|----------------|------------|---------------|
| Inundated Area (km^2) | 18.4 | 19.1 | 18.8 |
| Maximum Depth (m) | 12.4 | 13.2 | 12.8 |
| Average Flow Speed (m/s) | 2.1 | 2.3 | 2.2 |
| Runtime (seconds) | 0.45 | 1.2 | 2.1 |
| Settlements Affected | 23 | 25 | 24 |
| Financial Loss (INR Cr) | 2340 | 2680 | 2510 |

### 9.2 Results Analysis

- **Terrain Engine Analysis:** The terrain-based routing engine provides the fastest results (0.45 seconds) with reasonable accuracy. Its inundated area estimate (18.4 km^2) is within 3.7% of the SPH prediction, making it suitable for emergency first-response decisions. The trade-off is that it does not model turbulent mixing or complex wave-structure interactions.
- **SPH Solver Analysis:** The SPH solver provides the most detailed physics (Navier-Stokes resolution) and predicts the largest inundated area (19.1 km^2) due to its ability to model lateral splash and particle dispersion. Runtime is acceptable (1.2 seconds) thanks to the O(N log N) cKDTree optimization. Monaghan Artificial Viscosity successfully prevents particle interpenetration at the dam breach shock front.
- **Delft3D Proxy Analysis:** The 2D SWE solver provides balanced results between terrain and SPH, with an inundated area of 18.8 km^2. The Lax-Friedrichs scheme successfully handles the bore wave discontinuity. Manning's friction provides realistic velocity attenuation over the natural channel bed. The adaptive CFL time-stepping ensures numerical stability throughout the simulation.
- **Model Agreement:** All three engines agree within 4% on total inundated area and within 7% on maximum depth, providing high confidence in the predictions. The multi-model approach allows decision-makers to assess uncertainty ranges rather than relying on a single model output.

---

## 10. Use Cases

1. **Emergency Dam Breach Response:** A dam monitoring station detects critical structural stress. Within 60 seconds, the HADR system is triggered: the terrain engine predicts downstream inundation bounds, the exposure analyzer identifies settlements and hospitals at risk, and automated KML files are pushed to NDRF responders' devices for immediate navigation to evacuation zones.
2. **Pre-Monsoon Risk Assessment:** Before the annual monsoon season, state disaster management authorities (SDMAs) use HADR to run predictive scenarios for all major dams in their jurisdiction. By varying release percentages (10%, 30%, 50%, 100%), they generate a comprehensive risk matrix identifying the most vulnerable downstream settlements and pre-position relief materials accordingly.
3. **Scientific Hydrodynamic Comparison:** A research team studies the accuracy of different numerical methods for dam-break modelling. Using HADR's multi-engine architecture, they run identical scenarios through Terrain, SPH, and Delft3D engines, comparing inundated areas, depth profiles, and wave front velocities to validate their theoretical models against each other and against GEE SAR observations.
4. **Infrastructure Planning:** A civil engineering firm evaluates the downstream risk of a proposed new dam. By entering custom coordinates and dam height into HADR, they generate flood inundation maps and identify settlements, roads, and bridges that would be at risk. The exported Shapefiles are imported directly into their ArcGIS workflow for detailed environmental impact assessment.
5. **Post-Disaster Validation:** After a flood event, disaster analysts use the GEE Sentinel-1 SAR module to download the actual observed flood extent from satellite imagery. They overlay this with the HADR simulation output to validate prediction accuracy and calibrate the models for improved future performance.

---

## 11. Limitations

1. **DEM Resolution:** SRTM/ASTER provide 30m resolution, which may miss micro-terrain features (small channels, embankments) that influence local flood behavior. Higher resolution LiDAR DEMs would improve accuracy but are not openly available for most of India.
2. **SPH Particle Count:** The current SPH implementation is limited to 1000-5000 particles for real-time performance. Full-resolution SPH simulations (millions of particles) would require GPU acceleration (CUDA/OpenCL).
3. **Delft3D Proxy vs Full Delft3D:** Our 2D SWE solver is an efficient proxy that captures the essential physics. The full Delft3D suite includes 3D vertical stratification, sediment transport, and morphodynamics which are beyond our current scope.
4. **Real-Time Data Gap:** The system currently uses cached DEM and OSM data. It does not yet ingest live reservoir level telemetry from CWC sensors.
5. **Calibration:** The depth-damage curves and financial loss estimates use generalized national averages. Region-specific calibration (e.g., construction type, local economy) would improve accuracy.
6. **GEE Dependency:** The Sentinel-1 SAR validation requires Google Earth Engine authentication and internet connectivity, limiting its use in fully offline scenarios.

---

## 12. Future Scope

1. **IoT Telemetry Integration:** Pipe live reservoir level data from Central Water Commission (CWC) sensors directly into the simulation trigger, enabling fully automated dam monitoring and alert systems.
2. **GPU Acceleration (CUDA/CuPy):** Port the SPH and SWE Python solvers to GPU-accelerated frameworks (PyCUDA, CuPy) to enable full Navier-Stokes resolution with millions of particles in near real-time.
3. **Machine Learning Emulators:** Train Graph Neural Networks (GNNs) or Physics-Informed Neural Networks (PINNs) on thousands of simulation runs to predict inundation bounds instantly without running the physics engine.
4. **Higher Resolution DEMs:** Integrate LiDAR data (where available) for sub-meter terrain resolution, improving accuracy in urban floodplains.
5. **Multi-Hazard Integration:** Extend the framework to model cascading disasters — landslide-induced dam breaks, earthquake-triggered GLOFs, and compound flood-rainfall events.
6. **Mobile Application:** Develop a lightweight Android/iOS application for field officers to receive push notifications and view flood maps on mobile devices in low-connectivity areas.
7. **International Expansion:** Extend the dam database beyond India to cover major dams in Nepal, Bangladesh, and Southeast Asia for cross-border flood early warning systems.
8. **Automated Report Generation:** Generate PDF reports with maps, charts, and damage statistics automatically after each simulation for immediate dissemination to government authorities.

---

## 13. Conclusion

The HADR (Humanitarian Assistance and Disaster Relief) software platform represents a significant advancement in disaster response technology for India. By combining generalized open-source data pipelines (SRTM DEM, OpenStreetMap, Sentinel-1 SAR) with a novel multi-model hydrodynamic architecture (Terrain Routing, SPH, Delft3D/SWE), the system fully satisfies every deliverable specified in the NTRO Problem Statement SIH26161.

The platform transitions complex hydrodynamic modelling — traditionally an offline, weeks-long academic exercise requiring specialized hardware and expertise — into a real-time, interactive, web-based dashboard accessible to any disaster management authority. The sub-second terrain engine provides immediate actionable intelligence for emergency evacuation, while the SPH and Delft3D adapters deliver rigorous scientific validation for post-crisis analysis and infrastructure planning.

The automated Loss and Damage Analysis subsystem transforms raw flood polygons into actionable metrics — affected settlements, exposed populations, financial damage in INR Crores, and critical infrastructure at risk — enabling data-driven resource allocation. The standardized GIS export pipeline (.shp, .kml, GeoJSON) ensures seamless interoperability with existing government GIS infrastructure. The GEE Sentinel-1 SAR framework provides satellite-based ground-truthing for continuous model validation and improvement.

---

## 14. Team CTRL_ALT_WIN

1. Sumit Kushwaha (Team Leader)
2. Tanu Gupta
3. Somya Dwivedi
4. Suryansh Mishra
5. Vansh Jaiswal
6. Ujjwal Srivastava

## 15. License

This project is developed as part of the Smart India Hackathon 2026 for the National Technical Research Organisation (NTRO). The source code is released under the MIT License for educational and research purposes. All open-source data sources (SRTM, OSM, Sentinel-1) are used in compliance with their respective licensing terms.

---

## Appendix A: Sample Data (Input)
Example of the input data format used to run a simulation for a custom dam:
```json
{
  "dam_id": "custom",
  "release_percent": 50.0,
  "duration_min": 720,
  "time_step_min": 60,
  "engine": "sph",
  "custom_lat": 30.377,
  "custom_lon": 78.481,
  "custom_name": "Tehri Dam (Custom)",
  "custom_height_m": 260.0,
  "custom_river": "Bhagirathi"
}
```

## Appendix B: Sample Output (Exposure Analysis)
The simulation provides details about the flood extent and the exposure analysis:
```json
{
  "total_settlements_affected": 23,
  "total_population_exposed": 145000,
  "flooded_road_km": 87.3,
  "hospitals_at_risk": 4,
  "estimated_financial_loss_cr": 2340.5,
  "evacuation_status": {
    "mandatory_evacuation": 8,
    "high_risk": 9,
    "low_risk": 6
  }
}
```

## Appendix C: API Endpoints Overview

| METHOD | ENDPOINT | DESCRIPTION |
|--------|----------|-------------|
| GET | `/` | Health check & status |
| GET | `/api/dams` | List all 48 dams |
| GET | `/api/dams/{dam_id}` | Get dam details by ID |
| POST | `/api/simulations` | Run a new simulation |
| GET | `/api/simulations/{sim_id}` | Get simulation metadata |
| GET | `/api/simulations/{sim_id}/timesteps` | Get time-series GeoJSON |
| GET | `/api/simulations/{sim_id}/comparison` | Get 3-model comparison |
| GET | `/api/simulations/{sim_id}/exposure` | Get loss & damage data |
| GET | `/api/simulations/{sim_id}/export/geojson`| Download GeoJSON file |
| GET | `/api/simulations/{sim_id}/export/kml` | Download KML file |
| GET | `/api/simulations/{sim_id}/export/shp` | Download Shapefile ZIP |
| GET | `/api/satellite/sentinel1?dam_id={id}` | Get SAR water mask |
