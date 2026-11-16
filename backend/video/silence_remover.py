import re
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple
from backend.core.logger import logger

class SilenceDetector:
    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    def detect_silences(self, audio_path: Path, noise_db: int = -32, min_duration: float = 0.5) -> List[Tuple[float, float]]:
        """
        Returns list of (start_time, end_time) ranges representing silent pauses.
        """
        cmd = [
            self.ffmpeg_path,
            "-i", str(audio_path),
            "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
            "-f", "null",
            "-",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        output = res.stderr

        silence_starts = []
        silence_ends = []

        for line in output.splitlines():
            if "silence_start:" in line:
                m = re.search(r"silence_start:\s*([\d\.]+)", line)
                if m:
                    silence_starts.append(float(m.group(1)))
            elif "silence_end:" in line:
                m = re.search(r"silence_end:\s*([\d\.]+)", line)
                if m:
                    silence_ends.append(float(m.group(1)))

        pauses = []
        for i in range(min(len(silence_starts), len(silence_ends))):
            pauses.append((silence_starts[i], silence_ends[i]))

        logger.info(f"Detected {len(pauses)} silence pauses in {audio_path.name}")
        return pauses

silence_detector = SilenceDetector()
