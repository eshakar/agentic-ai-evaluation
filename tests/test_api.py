def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_catalog(client):
    body = client.get("/api/v1/evaluations/catalog").json()
    assert "echo" in body["agents"]
    assert "llm_judge" in body["evaluators"]
    assert "sample_eval.jsonl" in body["datasets"]


def test_run_echo_agent_inline_cases_and_fetch(client):
    payload = {
        "agent": "echo",
        "cases": [
            {"id": "a", "input": "hello", "expected_output": "hello"},
            {"id": "b", "input": "hello", "expected_output": "bye"},
        ],
        "evaluators": ["exact_match"],
    }
    r = client.post("/api/v1/evaluations/run", json=payload)
    assert r.status_code == 200
    summary = r.json()
    assert summary["num_cases"] == 2
    assert summary["pass_rate"] == 0.5

    fetched = client.get(f"/api/v1/evaluations/{summary['run_id']}")
    assert fetched.status_code == 200


def test_score_external_traces(client):
    payload = {
        "items": [
            {
                "case": {
                    "id": "x",
                    "input": "2+2?",
                    "expected_output": "4",
                    "expected_tools": ["calculator"],
                },
                "trace": {"output": "4", "tool_calls": [{"name": "calculator"}]},
            }
        ],
        "evaluators": ["exact_match", "tool_sequence"],
    }
    r = client.post("/api/v1/evaluations/score", json=payload)
    assert r.status_code == 200
    assert r.json()["pass_rate"] == 1.0


def test_unknown_evaluator_returns_422(client):
    r = client.post(
        "/api/v1/evaluations/run",
        json={"agent": "echo", "cases": [{"id": "a", "input": "x"}], "evaluators": ["nope"]},
    )
    assert r.status_code == 422


def test_missing_dataset_returns_404(client):
    r = client.post("/api/v1/evaluations/run", json={"agent": "echo", "dataset": "missing.jsonl"})
    assert r.status_code == 404
