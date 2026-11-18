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





async def render_clip_by_id(clip_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Renders or re-renders an individual clip with updated preset, crop, or aspect ratio."""
    opts = options or {}
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
        clip_row = await cursor.fetchone()
        if not clip_row:
            raise HTTPException(status_code=404, detail=f"Clip {clip_id} not found")

        clip = dict(clip_row)
        p_cursor = await conn.execute("SELECT source_video_path FROM projects WHERE id = ?", (clip["project_id"],))
        p_row = await p_cursor.fetchone()
        if not p_row or not p_row["source_video_path"]:
            raise HTTPException(status_code=400, detail="Source video path not found for clip's project")

        p_str = p_row["source_video_path"]
        p_path = Path(p_str)
        if p_path.is_absolute() and p_path.exists():
            source_video = p_path
        elif (settings.ROOT_DIR / p_str).exists():
            source_video = settings.ROOT_DIR / p_str
        elif (settings.STORAGE_DIR / p_str).exists():
            source_video = settings.STORAGE_DIR / p_str
        elif (settings.UPLOADS_DIR / p_path.name).exists():
            source_video = settings.UPLOADS_DIR / p_path.name
        else:
            raise HTTPException(status_code=404, detail=f"Source video file not found: {p_str}")

    preset_name = opts.get("caption_preset") or opts.get("preset") or clip.get("caption_preset") or "mrbeast"
    target_aspect = opts.get("aspect_ratio") or clip.get("aspect_ratio") or "9:16"

    # Load preset details
    async with db.get_connection() as conn:
        c = await conn.execute("SELECT * FROM caption_presets WHERE preset_id = ?", (preset_name,))
        pres_row = await c.fetchone()
    preset_conf = dict(pres_row) if pres_row else {"name": preset_name, "position": "bottom"}

    # Determine canvas dimensions
    if target_aspect == "9:16":
        out_w, out_h = 1080, 1920
    elif target_aspect == "1:1":
        out_w, out_h = 1080, 1080
    else:
        out_w, out_h = 1920, 1080

    editing_plan = json.loads(clip.get("editing_plan_json") or "{}")
    kws = editing_plan.get("keywords", [])

    # Extract words from transcript if not stored directly
    transcript_text = clip.get("transcript", "")
    words = []
    dur = float(clip["duration"])
    toks = transcript_text.split()
    tok_dur = dur / max(1, len(toks))
    for i, tok in enumerate(toks):
        words.append({
            "word": tok,
            "start": round(clip["start_time"] + i * tok_dur, 2),
            "end": round(clip["start_time"] + (i + 1) * tok_dur, 2)
        })

    ass_path = settings.CAPTIONS_DIR / f"{clip_id}.ass"
    ass_writer.generate_ass(
        words=words,
        preset=preset_conf,
        output_path=ass_path,
        video_width=out_w,
        video_height=out_h,
        clip_start_offset=float(clip["start_time"]),
        keywords=kws,
        title=clip.get("title", "")
    )

    output_clip_path = settings.CLIPS_DIR / f"{clip_id}_rendered.mp4"
    thumb_path = settings.THUMBNAILS_DIR / f"{clip_id}_thumb.jpg"

    # Analyze speakers for face centering
    speaker_analysis = face_tracker.analyze_speakers(source_video, float(clip["start_time"]), dur)
    crop_center_x = speaker_analysis["single_center_x"]
    speaker_layout = speaker_analysis["layout"]
    left_c = speaker_analysis["left_center_x"]
    right_c = speaker_analysis["right_center_x"]

    punch_moments = calculate_punch_moments(
        words=words,
        clip_start_offset=float(clip["start_time"]),
        duration=dur,
        keywords=kws
    )

    rendered_path, fallback_used, render_warn = ffmpeg_engine.render_clip(
        input_video=source_video,
        start_time=float(clip["start_time"]),
        duration=dur,
        output_clip=output_clip_path,
        aspect_ratio=target_aspect,
        crop_center_x=crop_center_x,
        layout=speaker_layout,
        left_center_x=left_c,
        right_center_x=right_c,
        punch_moments=punch_moments,
        zoom_in=bool(editing_plan.get("smart_zoom", True)),
        ass_subtitles_path=ass_path,
        normalize_audio=True,
        threads=settings.FFMPEG_THREADS,
    )

    ffmpeg_engine.extract_thumbnail(output_clip_path, 0.5, thumb_path)

    rel_clip = str(output_clip_path.resolve().relative_to(settings.STORAGE_DIR.resolve())).replace("\\", "/")
    rel_thumb = str(thumb_path.resolve().relative_to(settings.STORAGE_DIR.resolve())).replace("\\", "/")

    async with db.get_connection() as conn:
        await conn.execute("""
            UPDATE clips SET
                rendered_path = ?,
                thumbnail_path = ?,
                caption_preset = ?,
                aspect_ratio = ?,
                status = 'ready'
            WHERE id = ?
        """, (rel_clip, rel_thumb, preset_name, target_aspect, clip_id))
        await conn.commit()

    return {
        "success": True,
        "clip_id": clip_id,
        "rendered_path": rel_clip,
        "thumbnail_path": rel_thumb,
        "warning": render_warn,
        "message": f"Clip {clip_id} successfully re-rendered."
    }

@router.post("/{clip_id}/render")
async def render_clip_endpoint(clip_id: str, options: Optional[Dict[str, Any]] = None):
    return await render_clip_by_id(clip_id, options)

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
