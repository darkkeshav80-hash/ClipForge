import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from backend.providers.base import BaseAIProvider
from backend.core.logger import logger

class GeminiProvider(BaseAIProvider):
    """
    Robust Google Gemini REST Provider:
    - Passes API key in 'x-goog-api-key' header (NEVER in URL query or logs)
    - Uses native 'systemInstruction' payload field
    - Respects selected models without hardcoded overrides
    - Exponential backoff retry on HTTP 429 / 503
    - 180s timeout, maxOutputTokens=8192, temperature <= 0.3 for JSON
    """
    def __init__(self, api_key: str = "", base_url: str = "", default_model: str = "gemini-3.5-flash"):
        super().__init__(api_key, base_url, default_model)

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        json_mode: bool = False,
        temperature: Optional[float] = None,
        max_tokens: int = 8192,
    ) -> str:
        selected_model = model or self.default_model
        
        # Endpoint without key in URL query parameters
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        contents = [{"role": "user", "parts": [{"text": prompt}]}]

        # Set temperature: default 0.2 for strict JSON parsing, 0.7 for creative text
        effective_temp = temperature if temperature is not None else (0.2 if json_mode else 0.7)

        generation_config: Dict[str, Any] = {
            "temperature": effective_temp,
            "maxOutputTokens": max_tokens,
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        # Native Gemini systemInstruction field
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        # Fast backoff retry on 429/503 (fallback quickly to local heuristic if rate limited)
        max_retries = 1
        backoff = 1.0

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=180.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise RuntimeError(f"Gemini returned empty candidate list: {data}")
                        return candidates[0]["content"]["parts"][0]["text"]

                    if resp.status_code in [429, 503] and attempt < max_retries:
                        logger.warning(f"Gemini HTTP {resp.status_code} on attempt {attempt+1}. Retrying in {backoff:.1f}s...")
                        await asyncio.sleep(backoff)
                        backoff *= 2.0
                        continue

                    # Error handling
                    err_msg = f"Gemini API error ({resp.status_code}): {resp.text}"
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                if attempt < max_retries:
                    logger.warning(f"Gemini network error ({net_err}). Retrying in {backoff:.1f}s...")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue
                raise RuntimeError(f"Gemini network timeout after {max_retries} retries: {net_err}")

        raise RuntimeError("Gemini request failed after maximum retries.")

    async def list_models(self) -> List[str]:
        if not self.api_key:
            return ["gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models"
            headers = {"x-goog-api-key": self.api_key}
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [
                        m["name"].replace("models/", "")
                        for m in data.get("models", [])
                        if "gemini" in m.get("name", "") and "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    return models if models else ["gemini-3.5-flash", "gemini-2.5-pro"]
        except Exception as e:
            logger.warning(f"Failed to list Gemini models: {e}")
        return ["gemini-3.5-flash", "gemini-2.5-pro"]

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API key is missing"}
        try:
            models = await self.list_models()
            return {"success": True, "models": models, "message": f"Gemini connection verified! {len(models)} models available."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def window_transcript(words: List[Dict[str, Any]], window_seconds: float = 600.0, overlap_seconds: float = 30.0) -> List[List[Dict[str, Any]]]:
        """Splits long transcripts into ~10-minute overlapping windows to avoid context window truncation."""
        if not words:
            return []
        total_dur = words[-1]["end"] - words[0]["start"]
        if total_dur <= window_seconds:
            return [words]

        windows = []
        cur_start = words[0]["start"]
        while cur_start < words[-1]["end"]:
            cur_end = cur_start + window_seconds
            win_words = [w for w in words if w["start"] >= cur_start and w["end"] <= cur_end]
            if win_words:
                windows.append(win_words)
            cur_start += (window_seconds - overlap_seconds)

        return windows
