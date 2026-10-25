"""Orchestrates an evaluation run: load cases -> run agent -> score -> aggregate -> persist."""

import asyncio
import json
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.agents import BaseAgent, get_agent
from app.core.config import get_settings
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


def load_dataset(name: str) -> list[EvalCase]:
    """Load a JSONL dataset (one EvalCase per line) from the datasets directory."""
    datasets_dir = get_settings().datasets_dir.resolve()
    path = (datasets_dir / name).resolve()
    if datasets_dir not in path.parents or not path.is_file():
        raise FileNotFoundError(f"Dataset '{name}' not found in {datasets_dir}")
    with path.open(encoding="utf-8") as f:
        return [EvalCase.model_validate_json(line) for line in f if line.strip()]


def list_datasets() -> list[str]:
    return sorted(p.name for p in get_settings().datasets_dir.glob("*.jsonl"))


_dataset_lock = asyncio.Lock()


def _slug(text: str, max_words: int = 6) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:max_words]
    return "-".join(words) or "question"


async def save_case(request: SaveCaseRequest) -> SaveCaseResponse:
    """Append a question to datasets/<name>.jsonl, creating the file if needed."""
    if not (request.expected_output or request.expected_tools is not None or request.rubric):
        raise ValueError(
            "Add at least one way to check the answer: an expected answer, "
            "expected tools, or grading rules for the AI judge."
        )
    path = get_settings().datasets_dir / request.dataset
    async with _dataset_lock:
        existing = load_dataset(request.dataset) if path.is_file() else []
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
        path.parent.mkdir(parents=True, exist_ok=True)
        needs_newline = (
            path.is_file() and path.stat().st_size > 0 and not path.read_bytes().endswith(b"\n")
        )
        with path.open("a", encoding="utf-8", newline="\n") as f:
            if needs_newline:
                f.write("\n")
            f.write(case.model_dump_json(exclude_defaults=True) + "\n")
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


def save_run(summary: RunSummary) -> Path:
    results_dir = get_settings().results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{summary.run_id}.json"
    path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_run(run_id: str) -> RunSummary | None:
    if not run_id.isalnum():
        return None
    path = get_settings().results_dir / f"{run_id}.json"
    if not path.is_file():
        return None
    return RunSummary.model_validate(json.loads(path.read_text(encoding="utf-8")))


def delete_run(run_id: str) -> bool:
    """Delete a saved run report. Returns False if there is no such run."""
    if not run_id.isalnum():
        return False
    path = get_settings().results_dir / f"{run_id}.json"
    if not path.is_file():
        return False
    path.unlink()
    logger.info("Deleted run %s", run_id)
    return True


def list_runs(limit: int = 20) -> list[RunListItem]:
    """Most recent saved runs first."""
    items: list[RunListItem] = []
    for path in get_settings().results_dir.glob("*.json"):
        try:
            items.append(RunListItem.model_validate_json(path.read_text(encoding="utf-8")))
        except ValueError:
            logger.warning("Skipping unreadable run file %s", path.name)
    items.sort(key=lambda r: r.created_at, reverse=True)
    return items[:limit]


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
    save_run(summary)
    logger.info(
        "Run %s: pass_rate=%.2f over %d cases", summary.run_id, summary.pass_rate, len(cases)
    )
    return summary
