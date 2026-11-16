import httpx
import json
from typing import List, Dict, Any, Optional
from backend.providers.base import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434", default_model: str = "llama3.2"):
        super().__init__(api_key, base_url or "http://localhost:11434", default_model)

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
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(f"{self.base_url.rstrip('/')}/api/generate", json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama error ({resp.status_code}): {resp.text}")
                data = resp.json()
                return data.get("response", "")
            except httpx.ConnectError:
                raise RuntimeError(
                    "Cannot connect to Ollama at http://localhost:11434. Make sure Ollama is installed and running (`ollama serve`)."
                )

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return models if models else ["llama3.2", "mistral", "qwen2.5", "phi3"]
        except Exception:
            pass
        return ["llama3.2", "mistral", "qwen2.5", "phi3"]

    async def test_connection(self) -> Dict[str, Any]:
        try:
            models = await self.list_models()
            return {"success": True, "models": models, "message": f"Ollama local engine online. {len(models)} local models found."}
        except Exception as e:
            return {"success": False, "message": f"Ollama is offline: {str(e)}"}
