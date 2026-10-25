import pytest

from app.core.config import get_settings

KEY = "test-secret-key"


@pytest.fixture
def locked(monkeypatch):
    monkeypatch.setattr(get_settings(), "api_access_key", KEY)


def test_open_when_no_key_is_configured(client):
    assert client.get("/api/v1/evaluations/catalog").status_code == 200


def test_rejects_missing_and_wrong_key(client, locked):
    assert client.get("/api/v1/evaluations/catalog").status_code == 401
    r = client.get("/api/v1/evaluations/catalog", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "APIKey"


def test_accepts_correct_key_on_every_router(client, locked):
    h = {"X-API-Key": KEY}
    assert client.get("/api/v1/evaluations/catalog", headers=h).status_code == 200
    assert (
        client.post(
            "/api/v1/agents/ask", json={"agent": "echo", "question": "hi"}, headers=h
        ).status_code
        == 200
    )
    assert client.get("/api/v1/datasets/sample_eval.jsonl", headers=h).status_code == 200


def test_every_api_route_is_protected(client, locked):
    # Guards against adding a router later and forgetting the key check.
    from app.main import app

    for route in app.routes:
        path = getattr(route, "path", "")
        if path.startswith("/api/v1"):
            for method in route.methods - {"HEAD", "OPTIONS"}:
                url = path.replace("{run_id}", "abc").replace("{name}", "x.jsonl")
                r = client.request(method, url, json={})
                assert r.status_code == 401, f"{method} {path} is not protected"


def test_health_stays_public(client, locked):
    assert client.get("/health").status_code == 200
