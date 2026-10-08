from abc import ABC, abstractmethod

from app.schemas.evaluation import AgentTrace, EvalCase, MetricResult


class BaseEvaluator(ABC):
    """Scores one agent trace against one eval case.

    Return None when the metric does not apply to the case (e.g. no expected output given),
    so it is skipped rather than counted as a failure.
    """

    name: str = "base"

    @abstractmethod
    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None: ...
