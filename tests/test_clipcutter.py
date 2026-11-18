import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings
from backend.api.clipcutter import _validate_youtube_url, ALLOWED_YOUTUBE_HOSTS


class TestClipCutter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_youtube_url_whitelist(self):
        # Valid youtube URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                res = _validate_youtube_url(url)
                self.assertEqual(res, url)

        # Invalid domains or schemes
        invalid_urls = [
            "https://vimeo.com/123456",
            "https://twitch.tv/streamer",
            "https://evil.com/fake-youtube",
            "http://127.0.0.1:8000/api",
            "http://localhost:3000",
            "file:///C:/Windows/System32",
        ]
        for url in invalid_urls:
            with self.subTest(url=url), self.assertRaises(HTTPException):
                _validate_youtube_url(url)

    def test_clip_range_validation(self):
        # end <= start
        res = self.client.post("/api/clipcutter/clip", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "start": 10.0,
            "end": 5.0,
            "quality": "720"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("greater than start", res.json()["detail"])

        # duration > MAX_CLIP_SECONDS
        res = self.client.post("/api/clipcutter/clip", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "start": 0.0,
            "end": float(settings.MAX_CLIP_SECONDS + 100),
            "quality": "720"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("exceeds the maximum allowed limit", res.json()["detail"])

    def test_download_path_traversal_blocked(self):
        bad_filenames = [
            "../secret.txt",
            "..\\config.py",
            "subdir/file.mp4",
            "../../storage/clipforge.db",
        ]
        for fn in bad_filenames:
            with self.subTest(filename=fn):
                res = self.client.get(f"/api/clipcutter/file/{fn}")
                self.assertIn(res.status_code, (400, 404))

    @patch("backend.api.clipcutter.yt_dlp.YoutubeDL")
    def test_get_clip_info_mocked(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
            "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            "duration": 213,
            "is_live": False,
            "was_live": False,
            "formats": [
                {"height": 360, "acodec": "mp4a.40.2"},
                {"height": 720, "acodec": "mp4a.40.2"},
                {"height": 1080, "acodec": "none"},
            ]
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        res = self.client.post("/api/clipcutter/info", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["video_id"], "dQw4w9WgXcQ")
        self.assertEqual(data["title"], "Never Gonna Give You Up")
        self.assertEqual(data["channel"], "Rick Astley")
        self.assertEqual(data["duration"], 213)
        self.assertIn(720, data["available_heights"])
        self.assertIn(1080, data["available_heights"])

    @patch("backend.api.clipcutter.ffmpeg_engine.extract_thumbnail")
    @patch("backend.api.clipcutter.ffmpeg_engine.probe_video")
    @patch("backend.api.clipcutter.yt_dlp.YoutubeDL")
    def test_cut_clip_mocked(self, mock_ydl_cls, mock_probe, mock_thumb):
        # Mock probe
        mock_probe.return_value = {
            "duration": 15.0,
            "width": 1920,
            "height": 1080,
            "fps": 30.0
        }

        # Mock YoutubeDL
        def mock_ydl_download(urls):
            # Create a fake output file in UPLOADS_DIR
            out_files = list(settings.UPLOADS_DIR.glob("clipcut_*"))
            # The code searches for clipcut_{video_id}...
            return None

        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {"id": "test1234", "is_live": False}
        
        def fake_download(urls):
            # Touch the expected file
            for p in settings.UPLOADS_DIR.glob("clipcut_*"):
                pass
            p = settings.UPLOADS_DIR / "clipcut_test1234_10_25_mocked.mp4"
            p.write_bytes(b"dummy mp4 content")
            return None

        mock_instance.download = fake_download
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        # Also patch download_range_func
        with patch("backend.api.clipcutter.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = "mocked"
            res = self.client.post("/api/clipcutter/clip", json={
                "url": "https://www.youtube.com/watch?v=test1234",
                "start": 10.0,
                "end": 25.0,
                "quality": "1080"
            })

            # Clean up created dummy file
            dummy_file = settings.UPLOADS_DIR / "clipcut_test1234_10_25_mocked.mp4"
            if dummy_file.exists():
                dummy_file.unlink()

            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["duration"], 15.0)
            self.assertEqual(data["width"], 1920)
            self.assertEqual(data["height"], 1080)
            self.assertTrue(data["download_url"].startswith("/api/clipcutter/file/"))


if __name__ == "__main__":
    unittest.main()
