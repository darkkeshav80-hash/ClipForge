#!/usr/bin/env bash
# ==============================================================================
# CLIPFORGE AI — One-Command Startup Script for Linux & macOS
# ==============================================================================

set -e

echo "=============================================================================="
echo "                 CLIPFORGE AI - AUTONOMOUS VIDEO FACTORY"
echo "                      One-Command Linux & Mac Setup"
echo "=============================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10+."
    exit 1
fi

# 2. Check Node
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in PATH."
    echo "Please install Node.js 18+."
    exit 1
fi

# 3. Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] ffmpeg not found in PATH."
    echo "FFmpeg is required for 9:16 vertical cropping and subtitle burn-in."
fi

# 4. Auto-setup .env if missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[OK] Created default .env configuration file."
fi

# 5. Virtual Environment & Dependencies
if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment (venv)..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Frontend Dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "[INFO] Installing frontend npm dependencies..."
    (cd frontend && npm install)
fi

# 7. Database Initialization
if [ ! -f "storage/clipforge.db" ]; then
    echo "[INFO] Initializing ClipForge SQLite database schema and presets..."
    python -c "import asyncio; from backend.core.db import db; asyncio.run(db.init_db())"
fi

# 8. Launch Services
echo "[INFO] Starting ClipForge AI Backend on http://127.0.0.1:8000..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "[INFO] Starting ClipForge Frontend on http://localhost:3000..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

sleep 3
echo ""
echo "=============================================================================="
echo "                 CLIPFORGE AI IS RUNNING!"
echo "App URL:   http://localhost:3000"
echo "API Docs:  http://127.0.0.1:8000/docs"
echo "=============================================================================="
echo "Press Ctrl+C to stop all services."

wait
