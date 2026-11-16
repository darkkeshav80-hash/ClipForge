import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.config import settings
from backend.core.security import validate_video_extension, sanitize_filename
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.core.logger import logger

router = APIRouter(prefix="/api/videos", tags=["videos"])

class URLImportRequest(BaseModel):
    url: str

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    validate_video_extension(file.filename)
    safe_name = sanitize_filename(file.filename)
    
    # Save to uploads directory
    target_path = settings.UPLOADS_DIR / safe_name
    
    # Write in chunks
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    # Extract probe information
    try:
        probe = ffmpeg_engine.probe_video(target_path)
    except Exception as e:
        logger.warning(f"FFprobe failed on uploaded video: {e}")
        probe = {"duration": 60.0, "width": 1920, "height": 1080, "fps": 30.0}

    # Extract thumbnail
    thumb_name = f"{Path(safe_name).stem}_thumb.jpg"
    thumb_path = settings.THUMBNAILS_DIR / thumb_name
    try:
        ffmpeg_engine.extract_thumbnail(target_path, 1.0, thumb_path)
    except Exception:
        pass

    rel_video_path = str(target_path.relative_to(settings.ROOT_DIR)).replace("\\", "/")
    rel_thumb_path = str(thumb_path.relative_to(settings.STORAGE_DIR)).replace("\\", "/")

    return {
        "path": rel_video_path,
        "filename": file.filename,
        "duration": probe["duration"],
        "width": probe["width"],
        "height": probe["height"],
        "fps": probe["fps"],
        "thumbnail_path": rel_thumb_path,
    }

@router.post("/import-url")
async def import_url(req: URLImportRequest):
    url = req.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL scheme. Must start with http:// or https://")

    logger.info(f"Downloading video from URL via yt-dlp: {url}")
    
    try:
        import yt_dlp
        outtmpl = str(settings.UPLOADS_DIR / "%(title).50s-%(id)s.%(ext)s")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)
            p = Path(downloaded)
            if not p.exists() and p.with_suffix('.mp4').exists():
                p = p.with_suffix('.mp4')

        # Probe the downloaded video
        try:
            probe = ffmpeg_engine.probe_video(p)
        except Exception as e:
            logger.warning(f"FFprobe failed on downloaded video: {e}")
            probe = {"duration": info.get("duration", 60.0), "width": 1920, "height": 1080, "fps": 30.0}

        # Extract thumbnail
        thumb_name = f"{p.stem}_thumb.jpg"
        thumb_path = settings.THUMBNAILS_DIR / thumb_name
        try:
            ffmpeg_engine.extract_thumbnail(p, 1.0, thumb_path)
        except Exception:
            pass

        rel_video_path = str(p.relative_to(settings.ROOT_DIR)).replace("\\", "/")
        rel_thumb_path = str(thumb_path.relative_to(settings.STORAGE_DIR)).replace("\\", "/")

        return {
            "title": info.get("title", p.stem),
            "filename": p.name,
            "path": rel_video_path,
            "video_path": rel_video_path,
            "duration": probe["duration"],
            "width": probe["width"],
            "height": probe["height"],
            "fps": probe["fps"],
            "thumbnail_path": rel_thumb_path,
        }
    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download video from URL: {str(e)}")
