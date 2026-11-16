import os
import json
import hashlib
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from backend.core.db import db
from backend.captions.ass_writer import ass_writer, STYLE_PRESETS
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.ai.language_engine import language_engine
from backend.config import settings
from backend.core.logger import logger

router = APIRouter(prefix="/api/captions", tags=["captions"])

PREVIEWS_DIR = settings.STORAGE_DIR / "previews"
PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/presets", response_model=List[Dict[str, Any]])
async def list_presets():
    async with db.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM caption_presets ORDER BY name ASC")
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["all_caps"] = bool(d["all_caps"])
            d["emoji_enabled"] = bool(d["emoji_enabled"])
            result.append(d)
        return result

@router.post("/presets", response_model=Dict[str, Any])
async def save_preset(preset: Dict[str, Any]):
    p_id = preset.get("preset_id")
    if not p_id:
        raise HTTPException(status_code=400, detail="preset_id is required")

    async with db.get_connection() as conn:
        await conn.execute("""
            INSERT OR REPLACE INTO caption_presets (
                preset_id, name, description, category, font_family, font_size,
                font_weight, text_color, highlight_color, outline_color, outline_width,
                shadow_color, shadow_blur, background_color, border_radius, position,
                words_per_line, animation_style, animation_speed, all_caps, emoji_enabled, line_spacing
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p_id, preset.get("name", "Custom Preset"), preset.get("description", ""),
            preset.get("category", "social"), preset.get("font_family", "Inter"),
            preset.get("font_size", 40), preset.get("font_weight", "800"),
            preset.get("text_color", "#FFFFFF"), preset.get("highlight_color", "#FACC15"),
            preset.get("outline_color", "#000000"), preset.get("outline_width", 3),
            preset.get("shadow_color", "rgba(0,0,0,0.8)"), preset.get("shadow_blur", 4),
            preset.get("background_color", "transparent"), preset.get("border_radius", 0),
            preset.get("position", "bottom"), preset.get("words_per_line", 3),
            preset.get("animation_style", "word_bounce"), preset.get("animation_speed", 1.2),
            1 if preset.get("all_caps") else 0, 1 if preset.get("emoji_enabled") else 0,
            preset.get("line_spacing", 1.2)
        ))
        await conn.commit()

    return preset

@router.post("/preview")
async def generate_libass_preview(payload: Dict[str, Any]):
    """
    Generates an authentic 3-second looping MP4 preview using the EXACT same
    libass and ASS subtitle pipeline as final export.
    Caches previews by hash for instantaneous playback.
    """
    clip_id = payload.get("clip_id")
    preset_data = payload.get("preset") or {}
    sample_text = payload.get("sample_text", "THIS IS HOW YOU CREATE VIRAL HOOKS")
    target_lang = payload.get("language", "en").lower()
    position = payload.get("position", preset_data.get("position", "bottom"))

    # 1. Resolve source video
    source_video = None
    start_time = 0.0

    if clip_id:
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
            clip_row = await cursor.fetchone()
            if clip_row:
                p_id = clip_row["project_id"]
                start_time = float(clip_row["start_time"])
                cur_p = await conn.execute("SELECT source_video_path FROM projects WHERE id = ?", (p_id,))
                p_row = await cur_p.fetchone()
                if p_row and p_row["source_video_path"]:
                    p_path = Path(p_row["source_video_path"])
                    if p_path.is_absolute() and p_path.exists():
                        source_video = p_path
                    elif (settings.ROOT_DIR / p_row["source_video_path"]).exists():
                        source_video = settings.ROOT_DIR / p_row["source_video_path"]
                    elif (settings.STORAGE_DIR / p_row["source_video_path"]).exists():
                        source_video = settings.STORAGE_DIR / p_row["source_video_path"]

    if not source_video or not source_video.exists():
        # Fallback to any available video in uploads or dummy video
        uploads = list(settings.UPLOADS_DIR.glob("*.mp4"))
        if uploads:
            source_video = uploads[0]
            start_time = 10.0
        else:
            source_video = settings.STORAGE_DIR / "test_dummy_src.mp4"
            start_time = 0.0

    # 2. Build 3-second sample words
    if target_lang == "hi":
        preview_text = "यह तरीका आपके वीडियो को वायरल बना देगा हर बार"
    elif target_lang == "hinglish":
        preview_text = "Aise hooks banao jo audience ko scroll stop karwa de"
    else:
        preview_text = sample_text

    tokens = preview_text.split()
    total_preview_dur = 3.0
    tok_dur = total_preview_dur / max(1, len(tokens))

    words = []
    for i, tok in enumerate(tokens):
        words.append({
            "word": tok,
            "start": round(start_time + i * tok_dur, 2),
            "end": round(start_time + (i + 1) * tok_dur, 2),
            "probability": 0.95
        })

    # 3. Compute unique hash
    preset_dict = preset_data if isinstance(preset_data, dict) else {"name": str(preset_data)}
    preset_name = preset_dict.get("name", "MrBeast Bold")
    cache_seed = (
        f"{source_video.name}|{start_time}|{preset_name}|{preview_text}|{position}|"
        f"{preset_dict.get('font_size')}|{preset_dict.get('words_per_line')}|"
        f"{preset_dict.get('all_caps')}|{preset_dict.get('font_family')}|"
        f"{preset_dict.get('highlight_color')}|{preset_dict.get('text_color')}|"
        f"{preset_dict.get('outline_width')}|{preset_dict.get('auto_avoid_hud')}"
    )
    h = hashlib.md5(cache_seed.encode()).hexdigest()[:12]

    slice_hash = hashlib.md5(f"{source_video.name}|{start_time}".encode()).hexdigest()[:10]
    out_orig = PREVIEWS_DIR / f"orig_slice_{slice_hash}.mp4"
    out_preview = PREVIEWS_DIR / f"preview_{h}.mp4"
    ass_file = PREVIEWS_DIR / f"preview_{h}.ass"

    # Fast cache hit
    if out_preview.exists() and out_preview.stat().st_size > 10000:
        return {
            "success": True,
            "preview_url": f"/storage/previews/{out_preview.name}",
            "original_url": f"/storage/previews/{out_orig.name}" if out_orig.exists() else None,
            "duration": total_preview_dur,
            "cached": True
        }

    # 4. Generate exact ASS file
    ass_writer.generate_ass(
        words=words,
        preset=preset_data,
        output_path=ass_file,
        video_width=1080,
        video_height=1920,
        clip_start_offset=start_time,
        position_override=position
    )

    # 5. Render 3-second looping mp4 with FFmpeg libass (ultra-fast preview mode: < 0.2s)
    try:
        ffmpeg_engine.render_clip(
            input_video=source_video,
            start_time=start_time,
            duration=total_preview_dur,
            output_clip=out_preview,
            aspect_ratio="9:16",
            ass_subtitles_path=ass_file,
            normalize_audio=False,
            threads=settings.FFMPEG_THREADS,
            is_preview=True
        )

        # Also render before/original clip (without ASS filter) once per source slice
        if not out_orig.exists():
            ffmpeg_engine.render_clip(
                input_video=source_video,
                start_time=start_time,
                duration=total_preview_dur,
                output_clip=out_orig,
                aspect_ratio="9:16",
                ass_subtitles_path=None,
                normalize_audio=False,
                threads=settings.FFMPEG_THREADS,
                is_preview=True
            )

        return {
            "success": True,
            "preview_url": f"/storage/previews/{out_preview.name}",
            "original_url": f"/storage/previews/{out_orig.name}",
            "duration": total_preview_dur,
            "cached": False
        }
    except Exception as e:
        logger.error(f"Failed to generate libass preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview render failed: {str(e)}")
