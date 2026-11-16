import json
from typing import Dict, Any, List
from backend.providers.adapter_registry import provider_registry
from backend.core.logger import logger

class EditingBrain:
    """
    Intelligent Editing Decision Engine:
    Transforms raw transcript moments into structured execution plans.
    """
    async def generate_editing_plan(
        self,
        clip_id: str,
        start_time: float,
        end_time: float,
        transcript: str,
        category: str = "podcast",
        default_preset: str = "mrbeast-bold",
    ) -> Dict[str, Any]:
        duration = round(end_time - start_time, 2)
        system_prompt = """You are an elite video editing director specialized in autonomous 9:16 vertical shorts.
Given a video moment timestamp range and transcript, formulate an intelligent editing decision plan.
Always output strict JSON with this exact schema:
{
  "hook_text": "<punchy 1-sentence hook to display on the first frame>",
  "keywords": ["<punchy hook word 1>", "<emphasis word 2>"],
  "important_sentences": ["<key sentence 1>", "<key sentence 2>"],
  "silence_removal": true,
  "zooms": [
    {"timestamp": <seconds offset from start>, "type": "zoom_in", "scale": 1.15}
  ],
  "caption_preset": "<one of: mrbeast-bold, hormozi-emphasis, clean-white, yellow-highlight, neon-gaming, karaoke-highlight, pop-up-animation>",
  "caption_placement": "bottom",
  "target_aspect_ratio": "9:16",
  "face_tracking": true,
  "speaker_tracking": true,
  "crop_center_x": 0.5,
  "audio_enhanced": true,
  "recommended_resolution": "1080p"
}"""

        prompt = f"""Moment: {start_time:.1f}s to {end_time:.1f}s (Duration: {duration:.1f}s)
Category: {category}
Preferred Preset: {default_preset}
Transcript:
"{transcript}"
---
Generate the editing plan JSON."""

        try:
            provider, model = await provider_registry.get_provider_for_task("editing_decisions")
            res_text = await provider.complete(prompt, system_prompt=system_prompt, model=model, json_mode=True, max_tokens=600)
            
            cleaned = res_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            plan = json.loads(cleaned)
            plan["clip_id"] = clip_id
            plan["start_time"] = start_time
            plan["end_time"] = end_time
            plan["duration"] = duration
            return plan
        except Exception as e:
            logger.warning(f"Editing brain fallback due to: {e}")
            # Deterministic fallback plan
            sentences = transcript.split(". ")
            first_sentence = sentences[0].strip() if sentences else transcript[:60]
            # Extract high-energy keyword candidates for zoom and subtitle highlights
            words_in_hook = [w.strip(".,!?:;\"'()").lower() for w in first_sentence.split()]
            stop_words = {"the", "and", "a", "an", "in", "on", "at", "to", "for", "of", "with", "is", "it", "this", "that"}
            fallback_kws = [w for w in words_in_hook if len(w) >= 4 and w not in stop_words][:4]

            return {
                "clip_id": clip_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "hook_text": first_sentence[:70],
                "keywords": fallback_kws,
                "important_sentences": sentences[:2],
                "unnecessary_pauses": [],
                "silence_removal": True,
                "zooms": [{"timestamp": round(start_time + 3.0, 1), "type": "zoom_in", "scale": 1.15}],
                "caption_preset": default_preset,
                "caption_placement": "bottom",
                "target_aspect_ratio": "9:16",
                "face_tracking": True,
                "speaker_tracking": True,
                "crop_center_x": 0.5,
                "audio_enhanced": True,
                "recommended_resolution": "1080p",
            }

editing_brain = EditingBrain()
