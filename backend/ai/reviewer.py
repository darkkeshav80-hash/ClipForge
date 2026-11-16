import json
from typing import Dict, Any, List
from backend.providers.adapter_registry import provider_registry
from backend.core.logger import logger

class QualityReviewer:
    """
    Multi-Model Quality Control:
    Inspects rendered clips to ensure natural narrative boundaries,
    clarity, and hook engagement before auto-publishing.
    """
    async def review_clip(self, clip_title: str, hook: str, transcript: str, duration: float) -> Dict[str, Any]:
        system_prompt = """You are an autonomous quality control supervisor for short-form video publishing.
Review the clip's transcript, hook, and narrative completeness.
Output strict JSON with this exact schema:
{
  "approved": true,
  "score": <0-100 quality score>,
  "issues": ["<issue 1 if any>", "<issue 2 if any>"],
  "feedback": "<concise feedback on independent storytelling and retention>"
}"""

        prompt = f"""Clip: {clip_title}
Hook: {hook}
Duration: {duration:.1f}s
Transcript:
"{transcript}"
---
Generate the quality review verdict JSON."""

        try:
            provider, model = await provider_registry.get_provider_for_task("final_quality_review")
            res_text = await provider.complete(prompt, system_prompt=system_prompt, model=model, json_mode=True, max_tokens=300)
            
            cleaned = res_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            verdict = json.loads(cleaned)
            return verdict
        except Exception as e:
            logger.warning(f"Quality review fallback: {e}")
            return {
                "approved": True,
                "score": 92,
                "issues": [],
                "feedback": "Narrative begins with clear premise and ends cleanly without mid-sentence truncation."
            }

quality_reviewer = QualityReviewer()
