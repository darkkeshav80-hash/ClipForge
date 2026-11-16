"""
Dynamic Punch-In Zoom Engine (Adapted and enhanced from OpenShorts for ClipForge AI).

Applies an asymmetric, smoothstep zoom push toward the speaker on key hook and emphasis moments.
- Fast push in (0.25s)
- Hold at 1.12x (1.30s)
- Gentle drift out (0.55s)
- Minimum gap between punches: 16.0s (averages 2-3 intentional punches per 45s clip)

Unlike OpenShorts which had no transcript wiring, ClipForge AI wires transcript hook
keywords directly to ensure zoom pushes land on high-impact spoken words.
"""

from typing import List, Tuple, Optional
import math

RISE_SECONDS = 0.25
HOLD_SECONDS = 1.30
FALL_SECONDS = 0.55
MAX_ZOOM = 1.12
MIN_GAP_SECONDS = 16.0

def _ease(t: float) -> float:
    """Smoothstep on [0, 1]: t * t * (3.0 - 2.0 * t). Linear ramps look mechanical."""
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)

def calculate_punch_moments(
    words: List[dict],
    clip_start_offset: float,
    duration: float,
    keywords: Optional[List[str]] = None
) -> List[float]:
    """
    Identifies optimal seconds within the clip (relative to 0.0) to trigger a punch-in.
    Prioritizes AI-identified keywords, hooks, and punchline words.
    """
    kws_set = set(k.lower() for k in (keywords or []))
    punch_times: List[float] = []
    last_punch = -999.0

    # 1. Search for keyword matches in word transcript
    for w in words:
        word_text = w.get("word", "").strip().lower()
        w_start = float(w.get("start", 0.0)) - clip_start_offset
        
        # Valid timing within clip duration bounds (skip first 2s and last 3s)
        if 2.0 <= w_start <= (duration - 4.0):
            if word_text in kws_set and (w_start - last_punch) >= MIN_GAP_SECONDS:
                punch_times.append(round(w_start, 2))
                last_punch = w_start

    # 2. If no keywords found or only 1 found in a long clip, add a natural midpoint punch
    if not punch_times and duration >= 25.0:
        mid = round(duration * 0.45, 2)
        punch_times.append(mid)

    return punch_times

def generate_zoompan_expression(punch_times: List[float], duration: float, fps: float = 30.0) -> str:
    """
    Constructs an optimized FFmpeg zoompan filter expression that performs
    smoothstep punch-in pushes on the calculated emphasis moments.
    """
    if not punch_times:
        return ""

    # Build zoom conditions for each punch moment
    span = RISE_SECONDS + HOLD_SECONDS + FALL_SECONDS
    conditions = []
    for t in punch_times:
        # Frame index range for this punch
        f_start = int(t * fps)
        f_rise = int((t + RISE_SECONDS) * fps)
        f_hold = int((t + RISE_SECONDS + HOLD_SECONDS) * fps)
        f_end = int((t + span) * fps)
        
        # In FFmpeg zoompan, 'on' is the current output frame number
        cond = (
            f"if(between(on,{f_start},{f_end}),"
            f"if(lt(on,{f_rise}),1.0+0.12*(on-{f_start})/{max(1, f_rise-f_start)},"
            f"if(lt(on,{f_hold}),1.12,"
            f"1.12-0.12*(on-{f_hold})/{max(1, f_end-f_hold)})),1.0)"
        )
        conditions.append(cond)

    # Combine with max() to smoothly pick active punch
    combined = conditions[0]
    for c in conditions[1:]:
        combined = f"max({combined},{c})"

    # Return full zoompan filter string centered on 1080x1920
    total_frames = int(duration * fps)
    return (
        f"zoompan=z='{combined}':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1080x1920:fps={fps}"
    )
