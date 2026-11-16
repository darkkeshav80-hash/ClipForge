import asyncio
import unittest
from backend.ai.analyzer import VideoAnalyzer

class TestClipQuotaSelection(unittest.TestCase):
    def setUp(self):
        self.analyzer = VideoAnalyzer()

    def test_guaranteed_clip_quota_when_only_one_clears_threshold(self):
        """Verifies that if min_viral_score is high and only 1 candidate clears it,
        the analyzer tops up to the user-requested target_clips (e.g. 5) instead of returning just 1."""
        # 100 seconds of speech words
        words = []
        for i in range(120):
            t_start = i * 0.8
            t_end = t_start + 0.7
            punct = "." if i % 10 == 9 else ""
            words.append({
                "word": f"word{i}{punct}",
                "start": round(t_start, 2),
                "end": round(t_end, 2)
            })

        transcript_data = {
            "text": " ".join(w["word"] for w in words),
            "words": words,
            "language": "en"
        }

        async def run_discovery():
            # Request 5 clips with an aggressive min_viral_score of 92
            return await self.analyzer.discover_clips(
                transcript_data=transcript_data,
                target_clips=5,
                min_duration=15.0,
                max_duration=60.0,
                min_viral_score=92,
                default_preset="mrbeast"
            )

        clips = asyncio.run(run_discovery())
        self.assertEqual(len(clips), 5, f"Expected exactly 5 clips, but got {len(clips)}")
        # Check scores are sorted descending
        scores = [c["viral_score"]["overall"] for c in clips]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_short_transcript_generates_multiple_candidate_moments(self):
        """Verifies that even a short 40-second transcript yields multiple candidate clips via sliding window."""
        words = []
        for i in range(50):
            t_start = i * 0.8
            t_end = t_start + 0.7
            punct = "!" if i in (15, 30, 49) else ""
            words.append({
                "word": f"sentence{i}{punct}",
                "start": round(t_start, 2),
                "end": round(t_end, 2)
            })

        transcript_data = {
            "text": " ".join(w["word"] for w in words),
            "words": words,
            "language": "en"
        }

        async def run_discovery():
            return await self.analyzer.discover_clips(
                transcript_data=transcript_data,
                target_clips=3,
                min_duration=10.0,
                max_duration=30.0,
                min_viral_score=70,
                default_preset="hormozi"
            )

        clips = asyncio.run(run_discovery())
        self.assertGreaterEqual(len(clips), 2, f"Expected at least 2 clips for short video, got {len(clips)}")

if __name__ == "__main__":
    unittest.main()
