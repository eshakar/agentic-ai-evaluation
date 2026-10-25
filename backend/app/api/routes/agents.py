from fastapi import APIRouter, HTTPException

from app.schemas.evaluation import AskRequest, AskResponse
from app.services import evaluation_service as svc

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    """Ask one agent one question; get its answer, tool calls, timing and any checks back."""
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be blank.")
    try:
        return await svc.ask_agent(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
