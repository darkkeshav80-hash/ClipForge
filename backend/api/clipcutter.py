import asyncio
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import List, Optional, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError, download_range_func

from backend.config import settings
from backend.core.logger import logger
from backend.core.security import validate_public_url
from backend.video.ffmpeg_engine import ffmpeg_engine

router = APIRouter(prefix="/api/clipcutter", tags=["clipcutter"])

ALLOWED_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "music.youtube.com",
}

clip_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)


def _validate_youtube_url(raw_url: str) -> str:
    url = validate_public_url(raw_url.strip())
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in ALLOWED_YOUTUBE_HOSTS:
        raise HTTPException(
            status_code=400,
            detail="Only YouTube links (youtube.com, youtu.be, music.youtube.com) are supported by Clip Cutter."
        )
    return url


def _cleanup_old_clips():
    """Removes temporary clipcut files older than 24 hours."""
    try:
        cutoff = time.time() - 86400
        for p in settings.UPLOADS_DIR.glob("clipcut_*"):
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink(missing_ok=True)
            except Exception as ex:
                logger.warning(f"Failed to delete expired clip {p.name}: {ex}")
    except Exception as ex:
        logger.warning(f"Error during clipcut cleanup: {ex}")


class ClipInfoRequest(BaseModel):
    url: str


class ClipCutRequest(BaseModel):
    url: str
    start: float = Field(..., ge=0.0, description="Start time in seconds")
    end: float = Field(..., gt=0.0, description="End time in seconds")
    quality: Literal["1080", "720", "480", "360", "240", "144", "audio"]


@router.post("/info")
async def get_clip_info(req: ClipInfoRequest):
    url = _validate_youtube_url(req.url)

    def _extract_sync():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info = await asyncio.to_thread(_extract_sync)
    except DownloadError as e:
        err_msg = str(e).lower()
        logger.error(f"yt-dlp extract error for {url}: {e}", exc_info=True)
        if any(keyword in err_msg for keyword in ("private video", "video unavailable", "not found", "404")):
            raise HTTPException(status_code=404, detail="This YouTube video is private or unavailable.")
        if any(keyword in err_msg for keyword in ("sign in", "bot", "captcha", "confirm you're not a robot")):
            raise HTTPException(status_code=403, detail="YouTube requires sign-in or verification to access this video.")
        raise HTTPException(status_code=502, detail="Could not retrieve video information from YouTube.")
    except Exception as e:
        logger.error(f"Unexpected error extracting video info: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to inspect YouTube video.")

    video_id = info.get("id") or ""
    title = info.get("title") or "Untitled Video"
    channel = info.get("uploader") or info.get("channel") or ""
    thumbnail = info.get("thumbnail") or ""
    duration = int(info.get("duration") or 0)
    is_live = bool(info.get("is_live") or info.get("live_status") == "is_live")
    was_live = bool(info.get("was_live") or info.get("live_status") == "was_live")

    # Extract distinct heights from formats
    formats = info.get("formats") or []
    heights = set()
    has_audio = False
    for f in formats:
        h = f.get("height")
        if h and isinstance(h, int) and h > 0:
            heights.add(h)
        if f.get("acodec") and f.get("acodec") != "none":
            has_audio = True

    # Standard resolutions up to 1080p
    supported_heights = [144, 240, 360, 480, 720, 1080]
    available_heights = sorted([h for h in supported_heights if any(fh >= h for fh in heights)])
    if not available_heights and heights:
        available_heights = sorted(list(heights))[:6]
    if not available_heights:
        available_heights = [720, 1080]

    note: Optional[str] = None
    if is_live and duration == 0:
        note = "Currently-live stream: range selection is limited to the DVR window recorded so far."

    return {
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "thumbnail": thumbnail,
        "duration": duration,
        "is_live": is_live,
        "was_live": was_live,
        "available_heights": available_heights,
        "has_audio_only": has_audio or True,
        "note": note,
    }


