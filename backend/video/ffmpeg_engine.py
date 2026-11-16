import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from backend.core.logger import logger

class FFmpegEngine:
    """
    High-Performance Video Manipulation Engine:
    - Accurate face-centered aspect ratio cropping
    - Burn-in kinetic ASS subtitles with safe-style fallback
    - CPU first with optional AMD AMF GPU encoding
    - EBU R128 audio normalization, yuv420p, and faststart
    """
    MAX_CLIP_DURATION: float = 60.0

    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        self.ffprobe_path = shutil.which("ffprobe") or "ffprobe"

    def probe_video(self, video_path: Path) -> Dict[str, Any]:
        """Returns video duration, width, height, fps, bitrate."""
        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration,bit_rate",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]

        width = 1920
        height = 1080
        fps = 30.0
        duration = 0.0

        if len(lines) >= 2:
            try:
                width = int(lines[0])
                height = int(lines[1])
            except ValueError:
                pass

        if len(lines) >= 3 and "/" in lines[2]:
            num, den = lines[2].split("/")
            try:
                fps = round(float(num) / float(den), 2)
            except (ValueError, ZeroDivisionError):
                pass

        for line in lines[3:]:
            try:
                duration = float(line)
                break
            except ValueError:
                continue

        return {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
        }

    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extracts mono 16kHz PCM WAV audio for Whisper transcription."""
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(video_path),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(output_audio),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction error: {res.stderr}")
        return output_audio

    def extract_thumbnail(self, video_path: Path, timestamp: float, output_thumb_path: Path) -> Path:
        """Extracts a crisp thumbnail frame at given timestamp."""
        output_thumb_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss", str(max(0.0, timestamp)),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_thumb_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.warning(f"Thumbnail extraction warning: {res.stderr}")
        return output_thumb_path

    def render_clip(
        self,
        input_video: Path,
        start_time: float,
        duration: float,
        output_clip: Path,
        aspect_ratio: str = "9:16",
        crop_center_x: float = 0.5,
        ass_subtitles_path: Optional[Path] = None,
        normalize_audio: bool = True,
        threads: int = 4,
        zoom_in: bool = False,
        use_amf: bool = False,
        max_duration_clamp: float = 60.0,
        is_preview: bool = False,
    ) -> Tuple[Path, bool, str]:
        """
        Renders cropped video with burned-in subtitles.
        Guarantees:
        - Clamps duration so clips never exceed max_duration_clamp
        - Accurate face-centered horizontal cropping for 9:16
        - Retries with safe basic subtitles if custom ASS fails (NEVER silently drops captions!)
        - Adds -pix_fmt yuv420p and -movflags +faststart
        Returns: (output_clip_path, fallback_style_used, warning_message)
        """
        output_clip.parent.mkdir(parents=True, exist_ok=True)

        # Enforce strict maximum duration clamp
        clamped_duration = min(float(duration), float(max_duration_clamp))

        # Clamp face center to safe bounds
        cx = max(0.1, min(0.9, float(crop_center_x)))

        # Resolution & scaling profile
        if is_preview:
            scale_w, scale_h = 540, 960
            scale_flag = "bilinear"
            sw_enc = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-tune", "fastdecode"]
        else:
            scale_w, scale_h = 1080, 1920
            scale_flag = "lanczos"
            sw_enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]

        # 1. Build Base Video Crop Filter
        if aspect_ratio == "9:16":
            # Correct face centering formula:
            # Crop width = ih * 9 / 16
            # Center of crop is placed at cx * iw
            # crop_x = min(max(cx * iw - crop_w / 2, 0), iw - crop_w)
            base_vf = (
                f"crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)':"
                f"x='min(max({cx}*iw - min(iw,ih*9/16)/2, 0), iw - min(iw,ih*9/16))':"
                f"y='(ih - min(ih,iw*16/9))/2',"
                f"scale={scale_w}:{scale_h}:flags={scale_flag}"
            )
        elif aspect_ratio == "1:1":
            base_vf = (
                f"crop=w='min(iw,ih)':h='min(iw,ih)':"
                f"x='min(max({cx}*iw - min(iw,ih)/2, 0), iw - min(iw,ih))':"
                f"y='(ih - min(iw,ih))/2',"
                f"scale=1080:1080:flags=lanczos"
            )
        else: # 16:9
            base_vf = "scale=1920:1080:flags=lanczos"

        if zoom_in and not is_preview:
            base_vf += ",zoompan=z='min(zoom+0.001,1.08)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"

        audio_filter = "loudnorm=I=-14:LRA=11:TP=-1.5" if normalize_audio and not is_preview else "anull"

        # Codec choices: CPU (libx264) and AMD AMF (h264_amf)
        hw_enc = ["-c:v", "h264_amf", "-quality", "speed" if is_preview else "balanced", "-b:v", "8M" if is_preview else "14M"]

        def build_cmd(vf: str, enc_args: List[str]) -> List[str]:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", f"{max(0.0, start_time):.2f}",
                "-t", f"{clamped_duration:.2f}",
                "-i", str(input_video),
                "-vf", vf,
                "-af", audio_filter,
                *enc_args,
                "-pix_fmt", "yuv420p",
            ]
            if is_preview:
                cmd.extend(["-an"])
            else:
                cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            cmd.extend([
                "-threads", str(threads),
                "-movflags", "+faststart",
                str(output_clip),
            ])
            return cmd

        # Prepare subtitle filter variants
        clean_sub_filter = None
        if ass_subtitles_path and ass_subtitles_path.exists():
            clean_path = str(ass_subtitles_path).replace("\\", "/").replace(":", "\\:")
            clean_sub_filter = f"ass='{clean_path}'"

        # List of render attempts in order of preference:
        # 1. Custom ASS with AMF (if requested)
        # 2. Custom ASS with CPU libx264
        # 3. Safe Fallback ASS with CPU libx264 (if custom ASS fails)
        attempts = []
        if clean_sub_filter:
            vf_with_ass = f"{base_vf},{clean_sub_filter}"
            if use_amf:
                attempts.append((vf_with_ass, hw_enc, "AMD GPU + Custom Subtitles", False))
            attempts.append((vf_with_ass, sw_enc, "CPU + Custom Subtitles", False))

            # Build safe fallback ASS if needed
            safe_ass = ass_subtitles_path.with_name(ass_subtitles_path.stem + "_safe.ass")
            try:
                self._generate_safe_ass(ass_subtitles_path, safe_ass)
                safe_clean = str(safe_ass).replace("\\", "/").replace(":", "\\:")
                vf_safe = f"{base_vf},ass='{safe_clean}'"
                attempts.append((vf_safe, sw_enc, "CPU + Safe Subtitles Fallback", True))
            except Exception as e:
                logger.warning(f"Could not build safe fallback ASS: {e}")
        else:
            if use_amf:
                attempts.append((base_vf, hw_enc, "AMD GPU", False))
            attempts.append((base_vf, sw_enc, "CPU", False))

        last_error = ""
        for vf, enc, label, is_fallback in attempts:
            cmd = build_cmd(vf, enc)
            logger.info(f"Rendering attempt ({label}): {' '.join(cmd[:12])}...")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and output_clip.exists() and output_clip.stat().st_size > 10000:
                warning = "Rendered with safe fallback subtitles due to font error." if is_fallback else ""
                logger.info(f"Render successful using {label}")
                return output_clip, is_fallback, warning
            last_error = res.stderr[-500:]
            logger.warning(f"Attempt failed ({label}): {last_error}")

        raise RuntimeError(f"All render attempts failed for {output_clip.name}. Last error: {last_error}")

    def _generate_safe_ass(self, src_ass: Path, dest_ass: Path):
        """Creates a basic safe ASS file with Nirmala UI / Arial to guarantee rendering."""
        lines = src_ass.read_text(encoding="utf-8").splitlines()
        safe_lines = []
        for line in lines:
            if line.startswith("Style: Main"):
                # Replace font with universal Nirmala UI / Arial
                safe_lines.append(
                    "Style: Main,Nirmala UI,72,&H00FFFFFF&,&H00FFE600&,&H00000000&,&H80000000&,-1,0,0,0,100,100,1,0,1,6,2,2,70,70,300,1"
                )
            else:
                safe_lines.append(line)
        dest_ass.write_text("\n".join(safe_lines) + "\n", encoding="utf-8")

ffmpeg_engine = FFmpegEngine()
