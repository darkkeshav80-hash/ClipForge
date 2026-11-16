@echo off
setlocal enabledelayedexpansion
title CLIPFORGE AI - Diagnostic & Repair Tool
color 0E

echo ==============================================================================
echo                 CLIPFORGE AI - SYSTEM DIAGNOSTIC & REPAIR
echo ==============================================================================
echo.

echo [1/4] Checking filesystem folders...
for %%d in (storage storage\uploads storage\clips storage\thumbnails storage\captions storage\temp models logs config) do (
    if not exist "%%d" (
        echo Creating missing directory: %%d
        mkdir "%%d"
    )
)
echo [OK] Storage directories verified.

echo.
echo [2/4] Verifying Python package integrity...
python -m pip check >nul 2>&1
if %errorlevel% neq 0 (
    echo Re-installing required Python dependencies...
    python -m pip install -r requirements.txt
) else (
    echo [OK] Python dependencies sound.
)

echo.
echo [3/4] Re-indexing and repairing SQLite database tables...
python -c "import asyncio; from backend.core.db import db; asyncio.run(db.init_db())"
if %errorlevel% equ 0 (
    echo [OK] Database schema and presets successfully repaired.
) else (
    echo [ERROR] Database repair encountered an error. Check logs\clipforge.log.
)

echo.
echo [4/4] Verifying configuration files...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Restored default .env file.
    )
)

echo.
echo ==============================================================================
echo                  DIAGNOSTIC & REPAIR ROUTINE FINISHED
echo ==============================================================================
echo Run START.bat to launch ClipForge AI.
echo.
pause