@router.post("/clip")
async def cut_clip(req: ClipCutRequest):
    url = _validate_youtube_url(req.url)

    if req.end <= req.start:
        raise HTTPException(status_code=400, detail="End time must be greater than start time.")

    clip_length = req.end - req.start
    if clip_length > settings.MAX_CLIP_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Requested clip duration ({clip_length:.1f}s) exceeds the maximum allowed limit of {settings.MAX_CLIP_SECONDS} seconds."
        )

    # Clean up older temporary clips before processing
    _cleanup_old_clips()

    if clip_semaphore.locked():
        raise HTTPException(
            status_code=429,
            detail="Another clip job is currently in progress. Please wait for it to finish."
        )

    async with clip_semaphore:
        # Pre-probe to get video id and live state
        def _quick_probe():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(_quick_probe)
        except Exception as e:
            logger.error(f"Error probing video before cut: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail="Failed to connect to YouTube for clipping.")

        video_id = re.sub(r'[^a-zA-Z0-9_-]', '', info.get("id") or "video")[:20]
        is_live = bool(info.get("is_live") or info.get("live_status") == "is_live")
        is_audio = req.quality == "audio"
        ext = "m4a" if is_audio else "mp4"

        safe_stem = f"clipcut_{video_id}_{int(req.start)}_{int(req.end)}_{uuid.uuid4().hex[:6]}"

        if is_live:
            duration_sec = max(1, int(req.end - req.start))
            start_seek = max(0.0, float(req.start))
            formats = info.get("formats", [])

            if is_audio:
                a_fmts = [f for f in formats if f.get("acodec") != "none" and f.get("url")]
                best_a = a_fmts[-1] if a_fmts else None
                if not best_a:
                    raise HTTPException(status_code=400, detail="No audio stream found for this live stream.")

                def _capture_live_audio_sync() -> Path:
                    target = settings.UPLOADS_DIR / f"{safe_stem}.m4a"
                    captured = False
                    if start_seek > 0:
                        cmd = ["ffmpeg", "-y", "-ss", str(start_seek), "-i", best_a["url"], "-t", str(duration_sec), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(target)]
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 5000:
                                captured = True
                            else:
                                target.unlink(missing_ok=True)
                        except Exception:
                            target.unlink(missing_ok=True)

                    if not captured:
                        cmd = ["ffmpeg", "-y", "-sseof", f"-{duration_sec}", "-i", best_a["url"], "-t", str(duration_sec), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(target)]
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 5000:
                                captured = True
                            else:
                                target.unlink(missing_ok=True)
                        except Exception:
                            target.unlink(missing_ok=True)

                    if not captured:
                        cmd = ["ffmpeg", "-y", "-i", best_a["url"], "-t", str(duration_sec), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(target)]
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 5000:
                                captured = True
                        except Exception:
                            target.unlink(missing_ok=True)

                    if not captured or not target.exists() or target.stat().st_size == 0:
                        target.unlink(missing_ok=True)
                        raise RuntimeError("Failed to capture live audio stream.")
                    return target

                try:
                    output_file = await asyncio.to_thread(_capture_live_audio_sync)
                except Exception as e:
                    logger.error(f"Error during live audio cut: {e}", exc_info=True)
                    raise HTTPException(status_code=502, detail=f"Failed to cut live audio: {str(e)[:160]}")

            else:
                q_limit = int(req.quality) if req.quality.isdigit() else 1080
                v_fmts = [f for f in formats if f.get("vcodec") != "none" and f.get("height") and f["height"] <= q_limit and f.get("url")]
                if not v_fmts:
                    v_fmts = [f for f in formats if f.get("vcodec") != "none" and f.get("url")]
                if not v_fmts:
                    v_fmts = [f for f in formats if f.get("url")]

                best_v = sorted(v_fmts, key=lambda x: x.get("height", 0), reverse=True)[0] if v_fmts else None
                a_fmts = [f for f in formats if f.get("acodec") != "none" and f.get("url")]
                best_a = a_fmts[-1] if a_fmts else None

                if not best_v:
                    raise HTTPException(status_code=400, detail="No video stream found for this live stream.")

                def _capture_live_video_sync() -> Path:
                    target = settings.UPLOADS_DIR / f"{safe_stem}.mp4"
                    captured = False

                    # 1. Seek with -ss if start_seek > 0
                    if start_seek > 0:
                        cmd = ["ffmpeg", "-y"]
                        if best_a and best_v["url"] != best_a["url"]:
                            cmd.extend(["-ss", str(start_seek), "-i", best_v["url"], "-ss", str(start_seek), "-i", best_a["url"]])
                        else:
                            cmd.extend(["-ss", str(start_seek), "-i", best_v["url"]])
                        cmd.extend(["-t", str(duration_sec), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(target)])
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 10000:
                                captured = True
                            else:
                                target.unlink(missing_ok=True)
                        except Exception:
                            target.unlink(missing_ok=True)

                    # 2. Seek from DVR backwards (-sseof)
                    if not captured:
                        cmd = ["ffmpeg", "-y"]
                        if best_a and best_v["url"] != best_a["url"]:
                            cmd.extend(["-sseof", f"-{duration_sec}", "-i", best_v["url"], "-sseof", f"-{duration_sec}", "-i", best_a["url"]])
                        else:
                            cmd.extend(["-sseof", f"-{duration_sec}", "-i", best_v["url"]])
                        cmd.extend(["-t", str(duration_sec), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(target)])
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 10000:
                                captured = True
                            else:
                                target.unlink(missing_ok=True)
                        except Exception:
                            target.unlink(missing_ok=True)

                    # 3. Live head
                    if not captured:
                        cmd = ["ffmpeg", "-y"]
                        if best_a and best_v["url"] != best_a["url"]:
                            cmd.extend(["-i", best_v["url"], "-i", best_a["url"]])
                        else:
                            cmd.extend(["-i", best_v["url"]])
                        cmd.extend(["-t", str(duration_sec), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(target)])
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 10000:
                                captured = True
                        except Exception:
                            target.unlink(missing_ok=True)

                    # 4. Transcode fallback
                    if not captured:
                        cmd = ["ffmpeg", "-y"]
                        if best_a and best_v["url"] != best_a["url"]:
                            cmd.extend(["-i", best_v["url"], "-i", best_a["url"]])
                        else:
                            cmd.extend(["-i", best_v["url"]])
                        cmd.extend(["-t", str(duration_sec), "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(target)])
                        try:
                            r = subprocess.run(cmd, capture_output=True, timeout=max(60, duration_sec + 20))
                            if r.returncode == 0 and target.exists() and target.stat().st_size > 10000:
                                captured = True
                        except Exception:
                            target.unlink(missing_ok=True)

                    if not captured or not target.exists() or target.stat().st_size == 0:
                        target.unlink(missing_ok=True)
                        raise RuntimeError("Failed to capture live video stream.")
                    return target

                try:
                    output_file = await asyncio.to_thread(_capture_live_video_sync)
                except Exception as e:
                    logger.error(f"Error during live video cut: {e}", exc_info=True)
                    raise HTTPException(status_code=502, detail=f"Failed to cut live clip: {str(e)[:160]}")

        else:
            def _download_range_sync() -> Path:
                out_tmpl = str(settings.UPLOADS_DIR / f"{safe_stem}.%(ext)s")

                if is_audio:
                    fmt = "bestaudio[ext=m4a]/bestaudio"
                else:
                    q = req.quality
                    fmt = f"bestvideo[height<={q}][ext=mp4]+bestaudio[ext=m4a]/best[height<={q}][ext=mp4]/best[height<={q}]"

                ydl_opts = {
                    "format": fmt,
                    "outtmpl": out_tmpl,
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "force_keyframes_at_cuts": True,
                    "download_ranges": download_range_func(None, [(req.start, req.end)]),
                }
                if not is_audio:
                    ydl_opts["merge_output_format"] = "mp4"

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as err:
                    # Clean up any partial files
                    for f in settings.UPLOADS_DIR.glob(f"{safe_stem}*"):
                        f.unlink(missing_ok=True)
                    raise err

                target = settings.UPLOADS_DIR / f"{safe_stem}.{ext}"
                if target.exists() and target.stat().st_size > 0:
                    return target

                for cand in settings.UPLOADS_DIR.glob(f"{safe_stem}.*"):
                    if cand.is_file() and cand.stat().st_size > 0:
                        return cand

                raise RuntimeError("Clipped file was not produced by downloader.")

            try:
                output_file = await asyncio.to_thread(_download_range_sync)
            except Exception as e:
                logger.error(f"Error during yt-dlp range cut: {e}", exc_info=True)
                for f in settings.UPLOADS_DIR.glob(f"{safe_stem}*"):
                    f.unlink(missing_ok=True)
                raise HTTPException(status_code=502, detail=f"Failed to cut clip: {str(e)[:160]}")

        # Probe the resulting clip with FFprobe
        if is_audio:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(output_file)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            try:
                dur = float(res.stdout.strip())
            except Exception:
                dur = clip_length
            probe = {"duration": dur, "width": 0, "height": 0, "fps": 0.0}
            rel_thumb_path = ""
        else:
            try:
                probe = ffmpeg_engine.probe_video(output_file)
                if probe.get("duration", 0) <= 0:
                    cmd = [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(output_file)
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    try:
                        probe["duration"] = float(res.stdout.strip())
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"FFprobe failed on clipped file {output_file}: {e}")
                output_file.unlink(missing_ok=True)
                raise HTTPException(status_code=422, detail="Failed to verify cut video format with ffprobe.")

            if probe.get("duration", 0) <= 0:
                output_file.unlink(missing_ok=True)
                raise HTTPException(status_code=422, detail="Corrupted clip output: zero duration detected.")

            # Extract thumbnail frame
            thumb_name = f"{output_file.stem}_thumb.jpg"
            thumb_path = settings.THUMBNAILS_DIR / thumb_name
            try:
                thumb_time = min(1.0, max(0.1, probe.get("duration", 2.0) / 2.0))
                ffmpeg_engine.extract_thumbnail(output_file, thumb_time, thumb_path)
                rel_thumb_path = str(thumb_path.resolve().relative_to(settings.STORAGE_DIR.resolve())).replace("\\", "/")
            except Exception as ex:
                logger.warning(f"Could not extract thumbnail for cut clip: {ex}")
                rel_thumb_path = ""

        rel_video_path = str(output_file.resolve().relative_to(settings.ROOT_DIR.resolve())).replace("\\", "/")
        download_url = f"/api/clipcutter/file/{output_file.name}"

        return {
            "path": rel_video_path,
            "filename": output_file.name,
            "duration": probe["duration"],
            "width": probe["width"],
            "height": probe["height"],
            "fps": probe["fps"],
            "thumbnail_path": rel_thumb_path,
            "download_url": download_url,
        }


@router.get("/file/{filename}")
async def download_clip_file(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    target_path = (settings.UPLOADS_DIR / filename).resolve()
    try:
        target_path.relative_to(settings.UPLOADS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path traversal attempt.")

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="Requested file was not found.")

    ext = target_path.suffix.lower()
    media_type = "audio/mp4" if ext in (".m4a", ".aac") else "video/mp4"

    return FileResponse(
        path=str(target_path),
        media_type=media_type,
        filename=target_path.name,
        headers={"Content-Disposition": f'attachment; filename="{target_path.name}"'}
    )
