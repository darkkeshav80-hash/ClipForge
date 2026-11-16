import re
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.core.logger import logger

class CaptionSyncValidator:
    """
    Validates synchronization between burned-in ASS captions and spoken audio words.
    Flags any clip where median offset exceeds 100ms.
    """
    @staticmethod
    def parse_ass_dialogues(ass_path: Path) -> List[Dict[str, Any]]:
        if not ass_path.exists():
            return []
        dialogues = []
        lines = ass_path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) >= 10:
                    layer = int(parts[0].replace("Dialogue:", "").strip())
                    if layer == 0: # Only caption layer
                        s_parts = parts[1].strip().split(":")
                        e_parts = parts[2].strip().split(":")
                        start_s = int(s_parts[0]) * 3600 + int(s_parts[1]) * 60 + float(s_parts[2])
                        end_s = int(e_parts[0]) * 3600 + int(e_parts[1]) * 60 + float(e_parts[2])
                        clean_text = re.sub(r"\{.*?\}", "", parts[9]).strip()
                        dialogues.append({"start": start_s, "end": end_s, "text": clean_text})
        return dialogues

    def evaluate_sync(
        self,
        ass_path: Path,
        reference_words: List[Dict[str, Any]],
        clip_start_offset: float = 0.0,
        sync_offset_applied: float = 0.0
    ) -> Dict[str, Any]:
        """
        Compares reference Whisper word timestamps against the generated ASS dialogue events.
        """
        dialogues = self.parse_ass_dialogues(ass_path)
        if not dialogues or not reference_words:
            return {"synced": True, "median_offset_ms": 0.0, "max_offset_ms": 0.0, "events_checked": 0}

        offsets = []
        for d in dialogues:
            # Find the best matching word near this dialogue's start
            target_start = d["start"]
            closest_word = min(
                reference_words,
                key=lambda w: abs((w["start"] - clip_start_offset + sync_offset_applied) - target_start)
            )
            expected_start = max(0.0, closest_word["start"] - clip_start_offset + sync_offset_applied)
            diff_ms = abs(target_start - expected_start) * 1000.0
            offsets.append(diff_ms)

        if not offsets:
            return {"synced": True, "median_offset_ms": 0.0, "max_offset_ms": 0.0, "events_checked": 0}

        median_ms = float(np.median(offsets))
        max_ms = float(np.max(offsets))
        is_synced = median_ms <= 100.0

        if not is_synced:
            logger.warning(
                f"[SYNC WARNING] Clip captions median offset is {median_ms:.1f}ms (> 100ms threshold)! "
                f"Ass file: {ass_path.name}"
            )
        else:
            logger.info(f"Clip caption sync verified: median offset = {median_ms:.1f}ms (< 100ms threshold).")

        return {
            "synced": is_synced,
            "median_offset_ms": round(median_ms, 1),
            "max_offset_ms": round(max_ms, 1),
            "events_checked": len(offsets),
        }

sync_validator = CaptionSyncValidator()
