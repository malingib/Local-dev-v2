#!/usr/bin/env python3
"""
Run CodeAudit with the web console.
Usage: python run.py [--dev]

  --dev   Run frontend on Vite dev server (port 5173) with hot reload
          Backend runs on port 8000
  (default)  Build frontend and serve everything from port 8000
"""
import sys
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT.parent / "app"

def run_dev():
    """Run backend and frontend dev servers concurrently."""
    print("=" * 60)
    print("CodeAudit - Development Mode")
    print("=" * 60)
    print()
    print("Backend:  http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print()
    print("Press Ctrl+C to stop both servers.")
    print()

    # Check API keys
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("⚠  No .env file found. Copy .env.example to .env and add API keys.")
        print(f"   cp {ROOT}/.env.example {ROOT}/.env")
        sys.exit(1)

    # Start backend
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=str(ROOT),
    )

    # Wait for backend to start
    time.sleep(2)

    # Start frontend dev server
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(APP_DIR),
    )

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()

def run_prod():
    """Build frontend and run backend only."""
    print("=" * 60)
    print("CodeAudit - Production Mode")
    print("=" * 60)
    print()

    # Check API keys
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("⚠  No .env file found. Copy .env.example to .env and add API keys.")
        print(f"   cp {ROOT}/.env.example {ROOT}/.env")
        sys.exit(1)

    # Build frontend
    print("Building frontend...")
    build_script = ROOT / "build_frontend.py"
    if build_script.exists():
        result = subprocess.run([sys.executable, str(build_script)], cwd=str(ROOT))
        if result.returncode != 0:
            print("⚠  Frontend build failed. Continuing with backend only.")
    print()

    # Start backend (which will serve frontend)
    print("Backend:  http://localhost:8000")
    print()
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT),
    )

if __name__ == "__main__":
    dev_mode = "--dev" in sys.argv
    if dev_mode:
        run_dev()
    else:
        run_prod()
