import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import subprocess
import shutil
from backend.config import settings
from backend.core.logger import logger

def create_sample_video(output_path: Path, duration_sec: int = 15) -> Path:
    """
    Generates a 1080p test video with synthetic audio tone and speech counter
    using pure FFmpeg filters without requiring external media assets.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"

    # FFmpeg command:
    # Video: testsrc2 (1920x1080 @ 30fps) with drawtext timecode/counter
    # Audio: sine wave tone (440Hz / 880Hz cadence)
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc2=size=1920x1080:rate=30,drawtext=text='CLIPFORGE TEST VIDEO':x=(w-text_w)/2:y=(h-text_h)/2:fontsize=64:fontcolor=white:box=1:boxcolor=black@0.6",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:beep_factor=2:duration={duration_sec}",
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path),
    ]

    logger.info(f"Generating synthetic test video ({duration_sec}s) at {output_path.name}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        # Simplified fallback test pattern
        cmd_simple = [
            ffmpeg_bin,
            "-y",
            "-f", "lavfi", "-i", f"color=c=purple:s=1920x1080:d={duration_sec}",
            "-f", "lavfi", "-i", f"sine=f=440:d={duration_sec}",
            "-c:v", "libx264", "-c:a", "aac",
            str(output_path),
        ]
        subprocess.run(cmd_simple, check=True)

    logger.info(f"Sample test video generated successfully at: {output_path}")
    return output_path

if __name__ == "__main__":
    out = settings.UPLOADS_DIR / "sample_test_source.mp4"
    create_sample_video(out, duration_sec=10)
