from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dams, simulation, export, exposure, satellite

app = FastAPI(
    title="Humanitarian Flood & Dam-Break Simulation API",
    description="Backend service for 2-Day HADR Flood Propagation Prototype (Tehri Dam / Bhagirathi Valley)",
    version="1.0.0"
)

# Enable CORS for Next.js / React frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(dams.router)
app.include_router(simulation.router)
app.include_router(exposure.router)
app.include_router(export.router)
app.include_router(satellite.router)

@app.get("/")
def root():
    return {
        "title": "Humanitarian Flood & Dam-Break Simulation API",
        "status": "online",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
