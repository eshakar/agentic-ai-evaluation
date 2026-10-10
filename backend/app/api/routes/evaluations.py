from fastapi import APIRouter, HTTPException

from app.agents import list_agents
from app.evaluators import get_evaluators, list_evaluators
from app.schemas.evaluation import RunListItem, RunRequest, RunSummary, ScoreRequest
from app.services import evaluation_service as svc

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/catalog")
async def catalog() -> dict[str, list[str]]:
    """Available agents, evaluators and datasets."""
    return {
        "agents": list_agents(),
        "evaluators": list_evaluators(),
        "datasets": svc.list_datasets(),
    }


@router.get("/runs", response_model=list[RunListItem])
async def list_runs(limit: int = 20) -> list[RunListItem]:
    """Most recent runs first."""
    return svc.list_runs(limit)


@router.post("/run", response_model=RunSummary)
async def run(request: RunRequest) -> RunSummary:
    """Run an agent over a dataset or inline cases and score every trace."""
    try:
        if request.cases:
            cases = request.cases
        elif request.dataset:
            cases = svc.load_dataset(request.dataset)
        else:
            raise ValueError("Provide either 'dataset' or 'cases'.")
        return await svc.run_evaluation(request.agent, cases, request.evaluators)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/score", response_model=RunSummary)
async def score(request: ScoreRequest) -> RunSummary:
    """Score pre-recorded traces from any external agent (no agent execution)."""
    try:
        evaluators = get_evaluators(request.evaluators)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = [await svc.score_case(i.case, i.trace, evaluators) for i in request.items]
    summary = svc.summarize(request.agent, request.evaluators, results)
    svc.save_run(summary)
    return summary


@router.get("/{run_id}", response_model=RunSummary)
async def get_run(run_id: str) -> RunSummary:
    summary = svc.load_run(run_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return summary
