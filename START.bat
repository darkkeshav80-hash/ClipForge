@echo off
setlocal enabledelayedexpansion
title CLIPFORGE AI - Autonomous Video Factory
color 0B

echo ==============================================================================
echo                 CLIPFORGE AI - AUTONOMOUS VIDEO FACTORY
echo                      One-Command Automatic Startup
echo ==============================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo NOTE: Ensure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

:: 2. Check Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not found in system PATH.
    echo Please install Node.js 18+ from: https://nodejs.org/
    pause
    exit /b 1
)

:: 3. Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg not found in PATH!
    echo FFmpeg is required for 9:16 vertical cropping, zooms and subtitle burn-in.
    echo Download official Windows build from: https://www.gyan.dev/ffmpeg/builds/
    echo.
)

:: 4. Auto-setup .env configuration if missing
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Created default .env configuration file.
    )
)

:: 5. Verify & Install Python Dependencies
echo [1/4] Checking Python packages...
python -c "import fastapi, uvicorn, faster_whisper" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required Python packages (requirements.txt)...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python dependencies.
        pause
        exit /b 1
    )
    echo [OK] Python dependencies ready.
) else (
    echo [OK] Python dependencies verified.
)

:: 6. Verify & Install Frontend Dependencies
echo [2/4] Checking Frontend packages...
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend packages (npm install)...
    cd frontend
    call npm install
    cd ..
    echo [OK] Frontend packages ready.
) else (
    echo [OK] Frontend packages verified.
)

:: 7. Initialize Database & Presets if missing
if not exist "storage\clipforge.db" (
    echo [INFO] Initializing ClipForge database schema and presets...
    python -c "import asyncio; from backend.core.db import db; asyncio.run(db.init_db())"
)

:: 8. Launch Backend Server in background
echo [3/4] Starting ClipForge AI Backend on http://127.0.0.1:8000...
start "ClipForge Backend" /min cmd /c "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

:: 9. Launch Frontend Dev Server
echo [4/4] Starting ClipForge Frontend on http://localhost:3000...
start "ClipForge Frontend" /min cmd /c "cd frontend && npm run dev"

:: 10. Wait 3 seconds and launch browser
timeout /t 3 /nobreak >nul
echo.
echo ==============================================================================
echo                 CLIPFORGE AI IS LIVE AND READY!
echo ==============================================================================
echo App URL:     http://localhost:3000
echo API Docs:    http://127.0.0.1:8000/docs
echo WebSocket:   ws://127.0.0.1:8000/ws/logs
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo Keep this window open or minimize it.
echo To safely stop all ClipForge services, run: STOP.bat
echo ==============================================================================
pause
