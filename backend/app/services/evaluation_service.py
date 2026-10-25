"""Orchestrates an evaluation run: load cases -> run agent -> score -> aggregate -> persist."""

import asyncio
import logging
import re
import uuid
from datetime import UTC, datetime

from app.agents import BaseAgent, get_agent
from app.core.config import get_settings
from app.db.store import get_store
from app.evaluators import BaseEvaluator, get_evaluators
from app.schemas.evaluation import (
    AgentTrace,
    AskRequest,
    AskResponse,
    CaseResult,
    EvalCase,
    MetricResult,
    RunListItem,
    RunSummary,
    SaveCaseRequest,
    SaveCaseResponse,
)

logger = logging.getLogger(__name__)


def _file_cases(name: str) -> list[EvalCase] | None:
    """Cases from datasets/<name> on disk, or None if there is no such (safe) file."""
    datasets_dir = get_settings().datasets_dir.resolve()
    path = (datasets_dir / name).resolve()
    if datasets_dir not in path.parents or not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        return [EvalCase.model_validate_json(line) for line in f if line.strip()]


def list_file_datasets() -> list[str]:
    """Dataset files in datasets/ (the built-in ones, plus saved files when not using MongoDB)."""
    return sorted(p.name for p in get_settings().datasets_dir.glob("*.jsonl"))


async def load_dataset(name: str) -> list[EvalCase]:
    """A dataset = its file's questions (if any) + questions saved to it in the store."""
    file_cases = _file_cases(name)
    saved = await get_store().saved_cases(name)
    if file_cases is None and not saved:
        raise FileNotFoundError(f"Dataset '{name}' not found")
    cases = list(file_cases or [])
    seen = {c.id for c in cases}
    cases += [c for c in saved if c.id not in seen]
    return cases


async def list_datasets() -> list[str]:
    return sorted(set(list_file_datasets()) | set(await get_store().saved_dataset_names()))


_dataset_lock = asyncio.Lock()


def _slug(text: str, max_words: int = 6) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:max_words]
    return "-".join(words) or "question"


async def save_case(request: SaveCaseRequest) -> SaveCaseResponse:
    """Save a question into a dataset (MongoDB, or the datasets/<name>.jsonl file)."""
    if not (request.expected_output or request.expected_tools is not None or request.rubric):
        raise ValueError(
            "Add at least one way to check the answer: an expected answer, "
            "expected tools, or grading rules for the AI judge."
        )
    async with _dataset_lock:
        try:
            existing = await load_dataset(request.dataset)
        except FileNotFoundError:
            existing = []
        taken = {c.id for c in existing}
        base = _slug(request.question)
        case_id, n = base, 2
        while case_id in taken:
            case_id, n = f"{base}-{n}", n + 1

        case = EvalCase(
            id=case_id,
            input=request.question.strip(),
            expected_output=(request.expected_output or "").strip() or None,
            expected_tools=request.expected_tools,
            rubric=(request.rubric or "").strip() or None,
            metadata={"category": request.category or "custom", "source": "ask-page"},
        )
        await get_store().add_case(request.dataset, case)
    return SaveCaseResponse(dataset=request.dataset, case=case, total_cases=len(existing) + 1)


async def _safe_evaluate(
    evaluator: BaseEvaluator, case: EvalCase, trace: AgentTrace
) -> MetricResult | None:
    """A broken evaluator (e.g. the LLM judge with no API key) fails its metric, not the run."""
    try:
        return await evaluator.evaluate(case, trace)
    except Exception as exc:
        logger.exception("Evaluator %s failed on case %s", evaluator.name, case.id)
        return MetricResult(
            name=evaluator.name,
            score=0.0,
            passed=False,
            reason=f"evaluator error: {type(exc).__name__}: {exc}"[:500],
        )


