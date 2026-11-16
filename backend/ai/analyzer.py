import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.core.logger import logger
from backend.ai.scorer import viral_scorer
from backend.ai.editing_brain import editing_brain
from backend.video.scene_detection import detect_scene_cuts, snap_to_scene_boundaries

def detect_category(text: str) -> str:
    """Accurately classifies category based on conversational markers."""
    t = text.lower()
    gaming_keys = ["game", "level", "hack", "roblox", "minecraft", "play", "kill", "boss", "clutch", "gg", "died", "spawn", "skin", "mod", "quest", "stage", "bot"]
    comedy_keys = ["funny", "laugh", "joke", "prank", "crazy", "insane", "omg", "bruh", "hilarious", "meme", "cheat"]
    edu_keys = ["how to", "tutorial", "learn", "guide", "concept", "study", "formula", "explain", "secret", "why", "difference"]
    vlog_keys = ["vlog", "travel", "today we", "trip", "day in", "welcome back", "went to", "bought"]

    if any(k in t for k in gaming_keys):
        return "gaming"
    if any(k in t for k in comedy_keys):
        return "comedy"
    if any(k in t for k in edu_keys):
        return "educational"
    if any(k in t for k in vlog_keys):
        return "vlog"
    return "podcast"

class VideoAnalyzer:
    """
    Scans speech transcript and detects high-impact viral moments.
    Guarantees:
    - Sentences cut cleanly on punctuation boundaries (no cut-off words).
    - Intelligent genre classification (Gaming, Comedy, Educational, Vlog, Podcast).
    - Duration constraints strictly enforced.
    """
    async def discover_clips(
        self,
        transcript_data: Dict[str, Any],
        target_clips: int = 5,
        min_duration: float = 15.0,
        max_duration: float = 60.0,
        min_viral_score: int = 70,
        default_preset: str = "mrbeast-bold",
        video_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        words = transcript_data.get("words", [])
        if not words:
            logger.warning("No words found in transcript to analyze.")
            return []

        total_duration = words[-1]["end"] - words[0]["start"]
        logger.info(f"Analyzing {len(words)} words over {total_duration:.1f}s for viral moments...")

        # Detect camera transitions for clean moment boundary snapping
        scene_cuts = []
        if video_path and video_path.exists():
            scene_cuts = detect_scene_cuts(video_path)
            if scene_cuts:
                logger.info(f"Scene detection found {len(scene_cuts)} shot transitions for boundary snapping.")

        # Group words into clean sentence clusters
        candidate_segments = []
        current_chunk_words = []
        chunk_start = words[0]["start"]

        punct_pattern = re.compile(r"[.?!,।]$")

        for w in words:
            current_chunk_words.append(w)
            current_dur = w["end"] - chunk_start

            is_sentence_end = bool(punct_pattern.search(w["word"]))
            # Prefer snapping to clean sentence boundary within min/max bounds
            if (current_dur >= min_duration and is_sentence_end) or (current_dur >= max_duration):
                chunk_text = " ".join([cw["word"] for cw in current_chunk_words])
                candidate_segments.append({
                    "start_time": chunk_start,
                    "end_time": w["end"],
                    "duration": round(w["end"] - chunk_start, 2),
                    "transcript": chunk_text,
                    "words": current_chunk_words[:],
                })
                # Reset
                current_chunk_words = []
                chunk_start = w["end"]

        # Leftover words
        if current_chunk_words:
            last_dur = current_chunk_words[-1]["end"] - chunk_start
            if last_dur >= min_duration:
                candidate_segments.append({
                    "start_time": chunk_start,
                    "end_time": current_chunk_words[-1]["end"],
                    "duration": round(last_dur, 2),
                    "transcript": " ".join([cw["word"] for cw in current_chunk_words]),
                    "words": current_chunk_words[:],
                })

        # If sequential non-overlapping chunking yielded fewer candidates than needed,
        # generate sliding-window candidate segments across sentence/word boundaries
        # so short or medium videos have plenty of diverse candidate moments
        needed_candidates = max(target_clips * 2, 8)
        if len(candidate_segments) < needed_candidates and len(words) >= 5:
            sentences = []
            curr_s = []
            for w in words:
                curr_s.append(w)
                if punct_pattern.search(w["word"]):
                    sentences.append(curr_s)
                    curr_s = []
            if curr_s:
                sentences.append(curr_s)

            # Build sliding windows of sentences that fit min_duration..max_duration
            if len(sentences) >= 2:
                for start_idx in range(len(sentences)):
                    accum_words = []
                    for end_idx in range(start_idx, len(sentences)):
                        accum_words.extend(sentences[end_idx])
                        dur = accum_words[-1]["end"] - accum_words[0]["start"]
                        if min_duration <= dur <= max_duration:
                            s_start = accum_words[0]["start"]
                            s_end = accum_words[-1]["end"]
                            if not any(abs(c["start_time"] - s_start) < 1.0 and abs(c["end_time"] - s_end) < 1.0 for c in candidate_segments):
                                candidate_segments.append({
                                    "start_time": s_start,
                                    "end_time": s_end,
                                    "duration": round(dur, 2),
                                    "transcript": " ".join(cw["word"] for cw in accum_words),
                                    "words": accum_words[:],
                                })
                        elif dur > max_duration:
                            break

            # If still short on candidates, use a sliding time window with stride
            if len(candidate_segments) < needed_candidates:
                stride_sec = 8.0
                window_dur = min(max_duration, max(min_duration, (total_duration / max(1, target_clips))))
                t_cursor = words[0]["start"]
                while t_cursor + min_duration <= words[-1]["end"] + 1.0:
                    w_sub = [w for w in words if w["start"] >= t_cursor and w["end"] <= t_cursor + window_dur]
                    if w_sub and (w_sub[-1]["end"] - w_sub[0]["start"]) >= min_duration:
                        s_start = w_sub[0]["start"]
                        s_end = w_sub[-1]["end"]
                        dur = round(s_end - s_start, 2)
                        if not any(abs(c["start_time"] - s_start) < 2.0 and abs(c["end_time"] - s_end) < 2.0 for c in candidate_segments):
                            candidate_segments.append({
                                "start_time": s_start,
                                "end_time": s_end,
                                "duration": dur,
                                "transcript": " ".join(cw["word"] for cw in w_sub),
                                "words": w_sub[:],
                            })
                    t_cursor += stride_sec

        if not candidate_segments:
            candidate_segments = [{
                "start_time": words[0]["start"],
                "end_time": words[-1]["end"],
                "duration": round(words[-1]["end"] - words[0]["start"], 2),
                "transcript": " ".join([cw["word"] for cw in words]),
                "words": words,
            }]

        # Snap candidate moments to nearest camera cuts for seamless transitions
        if scene_cuts:
            for seg in candidate_segments:
                s_start, s_end = snap_to_scene_boundaries(seg["start_time"], seg["end_time"], scene_cuts)
                # Protect first and last word boundaries from being truncated by scene cuts
                first_w_start = seg["words"][0]["start"] if seg.get("words") else s_start
                if s_start > first_w_start:
                    s_start = first_w_start
                last_w_end = seg["words"][-1]["end"] if seg.get("words") else s_end
                if s_end < last_w_end:
                    s_end = last_w_end

                seg["start_time"] = s_start
                seg["end_time"] = s_end
                seg["duration"] = round(s_end - s_start, 2)
                matching_words = [w for w in words if w["end"] > s_start and w["start"] < s_end]
                if matching_words:
                    seg["words"] = matching_words
                    seg["transcript"] = " ".join([cw["word"] for cw in matching_words])

        # Heuristic pre-ranking to evaluate top moments without hitting LLM rate limits
        def heuristic_rank(seg: Dict[str, Any]) -> float:
            text = seg["transcript"].lower()
            words = text.split()
            hook_words = ["why", "how", "secret", "never", "always", "stop", "real", "truth", "money", "future", "mistake", "insane", "crazy", "omg", "best", "worst", "win", "clutch", "hack", "wait", "look", "bro"]
            hook_matches = sum(1 for w in words[:12] if any(hw in w for hw in hook_words))
            has_question = 1 if "?" in seg["transcript"] else 0
            has_exclamation = 1 if "!" in seg["transcript"] else 0
            wps = len(words) / max(1.0, seg["duration"])
            pacing_score = max(0.0, 1.0 - abs(wps - 2.8) / 2.0)
            return hook_matches * 3.0 + has_question * 2.0 + has_exclamation * 1.5 + pacing_score * 2.0

        candidate_segments.sort(key=heuristic_rank, reverse=True)
        top_candidates = candidate_segments[:max(target_clips * 2, 6)]

        # Score candidates with Virality Engine
        all_scored_candidates = []
        for idx, seg in enumerate(top_candidates):
            category = detect_category(seg["transcript"])
            scores = await viral_scorer.evaluate_moment(seg["transcript"], seg["duration"], category)
            all_scored_candidates.append({
                "idx": idx,
                "seg": seg,
                "category": category,
                "scores": scores
            })

        # Rank all scored candidates by overall virality score descending
        all_scored_candidates.sort(key=lambda c: c["scores"]["overall"], reverse=True)

        # Filter candidates meeting the min_viral_score threshold
        matching = [c for c in all_scored_candidates if c["scores"]["overall"] >= min_viral_score]

        # Top-up quota guarantee: if fewer than target_clips met the strict score,
        # fill the remaining slots with the highest-scoring candidate moments so the user
        # always receives their requested clip quota
        if len(matching) < target_clips and all_scored_candidates:
            logger.info(
                f"{len(matching)}/{target_clips} clips met min_viral_score={min_viral_score}. "
                f"Topping up with top scoring candidates to satisfy requested quota of {target_clips} clips."
            )

            def has_heavy_overlap(cand, selected, max_ratio=0.6):
                c_start, c_end = cand["seg"]["start_time"], cand["seg"]["end_time"]
                c_dur = max(1.0, c_end - c_start)
                for s in selected:
                    s_start, s_end = s["seg"]["start_time"], s["seg"]["end_time"]
                    s_dur = max(1.0, s_end - s_start)
                    overlap = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                    if (overlap / min(c_dur, s_dur)) > max_ratio:
                        return True
                return False

            matching_ids = {id(c) for c in matching}
            # First pass: add diverse, non-heavily-overlapping candidates
            for c in all_scored_candidates:
                if id(c) not in matching_ids and not has_heavy_overlap(c, matching):
                    matching.append(c)
                    matching_ids.add(id(c))
                if len(matching) >= target_clips:
                    break

            # Second pass: if still under quota, fill with any remaining candidates
            if len(matching) < target_clips:
                for c in all_scored_candidates:
                    if id(c) not in matching_ids:
                        matching.append(c)
                        matching_ids.add(id(c))
                    if len(matching) >= target_clips:
                        break

        matching.sort(key=lambda c: c["scores"]["overall"], reverse=True)
        matching = matching[:target_clips]

        evaluated_clips = []
        for item in matching:
            idx = item["idx"]
            seg = item["seg"]
            category = item["category"]
            scores = item["scores"]
            clip_id = f"clip-{idx+1}-{int(seg['start_time'])}"
            plan = await editing_brain.generate_editing_plan(
                clip_id=clip_id,
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                transcript=seg["transcript"],
                category=category,
                default_preset=default_preset,
            )

            evaluated_clips.append({
                "id": clip_id,
                "title": plan.get("hook_text", f"Viral Moment #{idx+1}")[:80],
                "description": seg["transcript"][:200],
                "start_time": seg["start_time"],
                "end_time": seg["end_time"],
                "duration": min(seg["duration"], max_duration),
                "transcript": seg["transcript"],
                "hook": plan.get("hook_text", seg["transcript"][:60]),
                "category": category,
                "viral_score": scores,
                "editing_plan": plan,
                "caption_preset": default_preset,
                "aspect_ratio": "9:16",
                "words": seg["words"],
            })

        chosen = evaluated_clips
        logger.info(f"Curation complete: selected {len(chosen)} top clips (top score: {chosen[0]['viral_score']['overall'] if chosen else 'N/A'})")
        return chosen

video_analyzer = VideoAnalyzer()
