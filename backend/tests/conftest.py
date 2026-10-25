import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.services.gemini_client import get_gemini_client
from app.services.llm_client import get_client


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Tests use built-in defaults, never the developer's backend/.env (keys, providers, models),
    so they behave the same on every machine and never call a paid API by accident."""
    settings = get_settings()
    clean = Settings(_env_file=None, anthropic_api_key=None, gemini_api_key=None)
    for name in Settings.model_fields:
        monkeypatch.setattr(settings, name, getattr(clean, name))
    # Write run reports to a temp dir so tests never touch results/.
    monkeypatch.setattr(settings, "results_dir", tmp_path)
    get_client.cache_clear()
    get_gemini_client.cache_clear()
    yield
    get_client.cache_clear()
    get_gemini_client.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
