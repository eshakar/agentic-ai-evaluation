from fastapi import APIRouter

from app.api.routes import agents, datasets, evaluations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(agents.router)
api_router.include_router(datasets.router)
api_router.include_router(evaluations.router)
