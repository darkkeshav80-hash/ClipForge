import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from backend.captions.ass_writer import ass_writer, hex_to_ass_color

def test_caption_ass_generation():
    # 1. Color conversion
    yellow_ass = hex_to_ass_color("#FACC15")
    assert yellow_ass == "&H0015CCFA&" # BGR order

    white_ass = hex_to_ass_color("#FFFFFF")
    assert white_ass == "&H00FFFFFF&"

    # 2. Timestamp formatting
    t1 = ass_writer.format_timestamp(65.42)
    assert t1 == "0:01:05.42"

    t2 = ass_writer.format_timestamp(3672.05)
    assert t2 == "1:01:12.05"

    # 3. ASS File Generation
    test_words = [
        {"word": "THIS", "start": 0.5, "end": 0.8},
        {"word": "IS", "start": 0.8, "end": 1.1},
        {"word": "HOW", "start": 1.1, "end": 1.4},
        {"word": "VIRAL", "start": 1.4, "end": 1.9},
        {"word": "SHORTS", "start": 1.9, "end": 2.4},
        {"word": "EXPLODE", "start": 2.4, "end": 3.0},
    ]

    preset = {
        "font_family": "Impact",
        "font_size": 48,
        "text_color": "#FFFFFF",
        "highlight_color": "#FACC15",
        "outline_color": "#000000",
        "outline_width": 4,
        "position": "middle",
        "all_caps": True,
        "animation_style": "pop_up",
    }

    out_ass = settings.CAPTIONS_DIR / "test_captions.ass"
    ass_writer.generate_ass(test_words, preset, out_ass, video_width=1080, video_height=1920)

    assert out_ass.exists()
    content = out_ass.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "Style: Default,Impact,48" in content
    assert "Dialogue:" in content
    assert "VIRAL" in content
    print(f"ASS subtitle generated successfully ({len(content)} chars)")

if __name__ == "__main__":
    test_caption_ass_generation()
    print("ALL CAPTION STUDIO TESTS PASSED SUCCESSFULLY!")
