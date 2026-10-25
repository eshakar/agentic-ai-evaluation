import json

from app.core.config import get_settings


def _isolate_datasets(tmp_path, monkeypatch):
    d = tmp_path / "datasets"
    d.mkdir()
    monkeypatch.setattr(get_settings(), "datasets_dir", d)
    return d


def test_save_case_creates_dataset_and_dedupes_ids(client, tmp_path, monkeypatch):
    d = _isolate_datasets(tmp_path, monkeypatch)
    payload = {"dataset": "mine.jsonl", "question": "What is 2 + 2?", "expected_output": "4"}
    first = client.post("/api/v1/datasets/cases", json=payload)
    second = client.post("/api/v1/datasets/cases", json=payload)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["case"]["id"] == "what-is-2-2"
    assert second.json()["case"]["id"] == "what-is-2-2-2"
    assert second.json()["total_cases"] == 2
    lines = (d / "mine.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["expected_output"] for line in lines] == ["4", "4"]
    # The saved dataset shows up for evaluation and loads cleanly.
    assert "mine.jsonl" in client.get("/api/v1/evaluations/catalog").json()["datasets"]
    assert len(client.get("/api/v1/datasets/mine.jsonl").json()) == 2


def test_save_case_requires_a_way_to_check(client, tmp_path, monkeypatch):
    _isolate_datasets(tmp_path, monkeypatch)
    r = client.post("/api/v1/datasets/cases", json={"question": "Anything?"})
    assert r.status_code == 422


def test_save_case_rejects_unsafe_dataset_names(client, tmp_path, monkeypatch):
    _isolate_datasets(tmp_path, monkeypatch)
    for bad in ["../evil.jsonl", "a/b.jsonl", "notes.txt", ".hidden.jsonl"]:
        r = client.post(
            "/api/v1/datasets/cases",
            json={"dataset": bad, "question": "q", "expected_output": "a"},
        )
        assert r.status_code == 422, bad


def test_delete_run(client):
    run = client.post(
        "/api/v1/evaluations/run",
        json={"agent": "echo", "cases": [{"id": "a", "input": "x"}], "evaluators": ["no_error"]},
    ).json()
    assert client.delete(f"/api/v1/evaluations/{run['run_id']}").status_code == 204
    assert client.get(f"/api/v1/evaluations/{run['run_id']}").status_code == 404
    assert client.delete(f"/api/v1/evaluations/{run['run_id']}").status_code == 404
    assert client.delete("/api/v1/evaluations/..%2Fx").status_code == 404
