"""Regression tests for bugs found in the 2026-10-25 bug check."""

import pytest

from app.agents.tools import calculator
from app.core.config import BASE_DIR, get_settings
from app.evaluators.base import BaseEvaluator
from app.schemas.evaluation import AgentTrace, EvalCase
from app.services.evaluation_service import score_case, summarize


class _BrokenEvaluator(BaseEvaluator):
    name = "broken"

    async def evaluate(self, case, trace):
        raise RuntimeError("no API key")


async def test_failing_evaluator_fails_its_metric_not_the_run():
    result = await score_case(
        EvalCase(id="a", input="x"), AgentTrace(output="x"), [_BrokenEvaluator()]
    )
    (metric,) = result.metrics
    assert not metric.passed
    assert "no API key" in metric.reason


def test_llm_judge_without_key_returns_200(client, monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("Could not resolve authentication method")

    monkeypatch.setattr("app.evaluators.llm_judge.create_message", boom)
    r = client.post(
        "/api/v1/evaluations/run",
        json={"agent": "echo", "cases": [{"id": "a", "input": "hi"}], "evaluators": ["llm_judge"]},
    )
    assert r.status_code == 200
    assert r.json()["results"][0]["metrics"][0]["passed"] is False


def test_unscored_cases_do_not_inflate_pass_rate(client):
    r = client.post(
        "/api/v1/evaluations/run",
        json={
            "agent": "echo",
            "cases": [
                {"id": "a", "input": "hi"},
                {"id": "b", "input": "yo", "expected_output": "no"},
            ],
            "evaluators": ["exact_match"],
        },
    )
    body = r.json()
    assert body["num_scored"] == 1
    assert body["pass_rate"] == 0.0


def test_no_scored_cases_gives_zero_not_crash():
    summary = summarize("echo", ["exact_match"], [])
    assert summary.pass_rate == 0.0 and summary.num_scored == 0


def test_paths_do_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_settings().datasets_dir == BASE_DIR / "datasets"
    assert (BASE_DIR / "datasets" / "sample_eval.jsonl").is_file()


@pytest.mark.parametrize("expr", ["9**9**9", "2**100000", "10**5000"])
def test_calculator_rejects_huge_powers(expr):
    with pytest.raises(ValueError):
        calculator(expr)


def test_calculator_still_handles_normal_math():
    assert calculator("2**10") == "1024"
    assert calculator("1.5 * 4") == "6"
