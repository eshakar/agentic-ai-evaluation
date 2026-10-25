"""Access key for the API. When API_ACCESS_KEY is set, every /api/v1 request must send it in the
X-API-Key header. When it is not set (local development), the API stays open."""

import hmac

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

# Declared with FastAPI's security helper so /docs shows an "Authorize" button for it.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str | None = Security(api_key_header)) -> None:
    expected = get_settings().api_access_key
    if not expected:
        return
    # Constant-time comparison, so the key can't be guessed from response timing.
    if not key or not hmac.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key (send it in the X-API-Key header).",
            headers={"WWW-Authenticate": "APIKey"},
        )
