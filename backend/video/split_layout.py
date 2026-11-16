"""
Dual-Speaker Podcast Split Layout Engine (Adapted and enhanced from OpenShorts for ClipForge AI).

Handles two speakers sharing a wide 16:9 shot (podcasts, interviews, co-op streams).
Instead of cropping out one speaker or shrinking both into a tiny letterbox with blurry padding,
it crops each speaker into a 1080x960 half-frame and stacks them vertically into a full 9:16 frame.
"""

from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import numpy as np

MIN_SEPARATION = 0.20 # Horizontal separation between two faces (fraction of frame)
MIN_COEXISTENCE = 0.35 # Minimum fraction of frames where both faces are visible
SPLIT_TIGHTNESS = 0.85 # Fraction of source height taken per half-crop

def calculate_half_crop(
    orig_w: int,
    orig_h: int,
    out_w: int,
    out_h: int,
    center_x: float,
    center_y: float = 0.5,
    tightness: float = SPLIT_TIGHTNESS
) -> Tuple[int, int, int, int, int]:
    """
    Computes (crop_w, crop_h, crop_x, crop_y, half_h) for one half of the vertical stack.
    Each half has aspect ratio out_w / (out_h / 2) = 1080 / 960 = 1.125.
    """
    half_h = out_h // 2
    half_h -= half_h % 2
    aspect = out_w / float(half_h)

    crop_h = int(round(orig_h * max(0.3, min(tightness, 1.0))))
    crop_w = int(round(crop_h * aspect))
    if crop_w > orig_w:
        crop_w = orig_w
        crop_h = int(round(crop_w / aspect))

    crop_w -= crop_w % 2
    crop_h -= crop_h % 2

    cx = center_x * orig_w
    cy = center_y * orig_h

    x = int(round(cx - crop_w / 2.0))
    x = max(0, min(x, orig_w - crop_w))

    # Bias crop slightly down to preserve natural headroom
    y = int(round(cy - crop_h * 0.42))
    y = max(0, min(y, orig_h - crop_h))

    return crop_w, crop_h, x - (x % 2), y - (y % 2), half_h

def build_split_filtergraph(
    orig_w: int,
    orig_h: int,
    out_w: int = 1080,
    out_h: int = 1920,
    left_center_x: float = 0.3,
    right_center_x: float = 0.7,
    tightness: float = SPLIT_TIGHTNESS
) -> str:
    """
    Constructs an FFmpeg vstack filtergraph placing Left Speaker on top and Right Speaker on bottom.
    """
    top_w, top_h, top_x, top_y, half_h = calculate_half_crop(
        orig_w, orig_h, out_w, out_h, left_center_x, 0.45, tightness
    )
    bot_w, bot_h, bot_x, bot_y, _ = calculate_half_crop(
        orig_w, orig_h, out_w, out_h, right_center_x, 0.45, tightness
    )

    return (
        f"[0:v]split=2[ta][ba];"
        f"[ta]crop=w={top_w}:h={top_h}:x={top_x}:y={top_y},"
        f"scale={out_w}:{half_h}:flags=lanczos[top];"
        f"[ba]crop=w={bot_w}:h={bot_h}:x={bot_x}:y={bot_y},"
        f"scale={out_w}:{half_h}:flags=lanczos[bot];"
        f"[top][bot]vstack=inputs=2,"
        f"pad={out_w}:{out_h}:0:0,setsar=1[v]"
    )
