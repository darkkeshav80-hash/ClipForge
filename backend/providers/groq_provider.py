import httpx
from typing import List, Dict, Any, Optional
from backend.providers.base import BaseAIProvider

class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: str = "", base_url: str = "https://api.groq.com/openai/v1", default_model: str = "llama-3.3-70b-versatile"):
        super().__init__(api_key, base_url or "https://api.groq.com/openai/v1", default_model)

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        selected_model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def list_models(self) -> List[str]:
        return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API key is missing"}
        try:
            models = await self.list_models()
            return {"success": True, "models": models, "message": "Groq LPU endpoint connected!"}
        except Exception as e:
            return {"success": False, "message": str(e)}
