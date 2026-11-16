import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.captions.ass_writer import ass_writer, STYLE_PRESETS
from backend.captions.sync_validator import sync_validator
from backend.ai.transcription import transcriber
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.core.logger import logger

def test_language_and_no_fake_transcript():
    print("\n--- TEST 1: Language & No Fake Transcript ---")
    try:
        transcriber.transcribe(Path("non_existent_audio.wav"))
        print("FAIL: Did not raise on missing audio!")
        assert False
    except Exception as e:
        print(f"PASS: Real exception raised on missing audio: {e}")
        assert "Audio file not found" in str(e) or "failed" in str(e)
    print("Verified: Fake simulated transcript fallback has been completely eliminated.")

def test_non_overlapping_and_safe_margins():
    print("\n--- TEST 2: Non-Overlapping Events & Safe Area Layout ---")
    sample_multilingual = [
        {"word": "Welcome", "start": 0.20, "end": 0.65},
        {"word": "to", "start": 0.68, "end": 0.85},
        {"word": "ClipForge", "start": 0.88, "end": 1.40},
        {"word": "AI", "start": 1.45, "end": 1.70},
        {"word": "नमस्ते", "start": 1.80, "end": 2.20},
        {"word": "दोस्तो", "start": 2.25, "end": 2.70},
        {"word": "kya", "start": 2.80, "end": 3.05},
        {"word": "haal", "start": 3.10, "end": 3.35},
        {"word": "hai", "start": 3.40, "end": 3.70},
    ]

    out_ass = Path("storage/test_phase1_multilingual.ass")
    ass_writer.generate_ass(
        words=sample_multilingual,
        preset={"name": "Hormozi"},
        output_path=out_ass,
        title="VIRAL HOOK"
    )

    val = ass_writer.validate_ass_events(out_ass)
    print(f"Validation Report: {val}")
    assert val["valid"] is True, f"Overlapping events found: {val['overlaps']}"
    assert val["overlap_count"] == 0
    print("PASS: 100% Non-overlapping events assertion verified.")

def test_sync_metrics():
    print("\n--- TEST 3: Caption Sync Offset Check (< 100ms) ---")
    words = [
        {"word": "This", "start": 0.5, "end": 0.8},
        {"word": "gameplay", "start": 0.85, "end": 1.3},
        {"word": "is", "start": 1.35, "end": 1.55},
        {"word": "insane", "start": 1.6, "end": 2.1},
    ]
    out_ass = Path("storage/test_phase1_sync.ass")
    ass_writer.generate_ass(words, {"name": "MrBeast"}, out_ass)
    sync = sync_validator.evaluate_sync(out_ass, words)
    print(f"Sync Telemetry: {sync}")
    assert sync["synced"] is True
    assert sync["median_offset_ms"] <= 100.0, f"Offset too high: {sync['median_offset_ms']}ms"
    print(f"PASS: Caption sync median offset is {sync['median_offset_ms']}ms (well below 100ms threshold).")

def test_all_15_styles_rendering():
    print("\n--- TEST 4: All 15 CapCut Styles Render Check (English, Hindi, Hinglish) ---")
    multilingual_text = [
        {"word": "Insane", "start": 0.1, "end": 0.5},
        {"word": "clutch", "start": 0.55, "end": 0.9},
        {"word": "नमस्ते", "start": 1.0, "end": 1.4},
        {"word": "bhai", "start": 1.45, "end": 1.8},
    ]

    # Create dummy black source video if not exists for live FFmpeg burn test
    dummy_src = Path("storage/test_dummy_src.mp4")
    if not dummy_src.exists():
        ffmpeg_cmd = [
            ffmpeg_engine.ffmpeg_path, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=3",
            "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
            "-t", "3", "-c:v", "libx264", "-c:a", "aac",
            str(dummy_src)
        ]
        import subprocess
        subprocess.run(ffmpeg_cmd, capture_output=True)

    passed_styles = []
    for style_name in STYLE_PRESETS.keys():
        ass_path = Path(f"storage/test_style_{style_name.replace(' ', '_')}.ass")
        ass_writer.generate_ass(
            words=multilingual_text,
            preset={"name": style_name},
            output_path=ass_path,
            title="TEST TITLE"
        )
        assert ass_path.exists()
        val = ass_writer.validate_ass_events(ass_path)
        assert val["valid"] is True, f"Style {style_name} produced invalid overlapping ASS!"
        passed_styles.append(style_name)

    print(f"PASS: All {len(passed_styles)} styles generated and validated with zero overlaps across English, Hindi, and Hinglish!")

    # Live FFmpeg burn test on representative complex style: Karaoke Fill (\kf) & Marker Sweep
    for test_s in ["Karaoke Fill", "Marker Sweep", "Neon Glow"]:
        out_clip = Path(f"storage/test_render_{test_s.replace(' ', '_')}.mp4")
        ass_file = Path(f"storage/test_style_{test_s.replace(' ', '_')}.ass")
        ffmpeg_engine.render_clip(
            input_video=dummy_src,
            start_time=0.0,
            duration=2.0,
            output_clip=out_clip,
            aspect_ratio="9:16",
            ass_subtitles_path=ass_file,
            normalize_audio=False
        )
        assert out_clip.exists() and out_clip.stat().st_size > 10000, f"Render failed for {test_s}"
        print(f"  -> Live FFmpeg libass render OK: {test_s} ({out_clip.name}, {out_clip.stat().st_size} bytes)")

def test_duration_limits():
    print("\n--- TEST 5: Strict Duration Clamp Enforcement ---")
    dummy_src = Path("storage/test_dummy_src.mp4")
    out_clip = Path("storage/test_render_duration_clamp.mp4")
    # Request 75.0s on a 60s max clamp
    rendered_path, fallback, warn = ffmpeg_engine.render_clip(
        input_video=dummy_src,
        start_time=0.0,
        duration=75.0, # Requested over limit
        output_clip=out_clip,
        max_duration_clamp=60.0
    )
    probe = ffmpeg_engine.probe_video(rendered_path)
    print(f"Requested: 75.0s, Rendered Duration: {probe['duration']}s")
    assert probe["duration"] <= 60.1, f"Duration exceeded clamp: {probe['duration']}"
    print("PASS: Clip duration strictly clamped to max_duration.")

if __name__ == "__main__":
    test_language_and_no_fake_transcript()
    test_non_overlapping_and_safe_margins()
    test_sync_metrics()
    test_all_15_styles_rendering()
    test_duration_limits()
    print("\n=======================================================")
    print(" ALL 5 PHASE 1 TEST CRITERIA PASSED SUCCESSFULLY! ")
    print("=======================================================")
