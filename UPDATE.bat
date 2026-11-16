@echo off
setlocal enabledelayedexpansion
title CLIPFORGE AI - Updater
color 0E

echo ==============================================================================
echo                 CLIPFORGE AI - SAFE APPLICATION UPDATER
echo ==============================================================================
echo.
echo Preserving your projects, rendered clips, and API keys...

:: Git pull if git repository
if exist ".git" (
    echo Pulling latest updates from Git...
    git pull
)

:: Update Python packages
echo Updating Python requirements...
python -m pip install -r requirements.txt --upgrade

:: Update & Rebuild Frontend
if exist "frontend" (
    echo Updating frontend packages...
    cd frontend
    call npm install
    echo Rebuilding optimized frontend bundle...
    call npm run build
    cd ..
)

:: Re-apply any new database schema migrations
echo Migrating database tables...
python -c "import asyncio; from backend.core.db import db; asyncio.run(db.init_db())"

echo.
echo ==============================================================================
echo         UPDATE COMPLETE! Your data & credentials remain safe.
echo ==============================================================================
echo Run START.bat to launch updated ClipForge AI.
echo.
pause
