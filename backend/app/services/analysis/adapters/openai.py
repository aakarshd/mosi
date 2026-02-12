"""OpenAI GPT-4V multimodal LLM adapter — placeholder.

Alternative to Claude for Layer 2 analysis.
"""

from pathlib import Path

from app.services.analysis.adapters.base import LLMAdapter, LLMResponse


class OpenAIAdapter(LLMAdapter):

    def __init__(self, api_key: str = "", model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def analyze_documents(
        self,
        system_prompt: str,
        user_prompt: str,
        pdf_paths: list[Path],
        max_pages_per_doc: int = 50,
    ) -> LLMResponse:
        raise NotImplementedError("OpenAI adapter pending LLM provider selection")

    async def health_check(self) -> bool:
        return False
