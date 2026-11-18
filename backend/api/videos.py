from pathlib import Path
import subprocess
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.config import settings
from backend.core.security import validate_video_extension, unique_filename, validate_public_url
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.core.logger import logger

router = APIRouter(prefix="/api/videos", tags=["videos"])

class URLImportRequest(BaseModel):
    url: str
    live_clip_minutes: Optional[int] = 10
    live_mode: Optional[str] = "last"

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    validate_video_extension(file.filename)
    safe_name = unique_filename(file.filename)
    target_path = settings.UPLOADS_DIR / safe_name

    # Stream to disk in chunks, enforcing a size limit
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    written = 0
    try:
        with open(target_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(status_code=413, detail=f"File too large. Limit is {settings.MAX_UPLOAD_MB} MB.")
                buffer.write(chunk)
    except HTTPException:
        target_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    # Extract probe information: reject files ffprobe can't read instead of inventing metadata
    try:
        probe = ffmpeg_engine.probe_video(target_path)
    except Exception as e:
        logger.warning(f"FFprobe failed on uploaded video: {e}")
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Could not read this file as a video. It may be corrupt or not a real video.")

    # Extract thumbnail
    thumb_name = f"{Path(safe_name).stem}_thumb.jpg"
    thumb_path = settings.THUMBNAILS_DIR / thumb_name
    try:
        ffmpeg_engine.extract_thumbnail(target_path, 1.0, thumb_path)
    except Exception:
        pass

    rel_video_path = str(target_path.resolve().relative_to(settings.ROOT_DIR.resolve())).replace("\\", "/")
    rel_thumb_path = str(thumb_path.resolve().relative_to(settings.STORAGE_DIR.resolve())).replace("\\", "/")

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
    url = validate_public_url(req.url.strip())

    logger.info(f"Downloading video from URL via yt-dlp: {url}")
    
    try:
        import yt_dlp
        
        # 1. Probe URL metadata first to detect if it is an active live stream
        probe_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(probe_opts) as ydl_probe:
            info = ydl_probe.extract_info(url, download=False)

        is_live = bool(info.get('is_live') or info.get('live_status') == 'is_live')

        if is_live:
            logger.info(f"Active livestream detected for {url}. Capturing live window...")
            duration_sec = max(30, min(int(req.live_clip_minutes or 10) * 60, 3600))

            formats = [f for f in info.get('formats', []) if f.get('height') and f['height'] <= 1080 and f.get('url')]
            if not formats:
                formats = [f for f in info.get('formats', []) if f.get('url')]

            stream_url = None
            if formats:
                best_fmt = sorted(formats, key=lambda x: x.get('height', 0), reverse=True)[0]
                stream_url = best_fmt.get('url')
            if not stream_url:
                stream_url = info.get('url')

            if not stream_url:
                raise HTTPException(status_code=400, detail="Could not find streamable format for this live stream.")

            clean_title = "".join(c for c in (info.get("title") or "livestream") if c.isalnum() or c in (" ", "-", "_")).strip()[:40] or "livestream"
            video_id = info.get("id", "live")
            safe_name = unique_filename(f"{clean_title}-{video_id}.mp4")
            p = settings.UPLOADS_DIR / safe_name

            captured = False
            # 1. Try DVR seek backwards if live_mode != "next"
            if req.live_mode != "next":
                cmd_dvr = [
                    'ffmpeg', '-y',
                    '-sseof', f'-{duration_sec}',
                    '-i', stream_url,
                    '-t', str(duration_sec),
                    '-c', 'copy',
                    '-bsf:a', 'aac_adtstoasc',
                    str(p)
                ]
                try:
                    res_dvr = subprocess.run(cmd_dvr, capture_output=True, text=True, timeout=max(300, duration_sec + 60))
                    if res_dvr.returncode == 0 and p.exists() and p.stat().st_size > 10000:
                        captured = True
                    else:
                        p.unlink(missing_ok=True)
                except subprocess.TimeoutExpired:
                    logger.warning("DVR capture timed out; falling back to live head")
                    p.unlink(missing_ok=True)

            # 2. If DVR was not captured or live_mode is "next", capture from live head
            if not captured:
                cmd_live = [
                    'ffmpeg', '-y',
                    '-i', stream_url,
                    '-t', str(duration_sec),
                    '-c', 'copy',
                    '-bsf:a', 'aac_adtstoasc',
                    str(p)
                ]
                try:
                    res_live = subprocess.run(cmd_live, capture_output=True, text=True, timeout=duration_sec + 60)
                    if res_live.returncode == 0 and p.exists() and p.stat().st_size > 10000:
                        captured = True
                    else:
                        p.unlink(missing_ok=True)
                        cmd_tc = [
                            'ffmpeg', '-y',
                            '-i', stream_url,
                            '-t', str(duration_sec),
                            '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac',
                            str(p)
                        ]
                        res_tc = subprocess.run(cmd_tc, capture_output=True, text=True, timeout=duration_sec + 60)
                        if res_tc.returncode == 0 and p.exists() and p.stat().st_size > 10000:
                            captured = True
                except subprocess.TimeoutExpired:
                    logger.warning("Live-head capture timed out")
                    p.unlink(missing_ok=True)

            if not captured or not p.exists() or p.stat().st_size == 0:
                raise HTTPException(status_code=500, detail="Failed to capture video segment from active live stream.")
        else:
            outtmpl = str(settings.UPLOADS_DIR / "%(title).50s-%(id)s.%(ext)s")
            ydl_opts = {
                'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'noplaylist': True,
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
            thumb_time = min(1.0, max(0.1, probe.get("duration", 2.0) / 2.0))
            ffmpeg_engine.extract_thumbnail(p, thumb_time, thumb_path)
        except Exception:
            pass

        rel_video_path = str(p.resolve().relative_to(settings.ROOT_DIR.resolve())).replace("\\", "/")
        rel_thumb_path = str(thumb_path.resolve().relative_to(settings.STORAGE_DIR.resolve())).replace("\\", "/")

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
            "is_live": is_live,
        }
    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download video from URL: {str(e)}")
