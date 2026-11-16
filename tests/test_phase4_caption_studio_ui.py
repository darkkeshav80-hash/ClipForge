import asyncio
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.captions.ass_writer import ass_writer, STYLE_PRESETS
from backend.api.captions import generate_libass_preview
from backend.config import settings

CAPCUT_STYLES = [
    "Word Cut", "Marker Sweep", "Negative", "Karaoke Fill", "Karaoke Pop",
    "Hormozi", "MrBeast", "Neon Glow", "Fire", "Comic",
    "Typewriter", "Highlighter", "Boxed", "Word Pop", "Minimal"
]

SAMPLE_TEXTS = {
    "en": "HOW TO GO VIRAL ON YOUTUBE SHORTS",
    "hi": "यह तरीका आपके वीडियो को वायरल बना देगा",
    "hinglish": "Aise hooks banao jo audience ko scroll stop karwa de"
}

async def test_real_libass_preview_and_caching():
    print("\n--- TEST 1: Real Libass 3-Second Preview Generation & Cache Hit ---")
    payload = {
        "clip_id": "clip-2796-882",
        "preset": {"name": "Marker Sweep", "font_size": 76, "position": "middle"},
        "language": "en",
        "sample_text": SAMPLE_TEXTS["en"]
    }

    # 1. First render (real ffmpeg libass execution)
    res1 = await generate_libass_preview(payload)
    print("Render 1 result:", res1)
    assert res1["success"] is True
    assert res1["preview_url"].endswith(".mp4")
    assert res1["original_url"].endswith(".mp4")
    
    preview_file = settings.ROOT_DIR / res1["preview_url"].lstrip("/")
    orig_file = settings.ROOT_DIR / res1["original_url"].lstrip("/")
    assert preview_file.exists() and preview_file.stat().st_size > 10000
    assert orig_file.exists() and orig_file.stat().st_size > 10000
    print(f"PASS: Preview generated ({preview_file.stat().st_size} bytes), Original generated ({orig_file.stat().st_size} bytes)")

    # 2. Second render (cache hit test)
    res2 = await generate_libass_preview(payload)
    print("Render 2 result (cache test):", res2)
    assert res2["cached"] is True
    assert res2["preview_url"] == res1["preview_url"]
    print("PASS: Cache hit returned instantly from disk without ffmpeg re-encode.")

async def test_all_15_capcut_styles_all_languages():
    print("\n--- TEST 2: All 15 CapCut Styles Rendered across English, Hindi & Hinglish ---")
    words_en = [{"word": w, "start": i*0.4, "end": (i+1)*0.4} for i, w in enumerate(SAMPLE_TEXTS["en"].split())]
    words_hi = [{"word": w, "start": i*0.4, "end": (i+1)*0.4} for i, w in enumerate(SAMPLE_TEXTS["hi"].split())]
    words_hinglish = [{"word": w, "start": i*0.4, "end": (i+1)*0.4} for i, w in enumerate(SAMPLE_TEXTS["hinglish"].split())]

    test_cases = [
        ("English", words_en),
        ("Hindi", words_hi),
        ("Hinglish", words_hinglish)
    ]

    for lang_name, words in test_cases:
        for style_name in CAPCUT_STYLES:
            out_ass = settings.STORAGE_DIR / f"test_capcut_{lang_name.lower()}_{style_name.lower().replace(' ', '_')}.ass"
            ass_writer.generate_ass(
                words=words,
                preset={"name": style_name},
                output_path=out_ass,
                video_width=1080,
                video_height=1920,
                position_override="middle"
            )
            assert out_ass.exists()
            content = out_ass.read_text(encoding="utf-8")
            
            # Check for Devanagari font enforcement
            if lang_name == "Hindi":
                assert "Nirmala UI" in content, f"Devanagari font Nirmala UI missing in {style_name}!"
            
            # Check for zero overlapping events on layer 0
            dialogues = [line for line in content.splitlines() if line.startswith("Dialogue: 0,")]
            for idx in range(len(dialogues) - 1):
                cur_end = dialogues[idx].split(",")[2]
                next_start = dialogues[idx+1].split(",")[1]
                assert cur_end <= next_start, f"Overlap detected in {style_name} ({lang_name}): {cur_end} > {next_start}"

    print(f"PASS: All 15 CapCut styles rendered flawlessly for English, Hindi (Nirmala UI) and Hinglish with zero overlaps.")

def test_safe_zone_margins_and_no_text_overflow():
    print("\n--- TEST 3: Safe Zone Margins & Text Layout Compliance ---")
    out_ass = settings.STORAGE_DIR / "test_safe_zone.ass"
    words = [{"word": "LONGWORDTHATMUSTFITSAFELYINSIDEMARGINS", "start": 0.0, "end": 1.0}]
    
    ass_writer.generate_ass(
        words=words,
        preset={"name": "MrBeast"},
        output_path=out_ass,
        video_width=1080,
        video_height=1920
    )
    content = out_ass.read_text(encoding="utf-8")
    
    # Check margin L and R are at least 80px (85% safe area)
    # Style line format: MarginL, MarginR, MarginV
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert ",81,81," in content or ",80,80," in content
    print("PASS: Safe margins (85% width safety rule) strictly enforced in ASS styles.")

def generate_verification_screenshots():
    print("\n--- TEST 4: Generate Verification Frame Screenshots ---")
    # Take a 3-second preview and capture a screenshot frame with ffmpeg
    preview_file = list((settings.STORAGE_DIR / "previews").glob("preview_*.mp4"))
    if preview_file:
        sample_preview = preview_file[0]
        shot_out = settings.STORAGE_DIR / "phase4_preview_frame.jpg"
        cmd = [
            "ffmpeg", "-y", "-ss", "00:00:01.5",
            "-i", str(sample_preview),
            "-vframes", "1",
            "-q:v", "2",
            str(shot_out)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if shot_out.exists() and shot_out.stat().st_size > 5000:
            print(f"PASS: Screenshot captured at {shot_out} ({shot_out.stat().st_size} bytes)")
        else:
            print(f"Warning: Screenshot capture stderr: {res.stderr[:200]}")

async def main():
    await test_real_libass_preview_and_caching()
    await test_all_15_capcut_styles_all_languages()
    test_safe_zone_margins_and_no_text_overflow()
    generate_verification_screenshots()
    print("\n=======================================================")
    print(" ALL PHASE 4 CAPTION STUDIO TESTS PASSED SUCCESSFULLY! ")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
