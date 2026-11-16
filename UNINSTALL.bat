@echo off
setlocal
title CLIPFORGE AI - Uninstaller
color 0C

echo ==============================================================================
echo                 CLIPFORGE AI - APPLICATION UNINSTALLER
echo ==============================================================================
echo.
echo WARNING: This tool will remove ClipForge AI application files.
echo.
set /p KEEP_DATA="Do you want to PRESERVE your projects, videos, and rendered clips? (Y/N) [Default: Y]: "
if /i "%KEEP_DATA%"=="" set KEEP_DATA=Y

echo.
echo Stopping any running ClipForge processes...
call STOP.bat >nul 2>&1

if /i "%KEEP_DATA%"=="Y" (
    echo.
    echo Preserving 'storage' and 'config' folders...
    echo Removing temporary node_modules, dist, and cache...
    if exist "frontend\node_modules" rd /s /q "frontend\node_modules"
    if exist "frontend\dist" rd /s /q "frontend\dist"
    if exist "storage\temp" rd /s /q "storage\temp"
    echo.
    echo [OK] Temporary artifacts removed. Your project videos and settings remain intact.
) else (
    echo.
    echo Performing complete clean wipe...
    if exist "storage" rd /s /q "storage"
    if exist "frontend\node_modules" rd /s /q "frontend\node_modules"
    if exist "frontend\dist" rd /s /q "frontend\dist"
    if exist "models" rd /s /q "models"
    if exist "logs" rd /s /q "logs"
    echo.
    echo [OK] Complete removal finished.
)

echo.
echo ClipForge uninstallation routine complete.
pause
