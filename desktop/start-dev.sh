#!/usr/bin/env bash
set -e

# CodeAudit Desktop - Dev mode startup
# Starts the Python backend and React frontend simultaneously

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== CodeAudit Desktop Dev ==="

# Start backend
echo "[1/3] Starting Python backend..."
cd "$PROJECT_DIR/codeaudit"
python3 -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "[2/3] Starting React frontend..."
cd "$PROJECT_DIR/app"
npx vite --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!

# Wait for both
echo "[3/3] Both servers starting..."
echo "  Backend:  http://127.0.0.1:8000"
echo "  Frontend: http://127.0.0.1:5173"
echo ""
echo "Press Ctrl+C to stop both"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
