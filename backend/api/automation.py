from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from backend.core.db import db
from backend.workers.pipeline import pipeline_worker
from backend.core.logger import logger

router = APIRouter(prefix="/api/automation", tags=["automation"])

class ControlRequest(BaseModel):
    action: str # start | pause | resume | stop
    project_id: str = None

@router.get("/settings", response_model=Dict[str, Any])
async def get_settings():
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM automation_settings WHERE id = 1")
        row = await cursor.fetchone()
        if not row:
            return {}
        d = dict(row)
        d["auto_start"] = bool(d["auto_start"])
        d["auto_generate_metadata"] = bool(d["auto_generate_metadata"])
        d["auto_quality_review"] = bool(d["auto_quality_review"])
        d["auto_publish_youtube"] = bool(d["auto_publish_youtube"])
        return d

@router.post("/settings", response_model=Dict[str, Any])
async def save_settings(data: Dict[str, Any]):
    async with db.get_connection() as conn:
        await conn.execute("""
            UPDATE automation_settings SET
                auto_start = ?,
                clips_per_video = ?,
                min_viral_score = ?,
                min_duration = ?,
                max_duration = ?,
                target_aspect_ratio = ?,
                default_caption_preset = ?,
                output_resolution = ?,
                language = ?,
                auto_generate_metadata = ?,
                auto_quality_review = ?,
                auto_publish_youtube = ?,
                daily_upload_limit = ?,
                publishing_schedule = ?
            WHERE id = 1
        """, (
            1 if data.get("auto_start") else 0,
            data.get("clips_per_video", 5),
            data.get("min_viral_score", 70),
            data.get("min_duration", 15),
            data.get("max_duration", 60),
            data.get("target_aspect_ratio", "9:16"),
            data.get("default_caption_preset", "mrbeast-bold"),
            data.get("output_resolution", "1080p"),
            data.get("language", "en"),
            1 if data.get("auto_generate_metadata") else 0,
            1 if data.get("auto_quality_review") else 0,
            1 if data.get("auto_publish_youtube") else 0,
            data.get("daily_upload_limit", 5),
            data.get("publishing_schedule", "immediate")
        ))
        await conn.commit()
    return data

@router.post("/control")
async def control_automation(req: ControlRequest):
    action = req.action.lower()
    logger.info(f"Automation command received: {action}")
    if action == "start":
        await pipeline_worker.start(req.project_id)
    elif action == "pause":
        await pipeline_worker.pause()
    elif action == "resume":
        await pipeline_worker.resume()
    elif action == "stop":
        await pipeline_worker.stop()
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    return {"status": action, "message": f"Automation factory {action} acknowledged."}
