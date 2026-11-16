import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from backend.video.ffmpeg_engine import ffmpeg_engine
from backend.video.face_tracker import face_tracker

def test_video_probing_and_rendering():
    sample_video = settings.UPLOADS_DIR / "sample_test_source.mp4"
    assert sample_video.exists(), "Sample test video must exist"

    # 1. Test Probing
    info = ffmpeg_engine.probe_video(sample_video)
    assert info["duration"] > 0
    assert info["width"] == 1920
    assert info["height"] == 1080
    assert info["fps"] > 0
    assert info["has_audio"] is True
    print(f"Probed video: {info['width']}x{info['height']} @ {info['fps']}fps, duration: {info['duration']}s")

    # 2. Test Thumbnail Extraction
    thumb_path = settings.THUMBNAILS_DIR / "test_thumb.jpg"
    ffmpeg_engine.extract_thumbnail(sample_video, 1.0, thumb_path)
    assert thumb_path.exists()
    assert thumb_path.stat().st_size > 1000
    print(f"Thumbnail extracted successfully ({thumb_path.stat().st_size} bytes)")

    # 3. Test Face/Center Tracking
    center_x = face_tracker.calculate_speaker_center(sample_video, 0.0, 5.0)
    assert 0.1 <= center_x <= 0.9
    print(f"Center tracker returned: {center_x}")

    # 4. Test 9:16 Vertical Render
    output_clip = settings.CLIPS_DIR / "test_rendered_916.mp4"
    ffmpeg_engine.render_clip(
        input_video=sample_video,
        start_time=0.0,
        duration=4.0,
        output_clip=output_clip,
        aspect_ratio="9:16",
        crop_center_x=center_x,
        normalize_audio=True,
        threads=2
    )
    assert output_clip.exists()
    assert output_clip.stat().st_size > 5000
    
    # Probe rendered clip to verify vertical dimensions
    rendered_info = ffmpeg_engine.probe_video(output_clip)
    assert rendered_info["width"] == 1080
    assert rendered_info["height"] == 1920
    print(f"Rendered 9:16 vertical Short verified: {rendered_info['width']}x{rendered_info['height']} ({output_clip.stat().st_size} bytes)")

if __name__ == "__main__":
    test_video_probing_and_rendering()
    print("ALL VIDEO PROCESSING TESTS PASSED SUCCESSFULLY!")
