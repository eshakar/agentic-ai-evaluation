"""Offline tests for the Gemini agent and judge, using fake responses built from real SDK types."""

import json

from google.genai import types

from app.agents.gemini_agent import GeminiToolAgent
from app.core.config import get_settings
from app.evaluators.llm_judge import LLMJudgeEvaluator
from app.schemas.evaluation import AgentTrace, EvalCase


def _response(*parts: types.Part, finish: str = "STOP") -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=list(parts)), finish_reason=finish
            )
        ],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=10, candidates_token_count=5
        ),
    )


class _FakeModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": list(contents), "config": config})
        return self.responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.models = _FakeModels(responses)
        self.aio = self


def _install(monkeypatch, target: str, responses) -> _FakeClient:
    fake = _FakeClient(responses)
    monkeypatch.setattr(target, lambda: fake)
    return fake


async def test_gemini_agent_runs_tool_and_records_trajectory(monkeypatch):
    fake = _install(
        monkeypatch,
        "app.agents.gemini_agent.get_gemini_client",
        [
            _response(
                types.Part(
                    function_call=types.FunctionCall(
                        id="c1", name="calculator", args={"expression": "(17 * 23) + 4"}
                    )
                )
            ),
            _response(types.Part.from_text(text="395")),
        ],
    )
    trace = await GeminiToolAgent().run("What is (17 * 23) + 4?")

    assert trace.output == "395"
    assert trace.error is None
    assert trace.turns == 2
    assert [(c.name, c.output) for c in trace.tool_calls] == [("calculator", "395")]
    assert trace.input_tokens == 20 and trace.output_tokens == 10
    # Second request must carry the model's turn and our function result, matched by call id.
    sent = fake.models.calls[1]["contents"]
    assert sent[1].role == "model"
    response_part = sent[2].parts[0].function_response
    assert response_part.id == "c1" and response_part.response == {"result": "395"}
    # Automatic function calling is off so we record every tool call ourselves.
    assert fake.models.calls[0]["config"].automatic_function_calling.disable is True


async def test_gemini_agent_reports_tool_errors_to_model(monkeypatch):
    fake = _install(
        monkeypatch,
        "app.agents.gemini_agent.get_gemini_client",
        [
            _response(
                types.Part(
                    function_call=types.FunctionCall(
                        id="c1", name="calculator", args={"expression": "1/0"}
                    )
                )
            ),
            _response(types.Part.from_text(text="Division by zero is undefined.")),
        ],
    )
    trace = await GeminiToolAgent().run("10/0?")
    assert trace.error is None
    sent = fake.models.calls[1]["contents"][2].parts[0].function_response.response
    assert "error" in sent


async def test_gemini_agent_flags_truncated_answer(monkeypatch):
    _install(
        monkeypatch,
        "app.agents.gemini_agent.get_gemini_client",
        [_response(types.Part.from_text(text="The answer is 3"), finish="MAX_TOKENS")],
    )
    trace = await GeminiToolAgent().run("q")
    assert trace.error == "max_tokens"
    assert trace.output == ""


async def test_gemini_agent_ignores_thought_text(monkeypatch):
    _install(
        monkeypatch,
        "app.agents.gemini_agent.get_gemini_client",
        [
            _response(
                types.Part(text="let me think...", thought=True),
                types.Part.from_text(text="Tokyo"),
            )
        ],
    )
    trace = await GeminiToolAgent().run("Capital of Japan?")
    assert trace.output == "Tokyo"


async def test_llm_judge_uses_gemini_when_configured(monkeypatch):
    monkeypatch.setattr(get_settings(), "judge_provider", "gemini")
    fake = _install(
        monkeypatch,
        "app.evaluators.llm_judge.get_gemini_client",
        [_response(types.Part.from_text(text=json.dumps({"reasoning": "Correct.", "score": 5})))],
    )
    metric = await LLMJudgeEvaluator().evaluate(
        EvalCase(id="a", input="2+2?", expected_output="4"), AgentTrace(output="4")
    )
    assert metric is not None and metric.passed and metric.score == 1.0
    config = fake.models.calls[0]["config"]
    assert config.response_mime_type == "application/json"


def test_gemini_agent_is_registered(client):
    assert "gemini" in client.get("/api/v1/evaluations/catalog").json()["agents"]
