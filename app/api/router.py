from fastapi import APIRouter

from app.api.routes import evaluations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(evaluations.router)
