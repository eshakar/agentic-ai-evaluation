"""Thin wrapper around the Anthropic SDK shared by the agent and the LLM judge."""

from functools import lru_cache
from typing import Any

from anthropic import AsyncAnthropic

from app.core.config import get_settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"


@lru_cache
def get_client() -> AsyncAnthropic:
    settings = get_settings()
    # With no key in settings, the SDK falls back to ANTHROPIC_API_KEY / `ant auth login` profiles.
    if settings.anthropic_api_key:
        return AsyncAnthropic(api_key=settings.anthropic_api_key)
    return AsyncAnthropic()


async def create_message(*, model: str, effort: str, max_tokens: int = 16000, **kwargs: Any) -> Any:
    """Call the Messages API with effort set and, optionally, server-side refusal fallbacks."""
    settings = get_settings()
    client = get_client()
    output_config = {"effort": effort, **kwargs.pop("output_config", {})}

    if settings.enable_fallbacks:
        # If a request is refused by a safety classifier, the API retries it on a fallback model.
        return await client.beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            output_config=output_config,
            betas=[FALLBACK_BETA],
            extra_body={"fallbacks": "default"},
            **kwargs,
        )
    return await client.messages.create(
        model=model, max_tokens=max_tokens, output_config=output_config, **kwargs
    )
