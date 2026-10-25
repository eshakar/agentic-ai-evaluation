"""Orchestrates an evaluation run: load cases -> run agent -> score -> aggregate -> persist."""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.agents import get_agent
from app.core.config import get_settings
from app.evaluators import BaseEvaluator, get_evaluators
from app.schemas.evaluation import (
    AgentTrace,
    CaseResult,
    EvalCase,
    MetricResult,
    RunListItem,
    RunSummary,
)

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 5


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


async def run_evaluation(
    agent_name: str, cases: list[EvalCase], evaluator_names: list[str]
) -> RunSummary:
    agent = get_agent(agent_name)
    evaluators = get_evaluators(evaluator_names)
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async def _one(case: EvalCase) -> CaseResult:
        async with semaphore:
            try:
                trace = await agent.run(case.input)
            except Exception as exc:
                logger.exception("Agent failed on case %s", case.id)
                trace = AgentTrace(output="", error=f"{type(exc).__name__}: {exc}")
            return await score_case(case, trace, evaluators)

    results = await asyncio.gather(*(_one(c) for c in cases))
    summary = summarize(agent_name, evaluator_names, list(results))
    save_run(summary)
    logger.info(
        "Run %s: pass_rate=%.2f over %d cases", summary.run_id, summary.pass_rate, len(cases)
    )
    return summary
