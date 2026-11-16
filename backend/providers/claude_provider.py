import httpx
from typing import List, Dict, Any, Optional
from backend.providers.base import BaseAIProvider

class ClaudeProvider(BaseAIProvider):
    def __init__(self, api_key: str = "", base_url: str = "https://api.anthropic.com/v1", default_model: str = "claude-3-5-haiku-20241022"):
        super().__init__(api_key, base_url or "https://api.anthropic.com/v1", default_model)

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
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        sys_msg = system_prompt
        if json_mode:
            sys_msg += "\n\nCRITICAL: Respond ONLY with valid, parseable JSON. Do not include markdown codeblocks or conversational text."

        payload = {
            "model": selected_model,
            "system": sys_msg,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url.rstrip('/')}/messages", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Claude API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["content"][0]["text"]

    async def list_models(self) -> List[str]:
        return ["claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"]

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API key is missing"}
        try:
            # Quick check with haiku
            await self.complete(prompt="Hi", model="claude-3-5-haiku", max_tokens=5)
            return {"success": True, "models": await self.list_models(), "message": "Anthropic Claude connection verified!"}
        except Exception as e:
            return {"success": False, "message": str(e)}
