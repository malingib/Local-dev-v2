#!/usr/bin/env bash
set -e

# CodeAudit Desktop - Production mode startup
# Starts the Python backend and runs the Electron app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== CodeAudit Desktop ==="

# Check if frontend is built
if [ ! -d "$PROJECT_DIR/app/dist" ]; then
  echo "[!] Frontend not built. Building..."
  cd "$PROJECT_DIR/app"
  npx vite build
fi

# Check if Electron is installed
if [ ! -d "$SCRIPT_DIR/node_modules/electron" ]; then
  echo "[!] Electron not installed. Installing..."
  cd "$SCRIPT_DIR"
  npm install
fi

# Start backend
echo "[1/2] Starting backend..."
cd "$PROJECT_DIR/codeaudit"
python3 -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 2

# Start Electron
echo "[2/2] Starting Electron app..."
cd "$SCRIPT_DIR"
npx electron .

# Cleanup
kill $BACKEND_PID 2>/dev/null