async def score_case(
    case: EvalCase, trace: AgentTrace, evaluators: list[BaseEvaluator]
) -> CaseResult:
    metrics = await asyncio.gather(*(_safe_evaluate(e, case, trace) for e in evaluators))
    return CaseResult(case_id=case.id, trace=trace, metrics=[m for m in metrics if m])


def summarize(agent: str, evaluator_names: list[str], results: list[CaseResult]) -> RunSummary:
    by_metric: dict[str, list[float]] = {}
    for r in results:
        for m in r.metrics:
            by_metric.setdefault(m.name, []).append(m.score)

    n = len(results)
    # Cases no evaluator applied to are left out of the pass rate rather than counted as passes.
    scored = [r for r in results if r.scored]
    return RunSummary(
        run_id=uuid.uuid4().hex[:12],
        created_at=datetime.now(UTC),
        agent=agent,
        evaluators=evaluator_names,
        num_cases=n,
        num_scored=len(scored),
        pass_rate=round(sum(r.passed for r in scored) / len(scored), 4) if scored else 0.0,
        mean_scores={k: round(sum(v) / len(v), 4) for k, v in sorted(by_metric.items())},
        mean_latency_ms=round(sum(r.trace.latency_ms for r in results) / n, 2) if n else 0.0,
        results=results,
    )


async def save_run(summary: RunSummary) -> None:
    await get_store().save_run(summary)


async def load_run(run_id: str) -> RunSummary | None:
    return await get_store().load_run(run_id)


async def delete_run(run_id: str) -> bool:
    """Delete a saved run report. Returns False if there is no such run."""
    deleted = await get_store().delete_run(run_id)
    if deleted:
        logger.info("Deleted run %s", run_id)
    return deleted


async def list_runs(limit: int = 20) -> list[RunListItem]:
    """Most recent saved runs first."""
    return await get_store().list_runs(limit)


async def _run_agent_safely(agent: BaseAgent, case: EvalCase) -> AgentTrace:
    """A crash or API error becomes an error on the trace, so it is reported, not raised."""
    try:
        return await agent.run(case.input)
    except Exception as exc:
        logger.exception("Agent %s failed on case %s", agent.name, case.id)
        return AgentTrace(output="", error=f"{type(exc).__name__}: {exc}"[:1000])


async def ask_agent(request: AskRequest) -> AskResponse:
    """Run one free-form question for a quick manual check. Not saved as a run.

    Checks run only when they can: an expected answer enables exact_match/contains,
    expected tools enable tool_sequence, and use_judge lets the AI judge grade it
    (against the rubric, or a default "is it correct and complete" rubric).
    """
    agent = get_agent(request.agent)
    question = request.question.strip()
    case = EvalCase(
        id="ask",
        input=question,
        expected_output=(request.expected_output or "").strip() or None,
        expected_tools=request.expected_tools,
        rubric=(request.rubric or "").strip() or None,
    )
    names = ["no_error"]
    if case.expected_output:
        names += ["exact_match", "contains"]
    if case.expected_tools is not None:
        names.append("tool_sequence")
    if request.use_judge:
        names.append("llm_judge")
    trace = await _run_agent_safely(agent, case)
    result = await score_case(case, trace, get_evaluators(names))
    return AskResponse(agent=request.agent, question=question, trace=trace, metrics=result.metrics)


async def run_evaluation(
    agent_name: str, cases: list[EvalCase], evaluator_names: list[str]
) -> RunSummary:
    agent = get_agent(agent_name)
    evaluators = get_evaluators(evaluator_names)
    semaphore = asyncio.Semaphore(get_settings().max_concurrency)

    async def _one(case: EvalCase) -> CaseResult:
        async with semaphore:
            trace = await _run_agent_safely(agent, case)
            return await score_case(case, trace, evaluators)

    results = await asyncio.gather(*(_one(c) for c in cases))
    summary = summarize(agent_name, evaluator_names, list(results))
    await save_run(summary)
    logger.info(
        "Run %s: pass_rate=%.2f over %d cases", summary.run_id, summary.pass_rate, len(cases)
    )
    return summary
