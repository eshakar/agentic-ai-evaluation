"""Shared Google Gemini client (google-genai SDK), used by the Gemini agent and the LLM judge."""

from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import get_settings

# The free tier allows only a few requests per minute, and busy models return 503.
# Back off and retry (5s, 10s, 20s, 40s) to ride out a per-minute limit. Kept short on purpose:
# a *daily* quota (GenerateRequestsPerDay...) won't reset for hours, so retrying longer just hangs.
RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=5,
    initial_delay=5.0,
    max_delay=60.0,
    exp_base=2.0,
    jitter=1.0,
    http_status_codes=[429, 500, 503, 504],
)


@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    http_options = types.HttpOptions(retry_options=RETRY_OPTIONS)
    # With no key in settings, the SDK reads GEMINI_API_KEY / GOOGLE_API_KEY from the environment.
    if settings.gemini_api_key:
        return genai.Client(api_key=settings.gemini_api_key, http_options=http_options)
    return genai.Client(http_options=http_options)
