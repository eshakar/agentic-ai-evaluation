from fastapi import APIRouter, Depends

from app.api.routes import agents, datasets, evaluations
from app.core.security import require_api_key

# Every /api/v1 route needs the access key (when API_ACCESS_KEY is set). /health stays public.
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])
api_router.include_router(agents.router)
api_router.include_router(datasets.router)
api_router.include_router(evaluations.router)
