from app.evaluators.base import BaseEvaluator
from app.evaluators.deterministic import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    LatencyEvaluator,
    NoErrorEvaluator,
    ToolSequenceEvaluator,
)
from app.evaluators.llm_judge import LLMJudgeEvaluator

_EVALUATORS: dict[str, type[BaseEvaluator]] = {
    cls.name: cls
    for cls in (
        ExactMatchEvaluator,
        ContainsEvaluator,
        ToolSequenceEvaluator,
        LatencyEvaluator,
        NoErrorEvaluator,
        LLMJudgeEvaluator,
    )
}


def list_evaluators() -> list[str]:
    return sorted(_EVALUATORS)


def get_evaluators(names: list[str]) -> list[BaseEvaluator]:
    unknown = [n for n in names if n not in _EVALUATORS]
    if unknown:
        raise ValueError(f"Unknown evaluator(s) {unknown}. Available: {list_evaluators()}")
    return [_EVALUATORS[n]() for n in names]
