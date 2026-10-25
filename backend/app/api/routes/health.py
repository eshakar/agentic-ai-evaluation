from fastapi import APIRouter

from app.core.config import get_settings
from app.db.store import storage_status

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "storage": storage_status(),
    }
