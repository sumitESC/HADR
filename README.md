# Dam Break Inundation Modelling & Scenario Generation — HADR

> A Generalized Hydrodynamic Framework for Humanitarian Assistance and Disaster Relief (HADR) using Multi-Model Flood Simulation, Loss & Damage Analysis, and Near Real-Time Satellite Validation.

**Project Type:** Software / GIS / Disaster Management  
**Problem Statement:** SIH26161 — Dam Break Inundation Modelling Using Hydrodynamic Modelling of any River (NTRO)  
**Team:** CTRL_ALT_WIN (SIH 2026)  

---

## 📖 Abstract

Flash floods triggered by catastrophic dam failures or natural lake bursts present an acute threat to downstream catchments across India. During a crisis, decision-makers need to rapidly estimate the volume of water release, the spatial extent of inundation, the propagation velocity, and the exact settlements, roads, hospitals, and bridges at risk. 

This project introduces **HADR**, a comprehensive, generalized simulation framework that automates dam-break inundation modelling for any river system in India. The platform dynamically ingests open-source Digital Elevation Models (SRTM/ASTER), hydrological vector data from OpenStreetMap, and Sentinel-1 SAR imagery via Google Earth Engine.

To balance emergency speed with scientific accuracy, the software implements a novel tri-model architecture:
1. A blazing-fast physics-based **Terrain Routing Engine** for sub-second emergency predictions.
2. A **Smooth Particle Hydrodynamics (SPH)** adapter implementing Lagrangian Navier-Stokes equations.
3. A **Delft3D proxy** implementing 2D Shallow Water Equations.

The system further automates end-to-end **Loss and Damage Analysis** and provides standard GIS exports (.shp, .kml, GeoJSON).

---

## 🎯 Key Features

- **Multi-Model Architecture:** Compare Terrain Routing, SPH, and Delft3D (SWE) predictions in real-time.
- **Automated Loss & Damage:** Computes financial exposure, exposed populations, and critical infrastructure at risk.
- **Real-Time Satellite Verification:** Integrates with Google Earth Engine using Sentinel-1 SAR.
- **Universal Dam Support:** Ships with 48 pre-loaded Indian dams and supports dynamic simulation for any custom dam worldwide.
- **Dashboard GUI:** Interactive React/MapLibre WebGL dashboard with side-by-side comparisons.
- **Standard GIS Outputs:** Export results seamlessly to `.shp`, `.kml`, and `GeoJSON`.

---

## 🛠 Technology Stack

- **Frontend:** React 19, MapLibre GL JS (WebGL), Tailwind CSS, Vite
- **Backend:** FastAPI (Python 3.10+), NumPy, SciPy, Rasterio, Shapely
- **OSM Processing:** Java Osmosis, pyosmium
- **Satellite Integration:** Google Earth Engine (ee API)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js (v18+)
- Java (for Osmosis processing)

### 1. Clone the Repository
```bash
git clone https://github.com/CTRL-ALT-WIN/HADR.git
cd HADR
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend Setup
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
npm install
```

### 4. Run the Application
You can run both backend and frontend servers using the unified runner script:
```bash
python run.py
```
This will start the FastAPI backend on `http://127.0.0.1:8000` and the Vite React frontend on `http://localhost:5173/`.

---

## 🧠 System Architecture

The HADR platform utilizes three core hydrodynamic engines:

1. **Terrain Routing Engine:** Physics-based slope routing using broad-crested weir breach hydrograph. Generates inundation bounds in under 1 second.
2. **SPH Solver:** Lagrangian particle-based Navier-Stokes solver with cKDTree spatial partitioning and Monaghan Artificial Viscosity.
3. **Delft3D Proxy (2D SWE):** Eulerian grid-based 2D Shallow Water Equation solver with Lax-Friedrichs shock stabilization and adaptive CFL time-stepping.

---

## 🤝 Team CTRL_ALT_WIN

- **Sumit Kushwaha** (Team Leader)
- **Tanu Gupta**
- **Somya Dwivedi**
- **Suryansh Mishra**
- **Vansh Jaiswal**
- **Ujjwal Srivastava**

---

## 📄 License

This project is developed as part of the Smart India Hackathon 2026 for the National Technical Research Organisation (NTRO). The source code is released under the MIT License for educational and research purposes. All open-source data sources (SRTM, OSM, Sentinel-1) are used in compliance with their respective licensing terms.
