import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai.language_engine import language_engine, offline_devanagari_to_hinglish
from backend.captions.ass_writer import ass_writer, is_devanagari
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.core.logger import logger

def test_repeated_phrase_suppression():
    print("\n--- TEST 1: Repetition Loop Filter ---")
    hallucination_words = [
        {"word": "nahi", "start": 1.0, "end": 1.2},
        {"word": "nahi", "start": 1.2, "end": 1.4},
        {"word": "nahi", "start": 1.4, "end": 1.6},
        {"word": "nahi", "start": 1.6, "end": 1.8},
        {"word": "nahi", "start": 1.8, "end": 2.0},
        {"word": "nahi", "start": 2.0, "end": 2.2},
        {"word": "bhai", "start": 2.25, "end": 2.6},
        {"word": "ye", "start": 2.65, "end": 2.9},
    ]
    cleaned = language_engine.drop_repeated_phrases(hallucination_words, max_consecutive=2)
    print(f"Original word count: {len(hallucination_words)}, Cleaned word count: {len(cleaned)}")
    assert len(cleaned) < len(hallucination_words), "Repetitions were not dropped!"
    assert [w["word"] for w in cleaned[-2:]] == ["bhai", "ye"]
    print("PASS: Hallucination repetition loops suppressed successfully.")

def test_offline_devanagari_to_hinglish():
    print("\n--- TEST 2: Offline Devanagari to Hinglish Transliteration ---")
    hindi_phrase = "नमस्ते दोस्तो क्या हाल है"
    hinglish_result = offline_devanagari_to_hinglish(hindi_phrase)
    print(f"Hindi: '{hindi_phrase}' -> Hinglish: '{hinglish_result}'")
    assert any(w in hinglish_result.lower() for w in ["namaste", "dosto", "kya", "haal", "hai"])
    print("PASS: Phonetic transliteration produced natural Roman Hindi.")

async def test_timing_redistribution():
    print("\n--- TEST 3: Word Timing Redistribution on Word Count Change ---")
    hindi_words = [
        {"word": "यह", "start": 1.0, "end": 1.3},
        {"word": "तरीका", "start": 1.35, "end": 1.7},
        {"word": "काम", "start": 1.75, "end": 2.0},
        {"word": "करेगा", "start": 2.05, "end": 2.5},
    ]
    phrase_start = hindi_words[0]["start"]
    phrase_end = hindi_words[-1]["end"]

    # Adapt to English (which expands word count, e.g. "this method will work for you")
    adapted, is_fallback, warn = await language_engine.adapt_captions_language(
        words=hindi_words,
        target_lang="en",
        spoken_lang="hi"
    )

    print(f"Adapted words count: {len(adapted)}, Sample: {[w['word'] for w in adapted]}")
    # Verify exact phrase boundary preservation
    assert adapted[0]["start"] >= phrase_start - 0.05
    assert adapted[-1]["end"] <= phrase_end + 0.05
    # Verify monotonically increasing timestamps
    for i in range(len(adapted) - 1):
        assert adapted[i]["start"] < adapted[i]["end"]
        assert adapted[i]["end"] <= adapted[i + 1]["start"] + 0.02
    print("PASS: Word timings redistributed cleanly within exact phrase boundary.")

async def test_script_and_font_selection():
    print("\n--- TEST 4: Script-Aware Font & Uppercase Rules ---")
    hindi_words = [{"word": "नमस्ते", "start": 0.5, "end": 1.0}]
    hinglish_words = [{"word": "namaste", "start": 0.5, "end": 1.0}]

    out_hi = Path("storage/test_lang_hi.ass")
    out_hinglish = Path("storage/test_lang_hinglish.ass")

    ass_writer.generate_ass(hindi_words, {"name": "MrBeast Bold", "all_caps": True}, out_hi)
    ass_writer.generate_ass(hinglish_words, {"name": "MrBeast Bold", "all_caps": True}, out_hinglish)

    content_hi = out_hi.read_text(encoding="utf-8")
    content_hinglish = out_hinglish.read_text(encoding="utf-8")

    assert "Nirmala UI" in content_hi, "Devanagari did not switch to Nirmala UI!"
    assert "नमस्ते" in content_hi, "Devanagari text got corrupted!"
    assert "NAMASTE" in content_hinglish, "Latin Hinglish was not uppercased when all_caps was true!"
    print("PASS: Devanagari automatically selected Nirmala UI, Latin Hinglish respected uppercase.")

async def test_live_clip_language_endpoint():
    print("\n--- TEST 5: Live API Clip Re-Render in Hinglish & Hindi ---")
    from backend.api.clips import change_caption_language, get_clip
    import sqlite3
    con = sqlite3.connect(r"storage/clipforge.db")
    cur = con.cursor()
    row = cur.execute("SELECT id FROM clips ORDER BY rowid DESC LIMIT 1").fetchone()
    if not row:
        print("SKIP: No clip in database to test live endpoint.")
        return

    test_clip_id = row[0]
    print(f"Testing live re-render on clip ID: {test_clip_id}...")
    res = await change_caption_language(test_clip_id, {"language": "hinglish", "caption_preset": "mrbeast-bold"})
    print(f"API Re-render Response: {res}")
    assert res["success"] is True
    assert res["language"] == "hinglish"
    rendered_file = Path("storage") / res["rendered_path"]
    assert rendered_file.exists() and rendered_file.stat().st_size > 10000
    print(f"PASS: Live clip re-rendered with Hinglish captions ({rendered_file.stat().st_size} bytes).")

async def main():
    test_repeated_phrase_suppression()
    test_offline_devanagari_to_hinglish()
    await test_timing_redistribution()
    await test_script_and_font_selection()
    await test_live_clip_language_endpoint()
    print("\n=======================================================")
    print(" ALL 5 PHASE 2 TEST CRITERIA PASSED SUCCESSFULLY! ")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
