"""Cheap, deterministic metrics. Prefer these over an LLM judge whenever they suffice."""

import re

from app.evaluators.base import BaseEvaluator
from app.schemas.evaluation import AgentTrace, EvalCase, MetricResult


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s.]", "", text.lower())).strip().rstrip(".")


class ExactMatchEvaluator(BaseEvaluator):
    name = "exact_match"

    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None:
        if case.expected_output is None:
            return None
        ok = _normalize(trace.output) == _normalize(case.expected_output)
        return MetricResult(name=self.name, score=float(ok), passed=ok)


class ContainsEvaluator(BaseEvaluator):
    """Passes when the expected answer appears anywhere in the agent's output."""

    name = "contains"

    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None:
        if case.expected_output is None:
            return None
        ok = _normalize(case.expected_output) in _normalize(trace.output)
        return MetricResult(name=self.name, score=float(ok), passed=ok)


class ToolSequenceEvaluator(BaseEvaluator):
    """Trajectory metric: did the agent call the expected tools, in the expected order?

    Score is the F1 between expected and actual tool names; it passes only when the
    expected tools appear as an in-order subsequence of the actual calls.
    """

    name = "tool_sequence"

    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None:
        if case.expected_tools is None:
            return None
        expected = case.expected_tools
        actual = [c.name for c in trace.tool_calls]

        if not expected:
            ok = not actual
            reason = "no tools expected" + ("" if ok else f", but called {actual}")
            return MetricResult(name=self.name, score=float(ok), passed=ok, reason=reason)

        hits = sum(min(expected.count(t), actual.count(t)) for t in set(expected))
        precision = hits / len(actual) if actual else 0.0
        recall = hits / len(expected)
        f1 = 2 * precision * recall / (precision + recall) if hits else 0.0

        it = iter(actual)
        in_order = all(tool in it for tool in expected)
        return MetricResult(
            name=self.name,
            score=round(f1, 4),
            passed=in_order,
            reason=f"expected={expected} actual={actual}",
        )


class LatencyEvaluator(BaseEvaluator):
    """Passes when the run finishes under `max_latency_ms` (per case via metadata, default 30s)."""

    name = "latency"
    default_budget_ms = 30_000.0

    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None:
        budget = float(case.metadata.get("max_latency_ms", self.default_budget_ms))
        ok = trace.latency_ms <= budget
        score = 1.0 if ok else max(0.0, budget / trace.latency_ms)
        return MetricResult(
            name=self.name,
            score=round(score, 4),
            passed=ok,
            reason=f"{trace.latency_ms:.0f}ms / budget {budget:.0f}ms",
        )


class NoErrorEvaluator(BaseEvaluator):
    """Fails when the agent errored, was refused, or hit its turn limit."""

    name = "no_error"

    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None:
        ok = trace.error is None
        return MetricResult(name=self.name, score=float(ok), passed=ok, reason=trace.error or "")
