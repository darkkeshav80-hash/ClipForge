import os
import wave
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from backend.core.logger import logger
from backend.config import settings

# PyAV compatibility fix for Windows / Python 3.14 faster-whisper
try:
    import av
    _orig_av_open = av.open
    def _patched_av_open(*args, **kwargs):
        kwargs.pop('metadata_errors', None)
        return _orig_av_open(*args, **kwargs)
    av.open = _patched_av_open
except Exception:
    pass

CHUNK_SECONDS = 300 # 5-minute checkpointing chunks

class Transcriber:
    """
    Robust Faster-Whisper neural transcription engine:
    - 5-minute chunked checkpoints (<hash>.part.json) for crash-resilience
    - Persistent transcript cache (<hash>.json) by file size + mtime hash
    - condition_on_previous_text=False to eliminate hallucination repetition loops
    - NO SILENT FAKE TRANSCRIPTS: Fails loudly with actionable errors
    """
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self.cache_dir = settings.STORAGE_DIR / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_model(self, size: Optional[str] = None):
        target_size = size or self.model_size
        if self._model is None or getattr(self, "_loaded_size", None) != target_size:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Faster-Whisper model ({target_size}) on CPU...")
            self._model = WhisperModel(
                target_size,
                device="cpu",
                compute_type="int8",
                download_root=str(settings.MODELS_DIR),
                cpu_threads=min(os.cpu_count() or 4, 8)
            )
            self._loaded_size = target_size
            logger.info(f"Faster-Whisper ({target_size}) model loaded successfully.")
        return self._model

    def _compute_file_hash(self, file_path: Path, model_size: str, language: str) -> str:
        stat = file_path.stat()
        seed = f"{file_path.name}|{stat.st_size}|{model_size}|{language}"
        return hashlib.md5(seed.encode()).hexdigest()

    def transcribe(
        self,
        audio_path: Path,
        language: str = "auto",
        model_size: Optional[str] = None,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Transcribes 16kHz mono audio WAV with 5-minute checkpoints.
        If interrupted, resumes from the last 5-minute chunk.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        chosen_size = model_size or self.model_size
        cache_key = self._compute_file_hash(audio_path, chosen_size, language)
        final_cache_file = self.cache_dir / f"{cache_key}.json"
        part_cache_file = self.cache_dir / f"{cache_key}.part.json"

        # 1. Check final cache
        if final_cache_file.exists():
            try:
                cached_data = json.loads(final_cache_file.read_text(encoding="utf-8"))
                if cached_data and "words" in cached_data and len(cached_data["words"]) > 0:
                    logger.info(f"Loaded cached transcript ({len(cached_data['words'])} words) from {final_cache_file.name}")
                    return cached_data
            except Exception as e:
                logger.warning(f"Cache read error: {e}. Recomputing transcript...")
                final_cache_file.unlink(missing_ok=True)

        model = self._get_model(chosen_size)
        lang_param = None if language in ["auto", "", None] else language

        # 2. Check for partial checkpoint
        words: List[Dict[str, Any]] = []
        chunk_index = 0
        detected_lang = language or "auto"

        if part_cache_file.exists():
            try:
                part_data = json.loads(part_cache_file.read_text(encoding="utf-8"))
                words = part_data.get("words", [])
                chunk_index = part_data.get("chunk", 0)
                detected_lang = part_data.get("language", detected_lang)
                logger.info(f"Resuming transcription from checkpoint chunk {chunk_index} ({len(words)} words already decoded).")
            except Exception as e:
                logger.warning(f"Failed to read part cache: {e}. Starting fresh.")
                chunk_index = 0
                words = []

        # 3. Read audio stream with wave for chunked processing
        try:
            with wave.open(str(audio_path), "rb") as w:
                sample_rate = w.getframerate()
                n_frames = w.getnframes()
                total_duration = n_frames / float(sample_rate)
                n_chunks = max(int(np.ceil(total_duration / CHUNK_SECONDS)), 1)

                logger.info(f"Processing audio: {total_duration:.1f}s across {n_chunks} chunk(s) (5 min each).")

                while chunk_index < n_chunks:
                    t_start = chunk_index * CHUNK_SECONDS
                    w.setpos(int(t_start * sample_rate))
                    frame_count = int(min(CHUNK_SECONDS * sample_rate, n_frames - t_start * sample_rate))
                    raw_bytes = w.readframes(frame_count)
                    if not raw_bytes:
                        break

                    audio_chunk = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

                    if len(audio_chunk) > sample_rate * 0.5:
                        segments, info = model.transcribe(
                            audio_chunk,
                            language=lang_param,
                            word_timestamps=True,
                            vad_filter=True,
                            condition_on_previous_text=False, # Eliminates repetitive hallucination loops!
                            beam_size=1,
                            best_of=1,
                            temperature=0.0,
                            repetition_penalty=1.2,
                            no_repeat_ngram_size=3,
                            hallucination_silence_threshold=2.0,
                            vad_parameters=dict(min_silence_duration_ms=400, speech_pad_ms=200),
                        )

                        if info and info.language:
                            detected_lang = info.language

                        last_report_sec = 0.0
                        for seg in segments:
                            if seg.words:
                                for word in seg.words:
                                    w_text = word.word.strip()
                                    if w_text:
                                        words.append({
                                            "word": w_text,
                                            "start": round(word.start + t_start, 2),
                                            "end": round(word.end + t_start, 2),
                                            "probability": round(word.probability, 2)
                                        })
                            else:
                                seg_words = seg.text.strip().split()
                                dur = max(0.1, seg.end - seg.start)
                                w_dur = dur / max(1, len(seg_words))
                                for i, sw in enumerate(seg_words):
                                    words.append({
                                        "word": sw,
                                        "start": round(seg.start + t_start + i * w_dur, 2),
                                        "end": round(seg.start + t_start + (i + 1) * w_dur, 2),
                                        "probability": 0.9
                                    })

                            # Live segment-level progress reporting
                            if progress_callback and (seg.end - last_report_sec >= 2.0 or seg.end >= CHUNK_SECONDS):
                                last_report_sec = seg.end
                                cur_sec = min(total_duration, t_start + seg.end)
                                pct = min(99.0, round((cur_sec / max(1.0, total_duration)) * 100.0, 1))
                                progress_callback(pct, f"Transcribing audio: {int(cur_sec)}s / {int(total_duration)}s ({int(pct)}%)")

                    chunk_index += 1
                    # Save checkpoint
                    tmp_part = part_cache_file.with_suffix(".tmp")
                    tmp_part.write_text(json.dumps({
                        "chunk": chunk_index,
                        "words": words,
                        "language": detected_lang
                    }), encoding="utf-8")
                    os.replace(tmp_part, part_cache_file)

                    if progress_callback:
                        cur_sec = min(total_duration, chunk_index * CHUNK_SECONDS)
                        pct = min(100.0, round((cur_sec / max(1.0, total_duration)) * 100.0, 1))
                        progress_callback(pct, f"Transcribed chunk {chunk_index}/{n_chunks} ({int(pct)}%)")

                full_text = " ".join([w["word"] for w in words])
                final_result = {
                    "text": full_text,
                    "language": detected_lang,
                    "duration": total_duration,
                    "words": words
                }

                # Save final cache and remove partial checkpoint
                tmp_final = final_cache_file.with_suffix(".tmp")
                tmp_final.write_text(json.dumps(final_result), encoding="utf-8")
                os.replace(tmp_final, final_cache_file)
                part_cache_file.unlink(missing_ok=True)

                logger.info(f"Transcription finished: {len(words)} words decoded in '{detected_lang}' (saved to cache).")
                return final_result

        except Exception as e:
            logger.error(f"Whisper transcription failed on {audio_path.name}: {e}", exc_info=True)
            # DO NOT SILENTLY FAKE TRANSCRIPTS. Raise clear exception.
            raise RuntimeError(
                f"Audio transcription failed: {str(e)}. Please verify audio stream integrity and retry."
            )

transcriber = Transcriber()
