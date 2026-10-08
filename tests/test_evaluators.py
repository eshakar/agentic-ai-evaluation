from app.agents.tools import calculator
from app.evaluators.deterministic import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    LatencyEvaluator,
    ToolSequenceEvaluator,
)
from app.schemas.evaluation import AgentTrace, EvalCase, ToolCall


def _case(**kw) -> EvalCase:
    return EvalCase(id="c1", input="q", **kw)


async def test_exact_match_normalizes_case_and_punctuation():
    m = await ExactMatchEvaluator().evaluate(
        _case(expected_output="Paris"), AgentTrace(output="paris.")
    )
    assert m and m.passed


async def test_exact_match_skipped_without_expected_output():
    assert await ExactMatchEvaluator().evaluate(_case(), AgentTrace(output="x")) is None


async def test_contains():
    m = await ContainsEvaluator().evaluate(
        _case(expected_output="395"), AgentTrace(output="The answer is 395.")
    )
    assert m and m.passed


async def test_tool_sequence_in_order_passes():
    trace = AgentTrace(output="", tool_calls=[ToolCall(name="search"), ToolCall(name="calculator")])
    m = await ToolSequenceEvaluator().evaluate(
        _case(expected_tools=["search", "calculator"]), trace
    )
    assert m and m.passed and m.score == 1.0


async def test_tool_sequence_wrong_order_fails():
    trace = AgentTrace(output="", tool_calls=[ToolCall(name="calculator"), ToolCall(name="search")])
    m = await ToolSequenceEvaluator().evaluate(
        _case(expected_tools=["search", "calculator"]), trace
    )
    assert m and not m.passed


async def test_tool_sequence_expects_no_tools():
    trace = AgentTrace(output="", tool_calls=[ToolCall(name="calculator")])
    m = await ToolSequenceEvaluator().evaluate(_case(expected_tools=[]), trace)
    assert m and not m.passed


async def test_latency_budget_from_metadata():
    m = await LatencyEvaluator().evaluate(
        _case(metadata={"max_latency_ms": 100}), AgentTrace(output="", latency_ms=200)
    )
    assert m and not m.passed and m.score == 0.5


def test_calculator_tool():
    assert calculator("(17 * 23) + 4") == "395"
    assert calculator("7 / 2") == "3.5"
