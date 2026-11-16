import httpx
from typing import List, Dict, Any, Optional
from backend.providers.base import BaseAIProvider
from backend.core.logger import logger

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str = "", base_url: str = "https://api.openai.com/v1", default_model: str = "gpt-4o-mini"):
        super().__init__(api_key, base_url or "https://api.openai.com/v1", default_model)

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

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def list_models(self) -> List[str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url.rstrip('/')}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", []) if "gpt" in m["id"] or "o1" in m["id"] or "o3" in m["id"]]
                    return models if models else ["gpt-4o-mini", "gpt-4o", "o3-mini"]
        except Exception:
            pass
        return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "o3-mini"]

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API key is missing"}
        try:
            models = await self.list_models()
            return {"success": True, "models": models, "message": f"Successfully connected! {len(models)} models found."}
        except Exception as e:
            return {"success": False, "message": str(e)}
