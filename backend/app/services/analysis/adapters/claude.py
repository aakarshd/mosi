"""Claude (Anthropic) multimodal LLM adapter.

Sends PDF pages as images to Claude's vision capability.
Requires: anthropic SDK, API key.
"""

import base64
import logging
from pathlib import Path

from app.services.analysis.adapters.base import LLMAdapter, LLMResponse

logger = logging.getLogger(__name__)

# Cost estimates per 1M tokens (Claude Sonnet 4.5 pricing as reference)
INPUT_COST_PER_1M = 3.00
OUTPUT_COST_PER_1M = 15.00


class ClaudeAdapter(LLMAdapter):

    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-5-20250929"):
        self.api_key = api_key
        self.model = model

    async def analyze_documents(
        self,
        system_prompt: str,
        user_prompt: str,
        pdf_paths: list[Path],
        max_pages_per_doc: int = 50,
    ) -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic SDK not installed. Run: pip install anthropic")

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        # Build content blocks: text prompt + PDF documents as base64
        content = [{"type": "text", "text": user_prompt}]

        for pdf_path in pdf_paths:
            if not pdf_path.exists():
                logger.warning(f"PDF not found: {pdf_path}")
                continue

            pdf_bytes = pdf_path.read_bytes()
            b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64,
                },
                "cache_control": {"type": "ephemeral"},
            })

        response = await client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1_000_000 * INPUT_COST_PER_1M) + (output_tokens / 1_000_000 * OUTPUT_COST_PER_1M)

        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    async def health_check(self) -> bool:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False
