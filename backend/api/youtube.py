from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from backend.publishing.youtube_client import youtube_client
from backend.core.db import db
from backend.config import settings

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

class PublishRequest(BaseModel):
    clip_id: str
    title: str
    description: str
    tags: List[str] = []
    privacy: str = "public"
    schedule_time: Optional[str] = None

@router.get("/status", response_model=Dict[str, Any])
async def get_youtube_status():
    return youtube_client.get_status()

@router.post("/publish")
async def publish_short_endpoint(req: PublishRequest):
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
        clip = await cursor.fetchone()

    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    clip_dict = dict(clip)
    rendered_path = clip_dict.get("rendered_path")
    if not rendered_path:
        raise HTTPException(status_code=400, detail="Clip has not been rendered yet. Please render before publishing.")

    full_video_path = settings.STORAGE_DIR / rendered_path

    res = await youtube_client.upload_short(
        video_path=full_video_path,
        title=req.title,
        description=req.description,
        tags=req.tags,
        privacy=req.privacy,
        schedule_time=req.schedule_time
    )

    # Record upload in DB
    async with db.get_connection() as conn:
        await conn.execute("""
            UPDATE clips SET
                youtube_published = 1,
                youtube_video_id = ?,
                youtube_url = ?
            WHERE id = ?
        """, (res.get("video_id"), res.get("url"), req.clip_id))
        await conn.commit()

    return res
