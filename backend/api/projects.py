import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from backend.core.db import db
from backend.core.logger import logger

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_projects():
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str):
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return dict(row)

@router.post("", response_model=Dict[str, Any])
async def create_project(data: Dict[str, Any]):
    project_id = data.get("id") or f"proj-{int(datetime.now().timestamp())}"
    now = datetime.now().isoformat()
    caption_preset = data.get("caption_preset", "mrbeast")
    
    target_clips = int(data.get("target_clips") or data.get("clips_count") or 3)
    min_viral_score = int(data.get("min_viral_score", 70))
    min_duration = float(data.get("min_duration", 15.0))
    max_duration = float(data.get("max_duration", 60.0))
    
    async with db.get_connection() as conn:
        await conn.execute("""
            INSERT OR REPLACE INTO projects (
                id, name, description, source_video_path, source_url, thumbnail_path,
                duration, width, height, fps, status, stage_progress, total_progress,
                clips_count, target_clips, min_viral_score, min_duration, max_duration,
                caption_preset, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            data.get("name", "Untitled Project"),
            data.get("description", ""),
            data.get("source_video_path", ""),
            data.get("source_url", ""),
            data.get("thumbnail_path", ""),
            data.get("duration", 0.0),
            data.get("width", 1920),
            data.get("height", 1080),
            data.get("fps", 30.0),
            data.get("status", "idle"),
            0.0, 0.0, 0, target_clips, min_viral_score, min_duration, max_duration,
            caption_preset, now, now
        ))
        await conn.commit()
    
    return await get_project(project_id)

@router.post("/{project_id}/apply-captions")
async def apply_captions_to_project(project_id: str, data: Dict[str, Any]):
    """Applies caption preset & positioning to all clips in the project and re-renders them."""
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT id FROM clips WHERE project_id = ?", (project_id,))
        rows = await cursor.fetchall()

    if not rows:
        return {"success": True, "message": "No clips found in project to update.", "updated_count": 0}

    from backend.api.clips import change_caption_language
    updated_count = 0
    for r in rows:
        try:
            await change_caption_language(r["id"], data)
            updated_count += 1
        except Exception as e:
            logger.warning(f"Failed to apply captions to clip {r['id']}: {e}")

    return {
        "success": True,
        "message": f"Successfully updated and re-rendered {updated_count} clips in project {project_id}!",
        "updated_count": updated_count
    }


@router.patch("/{project_id}", response_model=Dict[str, Any])
async def update_project(project_id: str, data: Dict[str, Any]):
    fields = []
    values = []
    for k in ["name", "description", "caption_preset", "status"]:
        if k in data:
            fields.append(f"{k} = ?")
            values.append(data[k])
    if fields:
        values.append(datetime.now().isoformat())
        values.append(project_id)
        sql = f"UPDATE projects SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
        async with db.get_connection() as conn:
            await conn.execute(sql, tuple(values))
            await conn.commit()
    return await get_project(project_id)

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    async with db.get_connection() as conn:
        await conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await conn.commit()
    return {"success": True, "message": f"Project {project_id} deleted."}
    return {"success": True, "message": f"Project {project_id} deleted."}
