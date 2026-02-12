"""Abstract LLM adapter for Layer 2 AI analysis.

LLM provider is TBD (Claude / GPT-4V / self-hosted).
Adapter pattern allows swapping without changing the analysis pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LLMResponse:
    content: str          # Raw text response
    model: str            # Model identifier used
    input_tokens: int     # Token usage for cost tracking
    output_tokens: int
    cost_usd: float       # Estimated cost of this call


class LLMAdapter(ABC):
    """Abstract adapter for multimodal LLM providers."""

    @abstractmethod
    async def analyze_documents(
        self,
        system_prompt: str,
        user_prompt: str,
        pdf_paths: list[Path],
        max_pages_per_doc: int = 50,
    ) -> LLMResponse:
        """Send documents + prompt to LLM and get analysis.

        Args:
            system_prompt: System instructions for the analysis.
            user_prompt: User prompt with stock-specific context.
            pdf_paths: Paths to PDF documents to analyze.
            max_pages_per_doc: Max pages to send per document (truncate large annual reports).

        Returns:
            LLMResponse with the analysis text and usage metadata.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
