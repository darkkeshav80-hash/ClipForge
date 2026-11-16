import os
import time
from pathlib import Path
from fastapi import APIRouter
from typing import Dict, Any
from backend.core.hardware import hardware_monitor
from backend.config import settings
from backend.core.logger import logger

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/settings", response_model=Dict[str, Any])
async def get_system_settings():
    hw = hardware_monitor.get_hardware_info()
    return {
        "hardware": {
            "profile": settings.HARDWARE_PROFILE,
            "max_ram_usage_gb": 12,
            "ffmpeg_threads": settings.FFMPEG_THREADS,
            "analysis_resolution": "480p",
            "whisper_model": settings.DEFAULT_WHISPER_MODEL,
            "enable_gpu": settings.ENABLE_GPU_ACCELERATION,
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
        },
        "detected_hardware": hw,
        "storage": {
            "root": str(settings.STORAGE_DIR),
        },
        "low_performance_mode": False,
    }

@router.post("/settings")
async def update_system_settings(data: Dict[str, Any]):
    hw = data.get("hardware", {})
    if "profile" in hw:
        settings.HARDWARE_PROFILE = hw["profile"]
    if "ffmpeg_threads" in hw:
        settings.FFMPEG_THREADS = int(hw["ffmpeg_threads"])
    if "whisper_model" in hw:
        settings.DEFAULT_WHISPER_MODEL = hw["whisper_model"]
    if "enable_gpu" in hw:
        settings.ENABLE_GPU_ACCELERATION = bool(hw["enable_gpu"])
    logger.info(f"Updated system settings: Hardware Profile={settings.HARDWARE_PROFILE}, Threads={settings.FFMPEG_THREADS}")
    return {"success": True}

@router.post("/cleanup")
async def storage_cleanup(data: Dict[str, Any]):
    days_old = data.get("days_old", 7)
    cutoff = time.time() - (days_old * 86400)
    freed_bytes = 0

    # Purge temp folder
    temp_dir = settings.TEMP_DIR
    if temp_dir.exists():
        for f in temp_dir.glob("*"):
            if f.is_file() and f.stat().st_mtime < cutoff:
                freed_bytes += f.stat().st_size
                f.unlink(missing_ok=True)

    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    logger.info(f"Storage cleanup: purged temp files older than {days_old} days, freed {freed_mb} MB")
    return {"success": True, "freed_mb": freed_mb, "message": f"Freed {freed_mb} MB from temp cache"}
