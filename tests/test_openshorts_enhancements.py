import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.video.punch_in import calculate_punch_moments, generate_zoompan_expression
from backend.video.split_layout import calculate_half_crop, build_split_filtergraph
from backend.video.scene_detection import snap_to_scene_boundaries

def test_punch_in():
    print("\n--- TEST: Punch-In Zoom Engine ---")
    mock_words = [
        {"word": "hello", "start": 1.0, "end": 1.5},
        {"word": "this", "start": 2.0, "end": 2.5},
        {"word": "secret", "start": 5.0, "end": 5.5}, # Keyword match
        {"word": "is", "start": 6.0, "end": 6.3},
        {"word": "insane", "start": 22.0, "end": 22.5}, # Keyword match after 16s
        {"word": "bye", "start": 30.0, "end": 30.5},
    ]
    kws = ["secret", "insane"]
    punches = calculate_punch_moments(mock_words, clip_start_offset=0.0, duration=35.0, keywords=kws)
    print(f"Calculated punch moments: {punches}")
    assert len(punches) == 2
    assert punches[0] == 5.0
    assert punches[1] == 22.0

    expr = generate_zoompan_expression(punches, duration=35.0, fps=30.0)
    print(f"Generated ZoomPan expression preview: {expr[:100]}...")
    assert "zoompan" in expr
    assert "1.12" in expr
    print("PASS: Punch-In engine correctly targets hook words with smoothstep zoom!")

def test_split_layout():
    print("\n--- TEST: Dual-Speaker Split Layout ---")
    crop_w, crop_h, crop_x, crop_y, half_h = calculate_half_crop(
        orig_w=1920, orig_h=1080, out_w=1080, out_h=1920, center_x=0.25
    )
    print(f"Half crop: w={crop_w}, h={crop_h}, x={crop_x}, y={crop_y}, half_h={half_h}")
    assert crop_w > 0 and crop_h > 0
    assert half_h == 960

    filtergraph = build_split_filtergraph(
        orig_w=1920, orig_h=1080, out_w=1080, out_h=1920, left_center_x=0.25, right_center_x=0.75
    )
    print(f"Generated Split filtergraph preview: {filtergraph[:120]}...")
    assert "vstack=inputs=2" in filtergraph
    assert "split=2" in filtergraph
    print("PASS: Split layout produces valid 1080x960 dual-speaker stack!")

def test_scene_snapping():
    print("\n--- TEST: Scene-Boundary Aware Snapping ---")
    cuts = [4.8, 12.1, 24.95, 38.0]
    # Raw clip start=5.0 (close to 4.8), end=25.0 (close to 24.95)
    s_start, s_end = snap_to_scene_boundaries(start_time=5.0, end_time=25.0, scene_cuts=cuts, snap_window=1.0)
    print(f"Original: 5.0 -> 25.0, Snapped: {s_start} -> {s_end}")
    assert s_start == 4.8
    assert s_end == 24.95
    print("PASS: Candidate boundaries snap cleanly to camera cuts!")

if __name__ == "__main__":
    test_punch_in()
    test_split_layout()
    test_scene_snapping()
    print("\nALL OPENSHORTS ENHANCEMENTS PASSED SUCCESSFULLY!")
