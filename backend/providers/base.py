from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIProvider(ABC):
    def __init__(self, api_key: str = "", base_url: str = "", default_model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        """Generates completion text or JSON from the provider."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """Discovers available models from provider API, or returns verified catalog."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Validates API key and endpoint connectivity."""
        pass
