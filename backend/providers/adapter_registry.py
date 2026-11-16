import json
from typing import Dict, Any, Optional
from backend.providers.base import BaseAIProvider
from backend.providers.openai_provider import OpenAIProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.claude_provider import ClaudeProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.ollama_provider import OllamaProvider
from backend.core.db import db
from backend.core.logger import logger

class ProviderRegistry:
    def __init__(self):
        self._instances: Dict[str, BaseAIProvider] = {}

    async def get_provider(self, provider_id: str) -> BaseAIProvider:
        """Retrieves or instantiates an AI provider based on current database credentials."""
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM ai_providers WHERE id = ?", (provider_id,))
            row = await cursor.fetchone()

        if not row:
            # Fallback to local Ollama if not found
            return OllamaProvider()

        p_type = row["type"]
        api_key = row["api_key"] or ""
        base_url = row["base_url"] or ""
        sel_model = row["selected_model"] or ""

        if p_type == "openai":
            return OpenAIProvider(api_key, base_url or "https://api.openai.com/v1", sel_model or "gpt-4o-mini")
        elif p_type == "gemini":
            return GeminiProvider(api_key, base_url, sel_model or "gemini-3.5-flash")
        elif p_type == "anthropic":
            return ClaudeProvider(api_key, base_url, sel_model or "claude-3-5-haiku")
        elif p_type == "groq":
            return GroqProvider(api_key, base_url, sel_model or "llama-3.3-70b-versatile")
        elif p_type == "ollama":
            return OllamaProvider(api_key, base_url or "http://localhost:11434", sel_model or "llama3.2")
        elif p_type in ("deepseek", "openrouter", "together", "custom"):
            return OpenAIProvider(api_key, base_url, sel_model or "default")
        else:
            return OllamaProvider()

    async def get_provider_for_task(self, task: str) -> tuple[BaseAIProvider, str]:
        """Returns (provider_instance, model_name) configured for the specific sub-task."""
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT provider_id, model FROM task_assignments WHERE task = ?", (task,))
            row = await cursor.fetchone()

        if row:
            provider = await self.get_provider(row["provider_id"])
            return provider, row["model"]

        # Default fallback: check if any cloud provider is enabled, otherwise use Ollama
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM ai_providers WHERE enabled = 1 AND api_key != '' LIMIT 1")
            active_p = await cursor.fetchone()

        if active_p:
            provider = await self.get_provider(active_p["id"])
            return provider, active_p["selected_model"]

        # 100% Free local Ollama fallback
        return OllamaProvider(), "llama3.2"

provider_registry = ProviderRegistry()
