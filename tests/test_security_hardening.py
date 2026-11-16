import unittest
from fastapi import HTTPException
from backend.core.security import (
    validate_public_url, unique_filename, mask_api_key, is_masked_key,
)


class TestSecurityHardening(unittest.TestCase):
    def test_ssrf_blocks_local_and_private_targets(self):
        for url in (
            "http://127.0.0.1/x", "http://localhost:8000/api", "http://169.254.169.254/latest",
            "http://10.0.0.5/a", "http://[::1]/", "file:///etc/passwd", "ftp://example.com",
        ):
            with self.subTest(url=url), self.assertRaises(HTTPException):
                validate_public_url(url)

    def test_unique_filename_never_collides_and_keeps_extension(self):
        a, b = unique_filename("my video.MP4"), unique_filename("my video.MP4")
        self.assertNotEqual(a, b)
        self.assertTrue(a.endswith(".mp4"))

    def test_masked_keys_are_detected(self):
        self.assertTrue(is_masked_key(mask_api_key("sk-abcdefghij1234")))
        self.assertFalse(is_masked_key("sk-abcdefghij1234"))


if __name__ == "__main__":
    unittest.main()
