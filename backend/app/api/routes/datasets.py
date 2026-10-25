from fastapi import APIRouter, HTTPException

from app.schemas.evaluation import EvalCase, SaveCaseRequest, SaveCaseResponse
from app.services import evaluation_service as svc

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/{name}", response_model=list[EvalCase])
async def get_dataset(name: str) -> list[EvalCase]:
    """All questions in one dataset file."""
    try:
        return svc.load_dataset(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/cases", response_model=SaveCaseResponse, status_code=201)
async def save_case(request: SaveCaseRequest) -> SaveCaseResponse:
    """Save a question (with its checks) into a dataset so full evaluations include it."""
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be blank.")
    try:
        return await svc.save_case(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
