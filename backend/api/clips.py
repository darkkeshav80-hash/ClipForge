import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.db import db
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.captions.ass_writer import ass_writer
from backend.captions.sync_validator import sync_validator
from backend.ai.language_engine import language_engine
from backend.config import settings
from backend.core.logger import logger, PipelineLogEmitter

router = APIRouter(prefix="/api/clips", tags=["clips"])

def parse_clip_row(row: Any) -> Dict[str, Any]:
    c = dict(row)
    c["viral_score"] = json.loads(c.get("viral_score_json") or "{}")
    c["editing_plan"] = json.loads(c.get("editing_plan_json") or "{}")
    c["review_verdict"] = json.loads(c.get("review_verdict_json") or "{}") if c.get("review_verdict_json") else None
    return c

@router.get("", response_model=List[Dict[str, Any]])
async def list_clips(project_id: Optional[str] = Query(None)):
    async with db.get_connection() as conn:
        if project_id:
            cursor = await conn.execute("SELECT * FROM clips WHERE project_id = ? ORDER BY start_time ASC", (project_id,))
        else:
            cursor = await conn.execute("SELECT * FROM clips ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [parse_clip_row(r) for r in rows]

@router.get("/{clip_id}", response_model=Dict[str, Any])
async def get_clip(clip_id: str):
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Clip not found")
        return parse_clip_row(row)

@router.patch("/{clip_id}", response_model=Dict[str, Any])
async def update_clip(clip_id: str, updates: Dict[str, Any]):
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Clip not found")

        current = dict(row)
        title = updates.get("title", current["title"])
        start_time = updates.get("start_time", current["start_time"])
        end_time = updates.get("end_time", current["end_time"])
        duration = updates.get("duration", end_time - start_time)
        caption_preset = updates.get("caption_preset", current["caption_preset"])
        aspect_ratio = updates.get("aspect_ratio", current["aspect_ratio"])

        editing_plan = updates.get("editing_plan")
        plan_json = json.dumps(editing_plan) if editing_plan else current["editing_plan_json"]

        await conn.execute("""
            UPDATE clips SET
                title = ?, start_time = ?, end_time = ?, duration = ?,
                caption_preset = ?, aspect_ratio = ?, editing_plan_json = ?
            WHERE id = ?
        """, (title, start_time, end_time, duration, caption_preset, aspect_ratio, plan_json, clip_id))
        await conn.commit()

    return await get_clip(clip_id)





@router.delete("/{clip_id}")
async def delete_clip(clip_id: str):
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT project_id, rendered_path, thumbnail_path FROM clips WHERE id = ?", (clip_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Clip not found")

        project_id = row["project_id"]

        if row["rendered_path"]:
            p = settings.STORAGE_DIR / row["rendered_path"]
            if p.exists():
                p.unlink(missing_ok=True)
        if row["thumbnail_path"]:
            t = settings.STORAGE_DIR / row["thumbnail_path"]
            if t.exists():
                t.unlink(missing_ok=True)

        await conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        if project_id:
            await conn.execute("""
                UPDATE projects SET clips_count = (
                    SELECT COUNT(*) FROM clips WHERE project_id = ?
                ) WHERE id = ?
            """, (project_id, project_id))
        await conn.commit()

    return {"success": True, "message": f"Clip {clip_id} deleted."}
