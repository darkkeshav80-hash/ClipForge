import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from backend.api.videos import URLImportRequest, import_url

class TestLivestreamClipping(unittest.TestCase):
    def test_url_import_request_defaults(self):
        req = URLImportRequest(url="https://youtube.com/watch?v=123")
        self.assertEqual(req.url, "https://youtube.com/watch?v=123")
        self.assertEqual(req.live_clip_minutes, 10)
        self.assertEqual(req.live_mode, "last")

    def test_url_import_request_custom(self):
        req = URLImportRequest(url="https://youtube.com/watch?v=123", live_clip_minutes=5, live_mode="next")
        self.assertEqual(req.live_clip_minutes, 5)
        self.assertEqual(req.live_mode, "next")

    @patch("backend.api.videos.validate_public_url")
    @patch("yt_dlp.YoutubeDL")
    @patch("backend.video.ffmpeg_engine.ffmpeg_engine.probe_video")
    @patch("backend.video.ffmpeg_engine.ffmpeg_engine.extract_thumbnail")
    def test_regular_video_uses_standard_pipeline(self, mock_thumb, mock_probe, mock_ydl, mock_val):
        mock_val.side_effect = lambda u: u
        mock_probe.return_value = {"duration": 120.0, "width": 1920, "height": 1080, "fps": 30.0}

        # Setup mock YDL for regular video
        ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = ydl_instance
        ydl_instance.extract_info.return_value = {
            "title": "Standard Video",
            "is_live": False,
            "live_status": "not_live",
            "duration": 120.0,
        }
        test_file = Path("backend/api/videos.py").resolve() # existing file for Path.exists()
        ydl_instance.prepare_filename.return_value = str(test_file)

        import asyncio
        req = URLImportRequest(url="https://www.youtube.com/watch?v=normalvideo")
        result = asyncio.run(import_url(req))

        self.assertFalse(result["is_live"])
        self.assertEqual(result["duration"], 120.0)

    @patch("backend.api.videos.validate_public_url")
    @patch("yt_dlp.YoutubeDL")
    @patch("subprocess.run")
    @patch("backend.video.ffmpeg_engine.ffmpeg_engine.probe_video")
    @patch("backend.video.ffmpeg_engine.ffmpeg_engine.extract_thumbnail")
    def test_live_stream_captures_window(self, mock_thumb, mock_probe, mock_subproc, mock_ydl, mock_val):
        mock_val.side_effect = lambda u: u
        mock_probe.return_value = {"duration": 300.0, "width": 1920, "height": 1080, "fps": 60.0}

        # Setup mock YDL for live stream
        ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = ydl_instance
        ydl_instance.extract_info.return_value = {
            "title": "Breaking News Live",
            "id": "live123",
            "is_live": True,
            "live_status": "is_live",
            "formats": [
                {"format_id": "1080p", "height": 1080, "url": "https://stream.example.com/hls.m3u8"}
            ]
        }

        # Mock successful subprocess FFmpeg run
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_subproc.return_value = mock_res

        # Patch Path.exists and stat to simulate captured file
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 5000000

            import asyncio
            req = URLImportRequest(url="https://www.youtube.com/watch?v=livestream123", live_clip_minutes=5, live_mode="last")
            result = asyncio.run(import_url(req))

            self.assertTrue(result["is_live"])
            self.assertEqual(result["title"], "Breaking News Live")
            # Verify FFmpeg was called with -sseof -300
            ffmpeg_calls = mock_subproc.call_args_list
            self.assertTrue(any("-sseof" in c[0][0] and "-300" in c[0][0] for c in ffmpeg_calls))

if __name__ == "__main__":
    unittest.main()
