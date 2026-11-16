@echo off
title CLIPFORGE AI - Shutdown
color 0C

echo ==============================================================================
echo                 STOPPING CLIPFORGE AI VIDEO FACTORY
echo ==============================================================================
echo.

echo Terminating running ClipForge background processes...

:: Kill processes running on port 8000 and 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Terminating Backend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo Terminating Frontend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] All ClipForge AI services have been stopped safely.
echo.
pause
