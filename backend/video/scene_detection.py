"""
Scene Detection & Boundary Snapping Engine (Adapted and enhanced from OpenShorts for ClipForge AI).

Detects shot boundaries and camera transitions via native FFmpeg scene analysis.
Snaps clip start/end timestamps to clean camera transitions so shorts never start
or end with a 0.2s jarring fragment of another shot. Zero external PyTorch dependencies required.
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple
from backend.core.logger import logger

def detect_scene_cuts(video_path: Path, threshold: float = 0.35, max_scan_seconds: float = 300.0) -> List[float]:
    """
    Detects scene transition timestamps (in seconds) in the video.
    Runs native FFmpeg scene filter for ultra-fast, zero-dependency cut detection.
    """
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [
        ffmpeg_bin,
        "-v", "info",
        "-t", str(max_scan_seconds),
        "-i", str(video_path),
        "-filter:v", f"select='gt(scene,{threshold})',metadata=print:key=lavfi.scene_score",
        "-f", "null",
        "-"
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        cuts: List[float] = []
        for line in res.stderr.splitlines():
            if "pts_time:" in line:
                parts = line.split("pts_time:")
                if len(parts) > 1:
                    try:
                        pts_str = parts[1].split()[0].strip()
                        cuts.append(float(pts_str))
                    except (ValueError, IndexError):
                        continue
        return sorted(list(set(cuts)))
    except Exception as e:
        logger.warning(f"Scene cut detection fallback: {e}")
        return []

def snap_to_scene_boundaries(
    start_time: float,
    end_time: float,
    scene_cuts: List[float],
    snap_window: float = 1.2
) -> Tuple[float, float]:
    """
    Snaps candidate clip start and end timestamps to the nearest camera transition
    if a cut occurs within `snap_window` seconds, producing clean, professional cuts.
    """
    new_start = start_time
    new_end = end_time

    for cut in scene_cuts:
        # Snap start time if cut is very close to clip beginning
        if abs(cut - start_time) <= snap_window:
            new_start = round(cut, 2)
            break

    for cut in reversed(scene_cuts):
        # Snap end time if cut is very close to clip ending
        if abs(cut - end_time) <= snap_window:
            new_end = round(cut, 2)
            break

    # Ensure minimum clip duration of 10s is preserved after snap
    if (new_end - new_start) >= 10.0:
        return new_start, new_end

    return start_time, end_time
