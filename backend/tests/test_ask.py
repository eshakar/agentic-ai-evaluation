from app.agents.base import BaseAgent
from app.agents.registry import _AGENTS


def test_ask_returns_answer_and_no_error(client):
    r = client.post("/api/v1/agents/ask", json={"agent": "echo", "question": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["trace"]["output"] == "hello"
    assert [m["name"] for m in body["metrics"]] == ["no_error"]


def test_ask_checks_expected_answer(client):
    right = client.post(
        "/api/v1/agents/ask",
        json={"agent": "echo", "question": "Paris", "expected_output": "paris"},
    ).json()
    wrong = client.post(
        "/api/v1/agents/ask",
        json={"agent": "echo", "question": "Paris", "expected_output": "London"},
    ).json()
    assert all(m["passed"] for m in right["metrics"])
    assert not next(m for m in wrong["metrics"] if m["name"] == "contains")["passed"]


def test_ask_reports_agent_crash_instead_of_500(client, monkeypatch):
    class Broken(BaseAgent):
        name = "broken"

        async def run(self, task):
            raise RuntimeError("API quota exceeded")

    monkeypatch.setitem(_AGENTS, "broken", Broken)
    r = client.post("/api/v1/agents/ask", json={"agent": "broken", "question": "hi"})
    assert r.status_code == 200
    assert "API quota exceeded" in r.json()["trace"]["error"]
    assert r.json()["metrics"][0]["passed"] is False


def test_ask_rejects_blank_question_and_unknown_agent(client):
    assert (
        client.post("/api/v1/agents/ask", json={"agent": "echo", "question": "   "}).status_code
        == 422
    )
    assert (
        client.post("/api/v1/agents/ask", json={"agent": "nope", "question": "hi"}).status_code
        == 422
    )


def test_ask_is_not_saved_as_a_run(client):
    client.post("/api/v1/agents/ask", json={"agent": "echo", "question": "hi"})
    assert client.get("/api/v1/evaluations/runs").json() == []


def test_ask_runs_tool_check_and_judge_when_requested(client, monkeypatch):
    async def fake_judge(prompt):
        assert "Must mention Tokyo" in prompt  # the user's grading rules reach the judge
        return '{"reasoning": "Correct.", "score": 5}'

    monkeypatch.setattr("app.evaluators.llm_judge._judge_with_claude", fake_judge)
    body = client.post(
        "/api/v1/agents/ask",
        json={
            "agent": "echo",
            "question": "Tokyo",
            "expected_tools": [],
            "rubric": "Must mention Tokyo",
            "use_judge": True,
        },
    ).json()
    names = {m["name"]: m["passed"] for m in body["metrics"]}
    assert names == {"no_error": True, "tool_sequence": True, "llm_judge": True}
