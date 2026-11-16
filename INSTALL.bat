@echo off
setlocal enabledelayedexpansion
title CLIPFORGE AI - Windows Installer
color 0B

echo ==============================================================================
echo                 CLIPFORGE AI - AUTONOMOUS VIDEO FACTORY
echo                      One-Click Windows Setup
echo ==============================================================================
echo.

:: 1. Check Operating System
echo [1/6] Verifying Windows Environment...
ver | findstr /i "Windows" >nul
if %errorlevel% neq 0 (
    echo [ERROR] CLIPFORGE AI installer requires Windows 10 or Windows 11.
    pause
    exit /b 1
)
echo [OK] Windows OS detected.

:: 2. Check Python
echo.
echo [2/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo NOTE: Ensure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [OK] Python %PY_VER% found.

:: 3. Check Node.js & npm
echo.
echo [3/6] Checking Node.js installation...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not found in system PATH.
    echo Please install Node.js 18+ from: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1" %%i in ('node -v 2^>^&1') do set NODE_VER=%%i
echo [OK] Node.js %NODE_VER% found.

:: 4. Check FFmpeg
echo.
echo [4/6] Checking FFmpeg video processing engine...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg not found in PATH!
    echo FFmpeg is required for 9:16 vertical cropping, smart zooms and subtitle burn-in.
    echo Download official Windows build from: https://www.gyan.dev/ffmpeg/builds/
    echo Extract to C:\ffmpeg and add C:\ffmpeg\bin to your Windows PATH environment variable.
    echo.
) else (
    echo [OK] FFmpeg engine detected on PATH.
)

:: 5. Install Python Dependencies
echo.
echo [5/6] Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install required Python packages.
    pause
    exit /b 1
)
echo [OK] Python packages installed.

:: 6. Setup Frontend & Initialize Database
echo.
echo [6/6] Initializing Frontend & Database...
if exist "frontend" (
    cd frontend
    echo Installing npm dependencies...
    call npm install
    echo Building production frontend bundle...
    call npm run build
    cd ..
)

echo Initializing local SQLite database and 22 caption presets...
python -c "import asyncio; from backend.core.db import db; asyncio.run(db.init_db())"

if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Created default .env configuration.
    )
)

echo.
echo ==============================================================================
echo          INSTALLATION COMPLETE! CLIPFORGE AI IS READY TO RUN
echo ==============================================================================
echo.
echo To launch the factory, double-click: START.bat
echo Access dashboard at: http://localhost:8000 or http://localhost:3000
echo.
pause
