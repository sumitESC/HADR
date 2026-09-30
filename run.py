#!/usr/bin/env python3
"""
HADR Flood Simulation & Dam-Break Analysis Platform
Unified Runner Script - Launches Backend (FastAPI) and Frontend (Vite React)
"""

import sys
import os
import subprocess
import time
import webbrowser
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

processes = []

def cleanup(signum=None, frame=None):
    """Clean up running subprocesses on exit."""
    print("\n\033[93m[HADR Platform]\033[0m Shutting down backend and frontend servers...")
    for proc in processes:
        if proc.poll() is None:
            try:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            except Exception as e:
                print(f"Error terminating process {proc.pid}: {e}")
    print("\033[92m[HADR Platform]\033[0m Cleanup complete. Goodbye!")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    print("=" * 70)
    print("\033[94m  HADR Flood Simulation & Dam-Break Analysis Platform\033[0m")
    print("  Safer Communities • Stronger Resilience • Open-Source Data")
    print("=" * 70)

    # 1. Start Backend FastAPI Server
    print("\n\033[96m[1/2] Starting Backend FastAPI Server...\033[0m")
    print("  • Directory:", BACKEND_DIR)
    print("  • URL: http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)")
    
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            shell=False
        )
        processes.append(backend_proc)
    except Exception as err:
        print(f"\033[91m[Error]\033[0m Failed to start backend: {err}")
        sys.exit(1)

    time.sleep(2)

    # 2. Start Frontend Vite Dev Server
    print("\n\033[96m[2/2] Starting Frontend Vite App...\033[0m")
    print("  • Directory:", FRONTEND_DIR)
    print("  • URL: http://localhost:5173/")

    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    
    try:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            shell=os.name == "nt"
        )
        processes.append(frontend_proc)
    except Exception as err:
        print(f"\033[91m[Error]\033[0m Failed to start frontend: {err}")
        cleanup()
        sys.exit(1)

    print("\n\033[92m[✓] System Running!\033[0m Press \033[97mCtrl+C\033[0m to stop all servers.")
    print("----------------------------------------------------------------------")

    # Open browser automatically after 2 seconds
    time.sleep(2)
    webbrowser.open("http://localhost:5173/")

    # Keep script running to handle signals and monitoring
    try:
        while True:
            time.sleep(1)
            # Check if any process crashed unexpectedly
            for p in processes:
                if p.poll() is not None:
                    print("\n\033[91m[Warning]\033[0m One of the services exited. Shutting down...")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
